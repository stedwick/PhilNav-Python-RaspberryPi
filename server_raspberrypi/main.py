import argparse
import logging
from time import time, ctime, perf_counter, sleep
from dataclasses import dataclass
from threading import Thread
import socket  # udp networking
import struct  # binary packing
from picamera2 import Picamera2, Preview, MappedArray  # Raspberry Pi camera
from libcamera import Transform  # taking selfies, so used to mirror image
import cv2  # OpenCV, for blob detection
from scale_contour import scale_contour


@dataclass
class text:
    intro = "\n\nSERVER: Starting PhilNav\n\nWelcome to PhilNav, I'm Phil!\n\nIf running PhilNav for the first time, use --help and --preview to set up your camera.\n"
    preview = "Adjust the camera controls (listed with --help) until you get a mostly black picture with bright white reflective IR sticker in the center. The controls default to what worked for Phil via trial and error.\n"


print(text.intro)


# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "-v", "--verbose", action="store_true", help="enable verbose logging"
)
parser.add_argument(
    "--preview",
    action="store_true",
    help="Use when logged into Raspberry Pi Gui; will show camera preview.",
)
parser.add_argument(
    "--fps", type=float, default=75.0, help="camera FrameRate, default 75"
)
parser.add_argument(
    "--width", type=int, default=320, help="camera resolution width, default 320"
)
parser.add_argument(
    "--height", type=int, default=240, help="camera resolution height, default 240"
)
parser.add_argument(
    "--gain", type=float, default=2.0, help="camera AnalogueGain, default 2.0"
)
parser.add_argument(
    "--brightness", type=float, default=-0.4, help="camera Brightness, default -0.4"
)
parser.add_argument(
    "--contrast", type=float, default=5.0, help="camera Contrast, default 5.0"
)
parser.add_argument(
    "--exposure", type=float, default=1.0, help="camera ExposureValue, default 1.0"
)
parser.add_argument(
    "--saturation", type=float, default=0.0, help="camera Saturation, default 0.0"
)
parser.add_argument(
    "--no-hflip",
    action="store_true",
    help="images are selfies and flipped horizontally by default",
)
parser.add_argument(
    "--blob-size", type=int, default=15, help="OpenCV blob minimum size, default 15"
)
parser.add_argument(
    "--blob-color",
    type=int,
    default=255,
    help="OpenCV blob detection color, default 255 (white = 255, or black = 0)",
)
parser.add_argument(
    "--blob-min-threshold",
    type=int,
    default=200,
    help="Blob must be this bright to detect, default 200 (white = 255, or black = 0)",
)
parser.add_argument(
    "--contours",
    action="store_true",
    help="Tracks the outer perimeter of your reflective sticker. Eg. a pacman shape is tracked as a full circle. This can provide better tracking if your sticker is dull or off-center.",
)
parser.add_argument(
    "--timeout",
    type=int,
    default=0,
    help="exit after n seconds, default none (uses heartbeat from client). Setting a timeout will run PhilNav for N seconds and then exit, ignoring heartbeats.",
)
parser.add_argument(
    "--ip",
    type=str,
    default="224.3.0.186",
    help="remote ip address of PC that will receive mouse movements, default 224.3.0.186 (udp multicast group). Or, find your PC's home network ip (not internet ip); usually 192.x.x.x, 172.x.x.x, or 10.x.x.x",
)
parser.add_argument(
    "--port",
    type=int,
    default=4245,
    help="send to remote port, default 4245. Receives heartbeats from client on port+1 (4246). If you have a firewall, these ports must be open to send/recv UDP.",
)
args = parser.parse_args()

if args.verbose:
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Logging verbosely\n")

if args.preview:
    print(text.preview)

hflip_num = 1
if args.no_hflip:
    hflip_num = 0


picam2 = Picamera2()
# The camera can be "configured" and "controlled" with different settings in each.
config_main = {"size": (args.width, args.height)}
# Not entirely sure how configurations work, preview/main etc.
config = picam2.create_preview_configuration(
    main=config_main, transform=Transform(hflip=hflip_num)
)
picam2.configure(config)

controls = {
    "AnalogueGain": args.gain,
    "Brightness": args.brightness,
    "Contrast": args.contrast,
    "ExposureValue": args.exposure,
    "Saturation": args.saturation,
    "FrameRate": args.fps,
}
picam2.set_controls(controls)


# OpenCV blob detection config
params = cv2.SimpleBlobDetector_Params()
params.filterByArea = True
params.minArea = args.blob_size
params.filterByColor = True
params.blobColor = args.blob_color
params.minThreshold = args.blob_min_threshold
params.maxThreshold = 255
params.thresholdStep = 50
params.minRepeatability = 2
params.minDistBetweenBlobs = 100
params.filterByCircularity = False
params.filterByConvexity = False
params.filterByInertia = False
detector = cv2.SimpleBlobDetector_create(params)


def philnav_start():
    if picam2.started:
        return
    if args.preview:
        picam2.start_preview(Preview.QT)
    else:
        picam2.start_preview(Preview.NULL)

    # Not sure if we need both start_preview and start.
    picam2.start()
    sleep(1)  # let camera warm up

    # show intro again
    print(text.intro)
    if args.preview:
        print(text.preview)


def philnav_stop():  # cleanup
    if not picam2.started:
        return
    picam2.stop_preview()
    picam2.stop()


# Set up UDP socket to receiving computer
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # datagrams over UDP
sock_addr = (args.ip, args.port)

# initialize networking
# Read heartbeat datagrams over UDP
sock_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Without a timeout, this script will "hang" if nothing is received
sock_heartbeat.settimeout(60 * 10)
sock_heartbeat.bind(("0.0.0.0", args.port + 1))  # Register our socket
# https://pymotw.com/2/socket/multicast.html
if args.ip.startswith("224"):  # join multicast group
    group = socket.inet_aton(args.ip)
    mreq = struct.pack("4sL", group, socket.INADDR_ANY)
    sock_heartbeat.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


def heartbeat_run():
    while True:
        try:
            data, addr = sock_heartbeat.recvfrom(48)
        except TimeoutError:
            logging.info(f"{ctime()} - Waiting for a heartbeat from client...")
            philnav_stop()
            continue
        else:
            logging.info(f"{ctime()} - Received heartbeat from client.")
            philnav_start()


now = time()
perf = perf_counter()
# Global for storing data from loop-to-loop, also stats for debugging


@dataclass
class phil:
    started_at = now
    heartbeat_at = now
    frame_started_at = now
    frame_perf = perf
    frame_between = perf
    frame_num = 0
    x = 0.0
    y = 0.0
    debug_num = 0
    keypoint = None  # for debugging inspection


# This is where the Magic happens! The camera should pick up nothing but a white
# dot from your reflective IR sticker. I use opencv blob detection to track its
# (x, y) coordinates and send the changes to the receiving computer, which moves
# the mouse.
def blobby(request):
    phil.frame_perf = perf_counter()
    phil.frame_started_at = time()
    phil.frame_num += 1
    ms_frame_between = (perf_counter() - phil.frame_between) * 1000
    x_diff = 0.0
    y_diff = 0.0

    # MappedArray gives direct access to the captured camera frame
    with MappedArray(request, "main") as m:
        # https://www.fypsolutions.com/opencv-python/findcontours-opencv-python-drawcontours-opencv-python/
        if args.contours:
            im_gray = cv2.cvtColor(m.array, cv2.COLOR_BGR2GRAY)
            _ret, thresh = cv2.threshold(im_gray, args.blob_min_threshold, 255, 0)
            contours, _hierarchy = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )
            if len(contours) > 0:
                contour_biggest = max(contours, key=cv2.contourArea)
                convex_hull = cv2.convexHull(contour_biggest)
                hull_scaled = scale_contour(convex_hull, 0.7)
                if hull_scaled is not None:
                    cv2.drawContours(
                        m.array, [hull_scaled], -1, (255, 255, 255), cv2.FILLED
                    )

        # Track the IR sticker
        keypoints = detector.detect(m.array)
        if args.preview:
            # Draw red circles around the detected blobs, in-place on array
            cv2.drawKeypoints(
                m.array,  # source image
                keypoints,
                m.array,  # dest image
                (255, 0, 0),  # RGB
                # For each keypoint the circle around keypoint with keypoint
                # size and orientation will be drawn.
                cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
            )

        # Ideally should be exactly one keypoint, or use biggest
        if len(keypoints) > 0:
            kp = max(keypoints, key=lambda x: x.size)
            # Compare the (x, y) coordinates from last frame
            x_new, y_new = kp.pt
            x_diff = x_new - phil.x
            y_diff = y_new - phil.y
            phil.x = x_new
            phil.y = y_new

            # If the IR sticker has moved smoothly, but not "jumped"...
            # Jumping can occur if multiple blobs are detected, such as other
            # IR reflective surfaces in the camera's view, like glasses lenses.
            if (x_diff**2 > 0 or y_diff**2 > 0) and x_diff**2 < 50 and y_diff**2 < 50:
                # Send the (x_diff, y_diff) to the receiving computer.
                # For performance stats, I'm also sending the time spent on
                # Raspberry Pi.
                #
                # 48 bytes of 6 doubles in binary C format. Why? Because it's
                # OpenTrack's protocol.
                # struct.pack('dddddd', x, y, z, pitch, yaw, roll)
                # PhilNav uses x, y as x_diff, y_diff and moves the mouse
                # relative to its current position.
                # https://github.com/opentrack/opentrack/issues/747
                ms_time_spent = (perf_counter() - phil.frame_perf) * 1000
                msg = struct.pack(
                    "dddddd",
                    x_diff,
                    y_diff,
                    0.0,
                    0.0,
                    phil.frame_started_at,
                    ms_time_spent,
                )
                sock.sendto(msg, sock_addr)

        # Log once per second
        if args.verbose and (phil.frame_num % int(args.fps) == 0):
            phil.debug_num += 1
            c_time = ctime()
            fps_measured = phil.frame_num / (time() - phil.started_at)
            ms_measured = (perf_counter() - phil.frame_perf) * 1000
            # display legend every 5 seconds
            if phil.debug_num % 5 == 1:
                logging.info(
                    f"{c_time} - {'Frame':>8}, ({'x_diff':>8}, {'y_diff':>8})  , {'FPS':>8}, {'cv ms':>8}, {'btw ms':>8}"
                )
            logging.info(
                f"{c_time} - {phil.frame_num:>8}, ({x_diff:> 8.2f}, {y_diff:> 8.2f})  , {int(fps_measured):>8}, {int(ms_measured):>8}, {int(ms_frame_between):>8}"
            )

        # Time between capturing frames from the camera.
        phil.frame_between = perf_counter()


picam2.pre_callback = blobby

if args.timeout == 0:
    heartbeat_thread = Thread(target=heartbeat_run, daemon=True)
    heartbeat_thread.start()

# Run the loop until Ctrl-C or timeout
try:
    t = args.timeout
    if t == 0:
        t = 60 * 60 * 24 * 365
    philnav_start()
    sleep(t)  # turn off after a year
except KeyboardInterrupt:
    pass

philnav_stop()
picam2.close()
