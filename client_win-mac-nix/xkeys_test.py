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

    print(f"Connected to {len(pedal.devices)} device(s)\n")

    # Track last state for each device separately
    last_states = {}  # device_index -> (last_state, last_data)

    try:
        while True:
            # Read raw data from each device
            for idx, device_entry in enumerate(pedal.devices):
                device = device_entry[0]
                product_id = device_entry[1]

                try:
                    data = device.read(64)  # Read up to 64 bytes
                    if data:
                        # Get last state for this device
                        if idx not in last_states:
                            last_states[idx] = (None, None)
                        last_state, last_data = last_states[idx]

                        if data != last_data:
                            timestamp = time.strftime("%H:%M:%S")
                            # Display raw data in hex
                            hex_data = ' '.join([f'{b:02x}' for b in data[:16]])  # First 16 bytes
                            print(f"[{timestamp}] Device {idx} (PID: {hex(product_id)}): {hex_data}")
                            last_states[idx] = (last_state, data)

                        # Check button state from the data we just read
                        if len(data) >= 3:
                            current_state = bool(data[2] & 0x04)

                            if current_state != last_state:
                                timestamp = time.strftime("%H:%M:%S")
                                status = "PRESSED" if current_state else "RELEASED"
                                print(f"[{timestamp}] Device {idx} (PID: {hex(product_id)}) Middle key: {status}")
                                last_states[idx] = (current_state, data)
                except:
                    pass

            time.sleep(0.01)  # 100Hz polling

    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        pedal.close()


if __name__ == "__main__":
    main()
