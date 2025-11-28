#!/usr/bin/env python3

import argparse
import serial
import time
import re
import sys
from pyproj import Transformer

# Terminal colour codes
class Colour:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'

# Accuracy thresholds (constants for easier adjustment)
ACCURACY_THRESHOLD_1M = 1.0
ACCURACY_THRESHOLD_10CM = 0.1

# Common baud rates to try for auto-detection
BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 921600]

def calculate_nmea_checksum(nmea_sentence: str) -> str:
    checksum = 0
    for char in nmea_sentence[1:]:
        checksum ^= ord(char)
    return f"{nmea_sentence}*{checksum:02X}"

def append_checksum_if_missing(nmea_sentence: str) -> str:
    if '*' not in nmea_sentence:
        return calculate_nmea_checksum(nmea_sentence)
    return nmea_sentence

def read_gps_messages(port: str, speed: int, timeout: int, verbose: bool = False):
    try:
        with serial.Serial(port, baudrate=speed, timeout=timeout) as ser:
            while True:
                response = ser.readline().decode('ascii', errors='ignore').strip()
                if response and response.startswith('$'):
                    if verbose:
                        print(f"{Colour.OKBLUE}Received message: {response}{Colour.ENDC}")
                    yield response
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")

def ecef_to_geodetic(x: float, y: float, z: float) -> tuple:
    transformer = Transformer.from_crs("EPSG:4978", "EPSG:4326", always_xy=True)
    lon, lat, alt = transformer.transform(x, y, z)
    return lat, lon, alt

def colour_diff(current: str, previous: str) -> str:
    """
    Compare digits in the current and previous strings. Mark changed digits in red.
    """
    result = []
    change_detected = False
    for c, p in zip(current, previous):
        if c.isdigit() and p.isdigit():
            if change_detected or c != p:
                result.append(f"{Colour.RED}{c}{Colour.ENDC}")
                change_detected = True
            else:
                result.append(f"{Colour.GREEN}{c}{Colour.ENDC}")
        else:
            result.append(c)
            change_detected = False
    if len(current) > len(previous):
        for c in current[len(previous):]:
            result.append(f"{Colour.RED}{c}{Colour.ENDC}" if c.isdigit() else c)
    return ''.join(result)

def redraw_terminal(lines: list, reset_cursor: bool):
    """
    Redraw lines in the terminal. If reset_cursor is True, reset cursor position for updates.
    If False, simply print lines without resetting the cursor.
    """
    if sys.stdout.isatty():
        if reset_cursor:
            sys.stdout.write('\033[F' * len(lines))  # Reset the cursor for updates
        for line in lines:
            sys.stdout.write('\033[K' + line + '\n')  # Print each line

def colourise_accuracy(accuracy: float) -> str:
    """Colour accuracy based on its value."""
    if accuracy > ACCURACY_THRESHOLD_1M:
        return f"{Colour.RED}{accuracy:.2f}{Colour.ENDC} metres"
    elif accuracy >= ACCURACY_THRESHOLD_10CM:
        return f"{Colour.YELLOW}{accuracy:.2f}{Colour.ENDC} metres"
    else:
        return f"{Colour.GREEN}{accuracy:.2f}{Colour.ENDC} metres"

def start_survey_in(port: str, speed: int, timeout: int, min_dur: int, acc_limit: float, verbose: bool):
    command = f"$PQTMCFGSVIN,W,1,{min_dur},{acc_limit},0.0,0.0,0.0"
    send_nmea_command(port, speed, command, timeout, verbose)
    
    print(Colour.HEADER + Colour.BOLD + "Starting survey-in..." + Colour.ENDC)
    
    start_time = time.time()
    prev_ecef = None
    prev_geo = None
    prev_latlon = None  # Cache to avoid unnecessary recalculations
    reset_cursor = False  # Track whether to reset the cursor

    for response in read_gps_messages(port, speed, timeout, verbose):
        match = re.match(r"\$PQTMSVINSTATUS,\d+,\d+,(\d+),,\d+,\d+,\d+,(-?\d+\.\d+),(-?\d+\.\d+),(-?\d+\.\d+),(\d+\.\d+)\*\w+", response)
        if match:
            valid_flag = int(match.group(1))
            mean_x, mean_y, mean_z = map(float, match.group(2, 3, 4))
            mean_acc = float(match.group(5))
            obs_count = int(response.split(',')[6])
            elapsed_time = int(time.time() - start_time)
            remaining_time = max(0, int(min_dur - elapsed_time))

            # Convert ECEF to geodetic only if ECEF coordinates have changed
            if prev_ecef != (mean_x, mean_y, mean_z):
                lat, lon, alt = ecef_to_geodetic(mean_x, mean_y, mean_z)
                prev_latlon = f"Lat={lat:.7f}, Lon={lon:.7f}, Alt={alt:.3f}"

            current_ecef = f"X={mean_x:.4f}, Y={mean_y:.4f}, Z={mean_z:.4f}"

            if prev_ecef:
                colourised_ecef = colour_diff(current_ecef, f"X={prev_ecef[0]:.4f}, Y={prev_ecef[1]:.4f}, Z={prev_ecef[2]:.4f}")
                colourised_geo = colour_diff(prev_latlon, prev_geo)
            else:
                colourised_ecef = current_ecef
                colourised_geo = prev_latlon

            prev_ecef = (mean_x, mean_y, mean_z)
            prev_geo = prev_latlon

            coloured_accuracy = colourise_accuracy(mean_acc)

            if valid_flag == 2:
                print(Colour.OKGREEN + "Survey-in complete." + Colour.ENDC)
                print(f"Final {Colour.BOLD}Accuracy{Colour.ENDC}: {coloured_accuracy}")
                print(f"Final {Colour.BOLD}ECEF{Colour.ENDC}: {current_ecef}")
                print(f"Final {Colour.BOLD}Geodetic{Colour.ENDC}: {prev_latlon}")
                break
            elif valid_flag == 1:
                lines_to_display = [
                    f"{Colour.WARNING}Survey-in in progress{Colour.ENDC}: {Colour.BOLD}Elapsed{Colour.ENDC}: {elapsed_time} seconds, {Colour.BOLD}Remaining{Colour.ENDC}: {remaining_time} seconds, {Colour.BOLD}Accuracy{Colour.ENDC}: {coloured_accuracy}, {Colour.BOLD}Observations{Colour.ENDC}: {obs_count}",
                    f"{Colour.HEADER}{Colour.BOLD}ECEF{Colour.ENDC}: {colourised_ecef}",
                    f"{Colour.HEADER}{Colour.BOLD}Geodetic{Colour.ENDC}: {colourised_geo}"
                ]
                redraw_terminal(lines_to_display, reset_cursor)
                reset_cursor = True  # Reset cursor for future updates
            time.sleep(1)

def send_nmea_command(port: str, speed: int, nmea_command: str, timeout: int, verbose: bool = False) -> str:
    try:
        with serial.Serial(port, baudrate=speed, timeout=timeout) as ser:
            nmea_command_with_checksum = append_checksum_if_missing(nmea_command)
            ser.write((nmea_command_with_checksum + '\r\n').encode('ascii'))
            if verbose:
                print(f"Sent command: {Colour.OKBLUE}{nmea_command_with_checksum}{Colour.ENDC}")
            
            response = ser.readline().decode('ascii', errors='ignore').strip()
            if response:
                if verbose:
                    print(f"Received response: {Colour.OKBLUE}{response}{Colour.ENDC}")
                return response
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")

def detect_speed(port: str, timeout: int, verbose: bool = False) -> int:
    command = "$PQTMVERNO"
    command_with_checksum = append_checksum_if_missing(command)
    for speed in BAUD_RATES:
        if verbose:
            print(f"Trying baud rate {speed}...")
        try:
            with serial.Serial(port, baudrate=speed, timeout=timeout) as ser:
                ser.write((command_with_checksum + '\r\n').encode('ascii'))
                if verbose:
                    print(f"Sent command: {Colour.OKBLUE}{command_with_checksum}{Colour.ENDC}")
                response = ser.readline().decode('ascii', errors='ignore').strip()
                if response.startswith("$PQTMVERNO"):
                    if verbose:
                        print(f"{Colour.OKGREEN}Received response at {speed} baud: {response}{Colour.ENDC}")
                    return speed
        except serial.SerialException:
            if verbose:
                print(f"{Colour.FAIL}Failed to open serial port at {speed} baud.{Colour.ENDC}")
    raise Exception("Failed to detect baud rate. No valid response for PQTMVERNO command.")

def disable_survey_in(port: str, speed: int, timeout: int, verbose: bool = False):
    command = "$PQTMCFGSVIN,W,0,0,0.0,0.0,0.0,0.0"
    send_nmea_command(port, speed, command, timeout, verbose)
    print(Colour.OKGREEN + "Survey-in disabled." + Colour.ENDC)

def set_fixed_mode(port: str, speed: int, ecef_x: float, ecef_y: float, ecef_z: float, timeout: int, verbose: bool = False):
    command = f"$PQTMCFGSVIN,W,2,0,0.0,{ecef_x},{ecef_y},{ecef_z}"
    response = send_nmea_command(port, speed, command, timeout, verbose)
    if response and "OK" in response:
        print(Colour.OKGREEN + "Fixed mode set successfully." + Colour.ENDC)
    else:
        print(Colour.FAIL + "Failed to set fixed mode." + Colour.ENDC)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Survey-in and Fixed mode tool for Quectel LC29H-BS GPS module.")
    parser.add_argument('port', type=str, help='Serial port to use (e.g., /dev/ttyUSB0 or COM3)')
    parser.add_argument('--timeout', type=int, default=3, help='Timeout in seconds for GPS response (default: 3 seconds)')
    parser.add_argument('--speed', type=int, help='Baud rate (e.g., 9600). If not provided, the script will attempt to detect the speed.')
    parser.add_argument('--mode', type=str, choices=['survey', 'fixed', 'disable'], required=True, help="Select mode: 'survey', 'fixed', or 'disable'")
    parser.add_argument('--ecef', nargs=3, type=float, help="ECEF coordinates (X Y Z) for fixed mode")
    parser.add_argument('--min-dur', type=int, default=86400, help="Minimum duration for survey-in mode (default: 86400 seconds / 1 day)")
    parser.add_argument('--acc-limit', type=float, default=15.0, help="Accuracy limit for survey-in mode in metres (default: 15 metres)")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    if args.speed:
        speed = args.speed
    else:
        speed = detect_speed(args.port, args.timeout, args.verbose)
        print(f"Detected speed: {speed} baud")

    if args.mode == 'disable':
        disable_survey_in(args.port, speed, args.timeout, args.verbose)
    elif args.mode == 'survey':
        start_survey_in(args.port, speed, args.timeout, args.min_dur, args.acc_limit, args.verbose)
    elif args.mode == 'fixed':
        if not args.ecef:
            print(Colour.FAIL + "Error: You must provide ECEF coordinates for fixed mode." + Colour.ENDC)
            exit(1)
        ecef_x, ecef_y, ecef_z = args.ecef
        set_fixed_mode(args.port, speed, ecef_x, ecef_y, ecef_z, args.timeout, args.verbose)

