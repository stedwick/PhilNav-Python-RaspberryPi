import Quartz  # type: ignore[import-untyped]


# PhilNav will only move the mouse on the main display. This might not be what you want, but I like it.
Qcgd_origin, Qcgd_size = Quartz.CGDisplayBounds(0)  # type: ignore[attr-defined]


def getCursorPos():
    blankEvent = Quartz.CGEventCreate(None)  # type: ignore[attr-defined]
    x, y = Quartz.CGEventGetLocation(blankEvent)  # type: ignore[attr-defined]
    return x, y

def setCursorPos(x, y):
    # On a Mac, the mouse is allowed to be "out of bounds". I'm keeping it in-bounds.
    # https://developer.apple.com/documentation/coregraphics/1456395-cgdisplaybounds
    if x < Qcgd_origin.x:
        x = Qcgd_origin.x
    if y < Qcgd_origin.y:
        y = Qcgd_origin.y
    right = Qcgd_origin.x + Qcgd_size.width
    bottom = Qcgd_origin.y + Qcgd_size.height
    if x > right:
        x = right
    if y > bottom:
        y = bottom

    # https://developer.apple.com/documentation/coregraphics/1454356-cgeventcreatemouseevent
    # CGEventType: case mouseMoved = 5
    # Ignored. CGMouseButton: case left = 0
    mouseEvent = Quartz.CGEventCreateMouseEvent(None, 5, (x, y), 0)  # type: ignore[attr-defined]
    # CGEventTapLocation: case cghidEventTap = 0
    Quartz.CGEventPost(0, mouseEvent)  # type: ignore[attr-defined]

    # Two other ways of doing the same thing.
    # But these "lock" the physical mouse and don't send events.
    # Quartz.CGDisplayMoveCursorToPoint(0, (x, y))
    # Quartz.CGWarpMouseCursorPosition((x,y))
