import Quartz

# PhilNav will only move the mouse on the main display. This might not be what you want, but I like it.
Qcgd_origin, Qcgd_size = Quartz.CGDisplayBounds(0)

def getCursorPos():
    blankEvent = Quartz.CGEventCreate(None)
    x, y = Quartz.CGEventGetLocation(blankEvent)
    return x, y

def setCursorPos(x, y):
    global Qcgd_origin, Qcgd_size
    # https://developer.apple.com/documentation/coregraphics/1454356-cgeventcreatemouseevent
    # CGEventType: case mouseMoved = 5
    # Ignored. CGMouseButton: case left = 0

    # On a Mac, the mouse is allowed to be "out of bounds". I'm keeping it in-bounds.
    # https://developer.apple.com/documentation/coregraphics/1456395-cgdisplaybounds
    if x < Qcgd_origin.x:
        x = Qcgd_origin.x
    if y < Qcgd_origin.y:
        y = Qcgd_origin.y
    if x > Qcgd_size.width:
        x = Qcgd_size.width
    if y > Qcgd_size.height:
        y = Qcgd_size.height

    mouseEvent = Quartz.CGEventCreateMouseEvent(None, 5, (x, y), 0)
    # CGEventTapLocation: case cghidEventTap = 0
    Quartz.CGEventPost(0, mouseEvent)

    Quartz.CGAssociateMouseAndMouseCursorPosition(True)

    # Two other ways of doing the same thing.
    # But these "lock" the physical mouse and don't send events.
    # Quartz.CGDisplayMoveCursorToPoint(0, (x, y))
    # Quartz.CGWarpMouseCursorPosition((x,y))
