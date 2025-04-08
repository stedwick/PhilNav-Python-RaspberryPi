from evdev import InputDevice, ecodes
from time import time
import glob
import select

# Key codes
F7_KEYCODE = 65
F8_KEYCODE = 66
SHIFT_KEYCODE = 42  # Left shift
SHIFT_KEYCODE_RIGHT = 54  # Right shift

hotkey_time_f7 = time()
hotkey_time_f8 = time()

def find_keyboards():
    """Find all keyboard devices"""
    keyboards = []
    for device_path in glob.glob("/dev/input/event*"):
        try:
            device = InputDevice(device_path)
            if ecodes.EV_KEY in device.capabilities():
                keyboards.append(device)
        except (PermissionError, OSError):
            continue
    return keyboards

def hotkey_run(callback=None, multiplier_callback=None):
    global hotkey_time_f7, hotkey_time_f8
    
    keyboards = find_keyboards()
    if not keyboards:
        raise RuntimeError("No keyboard devices found!")
    
    # Track shift key state for each device
    shift_pressed = {dev.fd: False for dev in keyboards}
    
    # Create a dictionary mapping file descriptors to devices
    devices = {dev.fd: dev for dev in keyboards}
    
    while True:
        # Wait for events on any keyboard device
        r, w, x = select.select(devices, [], [], 1.0)  # 1 second timeout
        
        for fd in r:
            device = devices[fd]
            try:
                for event in device.read():
                    if event.type == ecodes.EV_KEY:
                        # Update shift state
                        if event.code in (SHIFT_KEYCODE, SHIFT_KEYCODE_RIGHT):
                            shift_pressed[fd] = (event.value == 1 or event.value == 2)
                        
                        # Check for F7 press while shift is held
                        if event.code == F7_KEYCODE and event.value == 1 and shift_pressed[fd]:
                            now = time()
                            if now - hotkey_time_f7 > 0.25:
                                hotkey_time_f7 = now
                                callback()
                        
                        # Check for F8 press while shift is held
                        if event.code == F8_KEYCODE and event.value == 1 and shift_pressed[fd]:
                            now = time()
                            if now - hotkey_time_f8 > 0.25:
                                hotkey_time_f8 = now
                                multiplier_callback()
            except BlockingIOError:
                continue

# # CPU Fix Prompt: This works, but takes 5% CPU and spins up the fans. Need to optimize the loop.

# Ah yes, the busy-waiting loop is inefficient. We can optimize this using select() to wait for events instead of continuously polling. Here's the optimized version:

# # Key changes:
# Added select.select() to efficiently wait for events instead of busy-waiting
# Added a 1-second timeout to the select call to prevent complete blocking
# Created a devices dictionary mapping file descriptors to devices for easier lookup
# Only process events when select indicates data is available
# This should dramatically reduce CPU usage as the process will sleep while waiting for keyboard events instead of continuously checking for them. The CPU usage should now be close to 0% when idle.