import ctypes
try:
    # Test if windll is available (Windows only)
    ctypes.windll  # type: ignore[attr-defined]
except AttributeError:
    # Add windll for non-Windows systems
    from stubs.ctypes_windll_stubs import windll  # type: ignore[import-not-found]
    ctypes.windll = windll  # type: ignore[attr-defined]


# simple point.x, point.y
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def getCursorPos():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))  # type: ignore[attr-defined]
    return pt.x, pt.y

def setCursorPos(x, y):
    ctypes.windll.user32.SetCursorPos(x, y)  # type: ignore[attr-defined]
