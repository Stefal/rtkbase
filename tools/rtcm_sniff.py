#!/usr/bin/env python3
"""
rtcm_sniff.py - count RTCM3 message types on a serial port or file.

Frames are validated with CRC-24Q before being counted, so a desync in the
byte stream cannot invent message ids. Also reports NMEA talker sentences.

  ./rtcm_sniff.py /dev/ttyACM0 460800 --seconds 60
"""

import argparse
import collections
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial not found. Install with: sudo apt install python3-serial")


def crc24q(data: bytes) -> int:
    """RTCM3 CRC-24Q, polynomial 0x1864CFB."""
    crc = 0
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF


def scan(buf: bytearray, rtcm: collections.Counter):
    """Consume complete, CRC-valid RTCM3 frames from the head of buf."""
    while True:
        i = buf.find(b"\xd3")
        if i < 0:
            buf.clear()
            return
        if len(buf) - i < 6:
            del buf[:i]
            return
        length = ((buf[i + 1] & 0x03) << 8) | buf[i + 2]
        end = i + 3 + length + 3
        if len(buf) < end:
            del buf[:i]
            return
        frame = bytes(buf[i:end])
        payload, crc = frame[:-3], frame[-3:]
        if crc24q(payload) == int.from_bytes(crc, "big"):
            if length >= 2:
                rtcm[(frame[3] << 4) | (frame[4] >> 4)] += 1
            del buf[:end]
        else:
            # not a real frame - skip this D3 and resync
            del buf[:i + 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("baudrate", nargs="?", type=int, default=460800)
    ap.add_argument("--seconds", type=float, default=30.0)
    args = ap.parse_args()

    rtcm = collections.Counter()
    nmea = collections.Counter()
    buf = bytearray()
    line = bytearray()

    with serial.Serial(args.port, args.baudrate, timeout=1) as ser:
        deadline = time.time() + args.seconds
        while time.time() < deadline:
            chunk = ser.read(4096)
            if not chunk:
                continue
            buf += chunk
            for b in chunk:
                if b == 0x24:  # '$'
                    line = bytearray(b"$")
                elif line:
                    if b in (10, 13):
                        if len(line) > 6:
                            nmea[line[:6].decode("ascii", "replace")] += 1
                        line = bytearray()
                    else:
                        line.append(b)
            scan(buf, rtcm)

    total = sum(rtcm.values())
    print(f"RTCM3 frames (CRC-valid): {total} in {args.seconds:g}s")
    for k, v in sorted(rtcm.items()):
        print(f"  {k:5d}  x{v}")
    if nmea:
        print("NMEA:")
        for k, v in sorted(nmea.items()):
            print(f"  {k}  x{v}")
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
