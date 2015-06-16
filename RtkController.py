import pexpect
import time

class RtkController:

    def __init__(self, path_to_rtkrcv = "/home/root/RTKLIB/app/rtkrcv/gcc"):
        self.bin_path = path_to_rtkrcv
        self.child = 0
        self.status = {}
        self.obs = {}
        self.updated = False

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

    def start(self, config_name = "rtk.conf"):
        # run an rtkrcv instance with the specified config:
        # if there is a slash in the name we consider it a full location
        # otherwise, it's supposed to be in the upper directory(rtkrcv inside app)

        if "/" in config_name:
            spawn_command = self.bin_path + "/rtkrcv -o " + config_name
        else:
            spawn_command = self.bin_path + "/rtkrcv -o " + self.bin_path[0:-3] + config_name

        self.child = pexpect.spawn(spawn_command, cwd = self.bin_path, echo = False)
        print("Spawning command" + spawn_command)

        if self.expectAnswer("spawn") < 0:
            return -1

        print("launched rtklib")
        self.child.send("start\r\n")

        if self.expectAnswer("start") < 0:
            return -1

        # started without rtklib catching  errors
        print("RTKLIB launch and start succesful")

        return 1

    def restart(self):
	print("Sending restart command")
        self.child.send("restart\r\n")

        if self.expectAnswer("restart") < 0:
            return -1

        print("RTKLIB restart successful")
        print(self.child.before)

        return 1

    def loadConfig(self, config_name = "rtk.conf"):
        self.child.send("load " + config_name + "\r\n")

        if self.expectAnswer("load config"):
            return -1

        if self.restart() < 0:
            return -1

        return 1

    def stop(self):
        self.child.send("shutdown\r\n")

        a = self.child.expect([":", pexpect.EOF, "error"])
        print("first expect from stop")
        print("Stop expects: " + str(a))

        if a > 0:
            print("Stop error")
            r = -1
        else:
            self.child.send("y\r\n")
            r = 1

        if self.expectAnswer("shutdown yes") < 0:
            r = -1

        return r


    def getStatus(self):
        self.child.send("status\r\n")

        if self.expectAnswer("get status") < 0:
            return -1

        # time to extract information from the status form

        status = self.child.before.split("\r\n")

        if status != {}:
            for line in status:
                spl = line.split(":")

                if len(spl) > 1:
                    # get rid of extra whitespace

                    param = spl[0].strip()
                    value = spl[1].strip()

                    self.status[param] = value

                    # print("Gotten status:\n" + str(self.status))

            print("Current status:\n" + str(self.status))
            self.info = {}

            start_rover = self.status["# of input data rover"].find("(")
            end_rover = self.status["# of input data rover"].find(")")
            start_base = self.status["# of input data base"].find("(")
            end_base = self.status["# of input data base"].find(")")

            self.info["obs_rover"] = self.status["# of input data rover"][start_rover+1:end_rover]
            self.info["obs_base"] = self.status["# of input data base"][start_base+1:end_base]

            self.info["solution_status"] = self.status["solution status"]
            self.info["positioning_mode"] = self.status["positioning mode"]
            self.info["rover_llh"] = self.status["pos llh single (deg,m) rover"]

        return 1

    def getObs(self):
        self.child.send("obs\r\n")

        if self.expectAnswer("get obs") < 0:
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
