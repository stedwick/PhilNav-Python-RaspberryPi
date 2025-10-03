"""
Stub file for picamera2 to enable type checking on non-Pi systems.
This provides the basic API structure without actual camera functionality.
"""
from typing import Any, Optional, Callable, Dict, Tuple
import numpy as np

class MappedArray:
    """Stub for picamera2.MappedArray"""
    def __init__(self, request: Any, name: str = "main") -> None:
        self.array = np.zeros((480, 640, 3), dtype=np.uint8)
    
    def __enter__(self) -> 'MappedArray':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

class Preview:
    """Stub for picamera2.Preview"""
    QT = "qt"
    NULL = "null"

class Picamera2:
    """Stub for picamera2.Picamera2"""
    
    def __init__(self) -> None:
        self.started = False
        self.pre_callback: Optional[Callable] = None
    
    def configure(self, config: Dict[str, Any]) -> None:
        pass
    
    def start_preview(self, preview: Any) -> None:
        pass
    
    def stop_preview(self) -> None:
        pass
    
    def start(self) -> None:
        self.started = True
    
    def stop(self) -> None:
        self.started = False
    
    def close(self) -> None:
        pass
    
    def capture_array(self, name: str = "main") -> np.ndarray:
        # Return a dummy array for type checking
        return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def set_controls(self, controls: Dict[str, Any]) -> None:
        pass
    
    def create_preview_configuration(self, **kwargs) -> Dict[str, Any]:
        return {}
    
    def create_still_configuration(self, **kwargs) -> Dict[str, Any]:
        return {}
    
    def capture_request(self) -> Any:
        return MappedArray(np.zeros((480, 640, 3), dtype=np.uint8))
