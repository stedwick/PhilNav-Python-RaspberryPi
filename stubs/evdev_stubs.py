"""
Stub file for evdev to enable type checking on non-Linux systems.
This provides the basic API structure for Linux input device handling.
"""
from typing import Any, Dict, List, Optional, Iterator
import time

class ecodes:
    """Stub for evdev.ecodes"""
    # Event types
    EV_SYN = 0x00
    EV_KEY = 0x01
    EV_REL = 0x02
    EV_ABS = 0x03
    
    # Relative axes
    REL_X = 0x00
    REL_Y = 0x01
    
    # Key codes
    BTN_LEFT = 0x110
    BTN_RIGHT = 0x111
    BTN_MIDDLE = 0x112
    
    KEY_F7 = 65
    KEY_F8 = 66
    KEY_LEFTSHIFT = 42
    KEY_RIGHTSHIFT = 54

class InputEvent:
    """Stub for evdev.InputEvent"""
    def __init__(self, sec: int, usec: int, type: int, code: int, value: int) -> None:
        self.sec = sec
        self.usec = usec
        self.type = type
        self.code = code
        self.value = value
        self.timestamp = time.time()

class InputDevice:
    """Stub for evdev.InputDevice"""
    def __init__(self, path: str) -> None:
        self.path = path
        self.name = "Stub Input Device"
        self.capabilities = lambda: {}
        
    def read_loop(self) -> Iterator[InputEvent]:
        """Generator that yields input events"""
        while True:
            yield InputEvent(0, 0, 0, 0, 0)
    
    def grab(self) -> None:
        pass
    
    def ungrab(self) -> None:
        pass
    
    def close(self) -> None:
        pass

class UInput:
    """Stub for evdev.UInput"""
    def __init__(self, events: Optional[Dict[int, List[int]]] = None, name: str = "py-evdev-uinput", **kwargs) -> None:
        self.name = name
        self.events = events or {}
    
    def write(self, etype: int, code: int, value: int) -> None:
        pass
    
    def syn(self) -> None:
        pass
    
    def close(self) -> None:
        pass
    
    def __enter__(self) -> 'UInput':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
