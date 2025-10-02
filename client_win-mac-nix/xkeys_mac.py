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
    """Interface for X-keys foot pedal(s). Supports multiple devices."""

    def __init__(self):
        # List of [device, product_id, current_state, last_data, last_check_time]
        self.devices = []
        self._cache_duration = 0.01  # 10ms cache duration for responsiveness
        self._connect()

    def _connect(self):
        """Connect to all available X-keys devices."""
        # Enumerate all devices to find multiple instances
        for device_info in hid.enumerate(XKEYS_VENDOR_ID):
            product_id = device_info['product_id']
            if product_id in XKEYS_PRODUCT_IDS:
                try:
                    device = hid.device()
                    # Path is already bytes, use it directly
                    device.open_path(device_info['path'])
                    device.set_nonblocking(1)
                    # Initialize: [device, product_id, current_state, last_data, last_check_time]
                    self.devices.append([device, product_id, False, None, 0])
                    # Decode path for logging if it's bytes
                    path_str = device_info['path'].decode('utf-8') if isinstance(device_info['path'], bytes) else device_info['path']
                    logging.info(f"Connected to X-keys device (PID: {hex(product_id)}, Path: {path_str})")
                except (IOError, OSError):
                    # Silently ignore devices we can't connect to
                    continue

        if not self.devices:
            logging.warning("No X-keys foot pedal found")

    def is_connected(self):
        """
        Check if any device is connected.

        Returns:
            bool: True if at least one device is connected, False otherwise
        """
        return len(self.devices) > 0

    def _update_state(self, device_entry):
        """Update the cached button state for a specific device."""
        device = device_entry[0]

        try:
            # Read data from device (non-blocking)
            # Keep reading until we've drained the buffer
            latest_data = None
            while True:
                data = device.read(64)
                if not data:
                    break
                latest_data = data

            # Only update state if we got new data that's different from last time
            if latest_data and len(latest_data) >= 3 and latest_data != device_entry[3]:
                # Pi3 Matrix Board format:
                # Byte 0: Report ID (0x01)
                # Byte 1: Always 0x01
                # Byte 2: Button state (0x04 = middle key pressed, 0x00 = released)
                device_entry[2] = bool(latest_data[2] & 0x04)
                device_entry[3] = latest_data
        except (IOError, OSError, ValueError):
            # Silently keep current cached state if device read fails
            pass

    def _update_all_states(self):
        """Update cached states for all devices if cache has expired."""
        current_time = time.time()

        for device_entry in self.devices:
            if current_time - device_entry[4] >= self._cache_duration:
                self._update_state(device_entry)
                device_entry[4] = current_time

    def is_middle_key_pressed(self):
        """
        Check if the middle key is pressed on ANY connected pedal.

        Uses a 100ms cache to avoid blocking reads. Returns cached state
        immediately and updates cache if 100ms has elapsed.

        Returns:
            bool: True if middle key is pressed on any device, False otherwise
        """
        self._update_all_states()
        return any(device_entry[2] for device_entry in self.devices)

    def get_all_states(self):
        """
        Get the current state of all connected devices.

        Returns:
            list: List of tuples (product_id, is_pressed) for each device
        """
        self._update_all_states()
        return [(device_entry[1], device_entry[2]) for device_entry in self.devices]

    def close(self):
        """Close all device connections."""
        for device_entry in self.devices:
            try:
                device_entry[0].close()
            except:
                pass
        self.devices = []
