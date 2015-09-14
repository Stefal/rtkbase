#!/usr/bin/python

import os
import sys
import time
from GPIO import GPIO

class ReachLED:

    pwm_prefix = "/sys/class/pwm/pwmchip0/"

    def __init__(self):
        self.pins = [GPIO(12), GPIO(13), GPIO(182)] # green, red, blue

        self.colors_dict = {
            "off": [0, 0, 0],
            "red": [1, 0, 0],
            "green": [0, 1, 0],
            "blue": [0, 0, 1],
            "white": [1, 1, 1],
            "yellow": [1, 1, 0],
            "cyan": [0, 1, 1],
            "magenta": [1, 0, 1],
            "orange": [1, 0.4, 0],
            "weakred": [0.1, 0, 0]
        }

        # channel numbers
        self.pwm_channels = [0, 1, 2] # red, green, blue

        # first, we need to change the pin's pinmux to mode1
        for pin in self.pins:
            pin.setPinmux("mode1")

        # then, export the 3 pwn channels if needed
        for ch in self.pwm_channels:
            if not os.path.exists(self.pwm_prefix + "/pwm" + str(ch)):
                with open(self.pwm_prefix + "export", "w") as f:
                    f.write(str(ch))

        # enable all of the channels
        for ch in self.pwm_channels:
            with open(self.pwm_prefix + "pwm" + str(ch) + "/enable", "w") as f:
                f.write("1")

        # set period
        for ch in self.pwm_channels:
            with open(self.pwm_prefix + "pwm" + str(ch) + "/period", "w") as f:
                f.write("1000000")

        # turn off all of it by default
        for ch in self.pwm_channels:
            self.setDutyCycle(ch, 0)

    def setDutyCycle(self, channel, percentage):
        # 0% = 1000000
        # 100% = 0

        duty_value = (100 - percentage) * 10000
        duty_value = int(duty_value)

        with open(self.pwm_prefix + "pwm" + str(channel) + "/duty_cycle", "w") as f:
            f.write(str(duty_value))

    def setColor(self, color, power_percentage):
        # available colors:
        # red
        # green
        # blue
        # white
        # yellow
        # cyan
        # magenta

        if color in self.colors_dict:
            for i in range(0, 3):
                self.setDutyCycle(i, self.colors_dict[color][i] * power_percentage)
        else:
            print("Can't set this color. You may add this in the colors_dict variable")

def test():
    led = ReachLED()
    print("Starting...")
    led.setDutyCycle(0, 0)
    led.setDutyCycle(0, 0)
    led.setDutyCycle(0, 0)

    time.sleep(1)
    print("After pause...")
    print("Channel 0")
    led.setDutyCycle(0, 100)
    time.sleep(1)
    print("Channel 1")
    led.setDutyCycle(0, 0)
    led.setDutyCycle(1, 100)
    time.sleep(1)
    print("Channel 2")
    led.setDutyCycle(1, 0)
    led.setDutyCycle(2, 100)
    time.sleep(1)

if __name__ == "__main__":
    # test()
    led = ReachLED()

    if len(sys.argv) < 2:
        print("You need to specify a color\nList of colors: off, white, red, blue, green, cyan, magenta, yellow")
    else:
        led.setColor(sys.argv[1], 100)
    








