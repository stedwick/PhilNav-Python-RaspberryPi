"""
Stub file for Xlib to enable type checking on non-X11 systems.
This provides the basic API structure for X11 functionality.
"""
from typing import Any, Optional, Dict

class X:
    """Stub for Xlib.X constants"""
    KeyPress = 2
    KeyRelease = 3
    ButtonPress = 4
    ButtonRelease = 5
    MotionNotify = 6
    
    # Modifiers
    ShiftMask = 1
    ControlMask = 4
    Mod1Mask = 8  # Alt
    AnyModifier = 32768
    
    # Mouse buttons
    Button1 = 1  # Left
    Button2 = 2  # Middle
    Button3 = 3  # Right
    
    # Event masks
    KeyPressMask = 1
    KeyReleaseMask = 2
    
    # Grab modes
    GrabModeAsync = 1
    GrabModeSync = 0

class Display:
    """Stub for Xlib Display"""
    def __init__(self, display_name: Optional[str] = None) -> None:
        self.display_name = display_name
    
    def screen(self, screen_num: int = 0) -> 'Screen':
        return Screen()
    
    def get_input_focus(self) -> tuple:
        return (Window(), 0)
    
    def sync(self) -> None:
        pass
    
    def flush(self) -> None:
        pass
    
    def close(self) -> None:
        pass
    
    def next_event(self) -> 'Event':
        return Event()
    
    def pending_events(self) -> int:
        return 0

class Screen:
    """Stub for Xlib Screen"""
    def __init__(self) -> None:
        self.root = Window()
        self.width_in_pixels = 1920
        self.height_in_pixels = 1080

class Window:
    """Stub for Xlib Window"""
    def __init__(self) -> None:
        pass
    
    def warp_pointer(self, x: int, y: int) -> None:
        pass
    
    def query_pointer(self) -> Any:
        class PointerQuery:
            root_x = 0
            root_y = 0
            win_x = 0
            win_y = 0
        return PointerQuery()
    
    def grab_keyboard(self, owner_events: bool, pointer_mode: int, keyboard_mode: int, time: int) -> int:
        return 0
    
    def ungrab_keyboard(self, time: int) -> None:
        pass
    
    def change_attributes(self, **kwargs) -> None:
        pass
    
    def grab_key(self, key: int, modifiers: int, owner_events: bool, pointer_mode: int, keyboard_mode: int) -> None:
        pass

class Event:
    """Stub for Xlib Event"""
    def __init__(self) -> None:
        self.type = 0
        self.detail = 0
        self.state = 0
        self.time = 0
        self._data = {"detail": 0}

class display:
    """Stub for Xlib.display module"""
    @staticmethod
    def Display(display_name: Optional[str] = None) -> Display:
        """Factory function for Display"""
        return Display(display_name)
