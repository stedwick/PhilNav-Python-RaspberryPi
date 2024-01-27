import socket
import logging
import ctypes
import struct
import time

logging.debug("\n\n\nStarting\n\n")

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)] 

enabled = False
multiply = 20
count = 0

UDP_IP = "0.0.0.0"
UDP_PORT = 4245
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(0)
sock.bind((UDP_IP, UDP_PORT))

# hotkey = mouse.rightButton
# toggle = keyboard.getPressed(Key.Z)

# if toggle:
#   enabled = not enabled
#   logging.debug(">>>>> toggling")
    
# if (enabled and hotkey):
#   logging.debug("##### running")

loop_ms = time.time()*1000

while True:
  # time.sleep(0.005)
  count += 1
  if count % 10000 == 0:
    break
  try:
    data, addr = sock.recvfrom(48)
  except:
    time.sleep(0.005)
    continue
  x, y, z, pitch, yaw, roll = struct.unpack('dddddd', data)
  pos = POINT()
  ctypes.windll.user32.GetCursorPos(ctypes.byref(pos))
  ctypes.windll.user32.SetCursorPos(round(pos.x+x*30), round(pos.y+y*40))
  if count % 1 == 0:
    ms = time.time()*1000
    print(f"received message: ({int(x)}, {int(y)}, {z}, {pitch}, {yaw}, roundtrip-MS: {int(ms-roll)}) w/ local-MS: {int(ms-loop_ms)} from {addr}")
  loop_ms = time.time()*1000
