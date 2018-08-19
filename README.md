# photobox
My own little Raspberry Pi based photo box


Hardware
========


Used components:
- Raspberry PI (3+)
- Nikon D5100, DX AF-S 18-105mm ED
- HDMIPi 9" 1280x800 Display
- Simple Switch for "Delayed" 
- Keyboard Sustain Pedal as Switch for "Instant"
- 30x30cm 24W LED Panel, 3800 lm, 4000-4500K
- 2-channel Relais (switching Null + Phase)
  (please note they need to work with 3.3v from RPi GPIO)
- home-made Wooden Box



Software
========

- gphoto2 is used to take photos with the Nikon camera

Libraries for needed for Python:
- python-gpiozero
  gpiozero is used to control the Buttons and LED light switches
- python-configparser

