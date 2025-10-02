"""
X-keys foot pedal interface for macOS.
Detects button presses from X-keys USB HID devices.
"""

import hid
import logging

# X-keys vendor ID (PI Engineering)
XKEYS_VENDOR_ID = 0x05F3

# Common X-keys foot pedal product IDs
XKEYS_PRODUCT_IDS = [
    0x0050,  # XK-3
    0x00A5,  # XK-3 Switch Interface
]


class XKeysPedal:
    """Interface for X-keys foot pedal."""

    def __init__(self):
        self.device = None
        self._connect()

    def _connect(self):
        """Connect to the X-keys device."""
        for product_id in XKEYS_PRODUCT_IDS:
            try:
                self.device = hid.device()
                self.device.open(XKEYS_VENDOR_ID, product_id)
                self.device.set_nonblocking(1)
                logging.info(f"Connected to X-keys device (PID: {hex(product_id)})")
                return
            except (IOError, OSError):
                continue

        logging.warning("No X-keys foot pedal found")

    def is_connected(self):
        """
        Check if device is connected.

        Returns:
            bool: True if device is connected, False otherwise
        """
        return self.device is not None

    def is_middle_key_pressed(self):
        """
        Check if the middle key of the foot pedal is currently pressed.

        Returns:
            bool: True if middle key is pressed, False otherwise
        """
        if not self.device:
            return False

        try:
            # Read data from device (non-blocking)
            data = self.device.read(8)
            if not data:
                return False

            # X-keys reports button states in the data packet
            # Byte 0 is report ID, byte 1 typically contains button states
            # For XK-3, buttons are in bits 0-2 of byte 1
            # Middle button is typically bit 1
            button_state = data[1] if len(data) > 1 else 0
            middle_key_pressed = bool(button_state & 0x02)

            return middle_key_pressed
        except (IOError, OSError, ValueError):
            # Silently return False if device is not available
            return False

    def close(self):
        """Close the device connection."""
        if self.device:
            self.device.close()
            self.device = None
