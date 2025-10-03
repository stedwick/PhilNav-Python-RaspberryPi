try:
    from Xlib import display  # type: ignore[import-untyped]
except ImportError:
    from stubs.xlib_stubs import display  # type: ignore[import-not-found]

my_display = display.Display()
my_screen = my_display.screen()
my_root = my_screen.root

# https://stackoverflow.com/a/24158912


def getCursorPos():
    pointer = my_root.query_pointer()
    return pointer.root_x, pointer.root_y

# https://stackoverflow.com/a/1181517


def setCursorPos(x, y):
    my_root.warp_pointer(x, y)
    my_display.sync()
