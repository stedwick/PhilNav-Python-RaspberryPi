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
    try:
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
    finally:
        try:
            device.close()
        except (IOError, OSError, ValueError):
            pass

def xkeys_devices():
    """Return all connected X-keys pedals as opened ``hid.device`` objects."""

    candidates: dict[tuple, tuple[int, dict, str]] = {}

    for device_info in hid.enumerate(XKEYS_VENDOR_ID):
        product_id = device_info["product_id"]

        if product_id not in XKEYS_PRODUCT_IDS:
            continue

        location_id = device_info.get("location_id")
        serial_number = device_info.get("serial_number")
        usage_page = device_info.get("usage_page")
        usage = device_info.get("usage")
        path_bytes = device_info.get("path", b"")
        path_str = path_bytes.decode("utf-8") if isinstance(path_bytes, bytes) else str(path_bytes)

        logging.debug(
            "Enumerated X-keys interface: PID=%s usage_page=0x%04x usage=0x%04x location_id=%s serial=%s path=%s",
            hex(product_id),
            usage_page if usage_page is not None else 0,
            usage if usage is not None else 0,
            location_id,
            serial_number,
            path_str,
        )

        if usage == 0x0001:
            priority = 0  # Consumer Control usage maps directly to pedal events
        elif usage_page == 0x0001:
            priority = 1  # Generic Desktop fallback when usage is ambiguous
        elif usage_page is None:
            priority = 2
        else:
            logging.debug(
                "Skipping X-keys interface on unsupported usage page 0x%04x (usage 0x%04x)",
                usage_page,
                usage,
            )
            continue

        if location_id is not None or serial_number is not None:
            device_key = (product_id, location_id, serial_number)
        else:
            suffix = path_str.split(":", 1)[-1]
            if suffix.isdigit() and len(suffix) > 1:
                # Group similar DevSrvsIDs (which differ only by the last digit
                # per physical pedal) so we can prefer the best usage page.
                physical_hint = suffix[:-1]
            else:
                physical_hint = path_str
            device_key = (product_id, physical_hint)

        current = candidates.get(device_key)
        if current is None or priority < current[0]:
            candidates[device_key] = (priority, device_info, path_str)
            if current is not None:
                logging.debug(
                    "Replacing candidate for %s with higher-priority usage page 0x%04x",
                    device_key,
                    usage_page,
                )

    devices: list[hid.device] = []
    for priority, device_info, path_str in sorted(candidates.values(), key=lambda item: item[0]):
        product_id = device_info["product_id"]
        try:
            device = hid.device()
            device.open_path(device_info["path"])
            devices.append(device)

            logging.info(
                "Connected to X-keys device (PID: %s, Path: %s, usage_page=0x%04x)",
                hex(product_id),
                path_str,
                device_info.get("usage_page"),
            )

        except (IOError, OSError) as exc:
            logging.warning("Failed to connect to X-keys device: %s", exc)

    if not devices:
        logging.info("No X-keys foot pedal found.")

    return devices
