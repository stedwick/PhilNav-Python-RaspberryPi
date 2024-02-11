from pynput import keyboard  # for hotkeys

listener = None

# https://pynput.readthedocs.io/en/latest/keyboard.html#global-hotkeys


def for_canonical(f):
    global listener
    return lambda k: f(listener.canonical(k))


def hotkey_run(callback=None):
    global listener

    # Shift-F7 hard-coded for now
    hotkey_toggle = keyboard.HotKey(
        [keyboard.Key.shift, keyboard.Key.f7.value],
        callback)

    listener = keyboard.Listener(
        on_press=for_canonical(hotkey_toggle.press),
        on_release=for_canonical(hotkey_toggle.release))

    listener.start()
