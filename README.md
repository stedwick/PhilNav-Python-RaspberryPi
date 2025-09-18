# PhilNav-Python-RaspberryPi


## Intro

PhilNav is a *very good* infrared head mouse, sorta like the discontinued NaturalPoint SmartNav. It runs at 75 FPS for buttery smooth mouse movements and pixel perfect accuracy. 

[Note: zero hardware or software is from the SmartNav, everything is built and programmed 100% from scratch by me, Phil.]

PhilNav allows you to use your computer hands-free by tracking a reflective sticker on your head, and then moving the mouse accordingly.

I also have a speech-to-text dictation app. Combined with this, use your computer completely hands-free: https://phils.app

Watch Phil's YouTube video here: https://youtu.be/JTLs7z0PO-k

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/JTLs7z0PO-k/0.jpg)](https://www.youtube.com/watch?v=JTLs7z0PO-k)

There's \*lots\* of assembly required since the Raspberry Pi has to be built. You can buy a pre-built PhilNav from Phil here: https://philipb.gumroad.com/l/philnav

-----

PhilNav has exceeded all my expectations. It's better than other head-mice, and I hit all of my goals:

1. Pixel perfect accuracy
1. 5 ms latency, at 75 FPS
1. Cross-platform on Windows, Mac, & Linux
1. Configurable, with keyboard shortcuts
1. <1% CPU/RAM on client

The trade-offs I made include:

1. No graphical user interface
1. Not Plug-and-Play Over USB, uses the network (Wi-Fi, ethernet)
1. Difficult to assemble and install (knowledge of building Raspberry Pi computers and Python required)
1. No clicking. You'll have to use a switch, pedal, or other dwell clicking software.

There are many other head-mice, but mine's the best:
* https://smylemouse.com
* https://abilitare.com
* https://glassouse.com
* https://www.orin.com/access/headmouse/
* https://www.spectronics.com.au/product/trackerpro-2
* https://www.quha.com
* https://eviacam.crea-si.com/

It uses a client/server model; the server runs on a Raspberry Pi with a Picam 3 NoIR camera, and the client runs on your Windows, Apple macOS, or Linux PC. They communicate over Wi-Fi or ethernet via UDP multicast.

It's free and open source on GitHub, written from scratch in Python3 by Philip Brocoum. There are no dependencies on the 2002 SmartNav hardware or software (it's discontinued anyway by NaturalPoint as of 2018). 

## Running PhilNav

Start by running the following Python scripts on the client and server. You may have to ```pip install``` a bunch of things first. I put my reflective sticker on my headset mic boom. 

```
# server
sudo apt install python3-opencv

# client
pip install ...
```

#### Server - Raspberry Pi
```
python3 server_raspberrypi/main.py --verbose --preview
```

#### Client PC - Win/Mac/Nix
```
python3 client_win-mac-nix/main.py --verbose
```

On the Raspberry Pi you should see a preview of the camera, and on the client machine the mouse should start to move. Use ```--help``` to change your settings to your liking.

Here are my own settings:

```
python3 server_raspberrypi/main.py 

python3 client_win-mac-nix/main.py --speed 21 --smooth 3 --deadzone 0.04 --keepawake 56 --timeout $((60*60*8))
```

(If you have a firewall, ports 4245 & 4246 must be open to send/recv UDP.)

#### Note: Linux using `/dev/uinput` (with Wayland & X11)
I've modernized it to send mouse movements to /dev/uinput instead of X11 calls, so it works on Wayland (& X11) and should be future-proof. However, this requires permission to read and write /dev/uinput. You can run as root, or give your user permission:

You'll need to install ```pip install evdev``` or ```sudo apt install python3-evdev``` and add your user to the input group.

```
# Add user to input group
sudo usermod -a -G input $USER
# Create a udev rule
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-input.rules
# restart
sudo shutdown -r now
```

## Building PhilNav

Watch the YouTube video here:

Parts:
- Raspberry Pi 5 - https://www.canakit.com/canakit-raspberry-pi-5-starter-kit-turbine-black.html
- Pi Breadboard kit - https://www.canakit.com/raspberry-pi-gpio-breakout-bundle.html
- Pi Camera Module 3 NoIR - https://www.canakit.com/raspberry-pi-camera-module-3.html
- Pi 5 Camera Cable - https://www.canakit.com/raspberry-pi-5-camera-cable.html
- Infrared LEDs - https://www.amazon.com/gp/product/B01BVGIZIU
- Visible light filter - https://www.amazon.com/dp/B0CL2652X9
- Reflective tape - https://www.amazon.com/dp/B06VTTV6PR
- Selfie Stick - https://www.amazon.com/dp/B09W99QJBP

-----

With this open source project, disabled folks are not at the mercy of a private company that might discontinue products, and we are not stuck on Windows =)
