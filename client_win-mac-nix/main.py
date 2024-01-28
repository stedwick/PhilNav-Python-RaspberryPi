import argparse
import logging
from time import time, ctime
from dataclasses import dataclass
import ctypes  # for windows mouse
import socket  # udp networking
import struct  # binary unpacking

print("\n\nCLIENT: Starting PhilNav\n")

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "-v", "--verbose", action="store_true", help="provide verbose logging"
)
parser.add_argument(
    "-H",
    "--host",
    type=str,
    default="0.0.0.0",
    help="bind to ip address, default 0.0.0.0",
)
parser.add_argument(
    "-p", "--port", type=int, default=4245, help="bind to port, default 4245"
)
parser.add_argument(
    "-s", "--speed", type=int, default=30, help="mouse speed, default 30"
)
args = parser.parse_args()

if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info(" Logging verbosely\n")


# returned from ctypes.windll.user32.GetCursorPos
# simple point.x, point.y
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


# initialize networking
# Read datagrams over UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Without a timeout, this script will "hang" if nothing is received
sock.settimeout(1)
sock.bind((args.host, args.port))  # Register our socket

# How to get local IP address?
# Doesn't work for me: socket.gethostbyname(socket.gethostname())
# For now, just manually go to settings -> Wi-fi and look up your *local* IP
# address. It will be something like 192.x.x.x or 10.x.x.x This is not your
# public Internet address. This is your local area network address. On Windows,
# make sure it's set to a private network to allow discovery. You'd think public
# would allow discovery, but when you are *in public* - like at a coffee shop -
# you don't want strangers to access your PC.
text_listening = (
    f"Listening on {
        sock.getsockname()} for mouse data from Raspberry Pi server..."
)
print(ctime() + " - " + text_listening)
print("\nPress Ctrl-C to exit\n")


# Stats for debugging & performance. The goal is 60 frames per second, or
# 16.67ms per frame. That leads to a very smooth mouse cursor. (SmartNav was 100
# fps) A standard non-gaming monitor is also 60Hz. (TV is 30 fps)
@dataclass
class PhilNavDebug:
    time_start = time()
    time_debug = time()
    debug_num = 0
    msg_time_start = time()
    msg_time_total = 0
    msg_num = 0


# Main event loop:
# 1. Receive mouse delta over UDP
# 2. Update mouse cursor position
# 3. Repeat forever until Ctrl-C
while True:
    try:
        # 48 bytes of 6 doubles in binary C format. Why? Because it's
        # OpenTrack's protocol.
        # x, y, z, pitch, yaw, roll = struct.unpack('dddddd', data)
        # PhilNav uses x, y as x_diff, y_diff and moves the mouse relative to
        # its current position.
        # https://github.com/opentrack/opentrack/issues/747
        data, addr = sock.recvfrom(48)
    except TimeoutError:
        if int(time() - PhilNavDebug.time_start) % 5 == 0:
            logging.info(f" {ctime()} - {text_listening}")
        continue
    else:
        # measure time
        PhilNavDebug.msg_time_start = time()
        PhilNavDebug.msg_num += 1

        # Using OpenTrack protocol, but PhilNav uses:
        #  x_diff, y_diff, n/a, n/a, n/a, camera capture time
        x, y, z, pitch, yaw, roll = struct.unpack("dddddd", data)

        # The Magic Happens Now! eg. move mouse cursor =P
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(
            ctypes.byref(pt)
        )  # get current mouse position by reference (C++ thing)
        # I'm moving the Y axis slightly faster because looking left and right
        # is easier than nodding up and down. Also, monitors are wider than they
        # are tall.
        x_new = round(pt.x + x * args.speed)
        y_new = round(pt.y + y * args.speed * 1.33)
        ctypes.windll.user32.SetCursorPos(x_new, y_new)  # move mouse cursor

        # I'm trying to measure the total time from capturing the frame on the
        # camera to moving the mouse cursor on my PC. This isn't super accurate.
        # It's sometimes negative (TIME TRAVEL!!!). The clock difference between
        # the Raspberry Pi and my PC seems to be around 10-20ms?
        time_diff_ms = int((time() - roll) * 1000)

        # it's 60 FPS, so only debug once per second
        if time() - PhilNavDebug.time_debug > 1:
            PhilNavDebug.time_debug = time()
            PhilNavDebug.debug_num += 1
            # display legend every 5 seconds
            if PhilNavDebug.debug_num % 5 == 1:
                logging.info(
                    f" {ctime()} - Received: ({'x_diff':>8},{'y_diff':>8},{
                        'n/a':>8},{'n/a':>8},{'loc ns':>8},{'net ms':>8}  )"
                )
            logging.info(
                f" {ctime()} - Received: ({x:> 8.2f},{y:> 8.2f},{z:> 8.2f},{pitch:> 8.2f},{
                    (time() - PhilNavDebug.msg_time_start)*1000:> 8.2f},{time_diff_ms:> 8}  )"
            )
