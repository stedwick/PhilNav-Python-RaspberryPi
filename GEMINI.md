# Project Overview

This project, PhilNav, is a high-performance, open-source head-tracking mouse system. It allows for hands-free computer operation by tracking a reflective sticker on the user's head and translating its movement into mouse cursor motion.

The system is built with a client-server architecture:

- **Server:** Runs on a Raspberry Pi equipped with a PiCamera Module 3 NoIR. It uses Python with `picamera2` for camera interfacing and `opencv-python` for real-time blob detection of the reflective sticker. The server calculates the movement delta and broadcasts it over the local network via UDP.

- **Client:** Runs on a Windows, macOS, or Linux machine. It listens for the UDP broadcasts from the server and uses platform-specific libraries to control the mouse cursor.

The communication between the client and server is done using the OpenTrack protocol, with the movement data packed as `struct` doubles.

## Type Checking

This project uses Pyright for comprehensive static type checking across all platforms (Windows, Mac, Linux, Raspberry Pi). **Always run `pyright` after making any code changes** to ensure type correctness. The project maintains zero errors and zero warnings.

```bash
# Check entire project
pyright

# Check with statistics
pyright --stats
```

# Building and Running

## Dependencies

### Server (Raspberry Pi)

- `python3-opencv`
- `picamera2`
- `libcamera`

These can be installed via `apt`:

```bash
sudo apt install python3-opencv
```

### Client (Desktop)

- `evdev` (for Linux/Wayland)

This can be installed via `pip`:

```bash
pip install evdev
```

## Running the Application

1.  **Start the Server:** On the Raspberry Pi, run the following command. The `--preview` flag is useful for initial setup to ensure the camera is positioned correctly.

    ```bash
    python3 server_raspberrypi/main.py --verbose --preview
    ```

2.  **Start the Client:** On your desktop machine, run:

    ```bash
    python3 client_win-mac-nix/main.py --verbose
    ```

The application can be configured using various command-line arguments on both the client and server. Use the `--help` flag to see all available options.

# Development Conventions

- **Code Style:** The code follows standard Python conventions (PEP 8).
- **Modularity:** The project is organized into two main components: `client_win-mac-nix` and `server_raspberrypi`. Within the client, platform-specific logic is further separated into individual modules (e.g., `mouse_mac.py`, `mouse_win.py`, `mouse_nix_uinput.py`).
- **Configuration:** All configuration is handled through command-line arguments via the `argparse` library. There are no configuration files.
- **Networking:** Communication is done via UDP multicast, which simplifies network configuration as the client and server don't need to know each other's IP addresses.
- **Error Handling:** The code includes basic error handling, such as timeouts for network operations.
