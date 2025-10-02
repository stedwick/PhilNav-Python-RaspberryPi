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
    print("Debug mode: Will show raw data from device\n")

    pedal = XKeysPedal()

    if not pedal.is_connected():
        print("ERROR: No X-keys device found. Make sure it's connected.")
        sys.exit(1)

    last_state = None
    last_data = None

    try:
        while True:
            # Read raw data once and process it
            if pedal.device:
                try:
                    data = pedal.device.read(64)  # Read up to 64 bytes
                    if data:
                        if data != last_data:
                            timestamp = time.strftime("%H:%M:%S")
                            # Display raw data in hex
                            hex_data = ' '.join([f'{b:02x}' for b in data[:16]])  # First 16 bytes
                            print(f"[{timestamp}] Raw data: {hex_data}")
                            last_data = data

                        # Check button state from the data we just read
                        if len(data) >= 3:
                            current_state = bool(data[2] & 0x04)

                            if current_state != last_state:
                                timestamp = time.strftime("%H:%M:%S")
                                status = "PRESSED" if current_state else "RELEASED"
                                print(f"[{timestamp}] Middle key: {status}")
                                last_state = current_state
                except:
                    pass

            time.sleep(0.01)  # 100Hz polling

    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        pedal.close()


if __name__ == "__main__":
    main()
