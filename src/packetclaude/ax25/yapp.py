"""
YAPP (Yet Another Packet Protocol) implementation for file transfers
Standard amateur radio file transfer protocol

Reference: YAPP specification
"""
import logging
import hashlib
import time
from enum import Enum
from typing import Optional, Callable, Dict
from dataclasses import dataclass


logger = logging.getLogger(__name__)


# YAPP Control Characters
class YAPPControl:
    """YAPP protocol control characters"""
    ENQ = 0x05  # Enquiry - request to send
    ACK = 0x06  # Acknowledge
    NAK = 0x15  # Negative Acknowledge
    SOH = 0x01  # Start of Header
    STX = 0x02  # Start of Data
    ETX = 0x03  # End of Data
    EOT = 0x04  # End of Transmission
    CAN = 0x18  # Cancel


class YAPPState(Enum):
    """YAPP transfer states"""
    IDLE = "idle"
    WAIT_ACK = "wait_ack"
    RECEIVING_HEADER = "receiving_header"
    SENDING_HEADER = "sending_header"
    RECEIVING_DATA = "receiving_data"
    SENDING_DATA = "sending_data"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class YAPPHeader:
    """YAPP file header"""
    filename: str
    file_size: int
    timestamp: int = 0

    def encode(self) -> bytes:
        """
        Encode header to YAPP format

        Header format: <filename> <size> <timestamp>\r
        Max 128 bytes
        """
        header_str = f"{self.filename} {self.file_size} {self.timestamp}\r"
        if len(header_str) > 128:
            # Truncate filename if needed
            max_filename_len = 128 - len(str(self.file_size)) - len(str(self.timestamp)) - 4
            self.filename = self.filename[:max_filename_len]
            header_str = f"{self.filename} {self.file_size} {self.timestamp}\r"

        # Pad to 128 bytes
        header_bytes = header_str.encode('ascii', errors='replace')
        if len(header_bytes) < 128:
            header_bytes += b'\x00' * (128 - len(header_bytes))

        return header_bytes[:128]

    @staticmethod
    def decode(data: bytes) -> Optional['YAPPHeader']:
        """
        Decode YAPP header from bytes

        Args:
            data: Header bytes (128 bytes)

        Returns:
            YAPPHeader object or None if invalid
        """
        try:
            # Remove null padding and decode
            header_str = data.rstrip(b'\x00').decode('ascii', errors='ignore').strip()

            # Parse header
            parts = header_str.split()
            if len(parts) < 2:
                return None

            filename = parts[0]
            file_size = int(parts[1])
            timestamp = int(parts[2]) if len(parts) >= 3 else 0

            return YAPPHeader(filename, file_size, timestamp)
        except Exception as e:
            logger.error(f"Failed to decode YAPP header: {e}")
            return None


class YAPPTransfer:
    """
    Represents a single YAPP file transfer (upload or download)
    """

    BLOCK_SIZE = 128  # YAPP uses 128-byte blocks
    TIMEOUT = 30  # Timeout in seconds
    MAX_RETRIES = 3

    def __init__(self, is_upload: bool, callsign: str):
        """
        Initialize YAPP transfer

        Args:
            is_upload: True if receiving (upload), False if sending (download)
            callsign: Remote callsign
        """
        self.is_upload = is_upload
        self.callsign = callsign
        self.state = YAPPState.IDLE

        # Transfer data
        self.header: Optional[YAPPHeader] = None
        self.file_data = bytearray()
        self.current_block = 0
        self.expected_blocks = 0

        # Timing and retries
        self.last_activity = time.time()
        self.retry_count = 0

        # Callbacks
        self.on_complete: Optional[Callable[[bytes, str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_progress: Optional[Callable[[int, int], None]] = None

    def start_upload(self) -> bytes:
        """
        Start receiving a file (upload from remote)

        Returns:
            Response packet (ACK to send)
        """
        logger.info(f"Starting YAPP upload from {self.callsign}")
        self.state = YAPPState.WAIT_ACK
        self.last_activity = time.time()
        # Send ACK to indicate ready to receive
        return bytes([YAPPControl.ACK])

    def start_download(self, filename: str, file_data: bytes) -> bytes:
        """
        Start sending a file (download to remote)

        Args:
            filename: Name of file
            file_data: File contents

        Returns:
            ENQ packet to initiate transfer
        """
        logger.info(f"Starting YAPP download to {self.callsign}: {filename}")

        # Create header
        self.header = YAPPHeader(
            filename=filename,
            file_size=len(file_data),
            timestamp=int(time.time())
        )
        self.file_data = bytearray(file_data)
        self.expected_blocks = (len(file_data) + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE
        self.current_block = 0

        self.state = YAPPState.WAIT_ACK
        self.last_activity = time.time()

        # Send ENQ to request permission to send
        return bytes([YAPPControl.ENQ])

    def handle_packet(self, data: bytes) -> Optional[bytes]:
        """
        Handle incoming YAPP packet

        Args:
            data: Incoming packet data

        Returns:
            Response packet to send, or None
        """
        self.last_activity = time.time()

        if not data:
            return None

        control_byte = data[0]

        # Handle based on current state
        if self.state == YAPPState.WAIT_ACK:
            if control_byte == YAPPControl.ACK:
                if self.is_upload:
                    # We're receiving - move to header reception
                    self.state = YAPPState.RECEIVING_HEADER
                    return None  # Wait for header
                else:
                    # We're sending - send header
                    self.state = YAPPState.SENDING_HEADER
                    return self._send_header()
            elif control_byte == YAPPControl.NAK:
                logger.warning(f"Received NAK in WAIT_ACK state")
                return self._handle_nak()
            elif control_byte == YAPPControl.CAN:
                return self._handle_cancel()

        elif self.state == YAPPState.RECEIVING_HEADER:
            if control_byte == YAPPControl.SOH:
                # Header packet
                if len(data) >= 129:  # SOH + 128 bytes
                    header_data = data[1:129]
                    self.header = YAPPHeader.decode(header_data)

                    if self.header:
                        logger.info(f"Received header: {self.header.filename}, {self.header.file_size} bytes")
                        self.expected_blocks = (self.header.file_size + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE
                        self.state = YAPPState.RECEIVING_DATA
                        return bytes([YAPPControl.ACK])
                    else:
                        logger.error("Failed to decode header")
                        return bytes([YAPPControl.NAK])

        elif self.state == YAPPState.RECEIVING_DATA:
            if control_byte == YAPPControl.STX:
                # Data block
                if len(data) >= 2:
                    block_data = data[1:]
                    self.file_data.extend(block_data)
                    self.current_block += 1

                    # Report progress
                    if self.on_progress:
                        self.on_progress(self.current_block, self.expected_blocks)

                    # Check if we're done
                    if len(self.file_data) >= self.header.file_size:
                        # Truncate to exact size
                        self.file_data = self.file_data[:self.header.file_size]
                        logger.info(f"File transfer complete: {len(self.file_data)} bytes")
                        self.state = YAPPState.COMPLETE

                        if self.on_complete:
                            self.on_complete(bytes(self.file_data), self.header.filename)

                    return bytes([YAPPControl.ACK])

            elif control_byte == YAPPControl.ETX:
                # End of transfer
                if len(self.file_data) >= self.header.file_size:
                    self.state = YAPPState.COMPLETE
                    logger.info("Received ETX, transfer complete")
                    return bytes([YAPPControl.ACK])
                else:
                    logger.error(f"ETX received but file incomplete: {len(self.file_data)}/{self.header.file_size}")
                    return bytes([YAPPControl.NAK])

        elif self.state == YAPPState.SENDING_HEADER:
            if control_byte == YAPPControl.ACK:
                # Header acknowledged, start sending data
                self.state = YAPPState.SENDING_DATA
                return self._send_next_block()
            elif control_byte == YAPPControl.NAK:
                return self._handle_nak()

        elif self.state == YAPPState.SENDING_DATA:
            if control_byte == YAPPControl.ACK:
                # Block acknowledged
                self.current_block += 1

                # Report progress
                if self.on_progress:
                    self.on_progress(self.current_block, self.expected_blocks)

                # Send next block or finish
                if self.current_block >= self.expected_blocks:
                    # All blocks sent, send ETX
                    self.state = YAPPState.COMPLETE
                    logger.info("All blocks sent, transfer complete")
                    return bytes([YAPPControl.ETX])
                else:
                    return self._send_next_block()

            elif control_byte == YAPPControl.NAK:
                return self._handle_nak()

        return None

    def _send_header(self) -> bytes:
        """Send file header"""
        if not self.header:
            return bytes([YAPPControl.CAN])

        header_bytes = self.header.encode()
        packet = bytes([YAPPControl.SOH]) + header_bytes
        logger.debug(f"Sending header: {self.header.filename}")
        return packet

    def _send_next_block(self) -> bytes:
        """Send next data block"""
        if self.current_block >= self.expected_blocks:
            return bytes([YAPPControl.ETX])

        # Calculate block position
        start = self.current_block * self.BLOCK_SIZE
        end = min(start + self.BLOCK_SIZE, len(self.file_data))
        block_data = self.file_data[start:end]

        # Pad if necessary (last block might be shorter)
        if len(block_data) < self.BLOCK_SIZE:
            block_data = block_data + b'\x00' * (self.BLOCK_SIZE - len(block_data))

        packet = bytes([YAPPControl.STX]) + block_data
        logger.debug(f"Sending block {self.current_block + 1}/{self.expected_blocks}")
        return packet

    def _handle_nak(self) -> bytes:
        """Handle NAK - retry current operation"""
        self.retry_count += 1

        if self.retry_count >= self.MAX_RETRIES:
            logger.error(f"Max retries exceeded ({self.MAX_RETRIES})")
            self.state = YAPPState.ERROR
            if self.on_error:
                self.on_error("Max retries exceeded")
            return bytes([YAPPControl.CAN])

        logger.warning(f"Received NAK, retry {self.retry_count}/{self.MAX_RETRIES}")

        # Retry based on current state
        if self.state == YAPPState.SENDING_HEADER:
            return self._send_header()
        elif self.state == YAPPState.SENDING_DATA:
            return self._send_next_block()

        return None

    def _handle_cancel(self) -> None:
        """Handle cancel request"""
        logger.warning(f"Transfer cancelled by remote station")
        self.state = YAPPState.ERROR
        if self.on_error:
            self.on_error("Transfer cancelled by remote station")
        return None

    def is_timeout(self) -> bool:
        """Check if transfer has timed out"""
        return (time.time() - self.last_activity) > self.TIMEOUT

    def cancel(self) -> bytes:
        """Cancel the transfer"""
        logger.info(f"Cancelling transfer with {self.callsign}")
        self.state = YAPPState.ERROR
        return bytes([YAPPControl.CAN])

    def is_complete(self) -> bool:
        """Check if transfer is complete"""
        return self.state == YAPPState.COMPLETE

    def is_error(self) -> bool:
        """Check if transfer is in error state"""
        return self.state == YAPPState.ERROR

    def get_progress(self) -> tuple[int, int]:
        """
        Get transfer progress

        Returns:
            Tuple of (current_block, total_blocks)
        """
        return (self.current_block, self.expected_blocks)


class YAPPManager:
    """
    Manages YAPP transfers for multiple connections
    """

    def __init__(self):
        """Initialize YAPP manager"""
        self.transfers: Dict[str, YAPPTransfer] = {}

    def start_upload(self, callsign: str) -> Optional[bytes]:
        """
        Start receiving a file from a callsign

        Args:
            callsign: Remote callsign

        Returns:
            Response packet to send
        """
        if callsign in self.transfers:
            logger.warning(f"Transfer already in progress for {callsign}")
            return None

        transfer = YAPPTransfer(is_upload=True, callsign=callsign)
        self.transfers[callsign] = transfer
        return transfer.start_upload()

    def start_download(self, callsign: str, filename: str, file_data: bytes) -> Optional[bytes]:
        """
        Start sending a file to a callsign

        Args:
            callsign: Remote callsign
            filename: File name
            file_data: File contents

        Returns:
            ENQ packet to initiate transfer
        """
        if callsign in self.transfers:
            logger.warning(f"Transfer already in progress for {callsign}")
            return None

        transfer = YAPPTransfer(is_upload=False, callsign=callsign)
        self.transfers[callsign] = transfer
        return transfer.start_download(filename, file_data)

    def handle_packet(self, callsign: str, data: bytes) -> Optional[bytes]:
        """
        Handle incoming YAPP packet

        Args:
            callsign: Remote callsign
            data: Packet data

        Returns:
            Response packet to send, or None
        """
        transfer = self.transfers.get(callsign)
        if not transfer:
            # Check if this is an ENQ to start a new transfer
            if data and data[0] == YAPPControl.ENQ:
                logger.info(f"Received ENQ from {callsign}, starting upload")
                return self.start_upload(callsign)
            return None

        response = transfer.handle_packet(data)

        # Clean up completed or errored transfers
        if transfer.is_complete() or transfer.is_error():
            del self.transfers[callsign]

        return response

    def get_transfer(self, callsign: str) -> Optional[YAPPTransfer]:
        """Get active transfer for callsign"""
        return self.transfers.get(callsign)

    def cancel_transfer(self, callsign: str) -> Optional[bytes]:
        """Cancel a transfer"""
        transfer = self.transfers.get(callsign)
        if transfer:
            response = transfer.cancel()
            del self.transfers[callsign]
            return response
        return None

    def cleanup_timeouts(self):
        """Remove timed out transfers"""
        to_remove = []
        for callsign, transfer in self.transfers.items():
            if transfer.is_timeout():
                logger.warning(f"Transfer with {callsign} timed out")
                if transfer.on_error:
                    transfer.on_error("Transfer timed out")
                to_remove.append(callsign)

        for callsign in to_remove:
            del self.transfers[callsign]
