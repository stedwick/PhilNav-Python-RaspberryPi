#!/usr/bin/env python3
"""Minimal manual test for the callback-based X-keys helpers."""

import logging
import sys
import threading
import time

from xkeys_mac import xkeys_devices, xkeys_run


def log_state(is_pressed: bool) -> None:
    status = "PRESSED" if is_pressed else "RELEASED"
    logging.info("Middle pedal %s", status)

def main() -> None:
    """Spin up listener threads for each pedal and log state changes."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    print("X-keys Foot Pedal Callback Test")
    print("Press Ctrl-C to exit\n")

    devices = xkeys_devices()
    if not devices:
        print("ERROR: No X-keys device found. Make sure it's connected.")
        sys.exit(1)

    for idx, device in enumerate(devices, start=1):
        thread = threading.Thread(
            target=xkeys_run,
            kwargs={"device": device, "callback": log_state},
            daemon=True,
            name=f"xkeys-{idx}",
        )
        thread.start()

    print(f"Connected to {len(devices)} device(s). Waiting for pedal events...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()
