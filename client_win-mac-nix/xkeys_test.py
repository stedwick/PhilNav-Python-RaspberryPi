#!/usr/bin/env python3
"""
Test script for X-keys foot pedal.
Displays real-time button state changes.
"""

import time
import sys
from xkeys_mac import XKeysPedal


def main():
    print("X-keys Foot Pedal Test")
    print("Press Ctrl-C to exit\n")

    pedal = XKeysPedal()

    if not pedal.is_connected():
        print("ERROR: No X-keys device found. Make sure it's connected.")
        sys.exit(1)

    print(f"Connected to {len(pedal.devices)} device(s)\n")

    last_state = None

    try:
        while True:
            current_state = pedal.is_middle_key_pressed()

            if current_state != last_state:
                timestamp = time.strftime("%H:%M:%S")
                status = "PRESSED" if current_state else "RELEASED"
                print(f"[{timestamp}] Middle key: {status}")
                last_state = current_state

            time.sleep(0.1)  # 100ms polling

    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        pedal.close()


if __name__ == "__main__":
    main()
