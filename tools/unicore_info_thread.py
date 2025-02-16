#! /usr/bin/env python3

import logging
import serial
import threading
import time
import socket

logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)
#log.setLevel('DEBUG')

class UnicoreInfos():
    def __init__(self, tcp_host, tcp_port):
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.serial_port = None
        self.tcp_socket = None
        self.running = False
        self.thread = None
        self.model = ""
        self.firmware = ""
        self.ant_agc_values = {}
        self.ant_agc_status = {}
        
    def connect(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect((self.tcp_host, self.tcp_port))
        self.serial_port = serial.serial_for_url(f'socket://{self.tcp_host}:{self.tcp_port}')

    def start_parsing(self):
        self.running = True
        self.thread = threading.Thread(target=self._parse_data)
        self.thread.start()

    def stop_parsing(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def write_data(self, data):
        self.serial_port.write(data.encode())

    def close(self):
        self.stop_parsing()
        if self.serial_port:
            self.serial_port.close()
        if self.tcp_socket:
            self.tcp_socket.close()

    def _parse_data(self):
            while self.running:
                try:
                    line = self.serial_port.readline().decode(encoding = 'ASCII', errors='ignore').strip()
                    if '#AGCA' in line:
                        self._parse_agca()
                except serial.SerialException:
                    break

    def _parse_agca(self, line):
        #AGCA,65,GPS,FINE,2190,375570000,0,0,18,37;44,46,63,-1,-1,41,1,0,-1,-1*634f1e4b
        #Antenna 1 values: 44,46,63
        #Antenna 2 values: 41,1,0
        log.debug("line containing #AGCA: ",line)
        try:
            values_list = line.split('#')[-1]
            values_list = line.replace("'", "").split(";")[-1].split(",")
            agc_values = values_list[:3] + values_list[5:8]
            agc_values = [ int(x) for x in agc_values]
            self.ant_agc_values = {'L1': agc_values[0], 'L2': agc_values[1], 'L5': agc_values[2]}
            for k,v in self.ant_agc_values.items():
                if v >= 0 and v < 10:
                    self.ant_agc_status[k] = 'good'
                elif v >= 10:
                    self.ant_agc_status[k] = 'bad'
        except IndexError:
            pass

    def __del__(self):
        self.close()

if __name__ == '__main__':
    #um98x = Um98xInfo('/dev/ttyUSB0')
    um98x = TCPSerialParser('localhost', 5015)
    um98x.connect()
    um98x.start_parsing()
    #asyncio.run(um98x.read_and_write_serial())
    print("Antenna values: ",um98x.ant_agc_values)
    print("Antenna status: ",um98x.get_agc_status())
    print("sleeping 2")
    time.sleep(2)
    print("Antenna values: ",um98x.ant_agc_values)
    print("Antenna status: ",um98x.get_agc_status())
    time.sleep(2)
    print("Antenna values: ",um98x.ant_agc_values)
    print("Antenna status: ",um98x.get_agc_status())
    um98x.close()