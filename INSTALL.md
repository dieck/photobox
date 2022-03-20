# photobox
My own little Raspberry Pi based photo box

Raspberry Pi OS
================

Raspberry Pi OS
LEGACY Lite version (Buster), no Desktop GUI
https://www.raspberrypi.com/software/

This guide does NOT work with Debian Bullseye based OS.
OMXPlayer for video rendering is missing there and cannot be installed.

Photobox will need to be modified to use another player.

(I read that installing Buster and then upgrading to Bullseye might just work - but haven't tried this.)


Login with pi : raspberry
(for forgetful people like me: remember it's US keyboard setting)

sudo raspi-config

Set the following options:

If you are not on cabled LAN: System Options - S1 Wireless LAN

System Options - S5 Boot / Auto Login
set to B2 Console AutoLogin (pi user)

Interface Options - I2 SSH: enable

Localisation Options - L2 Timezone: set accordingly to your location

Localisation Options - L3 Keyboard: set accordingly to your device

Finish and reboot


If you encounter display problems later when using the Photobox, restart raspi-config and look for Display Options.


Required Software
==================

sudo apt-get update
sudo apt-get install git fbi gphoto2 omxplayer python2.7 python-gpiozero python-configparser python-colorzero 


Photobox Installation
======================

git clone https://github.com/dieck/photobox.git

cd photobox
cp photobox.ini-template photobox.ini

edit photobox.ini (with nano photobox.ini, or use your favorite editor)

Set GPIO ports with connected switches
Set storage directory. I really recommend NOT to use /tmp!

Set backup e.g. to /mnt if you want to use an USB stick


Backup Directory
=================

Do these steps as root

Create directory (if you are using /mnt, this should be already available)

Find device to mount. If you are using an USB stick, it's most likely /dev/sda1. Verify with fdisk -l /dev/sda

Edit /etc/fstab and add line:

/dev/sda1	/mnt	auto	noauto,user,rw,sync,umask=000	0	0

Mount before using the photobox.


Autostart Photobox
===================

Edit /home/pi/photobox/scripts/start.sh and validate paths for backup drive

Edit ~/.bashrc
Add line:
bash /home/pi/photobox/scripts/start.sh

reboot

