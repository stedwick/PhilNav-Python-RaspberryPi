"""
X-keys foot pedal interface for macOS.
Detects button presses from X-keys USB HID devices.
"""

import hid
import logging
import time

# X-keys vendor ID (PI Engineering)
XKEYS_VENDOR_ID = 0x05F3

# Pi3 Matrix Board product IDs (from hidutil list)
XKEYS_PRODUCT_IDS = [
    0x042C,  # Pi3 Matrix Board
    0x0438,  # Pi3 Matrix Board (alternate interface)
]


class XKeysPedal:
    """Interface for X-keys foot pedal."""

    def __init__(self):
        self.device = None
        self._cached_state = False
        self._last_check_time = 0
        self._cache_duration = 0.1  # 100ms cache duration
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

    def _update_state(self):
        """Update the cached button state by reading from device."""
        if not self.device:
            return

        try:
            # Read data from device (non-blocking)
            data = self.device.read(64)
            if data and len(data) >= 3:
                # Pi3 Matrix Board format:
                # Byte 0: Report ID (0x01)
                # Byte 1: Always 0x01
                # Byte 2: Button state (0x04 = middle key pressed, 0x00 = released)
                self._cached_state = bool(data[2] & 0x04)
        except (IOError, OSError, ValueError):
            # Silently keep current cached state if device read fails
            pass

    def is_middle_key_pressed(self):
        """
        Check if the middle key of the foot pedal is currently pressed.

        Uses a 100ms cache to avoid blocking reads. Returns cached state
        immediately and updates cache if 100ms has elapsed.

        Returns:
            bool: True if middle key is pressed, False otherwise
        """
        current_time = time.time()

        # Update cache if sufficient time has elapsed
        if current_time - self._last_check_time >= self._cache_duration:
            self._update_state()
            self._last_check_time = current_time

        return self._cached_state

    def close(self):
        """Close the device connection."""
        if self.device:
            self.device.close()
            self.device = None
