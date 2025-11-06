#!/usr/bin/env python3
"""
Simple test script to transmit a single packet
Use this to verify that your radio can receive and decode the transmission
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
MY_SSID = 3
DEST_CALL = 'CQ'  # or use your field station callsign
DEST_SSID = 0

def main():
    logger.info("=== SINGLE PACKET TRANSMIT TEST ===")
    logger.info(f"From: {MY_CALL}-{MY_SSID}")
    logger.info(f"To: {DEST_CALL}-{DEST_SSID}")

    # Connect to KISS TNC
    kiss = KISSClient(KISS_HOST, KISS_PORT)
    try:
        kiss.connect()
        logger.info(f"Connected to Direwolf KISS on {KISS_HOST}:{KISS_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to KISS TNC: {e}")
        return 1

    # Wait a moment for connection to stabilize
    time.sleep(0.5)

    # Create a UI frame with test message
    test_message = b"TEST BEACON FROM PACKET CLAUDE\rIf you can read this, your radio is receiving properly.\r73!\r"

    logger.info(f"Creating UI frame with message: {test_message[:50]}...")
    ui_frame = AX25Frame.create_ui_frame(
        DEST_CALL,      # Destination
        MY_CALL,        # Source
        test_message,   # Data
        DEST_SSID,      # Dest SSID
        MY_SSID         # Source SSID
    )

    # Encode frame
    encoded = ui_frame.encode()
    logger.info(f"Encoded frame size: {len(encoded)} bytes")

    # Send frame
    logger.info("*** TRANSMITTING NOW ***")
    success = kiss.send_frame(encoded)

    if success:
        logger.info("✓ Frame sent to KISS TNC successfully")
        logger.info("Check your radio - you should see this transmission!")
    else:
        logger.error("✗ Failed to send frame")

    # Wait a moment before disconnecting
    time.sleep(1)

    # Disconnect
    kiss.disconnect()
    logger.info("Disconnected from KISS TNC")
    logger.info("Test complete!")

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
