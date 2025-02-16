#! /usr/bin/env python3
import serial
import time


class SerialComm:
    def __init__(
        self,
        address,
        baudrate=115200,
        timeout=5,
        write_timeout=5,
        cmd_delay=0.1,
        connection_descriptor='USB2>',
        on_error=None,
        byte_encoding="ISO-8859-1",
    ):
        self.cmd_delay = cmd_delay
        self.connection_descriptor = connection_descriptor
        self.on_error = on_error
        self.byte_encoding = byte_encoding
        self.device_serial = serial.Serial(
            port=address,
            baudrate=baudrate,
            timeout=timeout,
            write_timeout=write_timeout
        )

    def send(self, cmd) -> str:
        self.device_serial.write(cmd.encode(self.byte_encoding) + b"\r")
        time.sleep(self.cmd_delay)

    def send_raw(self, cmd):
        self.device_serial.write(cmd)
        time.sleep(self.cmd_delay)

    def read_lines(self) -> list:
        read = self.device_serial.readlines()
        for i, line in enumerate(read):
            read[i] = line.decode(self.byte_encoding).strip()
        return read

    def read_until(self, expect = None) -> list:
        expect = self.connection_descriptor if expect == None else expect
        read = self.device_serial.read_until(expected=bytes(expect, encoding=self.byte_encoding))
        read = read.decode(self.byte_encoding).strip().splitlines()
        read = [ val for val in read if val != '']
        return read

    def read_until_line(self, expected='\r\n', eol='\r\n') -> str:
        read_start = self.device_serial.read_until(expected = expected.encode())
        read_start = read_start.decode(self.byte_encoding, errors='ignore').strip().splitlines()[-1]
        if expected in read_start:
            read_end = self.device_serial.readline().decode(self.byte_encoding, errors='ignore')
            return read_start + read_end

    def read_raw(self, size: int):
        return self.device_serial.read(size)

    def close(self):
        self.device_serial.close()