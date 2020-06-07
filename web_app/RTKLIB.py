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

from RtkController import RtkController
from ConfigManager import ConfigManager
from Str2StrController import Str2StrController
from LogManager import LogManager
#from ReachLED import ReachLED
from reach_tools import reach_tools, gps_time

import json
import time
import os
import signal
import zipfile

from subprocess import check_output, Popen, PIPE
from threading import Semaphore, Thread

# master class for working with all RTKLIB programmes
# prevents them from stacking up and handles errors
# also handles all data broadcast through websockets

class RTKLIB:

    # we will save RTKLIB state here for later loading
    state_file = os.path.join(os.path.expanduser("~"), ".reach/rtk_state")
    # if the state file is not available, these settings are loaded
    default_state = {
        "started": "no",
        "state": "base"
    }

    def __init__(self, socketio, rtklib_path = None, config_path=None, enable_led = True, log_path = None):

        print("RTKLIB 1")
        print(rtklib_path)
        print(log_path)

        if rtklib_path is None:
            rtklib_path = os.path.join(os.path.expanduser("~"), "RTKLIB")
        
        if config_path is None:
            self.config_path = os.path.join(os.path.dirname(__file__), "rtklib_configs")
        else:
            self.config_path = config_path

        if log_path is None:
            #TODO find a better default location
            self.log_path = "../data"
        else:
            self.log_path = log_path

        # This value should stay below the timeout value or the Satellite/Coordinate broadcast
        # thread will stop
        self.sleep_count = 0
        
        # default state for RTKLIB is "rover single"
        self.state = "base"

        # we need this to broadcast stuff
        self.socketio = socketio

        # these are necessary to handle rover mode
        self.rtkc = RtkController(rtklib_path, self.config_path)
        self.conm = ConfigManager(rtklib_path, self.config_path)

        # this one handles base settings
        self.s2sc = Str2StrController(rtklib_path)

        # take care of serving logs
        self.logm = LogManager(rtklib_path, self.log_path)

        # basic synchronisation to prevent errors
        self.semaphore = Semaphore()

        # we need this to send led signals
#        self.enable_led = enable_led

#        if self.enable_led:
#            self.led = ReachLED()

        # broadcast satellite levels and status with these
        self.server_not_interrupted = True
        self.satellite_thread = None
        self.coordinate_thread = None
        self.conversion_thread = None

        self.system_time_correct = False
#        self.system_time_correct = True

        self.time_thread = Thread(target = self.setCorrectTime)
        self.time_thread.start()

        # we try to restore previous state
        # in case we can't, we start as rover in single mode
        # self.loadState()

    def setCorrectTime(self):
        # determine if we have ntp service ready or we need gps time

        print("RTKLIB 2 GPS time sync")

##        if not gps_time.time_synchronised_by_ntp():
            # wait for gps time
##            print("Time is not synced by NTP")
#            self.updateLED("orange,off")
#        gps_time.set_gps_time("/dev/ttyACM0", 115200)

        print("Time is synced by GPS!")

        self.system_time_correct = True
        self.socketio.emit("system time corrected", {}, namespace="/test")

        self.loadState()
        self.socketio.emit("system state reloaded", {}, namespace="/test")

    
    
    def launchBase(self):
        # due to the way str2str works, we can't really separate launch and start
        # all the configuration goes to startBase() function
        # this launchBase() function exists to change the state of RTKLIB instance
        # and to make the process for base and rover modes similar

        self.semaphore.acquire()

        self.state = "base"

        #self.saveState()

#        if self.enable_led:
#            self.updateLED()

        print("RTKLIB 7 Base mode launched")


        self.semaphore.release()

    def shutdownBase(self):
        # due to the way str2str works, we can't really separate launch and start
        # all the configuration goes to startBase() function
        # this shutdownBase() function exists to change the state of RTKLIB instance
        # and to make the process for base and rover modes similar

        self.stopBase()

        self.semaphore.acquire()

        self.state = "inactive"

        
        print("RTKLIB 8 Base mode shutdown")

        self.semaphore.release()

    def startBase(self, rtcm3_messages = None, base_position = None, gps_cmd_file = None):

        self.semaphore.acquire()
        """
        print("RTKLIB 9 Attempting to start str2str...")

        
        res = self.s2sc.start(rtcm3_messages, base_position, gps_cmd_file)
        if res < 0:
            print("str2str start failed")
        elif res == 1:
            print("str2str start successful")
        elif res == 2:
            print("str2str already started")
        
        self.saveState()
        """
        #TODO need refactoring
        #maybe a new method to launch/start rtkrcv outside
        #startBase and startRover
        #TODO launchRover and startRover send a config_name to rtkc
        #I don't do this here :-/
        print("RTKLIB 9a Attempting to launch rtkrcv...")

        res2 = self.rtkc.launch()
        
        if res2 < 0:
            print("rtkrcv launch failed")
        elif res2 == 1:
            print("rtkrcv launch successful")
        elif res2 == 2:
            print("rtkrcv already launched")
        
        #TODO need refactoring
        #maybe a new method to launch/start rtkrcv outside
        #startBase and startRover
        print("RTKLIB 9b Attempting to start rtkrcv...")
        res3 = self.rtkc.start()

        if res3 == -1:
            print("rtkrcv start failed")
        elif res3 == 1:
            print("rtkrcv start successful")
            print("Starting coordinate and satellite broadcast")
        elif res3 == 2:
            print("rtkrcv already started")

        # start fresh data broadcast
        #TODO the satellite and coordinate broadcast start
        #when rtkrcv start failed

        self.server_not_interrupted = True

        if self.satellite_thread is None:
            self.satellite_thread = Thread(target = self.broadcastSatellites)
            self.satellite_thread.start()

        if self.coordinate_thread is None:
            self.coordinate_thread = Thread(target = self.broadcastCoordinates)
            self.coordinate_thread.start()

        self.semaphore.release()

        return res3

    def stopBase(self):

        self.semaphore.acquire()
        

        print("RTKLIB 10a Attempting to stop rtkrcv...")

        res2 = self.rtkc.stop()
        if res2 == -1:
            print("rtkrcv stop failed")
        elif res2 == 1:
            print("rtkrcv stop successful")
        elif res2 == 2:
            print("rtkrcv already stopped")

        print("RTKLIB 10b Attempting to stop satellite broadcasting...")

        self.server_not_interrupted = False

        if self.satellite_thread is not None:
            self.satellite_thread.join()
            self.satellite_thread = None

        if self.coordinate_thread is not None:
            self.coordinate_thread.join()
            self.coordinate_thread = None

        print("RTKLIB 10c Attempting rtkrcv shutdown")

        res = self.rtkc.shutdown()

        if res < 0:
            print("rtkrcv shutdown failed")
        elif res == 1:
            print("rtkrcv shutdown successful")
            self.state = "inactive"
        elif res == 2:
            print("rtkrcv already shutdown")
            self.state = "inactive"
        self.semaphore.release()

        return res

    def readConfigBase(self):

        self.semaphore.acquire()

        print("RTKLIB 11 Got signal to read base config")

        self.socketio.emit("current config base", self.s2sc.readConfig(), namespace = "/test")

        self.semaphore.release()

    def writeConfigBase(self, config):

        self.semaphore.acquire()

        print("RTKLIB 12 Got signal to write base config")

        self.s2sc.writeConfig(config)

        print("Restarting str2str...")

        res = self.s2sc.stop() + self.s2sc.start()

        if res > 1:
            print("Restart successful")
        else:
            print("Restart failed")

        self.saveState()

#        if self.enable_led:
#            self.updateLED()

        self.semaphore.release()

        return res

    def shutdown(self):
        # shutdown whatever mode we are in. stop broadcast threads

        print("RTKLIB 17 Shutting down")

        # clean up broadcast and blink threads
        self.server_not_interrupted = False
#        self.led.blinker_not_interrupted = False

        if self.coordinate_thread is not None:
            self.coordinate_thread.join()

        if self.satellite_thread is not None:
            self.satellite_thread.join()

#        if self.led.blinker_thread is not None:
#            self.led.blinker_thread.join()

        # shutdown base

        elif self.state == "base":
            return self.shutdownBase()

        # otherwise, we are inactive
        return 1

    def deleteConfig(self, config_name):
        # pass deleteConfig to conm

        print("RTKLIB 18 Got signal to delete config " + config_name)

        self.conm.deleteConfig(config_name)

        self.conm.updateAvailableConfigs()

        # send available configs to the browser
        self.socketio.emit("available configs", {"available_configs": self.conm.available_configs}, namespace="/test")

        print(self.conm.available_configs)

    def cancelLogConversion(self, raw_log_path):
        if self.logm.log_being_converted:
            print("Canceling log conversion for " + raw_log_path)

            self.logm.convbin.child.kill(signal.SIGINT)

            self.conversion_thread.join()
            self.logm.convbin.child.close(force = True)

            print("Thread killed")
            self.logm.cleanLogFiles(raw_log_path)
            self.logm.log_being_converted = ""

            print("Canceled msg sent")

    def processLogPackage(self, raw_log_path):

        currently_converting = False

        try:
            print("conversion thread is alive " + str(self.conversion_thread.isAlive()))
            currently_converting = self.conversion_thread.isAlive()
        except AttributeError:
            pass

        log_filename = os.path.basename(raw_log_path)
        potential_zip_path = os.path.splitext(raw_log_path)[0] + ".zip"

        can_send_file = True

        # can't send if there is no converted package and we are busy
        if (not os.path.isfile(potential_zip_path)) and (currently_converting):
            can_send_file = False

        if can_send_file:
            print("Starting a new bg conversion thread for log " + raw_log_path)
            self.logm.log_being_converted = raw_log_path
            self.conversion_thread = Thread(target = self.getRINEXPackage, args = (raw_log_path, ))
            self.conversion_thread.start()
        else:
            error_msg = {
                "name": os.path.basename(raw_log_path),
                "conversion_status": "A log is being converted at the moment. Please wait",
                "messages_parsed": ""
            }
            self.socketio.emit("log conversion failed", error_msg, namespace="/test")

    def conversionIsRequired(self, raw_log_path):
        log_filename = os.path.basename(raw_log_path)
        potential_zip_path = os.path.splitext(raw_log_path)[0] + ".zip"

        print("Comparing " + raw_log_path + " and " + potential_zip_path  + " for conversion")

        if os.path.isfile(potential_zip_path):
            print("Raw logs differ " + str(self.rawLogsDiffer(raw_log_path, potential_zip_path)))
            return self.rawLogsDiffer(raw_log_path, potential_zip_path)
        else:
            print("No zip file!!! Conversion required")
            return True

    def rawLogsDiffer(self, raw_log_path, zip_package_path):
        # check if the raw log is the same size in the zip and in filesystem
        log_name = os.path.basename(raw_log_path)
        raw_log_size = os.path.getsize(raw_log_path)

        zip_package = zipfile.ZipFile(zip_package_path)
        raw_file_inside_info = zip_package.getinfo("Raw/" + log_name)
        raw_file_inside_size = raw_file_inside_info.file_size

        print("Sizes:")
        print("Inside: " + str(raw_file_inside_size))
        print("Raw:    " + str(raw_log_size))

        if raw_log_size == raw_file_inside_size:
            return False
        else:
            return True

    def getRINEXPackage(self, raw_log_path):
        # if this is a solution log, return the file right away
        if "sol" in raw_log_path:
            log_url_tail = "/logs/download/" + os.path.basename(raw_log_path)
            self.socketio.emit("log download path", {"log_url_tail": log_url_tail}, namespace="/test")
            return raw_log_path

        # return RINEX package if it already exists
        # create one if not
        log_filename = os.path.basename(raw_log_path)
        potential_zip_path = os.path.splitext(raw_log_path)[0] + ".zip"
        result_path = ""

        if self.conversionIsRequired(raw_log_path):
            print("Conversion is Required!")
            result_path = self.createRINEXPackage(raw_log_path)
            # handle canceled conversion
            if result_path is None:
                log_url_tail = "/logs/download/" + os.path.basename(raw_log_path)
                self.socketio.emit("log download path", {"log_url_tail": log_url_tail}, namespace="/test")
                return None
        else:
            result_path = potential_zip_path
            print("Conversion is not Required!")
            already_converted_package = {
                "name": log_filename,
                "conversion_status": "Log already converted. Details inside the package",
                "messages_parsed": ""
            }
            self.socketio.emit("log conversion results", already_converted_package, namespace="/test")

        log_url_tail = "/logs/download/" + os.path.basename(result_path)
        self.socketio.emit("log download path", {"log_url_tail": log_url_tail}, namespace="/test")

        self.cleanBusyMessages()
        self.logm.log_being_converted = ""

        return result_path

    def cleanBusyMessages(self):
        # if user tried to convert other logs during conversion, he got an error message
        # this function clears them to show it's ok to convert again
        self.socketio.emit("clean busy messages", {}, namespace="/test")

    def createRINEXPackage(self, raw_log_path):
        # create a RINEX package before download
        # in case we fail to convert, return the raw log path back
        result = raw_log_path
        log_filename = os.path.basename(raw_log_path)

        conversion_time_string = self.logm.calculateConversionTime(raw_log_path)

        start_package = {
            "name": log_filename,
            "conversion_time": conversion_time_string
        }

        conversion_result_package = {
            "name": log_filename,
            "conversion_status": "",
            "messages_parsed": "",
            "log_url_tail": ""
        }

        self.socketio.emit("log conversion start", start_package, namespace="/test")
        try:
            log = self.logm.convbin.convertRTKLIBLogToRINEX(raw_log_path, self.logm.getRINEXVersion())
        except (ValueError, IndexError):
            print("Conversion canceled")
            conversion_result_package["conversion_status"] = "Conversion canceled, downloading raw log"
            self.socketio.emit("log conversion results", conversion_result_package, namespace="/test")
            return None

        print("Log conversion done!")

        if log is not None:
            result = log.createLogPackage()
            if log.isValid():
                conversion_result_package["conversion_status"] = "Log converted to RINEX"
                conversion_result_package["messages_parsed"] = log.log_metadata.formValidMessagesString()
            else:
                conversion_result_package["conversion_status"] = "Conversion successful, but log does not contain any useful data. Downloading raw log"
        else:
            print("Could not convert log. Is the extension wrong?")
            conversion_result_package["conversion_status"] = "Log conversion failed. Downloading raw log"

        self.socketio.emit("log conversion results", conversion_result_package, namespace="/test")

        print("Log conversion results:")
        print(str(log))

        return result

    def saveState(self):
        # save current state for future resurrection:
        # state is a list of parameters:
        # rover state example: ["rover", "started", "reach_single_default.conf"]
        # base state example: ["base", "stopped", "input_stream", "output_stream"]

        state = {}

        # save "rover", "base" or "inactive" state
        state["state"] = self.state

        if self.state == "rover":
            started = self.rtkc.started
        elif self.state == "base":
            started = self.s2sc.started
        elif self.state == "inactive":
            started = False

        state["started"] = "yes" if started else "no"

        # dump rover state
        state["rover"] = {"current_config": self.rtkc.current_config}

        # dump rover state
        state["base"] = {
            "input_stream": self.s2sc.input_stream,
            "output_stream": self.s2sc.output_stream,
            "rtcm3_messages": self.s2sc.rtcm3_messages,
            "base_position": self.s2sc.base_position,
            "gps_cmd_file": self.s2sc.gps_cmd_file
        }

        print("RTKLIB 20 DEBUG saving state")
        print(str(state))

        with open(self.state_file, "w") as f:
            json.dump(state, f, sort_keys = True, indent = 4)

        reach_tools.run_command_safely(["sync"])

        return state

    def byteify(self, input):
        # thanks to Mark Amery from StackOverflow for this awesome function
        if isinstance(input, dict):
            return {self.byteify(key): self.byteify(value) for key, value in input.items()}
        elif isinstance(input, list):
            return [self.byteify(element) for element in input]
        elif isinstance(input, str):
            #no need to convert to utf-8 anymore with Python v3.x
            #return input.encode('utf-8')
            return input
        else:
            return input

    def getState(self):
        # get the state, currently saved in the state file
        print("RTKLIB 21 Trying to read previously saved state...")

        try:
            f = open(self.state_file, "r")
        except IOError:
            # can't find the file, let's create a new one with default state
            print("Could not find existing state, Launching default mode...")

            return self.default_state
        else:

            print("Found existing state...trying to decode...")

            try:
                json_state = json.load(f)
            except ValueError:
                # could not properly decode current state
                print("Could not decode json state. Launching default mode...")
                f.close()

                return self.default_state
            else:
                print("Decoding succesful")

                f.close()

                # convert unicode strings to normal
                json_state = self.byteify(json_state)

                print("That's what we found:")
                print(str(json_state))

                return json_state

    def loadState(self):

        # get current state
        json_state = self.getState()

        print("RTKLIB 22 Now loading the state printed above... ")
        #print(str(json_state))
        # first, we restore the base state, because no matter what we end up doing,
        # we need to restore base state

        if json_state["state"] == "base":
            self.launchBase()

            if json_state["started"] == "yes":
                self.startBase()

        print(str(json_state["state"]) + " state loaded")

    def sendState(self):
        # send current state to every connecting browser

        state = self.getState()
        print("RTKLIB 22a")
        #print(str(state))
        self.conm.updateAvailableConfigs()
        state["available_configs"] = self.conm.available_configs

        state["system_time_correct"] = self.system_time_correct
        state["log_path"] = str(self.log_path)

        print("Available configs to send: ")
        print(str(state["available_configs"]))

        print("Full state: ")
        for key in state:
            print("{} : {}".format(key, state[key]))

        self.socketio.emit("current state", state, namespace = "/test")


    # this function reads satellite levels from an existing rtkrcv instance
    # and emits them to the connected browser as messages
    def broadcastSatellites(self):
        count = 0

        while self.server_not_interrupted:

            # update satellite levels
            self.rtkc.getObs()

#            if count % 10 == 0:
            #print("Sending sat rover levels:\n" + str(self.rtkc.obs_rover))
            #print("Sending sat base levels:\n" + str(self.rtkc.obs_base))

            self.socketio.emit("satellite broadcast rover", self.rtkc.obs_rover, namespace = "/test")
            #self.socketio.emit("satellite broadcast base", self.rtkc.obs_base, namespace = "/test")
            count += 1
            self.sleep_count +=1
            time.sleep(1)
        #print("exiting satellite broadcast")

    # this function reads current rtklib status, coordinates and obs count
    def broadcastCoordinates(self):
        count = 0

        while self.server_not_interrupted:

            # update RTKLIB status
            self.rtkc.getStatus()

#            if count % 10 == 0:
#                print("Sending RTKLIB status select information:")
#                print(self.rtkc.status)

            self.socketio.emit("coordinate broadcast", self.rtkc.status, namespace = "/test")

#            if self.enable_led:
#                self.updateLED()

            count += 1
            time.sleep(1)
        #print("exiting coordinate broadcast")
