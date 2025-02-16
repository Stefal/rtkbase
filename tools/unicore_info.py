#! /usr/bin/env python3

from time import sleep
from unicore.unicore_cmd import *
import asyncio
import serial_asyncio
import logging

logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel('DEBUG')

class Um98xInfo():
    def __init__(
                self,
                address,
                baudrate=115200,
                ):
        self.model = ""
        self.firmware = ""
        self.ant_agc_values = {}
        self.ant_agc_status = {}
        #asyncio.run(self.read_and_write_serial())
        self.task = asyncio.create_task(self.read_and_write_serial())
        await asyncio.sleep(0)
        asyncio.run(self.task)
        
    def get_agc_values(self):
        agc = self.conn.get_agc_values()
        self.ant_agc_values = {'L1': agc[0], 'L2': agc[1], 'L5': agc[2]}

    def get_agc_status(self):
        for k,v in self.ant_agc_values.items():
            if value >= 0 and value < 10:
                self.ant_agc_status[k] = 'good'
            elif value >= 10:
                self.ant_agc_status[k] = 'bad'
            
    async def read_and_write_serial(self):
        #reader, writer = await serial_asyncio.open_serial_connection(url='/dev/ttyUSB0', baudrate=115200)
        reader, writer = await serial_asyncio.open_serial_connection(url="socket://localhost:5015")

        async def read_serial():
            while True:
                line = await reader.readline()
                line = line.decode(encoding = 'ASCII', errors='ignore')
                if '#AGCA' in line:
                        #AGCA,65,GPS,FINE,2190,375570000,0,0,18,37;44,46,63,-1,-1,41,1,0,-1,-1*634f1e4b
                        #Antenna 1 values: 44,46,63
                        #Antenna 2 values: 41,1,0
                        log.debug("line containing #AGCA: ",line)
                        try:
                            values_list = line.split('#')[-1]
                            values_list = line.replace("'", "").split(";")[-1].split(",")
                            agc_values = values_list[:3] + values_list[5:8]
                            agc_values = [ int(x) for x in agc_values]
                            #print("buffer size: ", await reader.in_waiting)
                            self.ant_agc_values = {'L1': agc_values[0], 'L2': agc_values[1], 'L5': agc_values[2]}
                            #print("AGC values: ", self.ant_agc_values)
                        except IndexError:
                            pass

                        #return agc_values

        async def write_serial():
            while True:
                #message = await asyncio.get_event_loop().run_in_executor(None, input, "Entrez un message: ")
                writer.write(f"AGCA 1\n".encode())
                #print("sending AGCA 1")
                await writer.drain()
                await asyncio.sleep(1)

        await asyncio.gather(read_serial(), write_serial())
        #await asyncio.gather(read_serial())

um98x = Um98xInfo('/dev/ttyUSB0')
asyncio.run(um98x.read_and_write_serial())
print("Antenna values: ",um98x.ant_agc_values)
print("Antenna status: ",um98x.get_agc_status())
print("sleeping 2")
time.sleep(2)
print("Antenna values: ",um98x.ant_agc_values)
print("Antenna status: ",um98x.get_agc_status())