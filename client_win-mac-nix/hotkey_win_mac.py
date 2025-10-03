from pynput import keyboard  # for hotkeys
from typing import Optional, Callable, Union

listener: Optional[keyboard.Listener] = None

# https://pynput.readthedocs.io/en/latest/keyboard.html#global-hotkeys


def for_canonical(f):
    global listener
    return lambda k: f(listener.canonical(k))


def hotkey_run(callback: Optional[Callable[[], None]] = None, multiplier_callback: Optional[Callable[[], None]] = None):
    global listener

    # Shift-F7 hard-coded for now
    hotkey_toggle = keyboard.HotKey(
        [keyboard.Key.shift, keyboard.Key.f7.value],
        callback)
    
    # Shift-F8 for speed multiplier
    hotkey_multiplier = keyboard.HotKey(
        [keyboard.Key.shift, keyboard.Key.f8.value],
        multiplier_callback)

    listener = keyboard.Listener(
        on_press=lambda k: (
            for_canonical(hotkey_toggle.press)(k) or 
            for_canonical(hotkey_multiplier.press)(k)
        ),
        on_release=lambda k: (
            for_canonical(hotkey_toggle.release)(k) or 
            for_canonical(hotkey_multiplier.release)(k)
        ))

    listener.start()
