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
import time
import signal
import pexpect
from threading import Semaphore, Thread

# This module automates working with RTKRCV directly
# You can get sat levels, current status, start and restart the software

class RtkController:

    def __init__(self, rtklib_path, config_path):

        self.bin_path = rtklib_path
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
            config_name = "rtkbase_single_default.conf"

        if not self.launched:

            self.semaphore.acquire()

            if "/" in config_name:
                spawn_command = self.bin_path + "/rtkrcv -o " + config_name
            else:
                spawn_command = self.bin_path + "/rtkrcv -o " + os.path.join(self.config_path, config_name)

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

            self.child.kill(signal.SIGUSR2)

            # wait for rtkrcv to shutdown
            try:
                self.child.wait()
            except pexpect.ExceptionPexpect:
                print("Already dead!!")

            if self.child.isalive():
                r = -1
            else:
                r = 1

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

            self.restart()
            print("Restart")
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

        status = self.child.before.decode().split("\r\n")

        if status != {}:
            for line in status:
                spl = line.split(":", 1)

                if len(spl) > 1:

                    param = spl[0].strip()
                    value = spl[1].strip()

                    self.status[param] = value

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

        obs = self.child.before.decode().split("\r\n")
        obs = [_f for _f in obs if _f]

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

                else:
                    self.obs_base = {}
                    self.obs_rover = {}

        self.semaphore.release()

        return 1






