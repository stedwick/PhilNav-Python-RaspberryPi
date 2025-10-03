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

def hid_reader(device, event_queue, device_id):
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
                event_queue.put((device_id, data))
        except (IOError, OSError, ValueError):
            # Device was likely disconnected, exit the thread
            logging.warning(f"X-keys device {device_id} disconnected.")
            break

class XKeysPedal:
    """
    Interface for X-keys foot pedal(s). Manages multiple devices, each with its
    own reader thread.
    """

    def __init__(self):
        self.event_queue = queue.Queue()
        # device_states stores {device_id: {product_id, is_pressed}}
        self.device_states = {}
        self.reader_threads = []
        self._connect()

    def _connect(self):
        """
        Finds all connected X-keys pedals, stores their state, and starts a
        dedicated reader thread for each.
        """
        for device_info in hid.enumerate(XKEYS_VENDOR_ID):
            product_id = device_info['product_id']
            if product_id in XKEYS_PRODUCT_IDS:
                try:
                    device = hid.device()
                    device.open_path(device_info['path'])
                    
                    device_id = device_info['path'].decode('utf-8')
                    
                    # Initialize state for this device
                    self.device_states[device_id] = {
                        "product_id": product_id,
                        "is_pressed": False
                    }

                    # Start a dedicated reader thread for this device
                    thread = threading.Thread(
                        target=hid_reader,
                        args=(device, self.event_queue, device_id),
                        daemon=True
                    )
                    thread.start()
                    self.reader_threads.append(thread)
                    
                    logging.info(f"Connected to X-keys device (PID: {hex(product_id)}, Path: {device_id})")

                except (IOError, OSError) as e:
                    logging.error(f"Failed to connect to X-keys device: {e}")
                    continue
        
        if not self.reader_threads:
            logging.warning("No X-keys foot pedal found.")

    def _process_events(self):
        """
        Process all pending events from the queue and update device states.
        This method is non-blocking.
        """
        try:
            while not self.event_queue.empty():
                device_id, data = self.event_queue.get_nowait()

                if device_id in self.device_states and len(data) >= 3:
                    # Byte 2: Button state (0x04 = middle, 0x02=right, 0x01=left)
                    # We only care about the middle pedal for now.
                    is_pressed = bool(data[2] & 0x04)
                    self.device_states[device_id]["is_pressed"] = is_pressed

        except queue.Empty:
            pass # No events to process

    def is_connected(self):
        """Check if any device is connected."""
        return len(self.reader_threads) > 0

    def is_middle_key_pressed(self):
        """
        Check if the middle key is pressed on ANY connected pedal.

        This method is non-blocking and reflects the most recent state update
        from the background threads.

        Returns:
            bool: True if the middle key is pressed on any device, False otherwise.
        """
        self._process_events()
        return any(state["is_pressed"] for state in self.device_states.values())

    def get_all_states(self):
        """
        Get the current state of all connected devices.

        Returns:
            list: A list of tuples (product_id, is_pressed) for each device.
        """
        self._process_events()
        return [
            (state["product_id"], state["is_pressed"])
            for state in self.device_states.values()
        ]

    def close(self):
        """
        Stops the reader threads (by virtue of being daemon threads).
        This is mostly for cleanup in tests; in a real app, daemon threads
        are often sufficient.
        """
        # No explicit close needed for daemon threads, but good practice
        # if you needed to join them.
        logging.info("X-keys connections closed.")