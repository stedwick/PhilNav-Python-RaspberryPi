from evdev import InputDevice, categorize, ecodes
from time import time
import glob

# Key codes
F7_KEYCODE = 65
SHIFT_KEYCODE = 42  # Left shift
SHIFT_KEYCODE_RIGHT = 54  # Right shift

hotkey_time = time()

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

def hotkey_run(callback=None):
    global hotkey_time
    
    keyboards = find_keyboards()
    if not keyboards:
        raise RuntimeError("No keyboard devices found!")
    
    # Track shift key state for each device
    shift_pressed = {dev.fd: False for dev in keyboards}
    
    while True:
        for device in keyboards:
            try:
                for event in device.read():
                    if event.type == ecodes.EV_KEY:
                        # Update shift state
                        if event.code in (SHIFT_KEYCODE, SHIFT_KEYCODE_RIGHT):
                            shift_pressed[device.fd] = (event.value == 1 or event.value == 2)
                        
                        # Check for F7 press while shift is held
                        if event.code == F7_KEYCODE and event.value == 1 and shift_pressed[device.fd]:
                            now = time()
                            if now - hotkey_time > 0.25:
                                hotkey_time = now
                                if callback:
                                    callback()
            except BlockingIOError:
                continue
