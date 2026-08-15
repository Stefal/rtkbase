#!/usr/bin/env python3
"""
lg290p_set_fixed_position.py - automate the LG290P fixed-position base station workflow.

The LG290P's own internal survey-in is unreliable (confirmed on real hardware and by
independent Quectel forum reports - PQTMCFGSVIN,R can sit at ECEF 0,0,0 for hours without
ever validating). This script sidesteps it entirely: it averages a real position from
rtkbase_raw2nmea's NMEA output (a single-point solution computed directly from the
receiver's own RTCM3 observables, unrelated to the flaky internal survey-in engine),
converts that to WGS84 ECEF, and pushes it to the receiver as a fixed position.

Requires rtkbase_raw2nmea.service to be running and producing real fixes - enable it first
if it isn't:
    sudo systemctl enable --now rtkbase_raw2nmea.service

Note: this only fixes the position the RECEIVER broadcasts (RTCM 1005). RTKBase's own
"Base coordinates" setting in the web UI is a separate value fed to str2str's -p flag, which
does not reliably produce a working 1005 for this receiver - update both if you want the map
display to match, but this script is what a rover actually needs.

Also useful once you've logged enough raw data to get a precise coordinate from a
post-processing service (AUSPOS, OPUS, or similar PPP service) - skip the live averaging and
feed that result straight in with --llh or --ecef instead.

Usage:
    ./lg290p_set_fixed_position.py --port /dev/ttyACM0
    ./lg290p_set_fixed_position.py --port /dev/ttyACM0 --duration 600 --yes
    ./lg290p_set_fixed_position.py --port /dev/ttyACM0 --ecef -2368021.47 4862841.60 -3368903.03
    ./lg290p_set_fixed_position.py --port /dev/ttyACM0 --llh -32.0900781 115.9643451 9.408
"""

import argparse
import math
import socket
import sys
import time

from lg290p_tool import LG290P, DEFAULT_TIMEOUT, save_params, reboot, wait_for_port, response_ok

WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563


def llh_to_ecef(lat_deg: float, lon_deg: float, h: float):
    """WGS84 geodetic (deg, deg, m) -> ECEF X/Y/Z (m)."""
    e2 = WGS84_F * (2 - WGS84_F)
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    n = WGS84_A / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    x = (n + h) * math.cos(lat) * math.cos(lon)
    y = (n + h) * math.cos(lat) * math.sin(lon)
    z = (n * (1 - e2) + h) * math.sin(lat)
    return x, y, z


def nmea_deg(value: str, direction: str) -> float:
    """'3205.40145', 'S' -> -32.0900242 (decimal degrees)."""
    if len(value) < 4:
        return 0.0
    split = value.find(".") - 2
    deg = float(value[:split])
    minutes = float(value[split:])
    dec = deg + minutes / 60.0
    if direction in ("S", "W"):
        dec = -dec
    return dec


def collect_fixes(host: str, port: int, duration: float, min_fix_quality: int = 1):
    """Collect (lat, lon, height) from GGA sentences with a valid fix for `duration` seconds."""
    try:
        sock = socket.create_connection((host, port), timeout=10)
    except OSError as exc:
        sys.exit(
            f"Couldn't connect to {host}:{port} ({exc}).\n"
            "Is rtkbase_raw2nmea.service running? Enable it with:\n"
            "  sudo systemctl enable --now rtkbase_raw2nmea.service"
        )
    sock.settimeout(2)

    fixes = []
    buf = b""
    deadline = time.time() + duration
    last_report = 0.0
    while time.time() < deadline:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            continue
        if not chunk:
            sys.exit("Connection to raw2nmea's NMEA stream closed unexpectedly.")
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            line = line.decode("ascii", errors="replace").strip()
            if "GGA" not in line:
                continue
            fields = line.split(",")
            if len(fields) < 10:
                continue
            try:
                fix_quality = int(fields[6])
            except ValueError:
                continue
            if fix_quality < min_fix_quality:
                continue
            try:
                lat = nmea_deg(fields[2], fields[3])
                lon = nmea_deg(fields[4], fields[5])
                height = float(fields[9])
            except (ValueError, IndexError):
                continue
            fixes.append((lat, lon, height))

        remaining = deadline - time.time()
        if remaining > 0 and time.time() - last_report > 10:
            print(f"  collecting... {len(fixes)} fixes so far, {remaining:.0f}s remaining", file=sys.stderr)
            last_report = time.time()

    sock.close()
    return fixes


def main():
    ap = argparse.ArgumentParser(
        description="Average a real LG290P position and push it as a fixed base-station coordinate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--port", required=True, help="receiver serial port, e.g. /dev/ttyACM0")
    ap.add_argument("--baudrate", type=int, default=460800)
    ap.add_argument("--nmea-host", default="localhost", help="rtkbase_raw2nmea host (default: localhost)")
    ap.add_argument("--nmea-port", type=int, default=5014, help="rtkbase_raw2nmea NMEA port (default: 5014, matches settings.conf's nmea_port)")
    ap.add_argument("--duration", type=float, default=300.0, help="how long to average fixes for, in seconds (default: 300). Ignored if --llh or --ecef is given.")
    ap.add_argument("--min-fix-quality", type=int, default=1, help="minimum NMEA GGA fix quality to accept (default: 1, any fix)")
    ap.add_argument("--llh", nargs=3, type=float, metavar=("LAT", "LON", "HEIGHT"),
                     help="skip live averaging, use this WGS84 lat/lon (deg) + ellipsoidal height (m) instead - "
                          "e.g. from a post-processing service like AUSPOS/OPUS/PPP")
    ap.add_argument("--ecef", nargs=3, type=float, metavar=("X", "Y", "Z"),
                     help="skip live averaging, use this WGS84 ECEF X/Y/Z (m) directly - "
                          "most PPP post-processing reports include this alongside the LLH result")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    ap.add_argument("--retry", type=int, default=3)
    args = ap.parse_args()

    if args.ecef:
        x, y, z = args.ecef
        print(f"Using supplied ECEF directly: X={x} Y={y} Z={z}")
    elif args.llh:
        lat, lon, height = args.llh
        x, y, z = llh_to_ecef(lat, lon, height)
        print(f"Using supplied LLH: lat={lat} lon={lon} height={height} m")
        print(f"  -> ECEF: X={x:.4f}  Y={y:.4f}  Z={z:.4f}")
    else:
        print(f"Collecting fixes from {args.nmea_host}:{args.nmea_port} for {args.duration:.0f}s...")
        fixes = collect_fixes(args.nmea_host, args.nmea_port, args.duration, args.min_fix_quality)

        if not fixes:
            sys.exit(
                f"No fixes with quality >= {args.min_fix_quality} were received in "
                f"{args.duration:.0f}s. Nothing was written to the receiver."
            )

        lat = sum(f[0] for f in fixes) / len(fixes)
        lon = sum(f[1] for f in fixes) / len(fixes)
        height = sum(f[2] for f in fixes) / len(fixes)
        x, y, z = llh_to_ecef(lat, lon, height)

        print(f"\nAveraged {len(fixes)} fixes over {args.duration:.0f}s:")
        print(f"  LLH:  lat={lat:.7f}  lon={lon:.7f}  height={height:.3f} m")
        print(f"  ECEF: X={x:.4f}  Y={y:.4f}  Z={z:.4f}")

    if not args.yes:
        answer = input("\nWrite this as the receiver's fixed position? [y/N] ").strip().lower()
        if answer != "y":
            sys.exit("Aborted, nothing was written.")

    with LG290P(args.port, args.baudrate, DEFAULT_TIMEOUT) as dev:
        payload = f"PQTMCFGSVIN,W,2,0,0,{x:.4f},{y:.4f},{z:.4f}"
        resp = dev.command(payload, retry=args.retry)
        if not response_ok(resp):
            sys.exit(f"Failed to set fixed position: {resp}")
        print("\nFixed position accepted, saving...")
        if not save_params(dev, args.retry):
            sys.exit("Failed to save parameters.")
        print("Resetting so the new position takes effect (PQTMCFGSVIN needs a reset, a save alone isn't enough)...")
        path = dev.port
        reboot(dev)
        if not wait_for_port(path):
            sys.exit("Receiver didn't come back after reset - check the connection.")

    print("\nDone. The receiver should now broadcast this position via RTCM 1005.")
    print("Verify with: ./lg290p_tool.py --port " + args.port + " --command raw 'PQTMCFGSVIN,R'")


if __name__ == "__main__":
    main()
