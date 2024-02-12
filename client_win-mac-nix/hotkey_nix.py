from Xlib import X, display
from time import time

# F7
KEYCODE = 73

my_display = display.Display()
my_screen = my_display.screen()
my_root = my_screen.root

hotkey_time = time()


def hotkey_run(callback=None):
    global hotkey_time

    # we tell the X server we want to catch keyPress event
    my_root.change_attributes(event_mask=X.KeyPressMask)
    my_root.grab_key(KEYCODE, X.AnyModifier, True,
                     X.GrabModeAsync, X.GrabModeAsync)

    while True:
        my_event = my_display.next_event()
        if ("detail" not in my_event._data):
            continue
        if (my_event.detail != KEYCODE):
            continue
        now = time()
        if now - hotkey_time > 0.25:
            hotkey_time = now
            if callback:
                callback()
