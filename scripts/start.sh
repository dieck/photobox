#!/bin/bash

if ! mountpoint -q /mnt ; then
  mount /mnt
fi

if mountpoint -q /mnt ; then
  mkdir /mnt/photos
fi

TTY=`tty`

if [[ "$TTY" =~ ^/dev/tty.* ]] ; then

  while [ 1 -lt 2 ]
  do
    cd /home/pi/photobox
    python photobox.py
  done

fi
