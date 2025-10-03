try:
    from Xlib import X, display  # type: ignore[import-untyped]
except ImportError:
    from stubs.xlib_stubs import X, display  # type: ignore[import-not-found]
from time import time

# F7
KEYCODE_F7 = 73
# F8
KEYCODE_F8 = 74

my_display = display.Display()
my_screen = my_display.screen()
my_root = my_screen.root

hotkey_time_f7 = time()
hotkey_time_f8 = time()


def hotkey_run(callback=None, multiplier_callback=None):
    global hotkey_time_f7, hotkey_time_f8

    # we tell the X server we want to catch keyPress event
    my_root.change_attributes(event_mask=X.KeyPressMask)
    my_root.grab_key(KEYCODE_F7, X.AnyModifier, True,
                     X.GrabModeAsync, X.GrabModeAsync)
    
    # Add F8 key grab
    my_root.grab_key(KEYCODE_F8, X.AnyModifier, True,
                     X.GrabModeAsync, X.GrabModeAsync)

    while True:
        my_event = my_display.next_event()
        if ("detail" not in my_event._data):
            continue
        
        # Handle F7 key press
        if (my_event.detail == KEYCODE_F7):
            now = time()
            if now - hotkey_time_f7 > 0.25:
                hotkey_time_f7 = now
                callback()  # type: ignore[misc]
        
        # Handle F8 key press
        elif (my_event.detail == KEYCODE_F8):
            now = time()
            if now - hotkey_time_f8 > 0.25:
                hotkey_time_f8 = now
                multiplier_callback()  # type: ignore[misc]
