import argparse
import logging
from time import time, ctime
from dataclasses import dataclass
from collections import deque  # for storing x, y time series
import numpy as np  # for smoothing moving average
import ctypes  # for windows mouse POINT struct
import socket  # udp networking
import struct  # binary unpacking
# import keyboard # keyboard shortcuts

from pynput import keyboard




# Collect events until released
# with keyboard.Listener(
#         on_press=on_press,
#         on_release=on_release) as listener:
#     listener.join()

# ...or, in a non-blocking fashion:


enabled = True

def toggle():
    global enabled
    logging.info("\nToggled PhilNav on/off\n")
    enabled = not enabled

# https://pynput.readthedocs.io/en/latest/keyboard.html#global-hotkeys

def for_canonical(f):
    return lambda k: f(listener.canonical(k))

hotkey = keyboard.HotKey(
    [keyboard.Key.shift, keyboard.Key.f7.value],
    toggle)

listener = keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release))

listener.start()

# keyboard.add_hotkey('space', toggle)
# keyboard.add_hotkey('space', toggle)

# keyboard.write('The quick brown fox jumps over the lazy dog.')
# keyboard.add_hotkey('space', lambda: print('space was pressed!'))

# returned from ctypes.windll.user32.GetCursorPos
# simple point.x, point.y
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

import platform
# Done: Windows
# TODO: Mac, Linux
match platform.system():
    case "Darwin": # macOS
        from mouse_mac import getCursorPos, setCursorPos


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
    "-s", "--speed", type=int, default=25, help="mouse speed, default 25"
)
parser.add_argument(
    "-S", "--smooth", type=int, default=3, help="averages mouse movements to smooth out jittering, default 3"
)
args = parser.parse_args()
if args.smooth < 1:
    args.smooth = 1


if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info(" Logging verbosely\n")




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
    f"Listening on {sock.getsockname()} for mouse data from Raspberry Pi server..."
)
print(ctime() + " - " + text_listening)
print("\nPress Ctrl-C to exit\n")


# Stats for debugging & performance. The goal is 60 frames per second, or
# 16.67ms per frame. That leads to a very smooth mouse cursor. (SmartNav was 100
# fps) A standard non-gaming monitor is also 60Hz. (TV is 30 fps)
@dataclass
class PhilNav:
    time_start = time()
    time_debug = time()
    debug_num = 0
    msg_time_start = time()
    msg_time_total = 0
    msg_num = 0
    x_q = deque([], args.smooth)
    y_q = deque([], args.smooth)
    x_q_long = deque([], args.smooth*3)
    y_q_long = deque([], args.smooth*3)


def smooth(q):
    sum = np.sum(q)
    avg = sum / len(q)
    return avg


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
        if int(time() - PhilNav.time_start) % 5 == 0:
            logging.info(f" {ctime()} - {text_listening}")
        continue
    else:
        # measure time
        PhilNav.msg_time_start = time()
        PhilNav.msg_num += 1

        # Using OpenTrack protocol, but PhilNav uses:
        #  x_diff, y_diff, n/a, n/a, n/a, camera capture time
        x, y, z, pitch, yaw, roll = struct.unpack("dddddd", data)

        # Simple moving average to smooth out jitters
        PhilNav.x_q.append(x)
        PhilNav.y_q.append(y)
        PhilNav.x_q_long.append(x)
        PhilNav.y_q_long.append(y)
        if x**2 + y**2 < 0.2:
            x_smooth = smooth(PhilNav.x_q_long)
            y_smooth = smooth(PhilNav.y_q_long)
        elif x**2 + y**2 < 0.5:
            x_smooth = smooth(PhilNav.x_q)
            y_smooth = smooth(PhilNav.y_q)
        else:
            x_smooth = x
            y_smooth = y

        # The Magic Happens Now! eg. move mouse cursor =P
        x_cur, y_cur = getCursorPos()
        # get current mouse position by reference (C++ thing)
        # I'm moving the Y axis slightly faster because looking left and right
        # is easier than nodding up and down. Also, monitors are wider than they
        # are tall.
        x_new = round(x_cur + x_smooth * args.speed)
        y_new = round(y_cur + y_smooth * args.speed * 1.25)
        if enabled:
            setCursorPos(x_new, y_new)  # move mouse cursor

        # I'm trying to measure the total time from capturing the frame on the
        # camera to moving the mouse cursor on my PC. This isn't super accurate.
        # It's sometimes negative (TIME TRAVEL!!!). The clock difference between
        # the Raspberry Pi and my PC seems to be around 10-20ms?
        time_diff_ms = int((time() - roll) * 1000)

        # it's 60 FPS, so only debug once per second
        if time() - PhilNav.time_debug > 1:
            PhilNav.time_debug = time()
            PhilNav.debug_num += 1
            # display legend every 5 seconds
            if PhilNav.debug_num % 5 == 1:
                logging.info(
                    f" {ctime()} - Received: ({'x_diff':>8},{'y_diff':>8},{'n/a':>8},{'n/a':>8},{'loc ns':>8},{'net ms':>8}  )"
                )
            logging.info(
                f" {ctime()} - Received: ({x:> 8.2f},{y:> 8.2f},{z:> 8.2f},{pitch:> 8.2f},{(time() - PhilNav.msg_time_start)*1000:> 8.2f},{time_diff_ms:> 8}  )"
            )
