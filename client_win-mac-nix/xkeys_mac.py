"""macOS helpers for reacting to X-keys USB foot pedal input."""

import hid
import logging
from typing import Callable, Optional

# X-keys vendor ID (PI Engineering)
XKEYS_VENDOR_ID = 0x05F3

# Pi3 Matrix Board product IDs (from hidutil list)
XKEYS_PRODUCT_IDS = [
    0x042C,  # Pi3 Matrix Board
    0x0438,  # Pi3 Matrix Board (alternate interface)
]

def xkeys_run(
    device: hid.device, callback: Optional[Callable[[bool], None]] = None
):
    """
    Continuously read pedal events from an opened HID device and invoke the
    supplied callback with the middle-button state (True when pressed).

    Args:
        device: Forwarded ``hid.device`` instance returned by ``xkeys_devices``.
        callback: Callable receiving the pedal state as a bool.
    """
    while True:
        try:
            # Blocking read waits for data, using zero CPU when idle.
            data = device.read(64)
            if data and len(data) >= 3:
                # Byte 2: Button state (0x04 = middle, 0x02 = right, 0x01 = left).
                is_pressed = bool(data[2] & 0x04)
                if callback:
                    callback(is_pressed)
        except (IOError, OSError, ValueError):
            # Device was likely disconnected; exit the thread.
            logging.warning("X-keys device disconnected.")
            break

def xkeys_devices():
    """Return all connected X-keys pedals as opened ``hid.device`` objects."""

    devices: list[hid.device] = []

    for device_info in hid.enumerate(XKEYS_VENDOR_ID):
        product_id = device_info["product_id"]
        if product_id not in XKEYS_PRODUCT_IDS:
            continue
        usage = device_info.get("usage")
        if usage != 0x0001:
            continue
        usage_page = device_info.get("usage_page")
        if usage_page != 0x000c:
            continue

        logging.debug(
            "Enumerated X-keys device (PID: %s, Path: %s, usage=0x%04x, usage_page=0x%04x)",
            hex(product_id),
            device_info["path"],
            usage,
            usage_page,
        )

        try:
            device = hid.device()
            device.open_path(device_info["path"])
            devices.append(device)

            logging.info(
                "Connected to X-keys device (PID: %s, Path: %s, usage=0x%04x, usage_page=0x%04x)",
                hex(product_id),
                device_info["path"],
                usage,
                usage_page,
            )

        except (IOError, OSError) as exc:
            # logging.warning("Failed to connect to X-keys device: %s", exc)
            pass

    if not devices:
        logging.debug("No X-keys foot pedal found.")

    return devices
