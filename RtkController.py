import pexpect
from threading import Semaphore
import time

# This module automates working with RTKRCV directly
# You can get sat levels, current status, start and restart the software

class RtkController:

    def __init__(self, path_to_rtkrcv = "/home/reach/RTKLIB/app/rtkrcv/gcc"):
        self.bin_path = path_to_rtkrcv
        self.child = 0
        self.status = {}
        self.obs = {}
        self.info = {}
        self.semaphore = Semaphore()

        self.started = False
        self.launched = False

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

    def launch(self, config_name = "reach_rover_default.conf"):
        # run an rtkrcv instance with the specified config:
        # if there is a slash in the name we consider it a full location
        # otherwise, it's supposed to be in the upper directory(rtkrcv inside app)

        if not self.launched:

            self.semaphore.acquire()

            if "/" in config_name:
                spawn_command = self.bin_path + "/rtkrcv -o " + config_name
            else:
                spawn_command = self.bin_path + "/rtkrcv -o " + self.bin_path[0:-3] + config_name

            self.child = pexpect.spawn(spawn_command, cwd = self.bin_path, echo = False)

            print('Launching rtklib with: "' + spawn_command + '"')

            if self.expectAnswer("spawn") < 0:
                self.semaphore.release()
                return -1

            self.semaphore.release()
            self.launched = True

            return 1

        # already launched
        return 2

    def shutdown(self):

        if self.launched:
            self.semaphore.acquire()

            self.child.send("shutdown\r\n")

            a = self.child.expect([":", pexpect.EOF, "error"])
            print("Stop expects: " + str(a))

            if a > 0:
                print("Stop error")
                r = -1
            else:
                self.child.send("y\r\n")
                r = 1

            # wait for rtkrcv to shutdown
            self.child.wait()
            print("Process is alive " + str(self.child.isalive()))
            print("Process is alive " + str(self.child.isalive()))
            print("Process is alive " + str(self.child.isalive()))
            print("Process is alive " + str(self.child.isalive()))
            print("Process is alive " + str(self.child.isalive()))
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

            return 1
        else:
            # if we are not started yet, just start

            return self.start()

    def loadConfig(self, config_name = "rtk.conf"):

        self.semaphore.acquire()

        self.child.send("load " + config_name + "\r\n")

        if self.expectAnswer("load config") < 0:
            self.semaphore.release()
            return -1

        self.semaphore.release()

        if self.restart() < 0:
            self.semaphore.release()
            return -1

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

                if "# of input data rover" in self.status:

                    start_rover = self.status["# of input data rover"].find("(")
                    end_rover = self.status["# of input data rover"].find(")")
                    start_base = self.status["# of input data base"].find("(")
                    end_base = self.status["# of input data base"].find(")")

                    self.info["obs_rover"] = self.status["# of input data rover"][start_rover+1:end_rover]
                    self.info["obs_base"] = self.status["# of input data base"][start_base+1:end_base]

                if "solution status" in self.status:
                    self.info["solution_status"] = self.status["solution status"]

                if "positioning mode" in self.status:
                    self.info["positioning_mode"] = self.status["positioning mode"]

                if "pos llh single (deg,m) rover" in self.status:
                    llh = self.status["pos llh single (deg,m) rover"].split(",")
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

            # find the indexes of the needed columns
            if "S1" in header:
                sat_name_index = header.index("SAT")
                sat_level_index = header.index("S1")

                if len(obs) > (header_index + 1):
                    # we have some info about the actual satellites:

                    self.obs = {}

                    for line in obs[header_index+1:]:
                        spl = line.split()

                        if len(spl) > sat_level_index:
                            name = spl[sat_name_index]
                            level = spl[sat_level_index]

                            self.obs[name] = level
                            # print("print from getObs:\n" + str(self.obs))

    #                print("Useful info extracted from status: ")
    #                print(self.info)

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
