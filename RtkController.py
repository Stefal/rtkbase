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

import pexpect
from threading import Semaphore, Thread
import time

# This module automates working with RTKRCV directly
# You can get sat levels, current status, start and restart the software

class RtkController:

    def __init__(self, rtkrcv_path = None, config_path = None):

        if rtkrcv_path is None:
            self.bin_path = "/home/reach/RTKLIB/app/rtkrcv/gcc"
        else:
            self.bin_path = rtkrcv_path

        if config_path is None:
            self.config_path = "/home/reach/RTKLIB/app/rtkrcv/"
        else:
            self.config_path = config_path

        self.child = 0
        self.status = {}
        self.obs_rover = {}
        self.obs_base = {}
        self.info = {}
        self.semaphore = Semaphore()

        self.started = False
        self.launched = False
        self.current_config = ""

    def expectAnswer(self, last_command = ""):
        a = self.child.expect(["rtkrcv>", pexpect.EOF, "error"])
        # check rtklib output for any errors
        if a == 1:
            print("got EOF while waiting for rtkrcv> . Shutting down")
            print("This means something went wrong and rtkrcv just stopped")
            print("output before exception: " + str(self.child))
            return -1

        if a == 2:
            print("Could not " + last_command + ". Please check path to binary or config name")
            print("You may also check serial port for availability")
            return -2

        return 1

    def launch(self, config_name = None):
        # run an rtkrcv instance with the specified config:
        # if there is a slash in the name we consider it a full location
        # otherwise, it's supposed to be in the upper directory(rtkrcv inside app)

        if config_name is None:
            config_name = "reach_single_default.conf"

        if not self.launched:

            self.semaphore.acquire()

            if "/" in config_name:
                spawn_command = self.bin_path + "/rtkrcv -o " + config_name
            else:
                spawn_command = self.bin_path + "/rtkrcv -o " + self.config_path + config_name

            self.child = pexpect.spawn(spawn_command, cwd = self.bin_path, echo = False)

            print('Launching rtklib with: "' + spawn_command + '"')

            if self.expectAnswer("spawn") < 0:
                self.semaphore.release()
                return -1

            self.semaphore.release()
            self.launched = True
            self.current_config = config_name

            # launch success
            return 1

        # already launched
        return 2

    def shutdown(self):

        if self.launched:
            self.semaphore.acquire()

            self.child.send("shutdown\r\n")

            a = self.child.expect([":", pexpect.EOF, "error"])

            if a > 0:
                print("Stop error")
                r = -1
            else:
                self.child.send("y\r\n")
                r = 1

            # wait for rtkrcv to shutdown
            self.child.wait()
            if self.child.isalive():
                r = -1

            self.semaphore.release()

            self.launched = False

            return r

        # already shut down
        return 2


    def start(self):

        if not self.started:
            self.semaphore.acquire()

            self.child.send("start\r\n")

            if self.expectAnswer("start") < 0:
                self.semaphore.release()
                return -1

            self.semaphore.release()
            self.started = True

            return 1

        # already started
        return 2

    def stop(self):

        if self.started:
            self.semaphore.acquire()

            self.child.send("stop\r\n")

            if self.expectAnswer("stop") < 0:
                self.semaphore.release()
                return -1

            self.semaphore.release()

            self.started = False

            return 1

        # already stopped
        return 2

    def restart(self):

        if self.started:
            self.semaphore.acquire()

            self.child.send("restart\r\n")

            if self.expectAnswer("restart") < 0:
                self.semaphore.release()
                return -1

            self.semaphore.release()

            return 3
        else:
            # if we are not started yet, just start
            return self.start()

    def loadConfig(self, config_name = "rtk.conf"):

        self.semaphore.acquire()

        if "/" not in config_name:
            # we assume this is not the full path
            # so it must be in the upper dir
            self.child.send("load " + "../" + config_name + "\r\n")
        else:
            self.child.send("load " + config_name + "\r\n")

        if self.expectAnswer("load config") < 0:
            self.semaphore.release()
            return -1

        self.semaphore.release()

        self.current_config = config_name

        return 1

    def getStatus(self):

        self.semaphore.acquire()

        self.child.send("status\r\n")

        if self.expectAnswer("get status") < 0:
            self.semaphore.release()
            return -1

        # time to extract information from the status form

        status = self.child.before.split("\r\n")

        if status != {}:

            # print("Got status!!!:")

            for line in status:
                spl = line.split(":")

                if len(spl) > 1:
                    # get rid of extra whitespace

                    param = spl[0].strip()
                    value = spl[1].strip()

                    self.status[param] = value

                    # print(param + ":::"  + value)

                    # print("Gotten status:\n" + str(self.status))

            if self.status != {}:
                # print("Current status:\n" + str(self.status))
                self.info = {}


                for key in self.status:
                    # we want to parse all the messages received by rover, base or corr
                    # this entry has a form of "# of input data rover"
                    if key.startswith("# of input data"):
                        # first we figure out what is this - rover, base or corr
                        msg_from = key.rsplit(" ", 1)[1]

                        # after split the message information has the form of "obs(100)" or "ion(10)"
                        # split the messages by type
                        input_messages = self.status[key].split(",")

                        # the order for the messages is:
                        # obs(0),nav(0),gnav(0),ion(0),sbs(0),pos(0),dgps(0),ssr(0),err(0)
                        for msg in input_messages:
                            first_bracket_index = msg.find("(")
                            msg_type = msg[:first_bracket_index]
                            msg_amount_received = msg[first_bracket_index + 1:msg.find(")")]
                            # we save them in the form of self.info["obs_rover"] = "10"
                            self.info[msg_type + "_" + msg_from] = msg_amount_received

                    if key.startswith("# of rtcm messages"):
                        # first we figure out what is this - rover, base or corr
                        msg_from = key.rsplit(" ", 1)[1]

                        # after split the message information has the form of "1010(100)" or "1002(10)"
                        # split the messages by type
                        # unlike input data, this one can be empty, thus extra if
                        if self.status[key]:
                            input_messages = self.status[key].split(",")

                            # the order for the messages is:
                            # obs(0),nav(0),gnav(0),ion(0),sbs(0),pos(0),dgps(0),ssr(0),err(0)
                            for msg in input_messages:
                                first_bracket_index = msg.find("(")
                                msg_type = msg[:first_bracket_index]
                                msg_amount_received = msg[first_bracket_index + 1:msg.find(")")]
                                # we save them in the form of self.info["obs_rover"] = "10"
                                self.info["rtcm_" + msg_type + "_" + msg_from] = msg_amount_received

                    if key.startswith("# of satellites"):
                        msg_from = key.rsplit(" ", 1)[1]

                        if self.status[key]:
                            self.info["satellites_" + msg_from] = self.status[key]

                    if key == "# of valid satellites":
                        self.info["satellites_valid"] = self.status[key]


                    if key == "solution status":
                        self.info["solution_status"] = self.status[key]

                    if key == "positioning mode":
                        self.info["positioning_mode"] = self.status[key]

                    if key == "age of differential (s)":
                        self.info["age_of_differential"] = self.status[key]

                    if key == "pos llh single (deg,m) rover":
                        llh = self.status[key].split(",")
                        if len(llh) > 2:
                            lat = llh[0]
                            lon = llh[1]
                            height = llh[2]

                            self.info["lat"] = lat
                            self.info["lon"] = lon
                            self.info["height"] = height

        self.semaphore.release()

        return 1

    def getObs(self):

        self.semaphore.acquire()

        self.obs_rover = {}
        self.obs_base = {}

        self.child.send("obs\r\n")

        if self.expectAnswer("get obs") < 0:
            self.semaphore.release()
            return -1

        # time to extract information from the obs form

        obs = self.child.before.split("\r\n")

        # strip out empty lines
        obs = filter(None, obs)

        # check for the header string
        matching_strings = [s for s in obs if "SAT" in s]

        if matching_strings != []:
            # find the header of the OBS table
            header_index = obs.index(matching_strings[0])

            # split the header string into columns
            header = obs[header_index].split()

            if "S1" in header:
                # find the indexes of the needed columns
                sat_name_index = header.index("SAT")
                sat_level_index = header.index("S1")
                sat_input_source_index = header.index("R")

                if len(obs) > (header_index + 1):
                    # we have some info about the actual satellites:

                    self.obs_rover = {}
                    self.obs_base = {}

                    for line in obs[header_index+1:]:
                        spl = line.split()

                        if len(spl) > sat_level_index:
                            name = spl[sat_name_index]
                            level = spl[sat_level_index]

                            # R parameter corresponds to the input source number
                            if spl[sat_input_source_index] == "1":
                                # we consider 1 to be rover,
                                self.obs_rover[name] = level
                            elif spl[sat_input_source_index] == "2":
                                # 2 to be base
                                self.obs_base[name] = level

                            # print("print from getObs:\n" + str(self.obs))

    #                print("Useful info extracted from status: ")
    #                print(self.info)
                else:
                    self.obs_base = {}
                    self.obs_rover = {}

        self.semaphore.release()

        return 1
### example usage

#import timeit
#print(timeit.timeit("rc.getStatus()", "import RtkController; rc = RtkController.RtkController('/Users/fedorovegor/Documents/RTKLIB/app/rtkrcv/gcc'); rc.start()", number = 100))

#rtk_location = "/Users/fedorovegor/Documents/RTKLIB/app/rtkrcv/gcc"
#rc = RtkController(rtk_location)

# if rc.start() > 0:
#     rc.restart()

#     while(1):
#         rc.getStatus()
#         print("###STATUS###")
#         print(rc.status)
#         rc.getObs()
#         time.sleep(1)
