#!/bin/bash

TEXT="RETRY-3"
OUTPUT=error-retry.png
convert -pointsize 40 -fill black -draw "text 102,752 '$TEXT'" -blur 0x1 error.png - |
convert -pointsize 40 -fill yellow -draw "text 100,750 '$TEXT'" - $OUTPUT

TEXT="RAW/NEF"
OUTPUT=error-raw.png
convert -pointsize 40 -fill black -draw "text 102,752 '$TEXT'" -blur 0x1 error.png - |
convert -pointsize 40 -fill yellow -draw "text 100,750 '$TEXT'" - $OUTPUT

TEXT="NO CAM"
OUTPUT=error-nocam.png
convert -pointsize 40 -fill black -draw "text 102,752 '$TEXT'" -blur 0x1 error.png - |
convert -pointsize 40 -fill yellow -draw "text 100,750 '$TEXT'" - $OUTPUT

TEXT="NO DL"
OUTPUT=error-nodl.png
convert -pointsize 40 -fill black -draw "text 102,752 '$TEXT'" -blur 0x1 error.png - |
convert -pointsize 40 -fill yellow -draw "text 100,750 '$TEXT'" - $OUTPUT

TEXT="NO PTP/SD"
OUTPUT=storage-ptp.png
convert -pointsize 40 -fill black -draw "text 102,752 '$TEXT'" -blur 0x1 storage.png - |
convert -pointsize 40 -fill yellow -draw "text 100,750 '$TEXT'" - $OUTPUT

TEXT="NOT TO SD"
OUTPUT=storage-sd.png
convert -pointsize 40 -fill black -draw "text 102,752 '$TEXT'" -blur 0x1 storage.png - |
convert -pointsize 40 -fill yellow -draw "text 100,750 '$TEXT'" - $OUTPUT

TEXT="PI FULL"
OUTPUT=storage-pi.png
convert -pointsize 40 -fill black -draw "text 102,752 '$TEXT'" -blur 0x1 storage.png - |
convert -pointsize 40 -fill yellow -draw "text 100,750 '$TEXT'" - $OUTPUT

TEXT="PI"
OUTPUT=storage-file.png
convert -pointsize 40 -fill black -draw "text 102,752 '$TEXT'" -blur 0x1 storage.png - |
convert -pointsize 40 -fill yellow -draw "text 100,750 '$TEXT'" - $OUTPUT

TEXT="BACKUP"
OUTPUT=storage-backup.png
convert -pointsize 40 -fill black -draw "text 102,752 '$TEXT'" -blur 0x1 storage.png - |
convert -pointsize 40 -fill yellow -draw "text 100,750 '$TEXT'" - $OUTPUT

