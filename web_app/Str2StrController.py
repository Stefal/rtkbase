# ReachView code is placed under the GPL license.
# Written by Egor Fedorov (egor.fedorov@emlid.com)
# Copyright (c) 2015, Emlid Limited
# All rights reserved.

# If you are interested in using ReachView code as a part of a
# closed source project, please contact Emlid Limited (info@emlid.com).

# This file is part of ReachView.

# ReachView is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ReachView is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with ReachView.  If not, see <http://www.gnu.org/licenses/>.

import os
import signal
import pexpect
from glob import glob

from reach_tools import reach_tools

# This module automates working with STR2STR software

class Str2StrController:

    def __init__(self, rtklib_path):

        self.bin_path = rtklib_path

        self.gps_cmd_file_path = rtklib_path + "/app/rtkrcv"
        self.gps_cmd_file = "GPS_10Hz.cmd"

        self.child = 0
        self.started = False

        # port settings are kept as class properties:
        self.input_stream = ""
        self.output_stream = ""

        # Reach defaults for base position and rtcm3 messages:
        self.rtcm3_messages = ["1002", "1006", "1008", "1010", "1019", "1020"]
        self.base_position = [] # lat, lon, height

        self.setSerialStream() # input ublox serial
        #self.setTCPClientStream()
        self.setTCPServerStream(input = False) # output tcp server on port 9000

    def getAvailableReceiverCommandFiles(self):
        # returns a list of available cmd files in the working rtkrcv directory
        available_cmd_files = glob(self.gps_cmd_file_path + "/" +"*.cmd")
        available_cmd_files = [os.path.basename(cmd_file) for cmd_file in available_cmd_files]

        return available_cmd_files

    def formCommentString(self, options_list):

        comment = "("

        for index, option in enumerate(options_list):
            comment += str(index) + ":" + str(option)

            if index < len(options_list) - 1:
                comment += ","

        comment += ")"

        return comment

    def readConfig(self):
        parameters_to_send = {}

        parameters_to_send["0"] = {
            "parameter": "outstr-path",
            "value": self.output_stream,
            "comment": self.formCommentString(reach_tools.getAvailableSerialPorts()),
            "description": "Output path for corrections"
        }

        parameters_to_send["1"] = {"parameter": "rtcm3_out_messages", "value": ",".join(self.rtcm3_messages), "description": "RTCM3 messages for output"}

        # if we don't have a set base position we want to send empty strings
        if not self.base_position:
            base_pos = ["", "", ""]
        else:
            base_pos = self.base_position

        parameters_to_send["2"] = {"parameter": "base_pos_lat", "value": base_pos[0], "description": "Base latitude"}
        parameters_to_send["3"] = {"parameter": "base_pos_lon", "value": base_pos[1], "description": "Base longitude"}
        parameters_to_send["4"] = {"parameter": "base_pos_height", "value": base_pos[2], "description": "Base height"}

        parameters_to_send["5"] = {
                "parameter": "gps_cmd_file",
                "value": self.gps_cmd_file,
                "description": "Receiver configuration file",
                "comment": self.formCommentString(self.getAvailableReceiverCommandFiles())
        }

        print("DEBUG read")
        print(parameters_to_send)

        return parameters_to_send

    def writeConfig(self, parameters_received):

        print("DEBUG write")

        print(parameters_received)

        coordinate_filled_flag = 3
        base_pos = []

        self.output_stream = parameters_received["0"]["value"]

        # llh
        self.base_position = []
        self.base_position.append(parameters_received["2"]["value"])
        self.base_position.append(parameters_received["3"]["value"])
        self.base_position.append(parameters_received["4"]["value"])

        self.rtcm3_messages = parameters_received["1"]["value"].split(",")

        self.gps_cmd_file = parameters_received["5"]["value"]

    def setPort(self, port, input = True, format = "ubx"):
        if input:
            self.input_stream = port + "#" + format
        else:
            # str2str only supports rtcm3 for output
            self.output_stream = port + "#" + "rtcm3"

    def setSerialStream(self, serial_parameters = None, input = True, format = "ubx"):
        # easier way to specify serial port for str2str
        # serial_parameters is a list of options for our serial device:
        # 1. serial port
        # 2. baudrate
        # 3. byte size
        # 4. parity bit
        # 5. stop bit
        # 6. fctr
        # default parameters here are Reach standards

        def_parameters = [
            "ttyACM0",
            "230400",
            "8",
            "n",
            "1",
            "off"
        ]

        if serial_parameters is None:
            serial_parameters = def_parameters

        port = "serial://" + ":".join(serial_parameters)

        self.setPort(port, input, format)

    def setTCPClientStream(self, tcp_client_parameters = None, input = True, format = "ubx"):
        # easier way to specify tcp connection parameters for str2str
        # tcp client parameters include:
        # 1. ip address
        # 2. port number

        def_parameters = [
            "localhost",
            "5015"
        ]

        if tcp_client_parameters is None:
            tcp_client_parameters = def_parameters

        port = "tcpcli://" + ":".join(tcp_server_parameters)

        self.setPort(port, input, format)

    def setTCPServerStream(self, tcp_server_parameters = None, input = True, format = "ubx"):
        # tcp server parameters only include the port number:
        # 1. port number

        def_parameters = [
            "9000"
        ]

        if tcp_server_parameters is None:
            tcp_server_parameters = def_parameters

        port = "tcpsvr://:" + def_parameters[0]

        self.setPort(port, input, format)

    def setNTRIPClientStream(self, ntrip_client_parameters = None, input = True, format = "ubx"):
        # ntrip client parameters:
        # 1. user
        # 2. password
        # 3. address
        # 4. port
        # 5. mount point

        port = "ntrip://" + ntrip_client_parameters[0] + ":"
        port += ntrip_client_parameters[1] + "@" + ntrip_client_parameters[2] + ":"
        port += ntrip_client_parameters[3] + "/" + ntrip_client_parameters[4]

        self.setPort(port, input, format)

    def setNTRIPServerStream(self, ntrip_server_parameters = None, input = True, format = "ubx"):
        # ntrip client parameters:
        # 1. password
        # 2. address
        # 3. port
        # 4. mount point
        # 5. str ???

        port = "ntrips://:" + ntrip_client_parameters[0] + "@" + ntrip_client_parameters[1]
        port += ":" + ntrip_client_parameters[2] + "/" + ntrip_client_parameters[3] + ":"
        port += ntrip_client_parameters[4]

        self.setPort(port, input, format)

    def start(self, rtcm3_messages = None, base_position = None, gps_cmd_file = None):
        # when we start str2str we also have 3 important optional parameters
        # 1. rtcm3 message types. We have standard 1002, 1006, 1013, 1019 by default
        # 2. base position in llh. By default we don't pass any values, however it is best to use this feature
        # 3. gps cmd file will take care of msg frequency and msg types
        # To pass parameters to this function use string lists, like ["1002", "1006"] or ["60", "30", "100"]

        print(self.bin_path)

        if not self.started:
            if rtcm3_messages is None:
                rtcm3_messages = self.rtcm3_messages

            if base_position is None:
                base_position = self.base_position

            if gps_cmd_file is None:
                gps_cmd_file = self.gps_cmd_file

            cmd = "/str2str -in " + self.input_stream + " -out " + self.output_stream + " -msg " + ",".join(rtcm3_messages)

            if "" in base_position:
                base_position = []

            if base_position:
                cmd += " -p " + " ".join(base_position)

            if gps_cmd_file:
                cmd += " -c " + self.gps_cmd_file_path + "/" + gps_cmd_file

            cmd = self.bin_path + cmd
            print("Starting str2str with")
            print(cmd)

            self.child = pexpect.spawn(cmd, cwd = self.bin_path, echo = False)

            a = self.child.expect(["stream server start", pexpect.EOF, "error"])
            # check if we encountered any errors launching str2str
            if a == 1:
                print("got EOF while waiting for stream start. Shutting down")
                print("This means something went wrong and str2str just stopped")
                print("output before exception: " + str(self.child))
                return -1

            if a == 2:
                print("Could not start str2str. Please check path to binary or parameters, like serial port")
                print("You may also check serial, tcp, ntrip ports for availability")
                return -2

            # if we are here, everything is good
            self.started = True
            return 1

        # str2str already started
        return 2

    def stop(self):
        # terminate the stream

        if self.started:
            self.child.kill(signal.SIGUSR2)
            try:
                self.child.wait()
            except pexpect.ExceptionPexpect:
                print("Str2str already down")

            self.started = False
            return 1

        # str2str already stopped
        return 2


