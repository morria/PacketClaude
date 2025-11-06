#!/usr/bin/env python3
"""
Simple test script to debug AX.25 packet radio connectivity
Listens for connections, sends a welcome message, then waits
"""
import sys
import time
import logging

# Add src to path
sys.path.insert(0, 'src')

from packetclaude.ax25.kiss import KISSClient
from packetclaude.ax25.protocol import AX25Frame

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KISS_HOST = 'localhost'
KISS_PORT = 8001
MY_CALL = 'W2ASM'
MY_SSID = 10

def main():
    logger.info("Starting simple TNC test...")
    logger.info(f"My callsign: {MY_CALL}-{MY_SSID}")

    # Connect to KISS TNC
    kiss = KISSClient(KISS_HOST, KISS_PORT)
    try:
        kiss.connect()
        logger.info(f"Connected to Direwolf KISS on {KISS_HOST}:{KISS_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to KISS TNC: {e}")
        return 1

    logger.info("Listening for incoming connections...")
    logger.info("Press Ctrl-C to exit")

    try:
        while True:
            # Receive frame with 1 second timeout
            frame_data = kiss.receive_frame(timeout=1.0)

            if not frame_data:
                continue

            # Decode frame
            try:
                frame = AX25Frame.decode(frame_data)
                logger.info(f"Received: {frame.source.callsign.strip()}-{frame.source.ssid} -> {frame.destination.callsign.strip()}-{frame.destination.ssid}")

                # Check if frame is addressed to us
                if frame.destination.callsign.strip() != MY_CALL:
                    logger.debug(f"Frame not for us (dest={frame.destination.callsign.strip()})")
                    continue

                # Handle SABM (connection request)
                if frame.is_sabm_frame():
                    logger.info(f"*** CONNECTION REQUEST from {frame.source.callsign.strip()}-{frame.source.ssid}")

                    # Send UA (Unnumbered Acknowledge)
                    ua_frame = AX25Frame.create_ua_frame(
                        frame.source.callsign.strip(),
                        MY_CALL,
                        frame.source.ssid,
                        MY_SSID
                    )
                    kiss.send_frame(ua_frame.encode())
                    logger.info("Sent UA (connection accepted)")

                    # Send welcome message as UI frame
                    welcome = b"*** SIMPLE TNC TEST ***\rConnection successful!\rIf you can read this, the radio link is working.\r\r"
                    logger.info(f"Creating UI frame: remote={frame.source.callsign.strip()}-{frame.source.ssid}, local={MY_CALL}-{MY_SSID}")
                    ui_frame = AX25Frame.create_ui_frame(
                        frame.source.callsign.strip(),
                        MY_CALL,
                        welcome,
                        frame.source.ssid,
                        MY_SSID
                    )
                    encoded_frame = ui_frame.encode()
                    logger.info(f"UI frame encoded to {len(encoded_frame)} bytes: {encoded_frame.hex()[:100]}")
                    kiss.send_frame(encoded_frame)
                    logger.info("Sent welcome message")

                # Handle DISC (disconnect)
                elif frame.is_disc_frame():
                    logger.info(f"*** DISCONNECT from {frame.source.callsign.strip()}-{frame.source.ssid}")

                    # Send UA to acknowledge disconnect
                    ua_frame = AX25Frame.create_ua_frame(
                        frame.source.callsign.strip(),
                        MY_CALL,
                        frame.source.ssid,
                        MY_SSID
                    )
                    kiss.send_frame(ua_frame.encode())
                    logger.info("Sent UA (disconnect acknowledged)")

                # Log any data frames
                elif frame.info:
                    logger.info(f"Received data: {frame.info[:50]}")

            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                continue

    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        kiss.disconnect()
        logger.info("Disconnected from KISS TNC")

    return 0

if __name__ == '__main__':
    sys.exit(main())
