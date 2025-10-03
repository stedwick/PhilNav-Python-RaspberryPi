"""
Stub file for libcamera to enable type checking on non-Pi systems.
"""
from typing import Any, Union

class Transform:
    """Stub for libcamera.Transform"""
    
    def __init__(self, hflip: Union[bool, int] = False, vflip: Union[bool, int] = False) -> None:
        self.hflip = bool(hflip)
        self.vflip = bool(vflip)
