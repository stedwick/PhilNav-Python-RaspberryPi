# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PhilNav is an open-source infrared head mouse system that tracks a reflective sticker on your head to control mouse movements. It uses a client/server architecture:

- **Server**: Runs on Raspberry Pi 5 with Picam 3 NoIR camera, performs IR blob detection
- **Client**: Runs on Windows/Mac/Linux PC, receives tracking data and moves mouse

Communication happens over UDP multicast (ports 4245/4246).

## Architecture

### Server (Raspberry Pi)

- `server_raspberrypi/main.py`: Camera capture, blob detection, UDP broadcasting
- Uses picamera2 for camera control and cv2 (OpenCV) for blob detection
- Sends x,y coordinates at 75 FPS via UDP multicast

### Client (PC)

- `client_win-mac-nix/main.py`: Main client, receives coordinates, handles mouse movement
- Platform-specific mouse implementations:
  - `mouse_mac.py`: macOS via Quartz
  - `mouse_win.py`: Windows via ctypes
  - `mouse_nix_uinput.py`: Linux via evdev/uinput (Wayland & X11)
  - `mouse_nix_x11.py`: Legacy X11 via python-xlib
- Platform-specific hotkey implementations:
  - `hotkey_win_mac.py`: Windows/Mac via pynput
  - `hotkey_nix_uinput.py`: Linux via evdev
  - `hotkey_nix_x11.py`: Legacy X11 via python-xlib

## Development Commands

### Running the Server (Raspberry Pi)

```bash
# Basic run
python3 server_raspberrypi/main.py

# With preview (requires GUI)
python3 server_raspberrypi/main.py --preview --verbose

# Common configuration
python3 server_raspberrypi/main.py --fps 75 --width 320 --height 240
```

### Running the Client (PC)

```bash
# Basic run
python3 client_win-mac-nix/main.py

# With common settings
python3 client_win-mac-nix/main.py --speed 21 --smooth 3 --deadzone 0.04 --verbose

# Keep PC awake during 8-hour workday
python3 client_win-mac-nix/main.py --keepawake 56 --timeout $((60*60*8))
```

### Dependencies Installation

#### Server (Raspberry Pi)

```bash
sudo apt install python3-opencv
# picamera2 is typically pre-installed on Raspberry Pi OS
```

#### Client

```bash
# macOS
pip install pyobjc-framework-Quartz pynput

# Windows
pip install pynput

# Linux (Wayland/X11 with uinput)
pip install evdev
# or
sudo apt install python3-evdev

# Linux (X11 legacy)
pip install python-xlib
```

## Key Technical Details

### Hotkeys

- **Shift+F7**: Toggle PhilNav on/off
- **Shift+F8**: Toggle speed multiplier (default 3x)

### Network Protocol

- UDP multicast group: 224.3.0.186
- Port 4245: Mouse coordinate data (server → client)
- Port 4246: Heartbeat messages (client → server)
- Binary format: struct packed floats for x,y coordinates

### Linux /dev/uinput Setup

For modern Linux (Wayland & X11), the client uses /dev/uinput which requires permissions:

```bash
sudo usermod -a -G input $USER
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-input.rules
sudo shutdown -r now
```

### Platform Detection

The client automatically detects the platform and loads appropriate mouse/hotkey modules using Python's `platform.system()` and match/case statements.

### Type Checking with Pyright

The project includes comprehensive type checking support:

```bash
# Install Pyright (if not already installed)
pip install pyright

# Check entire project
pyright

**Cross-Platform Type Checking**: The server code includes conditional imports and type stubs in the `stubs/` directory that allow full type checking even on non-Pi development machines:

Configuration is in `pyrightconfig.json` with platform-specific file exclusions and stub path configuration.

## Important Configuration Parameters

### Client

- `--speed`: Mouse sensitivity (default 25)
- `--smooth`: Movement averaging to reduce jitter (default 3)
- `--deadzone`: Minimum movement threshold (default 0.03)
- `--multiplier`: Speed multiplier when F8 toggled (default 3.0)

### Server

- `--blob-size`: Minimum blob size for detection (default 15)
- `--blob-min-threshold`: Brightness threshold for blob detection (default 200)
- `--contours`: Enable contour tracking for better detection with dull stickers
- Camera controls: `--gain`, `--brightness`, `--contrast`, `--exposure`
```
