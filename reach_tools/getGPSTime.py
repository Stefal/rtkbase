#!/usr/bin/python

import serial
import binascii
import ctypes

def hexify(char_list):
    """ transform a char list into a list of int values"""
    return [ord(c) for c in char_list]

def enable_nav_timeutc(port):
    poll_time_utc = ["b5", "62", "06", "01", "03", "00", "01", "21", "01", "2d", "85"]
    msg = binascii.unhexlify("".join(poll_time_utc))
    port.write(msg)

class MSG_NAV_TIMEUTC:

    msg_start = [0xb5, 0x62, 0x01, 0x21, 0x14, 0x00]
    msg_length = 28

    def __init__(self, ubx_hex_log):
        self.time_valid = False
        self.utc_time = None

        extracted_messages = self.scan_log(ubx_hex_log)

        if extracted_messages:
            for msg in extracted_messages:
                if self.is_valid(msg):
                    if self.time_is_valid(msg):
                        self.time_valid = True
                        self.utc_time = self.unpack(msg)

    def __str__(self):
        to_print = "ubx NAV-TIMEUTC message\n"

        if self.time_valid:
            to_print += "Time data is valid\n"
            to_print += ".".join(str(x) for x in self.utc_time[:3])
            to_print += " "
            to_print += ":".join(str(x) for x in self.utc_time[3:])
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
        time = []

        # unpack year
        byte1 = ctypes.c_uint8(msg[18])
        byte2 = ctypes.c_uint8(msg[19])

        year = ctypes.c_uint16(byte2.value << 8 | byte1.value).value
        time.append(year)
        # unpack month, day, hour, minute, second
        for i in range(20, 25):
            time.append(msg[i])

        return time


if __name__ == "__main__":

    port = serial.Serial("/dev/ttyMFD1", 230400, timeout = 1.5)

    enable_nav_timeutc(port)

    while True:
        try:
            multiple_bytes = port.read(1024)
        except OSError:
            print("Could not open serial device")
        else:
            ubx_log = hexify(multiple_bytes)
            time_data = MSG_NAV_TIMEUTC(ubx_log)
            print(time_data)













