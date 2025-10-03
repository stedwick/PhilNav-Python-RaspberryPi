"""
Stub file for ctypes.windll to enable type checking on non-Windows systems.
This provides the basic API structure for Windows API calls.
"""
from typing import Any
import ctypes

class User32:
    """Stub for user32.dll"""
    def GetCursorPos(self, point: Any) -> bool:
        # Simulate getting cursor position
        if hasattr(point, 'contents'):
            point.contents.x = 0
            point.contents.y = 0
        return True
    
    def SetCursorPos(self, x: int, y: int) -> bool:
        return True

class Kernel32:
    """Stub for kernel32.dll"""
    def GetLastError(self) -> int:
        return 0

class WinDLL:
    """Stub for windll container"""
    def __init__(self) -> None:
        self.user32 = User32()
        self.kernel32 = Kernel32()

# Create the windll instance that ctypes would normally provide
windll = WinDLL()
