from typing import Dict, List, Sequence, TYPE_CHECKING, cast

try:
    from evdev import UInput, ecodes as e  # type: ignore[import-untyped]
except ImportError:
    from stubs.evdev_stubs import UInput, ecodes as e  # type: ignore[import-not-found]

if TYPE_CHECKING:
    CapabilitiesDict = Dict[int, List[int]]
else:
    CapabilitiesDict = Dict[int, Sequence[int]]

# Define capabilities for our virtual mouse
cap: CapabilitiesDict = {
    e.EV_REL: [e.REL_X, e.REL_Y],  # Relative positioning
    e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],  # Mouse buttons, required to be a mouse
}

# Create a uinput device
device = UInput(cast(Dict[int, List[int]], cap), name='pynav-virtual-mouse')

# We need to track the current position ourselves
current_x = 0
current_y = 0

def getCursorPos():
    # Note: we can't actually read the cursor position. We return our tracked
    # position, but it might get out of sync with reality. This doesn't matter;
    # we are moving the mouse relatively anyhow. Back on X11 it was absolute,
    # that's why this may seem silly. But we don't have to modify main.py.
    global current_x, current_y
    return current_x, current_y

def setCursorPos(x, y):
    global current_x, current_y
    
    # Calculate the relative movement needed
    dx = x - current_x
    dy = y - current_y
    
    # Update our tracked position
    current_x = x
    current_y = y
    
    # Move the cursor
    device.write(e.EV_REL, e.REL_X, dx)
    device.write(e.EV_REL, e.REL_Y, dy)
    device.syn()  # Synchronize state

# Updated Prompt: Switch it to using evdev @https://python-evdev.readthedocs.io/en/latest/tutorial.html#specifying-uinput-device-options 

# Key changes from the previous version:
# Using evdev instead of uinput
# Added mouse button capabilities (which might be useful later)
# Using device.syn() instead of separate sleeps
# More descriptive device name
# To use this, you'll need to:
# Install evdev:
# pip install evdev
# Add your user to the input group:
# Make sure you have the required permissions for /dev/uinput:
# The evdev implementation should be more reliable than the pure uinput one, as it's the standard way to handle input devices on modern Linux systems.
# # Add user to input group
# sudo usermod -a -G input $USER
# # Create a udev rule
# echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-input.rules
# # Reload udev rules
# sudo udevadm control --reload-rules
# sudo udevadm trigger

# Prompt: I'm making a virtual mouse in Python, and I have implementations for Windows, Mac, and Linux X11, see attached files. Linux is moving to Wayland which doesn't support X11 protocols to move the mouse, so I want to write an implementation using python-uinput. See https://pypi.org/project/python-uinput/ and https://github.com/pyinput/python-uinput.

# Create a setCursorPos function for me using /dev/uinput thanks!

# I'll help you create a Wayland implementation using python-uinput. Note that using uinput requires root privileges or adding the user to the input group.
# Here's the implementation for mouse_wayland.py:

# A few important notes about this implementation:
# This requires root privileges or the user needs to be in the input group
# You'll need to install python-uinput (pip install python-uinput) and the system package (sudo apt-get install python3-uinput on Ubuntu/Debian)
# The implementation uses relative movements since uinput doesn't support absolute positioning
# Position tracking might get out of sync with the actual cursor position since we can't read the true position
# The time.sleep() is added to ensure events are processed properly
# To use this on a Linux system with Wayland, you'll need to:
# Install the requirements: sudo apt-get install libudev-dev
# Add your user to the input group: sudo usermod -a -G input $USER
# Load the uinput kernel module: sudo modprobe uinput
# You might want to add error handling and initialization checks to make sure the uinput device is available and properly set up.
