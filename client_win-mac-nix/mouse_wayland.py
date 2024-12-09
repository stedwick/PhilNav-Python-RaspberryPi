import uinput
import time

# Define the events we'll need
events = [
    uinput.REL_X,
    uinput.REL_Y,
]

# Create a uinput device
device = uinput.Device(events)

# We need to track the current position ourselves since uinput works with relative movements
current_x = 0
current_y = 0

def getCursorPos():
    # Note: uinput can't actually read the cursor position
    # We return our tracked position, but it might get out of sync with reality
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
    device.emit(uinput.REL_X, dx)
    device.emit(uinput.REL_Y, dy)
    # Small sleep to ensure events are processed
    time.sleep(0.01)
