#!/usr/bin/env python3
"""Query and configure Quectel LG290P receivers over their NMEA command port."""

import argparse
import re
import sys
import time
from pathlib import Path


DEFAULT_BAUDRATE = 460800
SUPPORTED_FIRMWARE = "LG290P03"


def nmea_checksum(command: str) -> str:
    """Return the NMEA XOR checksum for a command body."""
    checksum = 0
    for character in command.strip().lstrip("$").split("*", 1)[0]:
        checksum ^= ord(character)
    return f"{checksum:02X}"


def nmea_sentence(command: str) -> bytes:
    command = command.strip().lstrip("$").split("*", 1)[0]
    return f"${command}*{nmea_checksum(command)}\r\n".encode("ascii")


def open_serial(port: str, baudrate: int):
    import serial

    return serial.Serial(port=port, baudrate=baudrate, timeout=0.2, write_timeout=2)


def get_firmware(port: str, baudrate: int) -> str:
    with open_serial(port, baudrate) as connection:
        connection.reset_input_buffer()
        connection.write(nmea_sentence("PQTMVERNO"))
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            line = connection.readline().decode("ascii", errors="ignore").strip()
            match = re.match(r"^\$?PQTMVERNO,([^,*]+),", line)
            if match:
                firmware = match.group(1)
                if re.fullmatch(
                    rf"{re.escape(SUPPORTED_FIRMWARE)}[A-Za-z0-9._-]+", firmware
                ):
                    return firmware
                raise RuntimeError(f"Unsupported Quectel firmware: {firmware}")
    raise TimeoutError("No Quectel PQTMVERNO response received")


def get_receiver_mode(port: str, baudrate: int) -> str:
    with open_serial(port, baudrate) as connection:
        connection.reset_input_buffer()
        connection.write(nmea_sentence("PQTMCFGRCVRMODE,R"))
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            line = connection.readline().decode("ascii", errors="ignore").strip()
            fields = line.split("*", 1)[0].lstrip("$").split(",")
            if fields[0] != "PQTMCFGRCVRMODE" or len(fields) < 2:
                continue
            if fields[1] == "ERROR":
                raise RuntimeError(f"Receiver rejected mode query: {line}")
            if fields[1] == "OK" and len(fields) >= 3:
                return fields[2]
    raise TimeoutError("No receiver mode response received")


def send_config_file(port: str, baudrate: int, config_file: Path) -> None:
    with config_file.open(encoding="utf-8") as config:
        commands = [
            line.strip()
            for line in config
            if line.strip() and not line.strip().startswith("#")
        ]
    if not commands:
        raise ValueError(f"Configuration file is empty: {config_file}")

    with open_serial(port, baudrate) as connection:
        for command in commands:
            command_name = command.lstrip("$").split(",", 1)[0].split("*", 1)[0]
            connection.reset_input_buffer()
            connection.write(nmea_sentence(command))

            if command_name == "PQTMSRR":
                time.sleep(5)
                continue

            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                line = connection.readline().decode("ascii", errors="ignore").strip()
                fields = line.split("*", 1)[0].lstrip("$").split(",")
                if fields[0] != command_name or len(fields) < 2:
                    continue
                if fields[1] == "ERROR":
                    raise RuntimeError(f"Receiver rejected {command}: {line}")
                if fields[1] == "OK":
                    break
            else:
                raise TimeoutError(f"No acknowledgement received for {command}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="Serial port, e.g. /dev/ttyACM0")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE)
    parser.add_argument(
        "--command",
        required=True,
        choices=("get_version", "get_mode", "send_config_file"),
    )
    parser.add_argument("--config-file", type=Path)
    args = parser.parse_args()

    try:
        if args.command == "get_version":
            print(get_firmware(args.port, args.baudrate))
        elif args.command == "get_mode":
            print(get_receiver_mode(args.port, args.baudrate))
        else:
            if args.config_file is None:
                parser.error("--config-file is required with send_config_file")
            send_config_file(args.port, args.baudrate, args.config_file)
    except (ImportError, OSError, RuntimeError, TimeoutError, ValueError) as error:
        print(f"Quectel receiver error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
