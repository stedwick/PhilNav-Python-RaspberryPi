import argparse, logging
from time import time, ctime
from dataclasses import dataclass
import math, random
from collections import deque  # for storing x, y time series
import socket  # udp networking
import struct  # binary unpacking
from pynput import keyboard # for hotkeys

print("\n\nCLIENT: Starting PhilNav\n\nWelcome to PhilNav, I'm Phil!\n\nUse --help for more info.\n")

import platform
match platform.system():
    case "Darwin": # macOS
        from mouse_mac import getCursorPos, setCursorPos
    case "Windows":
        from mouse_win import getCursorPos, setCursorPos
    case "Linux":
        from mouse_nix import getCursorPos, setCursorPos
    case _:
        raise RuntimeError(f"Platform {platform.system()} not supported (not Win, Mac, or Nix)")


# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "-v", "--verbose", action="store_true", help="enable verbose logging"
)
parser.add_argument(
    "-s", "--speed", type=int, default=25, help="mouse speed, default 25"
)
parser.add_argument(
    "-S", "--smooth", type=int, default=3, help="averages mouse movements to smooth out jittering, default 3"
)
parser.add_argument(
    "-d", "--deadzone", type=float, default=0.0, help="Mouse must move by at least this much, otherwise it stays still. Use this if you are having difficulty with small mouse movements, or with keeping the cursor still. Recommend 0.0, 0.05 or 0.1, default 0.0"
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
    "-w", "--keepawake", type=int, default=0, help="Keep PC awake by randomly moving the mouse a few pixels every N seconds, default off"
)

args = parser.parse_args()

if args.smooth < 1:
    args.smooth = 1

if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Logging verbosely\n")


# Hotkey to pause/resume moving the mouse
enabled = True

def toggle():
    global enabled
    enabled = not enabled
    logging.info("Toggled PhilNav on/off\n")

# Shift-F7 hard-coded for now
hotkey_toggle = keyboard.HotKey(
    [keyboard.Key.shift, keyboard.Key.f7.value],
    toggle)

# https://pynput.readthedocs.io/en/latest/keyboard.html#global-hotkeys
def for_canonical(f):
    global listener
    return lambda k: f(listener.canonical(k))

listener = keyboard.Listener(
        on_press=for_canonical(hotkey_toggle.press),
        on_release=for_canonical(hotkey_toggle.release))

listener.start()


# initialize networking
# Read datagrams over UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Without a timeout, this script will "hang" if nothing is received
sock.settimeout(1)
sock.bind((args.host, args.port))  # Register our socket

# How to get local IP address in python?
text_listening = (
    f"Listening on {sock.getsockname()} for mouse data from Raspberry Pi server..."
)
print(ctime() + " - " + text_listening)
print("\nPress Ctrl-C to exit, press Shift-F7 to pause/resume\n")


# Stats for debugging & performance. The goal is 60 frames per second, or
# 16.67ms per frame. That leads to a very smooth mouse cursor. (SmartNav was 100
# fps) A standard non-gaming monitor is also 60Hz. (TV is 30 fps)

# mouse (x_diff, y_diff) smoothing running averages
smooth_long = args.smooth*3+1
@dataclass
class phil:
    time_start = time()
    time_last_moved = time()
    time_debug = time()
    debug_num = 0
    x_q = deque([], args.smooth)
    x_q_smooth = 0
    x_q_long = deque([], smooth_long)
    x_q_long_smooth = 0
    y_q = deque([], args.smooth)
    y_q_smooth = 0
    y_q_long = deque([], smooth_long)
    y_q_long_smooth = 0


# simple moving average to reduce mouse jitter
def smooth(q):
    avg = sum(q) / len(q)
    return avg


# for keep-awake
def mouse_move_random():
    x_cur, y_cur = getCursorPos()
    x_new = round(x_cur + random.randint(-5, 5))
    y_new = round(y_cur + random.randint(-5, 5))
    setCursorPos(x_new, y_new)  # move mouse cursor


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
        if int(time() - phil.time_start) % 5 == 0:
            logging.info(f"{ctime()} - {text_listening}")
        continue
    else:
        time_iter = time()
        if not enabled:
            if args.keepawake > 0 and args.keepawake < (time_iter - phil.time_last_moved):
                mouse_move_random()
                phil.time_last_moved = time_iter
            continue

        # Using OpenTrack protocol, but PhilNav uses:
        #  x_diff, y_diff, n/a, n/a, camera capture time, OpenCV processing time
        x_diff, y_diff, a, b, time_cam, ms_opencv = struct.unpack("dddddd", data)

        # store recent mouse movements
        phil.x_q.append(x_diff)
        phil.x_q_smooth = smooth(phil.x_q)
        phil.y_q.append(y_diff)
        phil.y_q_smooth = smooth(phil.y_q)
        phil.x_q_long.append(x_diff)
        phil.x_q_long_smooth = smooth(phil.x_q_long)
        phil.y_q_long.append(y_diff)
        phil.y_q_long_smooth = smooth(phil.y_q_long)

        # Perform more smoothing the *slower* the mouse is moving.
        # A slow-moving cursor means the user is trying to precisely
        # point at something.
        if x_diff**2 + y_diff**2 < 0.2: # more smoothing
            x_smooth = phil.x_q_long_smooth
            y_smooth = phil.y_q_long_smooth
        elif x_diff**2 + y_diff**2 < 0.5: # less smoothing
            x_smooth = phil.x_q_smooth
            y_smooth = phil.y_q_smooth
        else: # moving fast, no smoothing
            x_smooth = x_diff
            y_smooth = y_diff

        # Prevent small jittering when holding mouse cursor still inside deadzone.
        accel_avg = math.sqrt(phil.x_q_smooth**2 + phil.y_q_smooth**2)
        if accel_avg > 0 and accel_avg < args.deadzone:
            continue

        # The Magic Happens Now!
        x_cur, y_cur = getCursorPos()
        # I'm moving the Y axis slightly faster because looking left and right
        # is easier than nodding up and down. Also, monitors are wider than they
        # are tall.
        x_new = round(x_cur + x_smooth * args.speed)
        y_new = round(y_cur + y_smooth * args.speed * 1.25)
        setCursorPos(x_new, y_new)  # move mouse cursor
        phil.time_last_moved = time()

        # I'm trying to measure the total time from capturing the frame on the
        # camera to moving the mouse cursor on my PC. This isn't super accurate.
        # It's sometimes negative (TIME TRAVEL!!!). The clock difference between
        # the Raspberry Pi and my PC seems to be around 10-20ms?
        now = time()
        now_str = ctime()
        ms_time_diff = int((now - time_cam) * 1000)

        # it's 60 FPS, so only debug once per second
        if now - phil.time_debug > 1:
            phil.time_debug = now
            phil.debug_num += 1
            # display legend every 5 seconds
            if phil.debug_num % 5 == 1:
                logging.info(
                    f"{now_str} - Received: ({'x_diff':>8},{'y_diff':>8})  ,{'n/a':>8},{'n/a':>8},{'time ms':>8},{'time cv':>8}"
                )
            logging.info(
                f"{now_str} - Received: ({x_diff:> 8.2f},{y_diff:> 8.2f})  ,{a:> 8.2f},{b:> 8.2f},{ms_time_diff:>8},{ms_opencv:>8.2f}"
            )
