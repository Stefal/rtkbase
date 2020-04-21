#!/bin/bash

#path="/home/kenm/RTK/"

echo 7 > /sys/class/gpio/export
echo 17 > /sys/class/gpio/export

echo "out" > /sys/class/gpio/gpio17/direction
echo "in" > /sys/class/gpio/gpio7/direction

cd /home/reach

sleep 10
python /home/reach/server.py &

# blink LEDs to let user know all is OK and we are collecting data
X=0
while [ $X -le 0 ]
 do
    echo 0 > /sys/class/gpio/gpio17/value
    sleep 1
    echo 1 > /sys/class/gpio/gpio17/value
    sleep 1
#   read val < /sys/class/gpio/gpio7/value
#    if (( val == 0 )); then
#    echo "ping"
#    X=1
#    fi

done

/bin/systemctl poweroff
