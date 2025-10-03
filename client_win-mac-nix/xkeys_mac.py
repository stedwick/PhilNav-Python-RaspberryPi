"""
X-keys foot pedal interface for macOS.
Detects button presses from X-keys USB HID devices using an event-driven,
multi-threaded approach for efficiency.
"""

import hid
import logging
import threading
import queue

# X-keys vendor ID (PI Engineering)
XKEYS_VENDOR_ID = 0x05F3

# Pi3 Matrix Board product IDs (from hidutil list)
XKEYS_PRODUCT_IDS = [
    0x042C,  # Pi3 Matrix Board
    0x0438,  # Pi3 Matrix Board (alternate interface)
]

def xkeys_run(device, callback):
    """
    Continuously reads from a single HID device in a blocking manner.

    When data is received, it's put into the shared event queue along with
    the device identifier.

    Args:
        device (hid.device): The HID device to read from.
        event_queue (queue.Queue): The queue to put event data into.
        device_id (str): A unique identifier for the device (e.g., its path).
    """
    while True:
        try:
            # Blocking read waits for data, using zero CPU when idle
            data = device.read(64)
            if data:
                if len(data) >= 3:
                    # Byte 2: Button state (0x04 = middle, 0x02=right, 0x01=left)
                    # We only care about the middle pedal for now.
                    is_pressed = bool(data[2] & 0x04)
                    callback(is_pressed)
        except (IOError, OSError, ValueError):
            # Device was likely disconnected, exit the thread
            logging.warning(f"X-keys device disconnected.")
            break

def xkeys_devices():
    """
    Returns a list of all connected X-keys devices.
    """
    xkeys_devices = []
    for device_info in hid.enumerate(XKEYS_VENDOR_ID):
        product_id = device_info['product_id']
        if product_id in XKEYS_PRODUCT_IDS:
            try:
                device = hid.device()
                device.open_path(device_info['path'])
                device_id = device_info['path'].decode('utf-8')
                xkeys_devices.append(device)
                
                logging.info(f"Connected to X-keys device (PID: {hex(product_id)}, Path: {device_id})")

            except (IOError, OSError) as e:
                logging.warning(f"Failed to connect to X-keys device: {e}")
                continue
    
    if len(xkeys_devices) == 0:
        logging.info("No X-keys foot pedal found.")

    return xkeys_devices
