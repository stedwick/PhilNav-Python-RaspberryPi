import argparse
import logging
from time import time, perf_counter, sleep
from dataclasses import dataclass
import socket  # udp networking
import struct  # binary packing
from picamera2 import Picamera2, Preview, MappedArray  # Raspberry Pi camera
from libcamera import Transform  # taking selfies, so used to mirror image
import cv2  # OpenCV, for blob detection

print("\n\nSERVER: Starting PhilNav\n")

preview_text = "Adjust the camera controls listed with --help such that you get a mostly black picture with bright white reflective IR sticker in the center. The controls default to what worked for me via trial and error."

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--ip",
    required=True,
    type=str,
    help="remote ip address of PC that will receive mouse movements",
)
parser.add_argument(
    "-p", "--port", type=int, default=4245, help="send to remote port, default 4245"
)
parser.add_argument(
    "-v", "--verbose", action="store_true", help="provide verbose logging"
)
parser.add_argument(
    "--preview", action="store_true", help="Use when logged into Raspberry Pi Gui; will show camera preview. " + preview_text
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
    "--no-hflip", action="store_true", help="images are selfies and flipped horizontally by default"
)
parser.add_argument(
    "--blob-color", type=int, default=255, help="OpenCV blob detection color, default 255 (white; I believe it's grayscale 0-255)"
)
args = parser.parse_args()

if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info(" Logging verbosely\n")

if args.preview:
    print(preview_text + "\n")
else:
    print("If running PhilNav for the first time, use --help and --preview to set up your camera.\n")

# The camera can be configured and controlled with different settings in each.
# Not entirely sure the difference.
config_main = {
    "size": (args.width, args.height)
}
picam2 = Picamera2()
# Not entirely sure how configurations work, preview/main etc.
hflip_num = 1
if args.no_hflip:
    hflip_num = 0
config = picam2.create_preview_configuration(main=config_main, transform=Transform(hflip=hflip_num))
picam2.configure(config)

controls_main = {
    "AnalogueGain": args.gain,
    "Brightness": args.brightness,
    "Contrast": args.contrast,
    "ExposureValue": args.exposure,
    "Saturation": args.saturation,
    "FrameRate": args.fps
}
picam2.set_controls(controls_main)

if args.preview:
    picam2.start_preview(Preview.QT)
else:
    picam2.start_preview(Preview.NULL)

# Not entirely sure the difference between start_preview and start.
picam2.start()
sleep(1)  # let camera warm up

# OpenCV blob detection config
params = cv2.SimpleBlobDetector_Params()
params.filterByColor = True
params.filterByArea = True
params.blobColor = args.blob_color
params.minArea = 25
params.minThreshold = 150
params.minRepeatability = 3
params.filterByCircularity = False
params.filterByConvexity = False
params.filterByInertia = False
params.minDistBetweenBlobs = 100
detector = cv2.SimpleBlobDetector_create(params)

# Set up UDP socket to receiving computer
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # datagrams over UDP


# Globals for storing data from loop-to-loop, also stats for debugging
@dataclass
class PhilNav:
    started_at = time()
    frame_started_at = time()
    frame_start = perf_counter()
    frame_num = 0
    x = 0.0
    y = 0.0
    keypoint = None  # for debugging inspection

# This is where the Magic happens! The camera should pick up nothing but a white
# dot from your reflective IR sticker. I use opencv blob detection to track its
# (x, y) coordinates and send the changes to the receiving computer, which moves
# the mouse.
def blobby(request):
    # MappedArray gives direct access to the captured camera frame
    with MappedArray(request, "main") as m:
        PhilNav.frame_num += 1
        x_diff = 0.0
        y_diff = 0.0

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

        # Ideally should be exactly one keypoint
        if len(keypoints) > 0:
            # Compare the (x, y) coordinates from last frame
            kp = PhilNav.keypoint = keypoints[0]
            x_new, y_new = kp.pt
            x_diff = x_new - PhilNav.x
            y_diff = y_new - PhilNav.y
            PhilNav.x = x_new
            PhilNav.y = y_new

            # If the mouse has moved smoothly, but not "jumped"...
            # Jumping can occur if multiple blobs are detected, such as other
            # IR reflective surfaces in the camera's view, like glasses lenses.
            if (
                (x_diff**2 > 0 or y_diff**2 > 0)
                and x_diff**2 < 10
                and y_diff**2 < 10
            ):
                # Send the (x_diff, y_diff) to the receiving computer.
                # For performance stats, I'm also sending the frame time on
                # Raspberry Pi; both absolute and relative. Absolute time doesn't
                # work well because the Raspberry Pi clock and PC clock will not
                # be synced to within 1 ms of each other.
                #
                # 48 bytes of 6 doubles in binary C format. Why? Because it's
                # OpenTrack's protocol.
                # struct.pack('dddddd', x, y, z, pitch, yaw, roll)
                # PhilNav uses x, y as x_diff, y_diff and moves the mouse
                # relative to its current position.
                # https://github.com/opentrack/opentrack/issues/747
                time_spent = perf_counter() - PhilNav.frame_start
                MESSAGE = struct.pack(
                    "dddddd", x_diff, y_diff, 0, 0, time_spent, PhilNav.frame_started_at)
                sock.sendto(MESSAGE, (args.ip, args.port))

        # Log once per second
        if PhilNav.frame_num % args.fps == 0:
            fps = PhilNav.frame_num / (time() - PhilNav.started_at)
            ms = (perf_counter() - PhilNav.frame_start) * 1000
            logging.info(
                f"Frame: {PhilNav.frame_num}, Diff: ({int(x_diff)}, {int(y_diff)}), FPS: {int(fps)}, loc ms: {int(ms)}"
            )

        # I'm setting these at the end rather than the beginning, because I want
        # to make sure to include the time capturing the image from the camera.
        PhilNav.frame_started_at = time()
        PhilNav.frame_start = perf_counter()


# Run the loop forever until Ctrl-C
try:
    picam2.pre_callback = blobby
    sleep(10000000)  # run for one hundred days
except KeyboardInterrupt:
    pass

picam2.stop_preview()
picam2.stop()
picam2.close()
