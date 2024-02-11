from Xlib import X, display
from time import time
import logging

my_display = display.Display()
my_screen = my_display.screen()
my_root = my_screen.root

hotkey_time = time()


def hotkey_run(callback=None):
    global hotkey_time

    # we tell the X server we want to catch keyPress event
    my_root.change_attributes(event_mask=X.KeyPressMask)
    # Shift + F7
    my_root.grab_key(73, X.ShiftMask, True, X.GrabModeAsync, X.GrabModeAsync)

    while True:
        my_event = my_display.next_event()
        now = time()
        if now - hotkey_time > 0.25:
            hotkey_time = now
            if callback:
                callback()
