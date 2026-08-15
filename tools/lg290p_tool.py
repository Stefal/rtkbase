#!/usr/bin/env python3
"""
lg290p_tool.py - configuration helper for the Quectel LG290P GNSS receiver.

Standalone version. CLI shape deliberately mirrors rtkbase's tools/unicore_tool.py
and tools/sept_tool.py so it can be dropped into rtkbase later with minimal edits.

Examples
--------
  # find the receiver
  ./lg290p_tool.py --detect

  # identify
  ./lg290p_tool.py --port /dev/ttyUSB0 --command get_model
  ./lg290p_tool.py --port /dev/ttyUSB0 --command get_firmware

  # factory reset, then push a config file and save it
  ./lg290p_tool.py --port /dev/ttyUSB0 --command reset --retry 5
  ./lg290p_tool.py --port /dev/ttyUSB0 --command send_config_file \
      LG290P_rtkbase_rtcm3.cfg --store --retry 3

Requires: pyserial  (apt install python3-serial)
"""

import argparse
import glob
import os
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial not found. Install with: sudo apt install python3-serial")

# LG290P default is 460800; the others are listed in the hardware design doc.
BAUD_RATES = (460800, 115200, 921600, 230400, 9600, 38400, 57600)

# CH343/CH342 USB-serial bridges used on the Waveshare and SparkFun boards.
# Verify yours with `lsusb` - WCH vendor id is 1a86, product id varies by part.
PORT_GLOBS = ("/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyCH343USB*")

DEFAULT_TIMEOUT = 2.0
REBOOT_WAIT = 20  # seconds to wait for USB re-enumeration after a reset


# --------------------------------------------------------------------------
# NMEA framing
# --------------------------------------------------------------------------

def nmea_checksum(payload: str) -> str:
    """XOR of every char between '$' and '*', as two uppercase hex digits."""
    cs = 0
    for ch in payload:
        cs ^= ord(ch)
    return f"{cs:02X}"


def build_sentence(payload: str) -> bytes:
    """'PQTMVERNO' -> b'$PQTMVERNO*58\\r\\n'. Accepts payload with or without $."""
    payload = payload.strip().lstrip("$")
    if "*" in payload:  # caller supplied their own checksum - trust it
        return f"${payload}\r\n".encode()
    return f"${payload}*{nmea_checksum(payload)}\r\n".encode()


def msg_id(payload: str) -> str:
    """'PQTMCFGMSGRATE,W,GGA,1' -> 'PQTMCFGMSGRATE'"""
    return payload.strip().lstrip("$").split(",")[0].split("*")[0]


# --------------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------------

class LG290P:
    def __init__(self, port, baudrate=460800, timeout=DEFAULT_TIMEOUT, debug=False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.debug = debug
        self.ser = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *exc):
        self.close()

    def open(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        time.sleep(0.2)
        self.ser.reset_input_buffer()

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None

    def _log(self, direction, data):
        if self.debug:
            print(f"{direction} {data!r}", file=sys.stderr)

    def send(self, payload, expect=None, wait=None):
        """
        Send one sentence, then read lines until we see a response whose message id
        matches (or `expect` if given), or until the timeout expires.

        Returns the matching response line as str, or None.
        """
        wait = self.timeout if wait is None else wait
        expect = expect or msg_id(payload)
        sentence = build_sentence(payload)

        self.ser.reset_input_buffer()
        self._log(">>", sentence)
        self.ser.write(sentence)
        self.ser.flush()

        deadline = time.time() + wait
        while time.time() < deadline:
            try:
                line = self.ser.readline().decode("ascii", errors="replace").strip()
            except serial.SerialException:
                return None
            if not line:
                continue
            self._log("<<", line)
            if line.startswith("$" + expect) or line.startswith(expect):
                return line
        return None

    def command(self, payload, retry=1, expect=None, wait=None):
        """send() with retries. Returns response line or None."""
        for attempt in range(max(1, retry)):
            resp = self.send(payload, expect=expect, wait=wait)
            if resp is not None:
                return resp
            if self.debug:
                print(f"   retry {attempt + 1}", file=sys.stderr)
            time.sleep(0.3)
        return None


def response_ok(resp) -> bool:
    """LG290P config writes ack with ',OK'; errors come back as ',ERROR,<code>'."""
    return bool(resp) and ",OK" in resp.upper()


def wait_for_port(path, timeout=REBOOT_WAIT):
    """After a reset the USB device re-enumerates - wait for the node to reappear."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            time.sleep(1.5)  # let udev finish and the receiver finish booting
            return True
        time.sleep(0.5)
    return False


# --------------------------------------------------------------------------
# High level operations
# --------------------------------------------------------------------------

def get_version(dev, retry=3):
    """Returns the raw PQTMVERNO response, e.g.
       $PQTMVERNO,LG290P03AANR01A05S,2024/01/01,12:00:00*XX"""
    return dev.command("PQTMVERNO", retry=retry)


def get_model(dev, retry=3):
    resp = get_version(dev, retry)
    if not resp:
        return None
    fields = resp.split(",")
    if len(fields) < 2:
        return None
    verstr = fields[1]
    # verstr looks like LG290P03AANR01A05S - take the family prefix
    for family in ("LG290P", "LG580P", "LG680P"):
        if verstr.startswith(family):
            return family
    return verstr


def get_firmware(dev, retry=3):
    resp = get_version(dev, retry)
    if not resp:
        return None
    fields = resp.split(",")
    return fields[1] if len(fields) > 1 else None


def factory_reset(dev, retry=3):
    """$PQTMRESTOREPAR then reboot. Port will re-enumerate."""
    resp = dev.command("PQTMRESTOREPAR", retry=retry, wait=3)
    if not response_ok(resp):
        return False
    path = dev.port
    reboot(dev)
    return wait_for_port(path)


def save_params(dev, retry=3):
    return response_ok(dev.command("PQTMSAVEPAR", retry=retry, wait=3))


def reboot(dev):
    """Software reset. Response is unreliable because the device drops off mid-reply."""
    try:
        dev.ser.write(build_sentence("PQTMSRR"))
        dev.ser.flush()
    except serial.SerialException:
        pass
    time.sleep(0.5)
    dev.close()


def send_config_file(dev, path, store=False, retry=3):
    """
    Config file format - one directive per line:
        # comment
        PQTMCFGRCVRMODE,W,2      <- checksum computed for you
        SLEEP 5                  <- pause n seconds
        SAVE                     <- $PQTMSAVEPAR
        RESET                    <- $PQTMSRR + wait for re-enumeration
    """
    with open(path, "r") as fh:
        lines = [ln.strip() for ln in fh]

    failures = []
    for lineno, line in enumerate(lines, 1):
        if not line or line.startswith("#"):
            continue

        upper = line.upper()

        if upper.startswith("SLEEP"):
            secs = float(line.split()[1]) if len(line.split()) > 1 else 1.0
            print(f"  sleeping {secs}s")
            time.sleep(secs)
            continue

        if upper == "SAVE":
            print("  saving parameters")
            if not save_params(dev, retry):
                failures.append((lineno, "SAVE"))
            continue

        if upper == "RESET":
            print("  resetting receiver, waiting for re-enumeration")
            path_ = dev.port
            reboot(dev)
            if not wait_for_port(path_):
                failures.append((lineno, "RESET (port did not reappear)"))
                return failures
            dev.open()
            continue

        resp = dev.command(line, retry=retry)
        status = "ok" if response_ok(resp) else f"FAILED ({resp})"
        print(f"  {line:<44} {status}")
        if not response_ok(resp):
            failures.append((lineno, line))

    if store and not failures:
        print("  saving parameters")
        if not save_params(dev, retry):
            failures.append((0, "final SAVE"))

    return failures


def detect(debug=False):
    """Scan likely ports and bauds for an LG290P. Returns (port, baud, model, fw)."""
    ports = []
    for pattern in PORT_GLOBS:
        ports.extend(sorted(glob.glob(pattern)))

    if not ports:
        return None

    for port in ports:
        for baud in BAUD_RATES:
            if debug:
                print(f"probing {port} @ {baud}", file=sys.stderr)
            try:
                with LG290P(port, baud, timeout=0.8, debug=debug) as dev:
                    resp = get_version(dev, retry=2)
                    if resp:
                        fields = resp.split(",")
                        fw = fields[1] if len(fields) > 1 else "?"
                        model = get_model(dev, retry=1) or "?"
                        return (port, baud, model, fw)
            except (serial.SerialException, OSError) as exc:
                if debug:
                    print(f"  {exc}", file=sys.stderr)
                break  # port unusable, move to the next one
    return None


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Quectel LG290P configuration tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--port", help="serial port, e.g. /dev/ttyUSB0")
    ap.add_argument("--baudrate", type=int, default=460800,
                    help="port speed (default: 460800, the LG290P factory default)")
    ap.add_argument("--command", choices=(
        "get_model", "get_firmware", "get_version", "get_mode",
        "reset", "save", "reboot", "send_config_file", "raw"))
    ap.add_argument("argument", nargs="?",
                    help="config file path for send_config_file, or sentence for raw")
    ap.add_argument("--detect", action="store_true",
                    help="scan for a connected LG290P and print port/baud/model/firmware")
    ap.add_argument("--store", action="store_true",
                    help="save parameters to flash after a successful config file")
    ap.add_argument("--retry", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    ap.add_argument("--debug", action="store_true", help="echo all traffic to stderr")
    args = ap.parse_args()

    if args.detect:
        found = detect(debug=args.debug)
        if not found:
            print("no LG290P found", file=sys.stderr)
            return 1
        port, baud, model, fw = found
        print(f"{port} - quectel - {baud} - {fw} - {model}")
        return 0

    if not args.port or not args.command:
        ap.error("--port and --command are required (or use --detect)")

    try:
        with LG290P(args.port, args.baudrate, args.timeout, args.debug) as dev:
            if args.command == "get_model":
                val = get_model(dev, args.retry)
            elif args.command == "get_firmware":
                val = get_firmware(dev, args.retry)
            elif args.command == "get_version":
                val = get_version(dev, args.retry)
            elif args.command == "get_mode":
                val = dev.command("PQTMCFGRCVRMODE,R", retry=args.retry)
            elif args.command == "save":
                val = "OK" if save_params(dev, args.retry) else None
            elif args.command == "reboot":
                reboot(dev)
                val = "OK" if wait_for_port(args.port) else None
            elif args.command == "reset":
                val = "OK" if factory_reset(dev, args.retry) else None
            elif args.command == "raw":
                if not args.argument:
                    ap.error("raw needs a sentence, e.g. 'PQTMCFGRCVRMODE,R'")
                val = dev.command(args.argument, retry=args.retry)
            elif args.command == "send_config_file":
                if not args.argument:
                    ap.error("send_config_file needs a file path")
                failures = send_config_file(dev, args.argument, args.store, args.retry)
                if failures:
                    print(f"\n{len(failures)} command(s) failed:", file=sys.stderr)
                    for lineno, cmd in failures:
                        print(f"  line {lineno}: {cmd}", file=sys.stderr)
                    return 1
                print("\nconfiguration applied successfully")
                return 0

            if val is None:
                print("no response from receiver", file=sys.stderr)
                return 1
            print(val)
            return 0

    except serial.SerialException as exc:
        print(f"serial error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
