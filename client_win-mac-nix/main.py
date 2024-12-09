import platform
import argparse
import logging
from time import time, ctime
from dataclasses import dataclass
import math
import random
from collections import deque  # for storing x, y time series
import socket  # udp networking
import struct  # binary unpacking
from threading import Thread

print("\n\nCLIENT: Starting PhilNav\n\nWelcome to PhilNav, I'm Phil!\n\nUse --help for more info.\n")

match platform.system():
    case "Darwin":  # macOS
        from mouse_mac import getCursorPos, setCursorPos
        from hotkey_win_mac import hotkey_run
    case "Windows":
        from mouse_win import getCursorPos, setCursorPos
        from hotkey_win_mac import hotkey_run
    case "Linux":
        from mouse_nix_wayland import getCursorPos, setCursorPos
        from hotkey_nix_wayland import hotkey_run
    case _:
        raise RuntimeError(
            f"Platform {platform.system()} not supported (not Win, Mac, or Nix)")


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
    "-d", "--deadzone", type=float, default=0.03, help="Mouse must move by at least this much, otherwise it stays still. Use this if you are having difficulty with small mouse movements, or with keeping the cursor still. Recommend 0.0 - 0.15, default 0.03"
)
parser.add_argument(
    "-t", "--timeout", type=int, default=60*60*24, help="turn off after N seconds (eg. 60*60*8 is 8 hours or one workday), default 24 hours"
)
parser.add_argument(
    "-w", "--keepawake", type=int, default=0, help="Keep PC awake by randomly moving the mouse a few pixels every N seconds, default off"
)
parser.add_argument(
    "--port", type=int, default=4245, help="bind to port, default 4245. Heartbeats use port+1 (4246). If you have a firewall, these ports must be open to send/recv UDP."
)
parser.add_argument(
    "--bind-ip", type=str, default="0.0.0.0", help="ip address to bind to, default 0.0.0.0 (all)"
)
parser.add_argument(
    "--client-ip", type=str, default="224.3.0.186", help="ip address to listen on, default 224.3.0.186 (udp multicast group). Use 0.0.0.0 for direct udp, but this requires the server to know the client's ip."
)
parser.add_argument(
    "--server-ip", type=str, default="224.3.0.186", help="ip address to send heartbeats to (will wake server), default 224.3.0.186 (udp multicast group). Direct udp requires the server's ip for heartbeats, or disable heartbeats on the server."
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

hotkey_thread = Thread(target=hotkey_run, kwargs={"callback": toggle}, daemon=True)
hotkey_thread.start()


# initialize networking
# Read datagrams over UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Without a timeout, this script will "hang" if nothing is received
sock.settimeout(1)
sock.bind((args.bind_ip, args.port))  # Register our socket
# https://pymotw.com/2/socket/multicast.html
if args.client_ip.startswith("224"):  # join multicast group
    group = socket.inet_aton(args.client_ip)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Set up UDP socket to server
sock_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # datagrams over UDP
sock_heartbeat_addr = (args.server_ip, args.port+1) # heartbeat on 1 port higher
heartbeat_msg = struct.pack("dddddd", 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
def heartbeat():
    sock_heartbeat.sendto(heartbeat_msg, sock_heartbeat_addr)
    logging.info("Sent heartbeat.\n")


# How to get local IP address in python?
text_listening = (
    f"Listening on {args.client_ip} for mouse data from Raspberry Pi server..."
)
print(ctime() + " - " + text_listening)
print("\nPress Ctrl-C to exit, press Shift-F7 to pause/resume\n")


# Stats for debugging & performance. The goal is 60 frames per second, or
# 16.67ms per frame. That leads to a very smooth mouse cursor. (SmartNav was 100
# fps) A standard non-gaming monitor is also 60Hz. (TV is 30 fps)

# mouse (x_diff, y_diff) smoothing running averages
smooth_long = args.smooth*3+1

now = time()

@dataclass
class phil:
    time_start = now
    time_last_moved = now
    time_debug = now
    time_heartbeat = now
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
    # timers
    time_iter = time()
    time_btwn_moves = time_iter - phil.time_last_moved
    time_since_start = time_iter - phil.time_start

    if enabled and (time_iter - phil.time_heartbeat > 3):
        heartbeat()
        phil.time_heartbeat = time_iter

    # time-based functionality
    if args.timeout > 0 and time_since_start > args.timeout:
        break
    if not enabled:
        if args.keepawake > 0 and time_btwn_moves > args.keepawake:
            mouse_move_random()
            phil.time_last_moved = time_iter

    # get mouse data from Raspberry Pi
    try:
        # 48 bytes of 6 doubles in binary C format. Why? Because it's
        # OpenTrack's protocol.
        # x, y, z, pitch, yaw, roll = struct.unpack('dddddd', data)
        # PhilNav uses x, y as x_diff, y_diff and moves the mouse relative to
        # its current position.
        # https://github.com/opentrack/opentrack/issues/747
        data, addr = sock.recvfrom(48)
    except TimeoutError:
        if enabled and (int(time() - phil.time_start) % 5 == 0):
            logging.info(f"{ctime()} - {text_listening}")
        continue
    else:
        if not enabled:
            continue

        # Using OpenTrack protocol, but PhilNav uses:
        #  x_diff, y_diff, n/a, n/a, camera capture time, OpenCV processing time
        x_diff, y_diff, a, b, time_cam, ms_opencv = struct.unpack(
            "dddddd", data)

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
        if x_diff**2 + y_diff**2 < 0.2:  # more smoothing
            x_smooth = phil.x_q_long_smooth
            y_smooth = phil.y_q_long_smooth
        elif x_diff**2 + y_diff**2 < 0.5:  # less smoothing
            x_smooth = phil.x_q_smooth
            y_smooth = phil.y_q_smooth
        else:  # moving fast, no smoothing
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
