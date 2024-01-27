import cv2
import numpy
from picamera2 import Picamera2, Preview, MappedArray
from libcamera import Transform
import time
import logging
import inspect
import socket
import struct
# from keyboard import is_pressed

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (320, 240)},transform=Transform(hflip=1))
picam2.configure(config)
picam2.set_controls({"AnalogueGain": 2.0, "Brightness": -0.4, "Contrast": 5, "ExposureValue": 1, "Saturation": 0, "FrameRate": 85})
picam2.start_preview(Preview.QT)
# picam2.start_preview(Preview.NULL)
picam2.start()
time.sleep(1)

params = cv2.SimpleBlobDetector_Params()
params.blobColor = 255
detector = cv2.SimpleBlobDetector_create(params)

# UDP_IP = "192.168.68.71"
UDP_IP = "10.10.113.22"
UDP_PORT = 4245
MESSAGE = None
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

frame=0
x=0
y=0
keypoints=None
started_at_ms = time.time()*1000
frame_start_ms = time.time()*1000

def blobby(request):
  with MappedArray(request, "main") as m:
    global frame
    global x
    global y
    global keypoints
    global frame_start_ms
    x_diff = 0
    y_diff = 0
    
    frame = frame + 1
    
    keypoints = detector.detect(m.array)
    cv2.drawKeypoints(m.array, keypoints, m.array, (255,0,0), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    
    if len(keypoints) > 0:
        kp = keypoints[0]
        x_new, y_new = kp.pt
        x_diff = x_new - x
        y_diff = y_new - y
        x = x_new
        y = y_new
        if (x_diff**2 > 0 or y_diff**2 > 0) and x_diff**2 < 10 and y_diff**2 < 10:
            MESSAGE = struct.pack("dddddd", x_diff, y_diff, 0, 0, 0, frame_start_ms)
            sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
        
    
    if frame % 1 == 0:
        fps = frame/((time.time()*1000-started_at_ms)/1000)
        ms = time.time()*1000 - frame_start_ms
        logging.warning(f"Frame: {frame}, Diff: ({int(x_diff)}, {int(y_diff)}), FPS: {int(fps)}, local-MS: {int(ms)}")
        
    frame_start_ms = time.time()*1000

picam2.pre_callback = blobby
time.sleep(75)

# started_at = time.time()
# try:
#     while True:
#         if is_pressed('p'):
#             print(f"\rCaptured {filename} succesfully")
#         if is_pressed('q'):
#             print("\rClosing camera...")
#             break
#         frame = picam2.capture_array("main")
#         keypoints = detector.detect(frame)
#         mat_with_keypoints = cv2.drawKeypoints(frame, keypoints, numpy.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
#         cv2.imshow("img", mat_with_keypoints)
#         
#         if time.time() - started_at > 5:
#             break
# finally:
picam2.stop_preview()
picam2.stop()
picam2.close()

# array = picam2.capture_array("main")
# cv2.imshow("img", array); cv2.waitKey(0)
# 
# src = cv2.imread("/home/philip/test.jpg", cv2.IMREAD_GRAYSCALE);
# 
# params = cv2.SimpleBlobDetector_Params()
# params.blobColor = 255
# detector = cv2.SimpleBlobDetector_create(params)
# 
# keypoints = detector.detect(src); keypoints
# im_with_keypoints = cv2.drawKeypoints(src, keypoints, numpy.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
# cv2.imshow("img", im_with_keypoints); cv2.waitKey(0)

cv2.destroyAllWindows()
