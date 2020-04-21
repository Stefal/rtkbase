#!/usr/bin/python

# ReachView code is placed under the GPL license.
# Written by Egor Fedorov (egor.fedorov@emlid.com)
# Copyright (c) 2015, Emlid Limited
# All rights reserved.

# If you are interested in using ReachView code as a part of a
# closed source project, please contact Emlid Limited (info@emlid.com).

# This file is part of ReachView.

# ReachView is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ReachView is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with ReachView.  If not, see <http://www.gnu.org/licenses/>.

import serial
import binascii
import ctypes
import subprocess
from . import reach_tools

def hexify(char_list):
    """ transform a char list into a list of int values"""
    return [ord(c) for c in char_list]

def enable_nav_timeutc(port):
    poll_time_utc = ["b5", "62", "06", "01", "03", "00", "01", "21", "01", "2d", "85"]
    msg = binascii.unhexlify("".join(poll_time_utc))
    port.write(msg)

def time_synchronised_by_ntp():
    out = subprocess.check_output("timedatectl")

    if "NTP synchronized: yes" in out:
        return True
    else:
        return False

def update_system_time(date, time):
    # requires a date list and a time list
    # ["YYYY", "MM", "DD"], ["hh", "mm", "ss"]
    print("##### UPDATING SYSTEM TIME #####")
    print(date)
    print(time)
    # busybox date cmd can use a following format
    # YYYY.MM.DD-hh:mm:ss
    # real date -s needs YYYY-MM-DD hh:mm:ss
    printable_date = "-".join(str(x) for x in date)
    printable_time = ":".join(str(x) for x in time)

    datetime_string = printable_date + " " + printable_time
    cmd = ["date", "-s", datetime_string]
    out = subprocess.check_output(cmd)

def get_gps_time(port):

    try:
        multiple_bytes = port.read(1024)
    except OSError:
        print("Could not open serial device")
    else:
        ubx_log = hexify(multiple_bytes)
        time_data = MSG_NAV_TIMEUTC(ubx_log)
        print(time_data)

        if time_data.time_valid:
            return time_data.date, time_data.time

    return None, None

def set_gps_time(serial_device, baud_rate):

    port = serial.Serial(serial_device, baud_rate, timeout = 1.5)
    enable_nav_timeutc(port)

    print("Restarting ntp service for faster sync...")
    reach_tools.run_command_safely(["timedatectl", "set-ntp", "false"])
    reach_tools.run_command_safely(["timedatectl", "set-ntp", "true"])

    print("TIMEUTC enabled")
    time = None
    ntp_not_synced = True

    while time is None and ntp_not_synced:
        date, time = get_gps_time(port)
        ntp_not_synced = not time_synchronised_by_ntp()

    if ntp_not_synced:
        update_system_time(date, time)

class MSG_NAV_TIMEUTC:

    msg_start = [0xb5, 0x62, 0x01, 0x21, 0x14, 0x00]
    msg_length = 28

    def __init__(self, ubx_hex_log):
        self.time_valid = False
        self.date = None
        self.time = None

        extracted_messages = self.scan_log(ubx_hex_log)

        if extracted_messages:
            for msg in extracted_messages:
                if self.is_valid(msg):
                    if self.time_is_valid(msg):
                        self.time_valid = True
                        self.date, self.time= self.unpack(msg)

    def __str__(self):
        to_print = "ubx NAV-TIMEUTC message\n"

        if self.time_valid:
            to_print += "Time data is valid\n"
            to_print += ".".join(str(x) for x in self.date)
            to_print += " "
            to_print += ":".join(str(x) for x in self.time)
        else:
            to_print += "Time data is invalid!"

        return to_print

    def scan_log(self, ubx_hex_log):
        """Search the provided log for a required msg header"""
        matches = []
        pattern = self.msg_start
        msg_length = self.msg_length

        for i in range(0, len(ubx_hex_log)):
            if ubx_hex_log[i] == pattern[0] and ubx_hex_log[i:i + len(pattern)] == pattern:
                matches.append(ubx_hex_log[i:i + msg_length])

        return matches

    def is_valid(self, msg):
        """Count and verify the checksum of a ubx message. msg is a list of hex values"""

        to_check = msg[2:-2]

        ck_a = ctypes.c_uint8(0)
        ck_b = ctypes.c_uint8(0)

        for num in to_check:
            byte = ctypes.c_uint8(num)
            ck_a.value = ck_a.value + byte.value
            ck_b.value = ck_b.value + ck_a.value

        if (ck_a.value, ck_b.value) == (ctypes.c_uint8(msg[-2]).value, ctypes.c_uint8(msg[-1]).value):
            return True
        else:
            return False

    def time_is_valid(self, msg):
        """Check the flags confirming utc time in the message is valid"""
        flag_byte = ctypes.c_uint8(msg[-3])
        return True if flag_byte.value & 4 == 4 else False

    def unpack(self, msg):
        """Extract the actual time from the message"""
        datetime = []

        # unpack year
        byte1 = ctypes.c_uint8(msg[18])
        byte2 = ctypes.c_uint8(msg[19])

        year = ctypes.c_uint16(byte2.value << 8 | byte1.value).value
        datetime.append(year)
        # unpack month, day, hour, minute, second
        for i in range(20, 25):
            datetime.append(msg[i])

        date = datetime[:3]
        time = datetime[3:]

        return date, time

