#! /usr/bin/env python3
from . serial_comm import SerialComm
from enum import Enum
import logging
from itertools import chain
import time
#Code inspired by https://github.com/jonamat/sim-modem

logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel('ERROR')

class UnicoGnss():
    """Class for sending commands to Unicore Gnss receivers"""

    RESET_REQUIRED = ('CONFIG SIGNALGROUP',
                      'RESET',
                      'FRESET',
                      )
    def __init__(
                self,
                address,
                baudrate=115200,
                timeout=2,
                cmd_delay=0.1,
                debug=False,
                ):
        self.comm = SerialComm(
            address=address,
            baudrate=baudrate,
            timeout=timeout,
            cmd_delay=cmd_delay,
        )
        if debug:
            log.setLevel('DEBUG')
        self.is_open = self.comm.device_serial.is_open
        self.connect()

    def connect(self) -> None:
        '''
            Connect to the Unicore receiver
        '''
        log.debug("Connecting...")
        try:
            # Send a line return to clear the Unicore input buffer
            # It was a problem when the ubxtool was sending some commands without LF just before the unicore detection script.
            self.comm.send('\r\n')
            if self.get_receiver_model():
                #print("GNSS receiver connected")
                return
            else:
                raise Exception
            log.debug("GNSS receiver connected, debug mode enabled")
            log.debug("read: {}".format(read))

        except Exception as e:
            log.warning("GNSS receiver did not respond correctly. Closing serial port.")
            log.warning(e)
            #log.debug(read)
            self.close()

    def close(self) -> None:
        self.comm.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

    # --------------------------------- Common methods --------------------------------- #

    def get_receiver_model(self) -> str:
        '''
            Get the Unicore receiver model (UM980, UM982, ....)
        '''
        log.debug("Get receiver model")
        read = self.send_read_until(self._cmd_with_checksum('VERSIONA'), expected=self._expected_res_for('VERSIONA'))
        #'$command,VERSIONA,response: OK*45\r\n
        # #VERSIONA,97,GPS,FINE,2343,48235000,0,0,18,813;"UM980","R4.10Build11833","HRPT00-S10C-P",
        # "2310415000001-MD22A2225022497","ff3ba396dcb0478d","2023/11/24"*270a13f7\r\n'
        log.debug("Receive ack: {}".format(read))
        read = self.comm.read_until_line(expected='#VERSIONA')
        log.debug("Received answer: {}".format(read))
        if '#VERSIONA' in read:
            model = read.replace("'", "").split(";")[-1].split(",")[0].replace('"','')
            return model
        return None

    def get_receiver_firmware(self) -> str:
        '''
            Get the Unicore receiver firmware version
        '''
        read = self.send_read_until(self._cmd_with_checksum('VERSIONA'), expected=self._expected_res_for('VERSIONA'))
        #'$command,VERSIONA,response: OK*45\r\n
        # #VERSIONA,97,GPS,FINE,2343,48235000,0,0,18,813;"UM980","R4.10Build11833","HRPT00-S10C-P",
        # "2310415000001-MD22A2225022497","ff3ba396dcb0478d","2023/11/24"*270a13f7\r\n'
        log.debug("Received ack: {}".format(read))
        read = self.comm.read_until_line(expected='#VERSIONA')
        log.debug("Received answer: {}".format(read))
        if '#VERSIONA' in read:
            firmware = read.replace("'", "").split(";")[-1].split(",")[1].replace('"','')
            return firmware
        return None

    def set_factory_default(self) -> None:
        '''
           Reset the Unicore receiver settings to factory defaults and restart it.
           Connection will be closed
        '''
        log.debug("Sending: 'FRESET'")
        read = self.send_read_until(self._cmd_with_checksum('FRESET'), expected='#FRESET')
        log.debug("Receiving ack: {}".format(read))
        if self._expected_res_for('FRESET') not in read:
            raise Exception("Command failed! {}".format(read))
        self.close()
        print("Resetting receiver. Connection closed")

    def send_config_file(self, file, perm=False) -> None:
        '''
            Send user commands from a txt file, line by line
            Set perm to True if you want to set these settings permanent

            Parameter
                file(file): the text file containing the settings to be sent
                perm(bool): if True, store permanently the settings
            
        '''
        with open(file, 'r') as f:
            for line in f:
                if line.strip() != '' and not line.startswith('#'):
                    log.debug("Sending cmd: {}".format(line.strip()))
                    read = self.send_read_until(self._cmd_with_checksum(line.strip()), expected=self._expected_res_for(line.strip()))
                    log.debug("Received answer: {}".format(read))
                    #self.send_read_raw(line.strip())
                    if any(x in line for x in self.RESET_REQUIRED):
                        log.info("Rebooting. Waiting for 10s...")
                        time.sleep(10)
        if perm:
            self.set_config_permanent()

    def set_config_permanent(self) -> None:
        '''
            Save current settings to boot config
        '''
        log.debug("Sending: 'SAVECONFIG'")
        read = self.send_read_until(self._cmd_with_checksum('SAVECONFIG'), expected=self._expected_res_for('SAVECONFIG'))
        log.debug("Received answer: {}".format(read))
        if self._expected_res_for('SAVECONFIG') not in read[-1]:
            raise Exception("Command failed! {}".format(read))
        print("Settings saved")

    def get_agc_values(self) -> list:
        '''
            Get the automatic gain control values
        '''
        read = self.send_read_until(self._cmd_with_checksum('AGCA '), expected=self._expected_res_for('AGCA '))
        log.debug("Receive ack: {}".format(read))
        # $command,AGCA,response: OK*5A
        # #AGCA,97,GPS,FINE,2345,328881000,0,0,18,22;40,76,65,-1,-1,-1,-1,-1,-1,-1*8c8123ba
        read = self.comm.read_until_line(expected='#AGCA')
        log.debug("Received answer: {}".format(read))
        if '#AGCA' in read:
            #AGCA,65,GPS,FINE,2190,375570000,0,0,18,37;44,46,63,-1,-1,41,1,0,-1,-1*634f1e4b
            #Antenna 1 values: 44,46,63
            #Antenna 2 values: 41,1,0
            values_list = read.replace("'", "").split(";")[-1].split(",")
            agc_values = values_list[:3] + values_list[5:8]
            agc_values = [ int(x) for x in agc_values]
            return agc_values
        else:
            raise Exception("Command failed! {}".format(read))

    def get_agc_status(self) -> list:
        '''
            Get the automatic gain control status (human readable)
            return value is a list of string, with good/bad for each frequency (L1/L2/L5)
            and for each antenna (ant 1 then ant 2)
        '''
        agc_values = self.get_agc_values()
        agc_status = []
        for i, value in enumerate(agc_values):
            if value >= 0 and value < 10: # TODO : check real values to set the limits
                agc_status.append('good')
            elif value >= 10:
                agc_status.append('bad')
        return agc_status
        
    # ----------------------------------- OTHERS --------------------------------- #

    def send_read_lines(self, cmd, *args) -> list:
        log.debug("Sending: {}{}{}".format(cmd, ' ' if args else '', ' '.join(args)))
        self.comm.device_serial.reset_input_buffer()
        self.comm.send(cmd)
        read = self.comm.read_lines()
        log.debug("Receiving: {}".format(read))
        return read

    def send_read_until(self, cmd, *args, expected='\n\r') -> list:
        log.debug("Sending: {}{}{}".format(cmd, ' ' if args else '', ' '.join(args)))
        self.comm.device_serial.reset_input_buffer()
        self.comm.send("{}{}{}".format(cmd, ' ' if args else '', ' '.join(args)))
        read = self.comm.read_until(expected)
        log.debug("send_read_until>Receiving: {}".format(read))
        return read

    def send_read_raw(self, cmd, *args, size=10000):
        """
            Send command(s) to the UM980, wait for the buffer to be filled
            and returns the answer from the UM980.

            Parameter:
                cmd(str): main command
                *args(str): command parameters
                size(int): answer size needed to return (or timeout)
            Return:
                bytes: the answer sent by the UM980
        """
        log.debug("Sending: {}{}{}".format(cmd, ' ' if args else '', ' '.join(args)))
        self.comm.device_serial.reset_input_buffer()
        self.comm.send("{}{}{}".format(cmd, ' ' if args else '', ' '.join(args)))
        read = self.comm.read_raw(size)
        log.debug("Receiving: {}".format(read))
        return read

    def _cmd_with_checksum(self, cmd):
        """
            Convert Ascii command to Ascii command with checksum
            It adds a '$' before the command
            and '*' + checskum value at the end.
            e.g. 'VERSIONA' returns '$VERSIONA*1b'

            Parameter
                cmd(str): the command
            Return
                str: the command concatenated with a XOR 8 checksum
        """
        return '${}*{}'.format(cmd, self._xor8_checksum(cmd))

    def _expected_res_for(self, cmd):
        """
            Create the expected answer for a sent command
            e.g. 'VERSIONA' returns '$command,VERSIONA,response: OK*45'

            Parameter
                cmd(str) : The sent command
            Return
                str : The command with prefix, suffixe and checksum
        """
        res_without_checksum = '$command,{},response: OK'.format(cmd)
        expected = '{}*{}'.format(res_without_checksum, self._xor8_checksum(res_without_checksum))
        log.debug("Expected response: {}".format(expected))
        return expected

    def _xor8_checksum(self, data):
        """
            Return XOR 8 checksum in hexadecimal with 0x stripped
            e.g. 'VERSIONA' returns '1B'
        """
        checksum = 0
        for char in data:
            checksum ^= ord(char)
        checksum = checksum & 0xFF
        return '{:x}'.format(checksum).zfill(2).upper()