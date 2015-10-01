#!/usr/bin/python

import os
import sys
import time
from threading import Thread
from GPIO import GPIO

class ReachLED:

    pwm_prefix = "/sys/class/pwm/pwmchip0/"

    def __init__(self):
        self.pins = [GPIO(12), GPIO(13), GPIO(182)] # green, red, blue

        # thread, used to blink later
        self.blinker_thread = None

        # to stop blinker later
        self.blinker_not_interrupted = True

        # keep current state in order to restore later
        self.current_blink_pattern = ""

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
        #for ch in self.pwm_channels:
        #    self.setDutyCycle(ch, 0)

    def setDutyCycle(self, channel, percentage = None):
        # 0% = 1000000
        # 100% = 0

        duty_value = (100 - percentage) * 10000
        duty_value = int(duty_value)

        with open(self.pwm_prefix + "pwm" + str(channel) + "/duty_cycle", "w") as f:
            f.write(str(duty_value))

    def setColor(self, color, power_percentage = None):
        # available colors:
        # red
        # green
        # blue
        # white
        # yellow
        # cyan
        # magenta

        # defalt power percentage value
        if power_percentage == None:
            power_percentage = 100

        if color in self.colors_dict:
            for i in range(0, 3):
                self.setDutyCycle(i, self.colors_dict[color][i] * power_percentage)

            return 0
        else:
            # no such color available :(
            return -1

    def startBlinker(self, pattern, delay = None):
        # start a new thread that blinks

        self.current_blink_pattern = pattern

        if self.blinker_thread == None:
            self.blinker_not_interrupted = True
            self.blinker_thread = Thread(target = self.blinkPattern, args = (pattern, delay))
            self.blinker_thread.start()
        else:
            # we already have a blinker started and need to restart it using new colors
            self.stopBlinker()
            self.startBlinker(pattern, delay)

    def stopBlinker(self):
        # stop existing thread

        self.blinker_not_interrupted = False

        if self.blinker_thread is not None:
            self.blinker_thread.join()
            self.blinker_thread = None

    def blinkPattern(self, pattern, delay = None):
        # start blinking in a special pattern
        # pattern is a string of colors, separated by commas
        # for example: "red,blue,off"
        # they will be flashed one by one
        # and separated by a time of delay, which 0.5s by default

        color_list = pattern.split(",")

        if delay == None:
            delay = 0.5

        while self.blinker_not_interrupted:
            for color in color_list:
                if self.blinker_not_interrupted == False:
                    break

                self.setColor(color)
                time.sleep(delay)

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
        print("You need to specify a color")
        print("List of colors:")

        colors = ""
        for color in led.colors_dict:
            colors += color + ", "

        print(colors)

    else:
        if led.setColor(sys.argv[1]) < 0:
            print("Can't set this color. You may add this in the colors_dict variable")








