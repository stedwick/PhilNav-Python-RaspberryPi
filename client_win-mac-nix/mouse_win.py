import ctypes


# simple point.x, point.y
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def getCursorPos():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def setCursorPos(x, y):
    ctypes.windll.user32.SetCursorPos(x, y)
