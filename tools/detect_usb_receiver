#!/bin/bash
# source https://unix.stackexchange.com/a/144735
for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do

        syspath="${sysdevpath%/dev}"
        devname="$(udevadm info -q name -p $syspath)"
        if [[ "$devname" == "bus/"* ]]; then continue; fi
        eval "$(udevadm info -q property --export -p $syspath)"
        if [[ -z "$ID_SERIAL" ]]; then continue; fi
        echo "/dev/$devname - $ID_SERIAL"

done
