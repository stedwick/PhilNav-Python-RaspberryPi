#!/usr/bin/env python3
"""
Test script for the event-driven X-keys foot pedal interface.
Displays real-time button state changes.
"""

import time
import sys
import logging
from xkeys_mac import XKeysPedal

def main():
    """Initializes the pedal and prints state changes."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("X-keys Foot Pedal Event-Driven Test")
    print("Press Ctrl-C to exit\n")

    pedal = XKeysPedal()

    if not pedal.is_connected():
        print("ERROR: No X-keys device found. Make sure it's connected.")
        sys.exit(1)

    print(f"Connected to {len(pedal.device_states)} device(s). Waiting for pedal events...\n")

    last_state = False

    try:
        while True:
            # This call now processes any pending events from the queue
            # and returns the current state.
            current_state = pedal.is_middle_key_pressed()

            if current_state != last_state:
                timestamp = time.strftime("%H:%M:%S")
                status = "PRESSED" if current_state else "RELEASED"
                print(f"[{timestamp}] Middle key: {status}")
                last_state = current_state

            # Sleep briefly to prevent the loop from consuming 100% CPU,
            # while still being highly responsive.
            time.sleep(0.01) # 10ms

    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        pedal.close()

if __name__ == "__main__":
    main()