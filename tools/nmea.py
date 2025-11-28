#!/usr/bin/env python3

import argparse
import serial
import time

# Function to calculate NMEA checksum
def calculate_nmea_checksum(nmea_sentence):
    checksum = 0
    # Iterate through each character after the starting '$' and before '*'
    for char in nmea_sentence[1:]:
        checksum ^= ord(char)
    return f"{nmea_sentence}*{checksum:02X}"

# Function to append checksum if not provided
def append_checksum_if_missing(nmea_sentence):
    if '*' not in nmea_sentence:
        # Calculate and append checksum if '*' is missing
        return calculate_nmea_checksum(nmea_sentence)
    return nmea_sentence

# Function to handle serial communication
def send_nmea_command(port, speed, timeout, nmea_command, verbose):
    # Open serial port
    try:
        with serial.Serial(port, baudrate=speed, timeout=timeout) as ser:
            # Append checksum if missing
            nmea_command_with_checksum = append_checksum_if_missing(nmea_command)
            
            # Write NMEA command to the serial port
            ser.write((nmea_command_with_checksum + '\r\n').encode('ascii'))
            if verbose:
                print(f"Sent command: {nmea_command_with_checksum}")

            # Wait for the response
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = ser.readline().decode('ascii', errors='ignore').strip()
                    # Process only valid ASCII responses
                    if response and response.startswith('$'):
                        if verbose:
                            print(f"Received response: {response}")
                        return response
                except UnicodeDecodeError as e:
                    # Skip non-ASCII responses (likely RTCM3 messages)
                    if verbose:
                        print(f"Non-ASCII data skipped: {e}")
            if verbose:
                print("Timeout: No matching response received.")
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")

# Function to read NMEA commands from a file and ignore lines starting with '#' and blank lines
def read_commands_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            commands = []
            for line in file:
                line = line.strip()
                # Ignore blank lines and lines starting with '#'
                if line and not line.startswith('#') or line.startswith('#SLEEP#'):
                    commands.append(line)
            return commands
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []

# Function to handle the sleep command in the file
def handle_sleep_command(command, verbose):
    try:
        sleep_time_ms = int(command.split('#SLEEP# ')[1])
        if verbose:
            print(f"Sleeping for {sleep_time_ms} ms")
        time.sleep(sleep_time_ms / 1000)  # Convert to seconds
    except (IndexError, ValueError):
        print(f"Invalid sleep command format: {command}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Send NMEA commands to Quectel LC29H module")
    parser.add_argument('port', type=str, help='Serial port to use (e.g., /dev/ttyUSB0 or COM3)')
    parser.add_argument('speed', type=int, help='Baud rate (e.g., 9600)')
    parser.add_argument('timeout', type=int, help='Timeout in seconds')
    parser.add_argument('command', nargs='?', type=str, help='NMEA command to send (optional, overrides file)')
    parser.add_argument('--file', type=str, help='File with NMEA commands to send')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output for tracing')

    args = parser.parse_args()

    # Determine which commands to send (from file or argument)
    if args.command:
        # Send the provided command as an argument
        nmea_commands = [args.command]
    elif args.file:
        # Read commands from the file, ignoring comments and blank lines
        nmea_commands = read_commands_from_file(args.file)
    else:
        print("Error: You must provide either a command or a file containing commands.")
        exit(1)

    # Send each NMEA command from the list
    for command in nmea_commands:
        if command.startswith('#SLEEP#'):
            handle_sleep_command(command, args.verbose)
        else:
            send_nmea_command(args.port, args.speed, args.timeout, command, args.verbose)
