from RtkController import RtkController
from ConfigManager import ConfigManager
from Str2StrController import Str2StrController

from threading import Semaphore

# master class for working with all RTKLIB programmes
# prevents them from stacking up and handles errors
# TODO: save current state and it reload it when relaunched

class RTKLIB:

    def __init__(self, socketio, path_to_rtkrcv = None, path_to_configs = None, path_to_str2str = None, path_to_gps_cmd_file = None):

        # we need this to broadcast stuff
        self.socketio = socketio

        # these are necessary to handle base mode
        self.rtkc = RtkController(socketio, path_to_rtkrcv)
        self.conm = ConfigManager(path_to_configs)

        # this one handles base settings
        self.s2sc = Str2StrController(path_to_str2str, path_to_gps_cmd_file)

        # basic synchronisation to prevent errors
        self.semaphore = Semaphore()

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
        elif res == 2:
            print("rtkrcv already launched")

        self.semaphore.release()

        return res

    def shutdownRover(self):

        self.semaphore.acquire()
        print("Attempting rtkrcv shutdown")

        res = self.rtkc.shutdown()

        if res < 0:
            print("rtkrcv shutdown failed")
        elif res == 1:
            print("rtkrcv shutdown successful")
        elif res == 2:
            print("rtkrcv already shutdown")

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

        self.semaphore.release()

        return res

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

        conm.writeConfig(config["config_file_name"], config)

        print("Reloading with new config...")

        res = self.rtkc.loadConfig("../" + self.conm.default_rover_config) + self.rtkc.restart()

        if res == 2:
            print("Restart successful")
        elif res == 1:
            print("rtkrcv started instead of restart")
        elif res == -1:
            print("rtkrcv restart failed")

        self.semaphore.release()

        return res

    def readConfigRover(self, config_name = None):

        self.semaphore.acquire()

        if config_name is None:
            config_name = self.conm.default_rover_config

        print("Got signal to read the current rover config")

        self.conm.readConfig(config_name)

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
        self.emit("current config rover", self.conm.buff_dict, namespace="/test")

        self.semaphore.release()
































