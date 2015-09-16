from RtkController import RtkController
from ConfigManager import ConfigManager
from Str2StrController import Str2StrController
from ReachLED import ReachLED

from threading import Semaphore
import json

# master class for working with all RTKLIB programmes
# prevents them from stacking up and handles errors
# TODO: save current state and it reload it when relaunched

class RTKLIB:

    # we will save RTKLIB state here for later loading
    state_file = "/home/reach/.reach/rtk_state"

    def __init__(self, socketio, path_to_rtkrcv = None, path_to_configs = None, path_to_str2str = None, path_to_gps_cmd_file = None):
        # default state for RTKLIB is "inactive"
        self.state = "inactive"

        # we need this to broadcast stuff
        self.socketio = socketio

        # these are necessary to handle base mode
        self.rtkc = RtkController(socketio, path_to_rtkrcv)
        self.conm = ConfigManager(path_to_configs)

        # this one handles base settings
        self.s2sc = Str2StrController(path_to_str2str, path_to_gps_cmd_file)

        # basic synchronisation to prevent errors
        self.semaphore = Semaphore()

        # we need this to send led signals
        self.led = ReachLED()

        # we try to restore previous state
        self.loadState()

    def launchRover(self, config_name = None):
        # config_name may be a name, or a full path
        # if the parameter contains "/", then we consider it a full path
        # else, we will be looking for it one directory higher than the rtkrcv bin

        self.semaphore.acquire()
        print("Attempting to launch rtkrcv...")

        if config_name == None:
            res = self.rtkc.launch()
        else:
            res = self.rtkc.launch(config_name)

        if res < 0:
            print("rtkrcv launch failed")
        elif res == 1:
            print("rtkrcv launch successful")
            self.state = "rover"
        elif res == 2:
            print("rtkrcv already launched")

        self.saveState()
        self.updateLED()

        print("Rover mode launched")

        self.semaphore.release()

        return res

    def shutdownRover(self):

        self.stopRover()

        self.semaphore.acquire()
        print("Attempting rtkrcv shutdown")

        res = self.rtkc.shutdown()

        if res < 0:
            print("rtkrcv shutdown failed")
        elif res == 1:
            print("rtkrcv shutdown successful")
            self.state = "inactive"
        elif res == 2:
            print("rtkrcv already shutdown")

        self.saveState()
        self.updateLED()

        print("Rover mode shutdown")

        self.semaphore.release()

        return res

    def startRover(self):

        self.semaphore.acquire()
        print("Attempting to start rtkrcv...")

        res = self.rtkc.start()

        if res == -1:
            print("rtkrcv start failed")
        elif res == 1:
            print("rtkrcv start successful")
            print("Starting coordinate and satellite broadcast")
        elif res == 2:
            print("rtkrcv already started")

        self.saveState()
        self.updateLED()
        self.semaphore.release()

        return res

    def stopRover(self):

        self.semaphore.acquire()
        print("Attempting to stop RTKLIB...")

        res = self.rtkc.stop()

        if res == -1:
            print("rtkrcv stop failed")
        elif res == 1:
            print("rtkrcv stop successful")
        elif res == 2:
            print("rtkrcv already stopped")

        self.saveState()
        self.updateLED()

        self.semaphore.release()

        return res

    def launchBase(self):
        # due to the way str2str works, we can't really separate launch and start
        # all the configuration goes to startBase() function
        # this launchBase() function exists to change the state of RTKLIB instance
        # and to make the process for base and rover modes similar

        self.semaphore.acquire()

        self.state = "base"

        self.saveState()
        self.updateLED()

        print("Base mode launched")

        self.semaphore.release()

    def shutdownBase(self):
        # due to the way str2str works, we can't really separate launch and start
        # all the configuration goes to startBase() function
        # this shutdownBase() function exists to change the state of RTKLIB instance
        # and to make the process for base and rover modes similar

        self.stopBase()

        self.semaphore.acquire()

        self.state = "inactive"

        self.saveState()
        self.updateLED()

        print("Base mode shutdown")

        self.semaphore.release()

    def startBase(self, rtcm3_messages = None, base_position = None, gps_cmd_file = None):

        self.semaphore.acquire()

        print("Attempting to start str2str...")

        if not self.rtkc.started:
            res = self.s2sc.start(rtcm3_messages, base_position, gps_cmd_file)

            if res < 0:
                print("str2str start failed")
            elif res == 1:
                print("str2str start successful")
            elif res == 2:
                print("str2str already started")
        else:
            print("Can't start str2str with rtkrcv still running!!!!")

        self.saveState()
        self.updateLED()
        self.semaphore.release()

        return res

    def stopBase(self):

        self.semaphore.acquire()

        print("Attempting to stop str2str...")

        res = self.s2sc.stop()

        if res == -1:
            print("str2str stop failed")
        elif res == 1:
            print("str2str stop successful")
        elif res == 2:
            print("str2str already stopped")

        self.saveState()
        self.updateLED()
        self.semaphore.release()

        return res

    def readConfigBase(self):

        self.semaphore.acquire()

        print("Got signal to read current base config")

        self.socketio.emit("current config base", self.s2sc.readConfig(), namespace = "/test")

        self.semaphore.release()

    def writeConfigBase(self, config):

        self.semaphore.acquire()

        print("Got signal to write current base config")

        self.s2sc.writeConfig(config)

        print("Restarting str2str...")

        res = self.s2sc.stop() + self.s2sc.start()

        if res > 1:
            print("Restart successful")
        else:
            print("Restart failed")

        self.saveState()

        self.semaphore.release()

        return res

    def writeConfigRover(self, config):
        # config dict must include config_name field

        self.semaphore.acquire()
        print("Got signal to write current rover config")

        if "config_file_name" not in config:
            config_file = None
        else:
            config_file = config["config_file_name"]

        self.conm.writeConfig(config_file, config)

        print("Reloading with new config...")

        res = self.rtkc.loadConfig(self.rtkc.current_config) + self.rtkc.restart()

        if res == 2:
            print("Restart successful")
        elif res == 1:
            print("rtkrcv started instead of restart")
        elif res == -1:
            print("rtkrcv restart failed")

        self.saveState()

        self.semaphore.release()

        return res

    def readConfigRover(self, config):

        self.semaphore.acquire()

        if "config_file_name" not in config:
            config_file = None
        else:
            config_file = config["config_file_name"]

        print("Got signal to read the current rover config")

        self.conm.readConfig(config_file)

        # after this, to preserve the order of the options in the frontend we send a special order message
        print("Sending rover config order")

        options_order = {}

        # create a structure the corresponds to the options order
        for index, value in enumerate(self.conm.buff_dict_order):
            options_order[str(index)] = value

        # send the options order
        self.socketio.emit("current config rover order", options_order, namespace="/test")

        # send the options comments
        print("Sending rover config comments")
        self.socketio.emit("current config rover comments", self.conm.buff_dict_comments, namespace="/test")

        # now we send the whole config with values
        print("Sending rover config values")
        self.socketio.emit("current config rover", self.conm.buff_dict, namespace="/test")

        self.semaphore.release()

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


        with open(self.state_file, "w") as f:
            json_state = json.dump(state, f, sort_keys = True, indent = 4)

    def byteify(self, input):
        # thanks to Mark Amery from StackOverFlow for this awesome function
        if isinstance(input, dict):
            return {self.byteify(key): self.byteify(value) for key, value in input.iteritems()}
        elif isinstance(input, list):
            return [self.byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input

    def loadState(self):
        # load previously saved state
        # we assume this function is not to be run until the very end of __init__ of RTKLIB

        try:
            f = open(self.state_file, "r")
        except IOError:
            # can't find the file, let's create a new one with default state
            self.saveState()
        else:

            json_state = json.load(f)
            f.close()

            # convert unicode strings to normal
            json_state = self.byteify(json_state)

            # first, we restore the base state, because no matter what we end up doing,
            # we need to restore base state

            self.s2sc.input_stream = json_state["base"]["input_stream"]
            self.s2sc.output_stream = json_state["base"]["output_stream"]
            self.s2sc.rtcm3_messages = json_state["base"]["rtcm3_messages"]
            self.s2sc.base_position = json_state["base"]["base_position"]
            self.s2sc.gps_cmd_file = json_state["base"]["gps_cmd_file"]

            if json_state["state"] == "rover":
                saved_config = json_state["rover"]["current_config"]

                if saved_config == "":
                    saved_config = None

                self.launchRover(saved_config)

                if json_state["started"] == "yes":
                    self.startRover()
            elif json_state["state"] == "base":
                self.launchBase()

                if json_state["started"] == "yes":
                    self.startBase()

            # if we are "inactive", don't do anything as this the default state

    def updateLED(self):

        blink_pattern = ""
        delay = 0.5

        if self.state == "base":
            if self.s2sc.started:
                # we have a started base
                blink_pattern = "green,off,magenta,off"
            else:
                # we have a stopped base
                blink_pattern = "red,off,magenta,off"
        elif self.state == "rover":
            if self.rtkc.started:
                # we have a started rover
                status_pattern_dict = {
                    "fix": "blue,off,green,off",
                    "float": "blue,off,green,off,yellow,off",
                    "single": "blue,off,yellow,off"
                }

                # we need to acquire RtkController in case it's currently updating info dict
                self.rtkc.semaphore.acquire()
                current_rover_solutuon_status = self.rtkc.info.get("solution_status", "")
                self.rtkc.semaphore.release()

                blink_pattern = status_pattern_dict.get(current_rover_solutuon_status, "blue,off")
            else:
                # we have a stopped rover
                blink_pattern = "blue,off,red,off"

        elif self.state == "inactive":
            blink_pattern = "yellow, off"
            delay = 1

        if blink_pattern:
            # if we decided we need a new pattern, then start blinking it
            self.led.startBlinker(blink_pattern, delay)







































