#!/bin/bash

### Script to configure a U-Blox Zed-F9P ###

BASEDIR=$(dirname "$0")

export GPS=$1
export DEVICE_SPEED=$2
export CONFIG=$3

set_F9P() {
    if [[ $(python3 ${BASEDIR}/ubxtool -p MON-VER) =~ 'ZED-F9P' ]]
    then
        echo 'U-Blox ZED-F9P detected'
        echo 'Resetting ZED-F9P to default settings'
        python3 ${BASEDIR}/ubxtool -p RESET
        sleep 5
        #Now the default speed is 38400. Change it to 115200
        #It is unuseful for a Usb connexion but needed with a UART.
        echo 'Set UART Baudrate....'
        python3 ${BASEDIR}/ubxtool -s 38400 -z CFG-UART1-BAUDRATE,115200

        echo 'Sending settings....'
        while read setting; do
            python3 ${BASEDIR}/ubxtool -s 115200 -z $setting
        done <${CONFIG}
        echo 'Done'
    fi
}

#echo $GPS
#echo $DEVICE_SPEED
#echo $CONFIG

if [[ -c ${GPS} ]] && [[ ${DEVICE_SPEED} -gt 0 ]] && [[ -f $CONFIG && -s $CONFIG && $CONFIG == *.txt ]]
then
    #Overwrite UBXOPTS with the settings from the command line
    export UBXOPTS="-f ${GPS} -s ${DEVICE_SPEED} -v 0"
    set_F9P
else
    echo "usage:   set_zed-f9p.sh device baudrate config_file.txt"
    echo "example: set_zed-f9p.sh /dev/ttyACM0 115200 config_file.txt"
    exit 1
fi
exit 0