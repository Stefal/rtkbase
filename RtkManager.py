import pexpect
import time

class RtkManager:

    def __init__(self, path_to_rtkrcv = "/home/root/RTKLIB/app/rtkrcv/gcc"):
        self.bin_path = path_to_rtkrcv
        self.child = 0
        self.status = {}
        self.obs = {}

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
            self.child = pexpect.spawn("./rtkrcv -o " + config_name, cwd = self.bin_path, echo = False)
        else:
            self.child = pexpect.spawn("./rtkrcv -o ../" + config_name, cwd = self.bin_path, echo = True)

        if self.expectAnswer("start") < 0:
            return -1

        print("launched rtklib")
        self.child.send("start\r\n")

        if self.expectAnswer("start") < 0:
            return -1

        # started without rtklib catching  errors
        print("RTKLIB launch and started succesful")

        return 1

    def restart(self):
        self.child.send("restart\r\n")

        if self.expectAnswer("restart") < 0:
            return -1

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

    def getStatus(self):
        self.child.send("status\r\n")

        if self.expectAnswer("get status") < 0:
            return -1

        if self.expectAnswer("get status") < 0:
            return -1

        # time to extract information from the status form

        status = self.child.before.split("\r\n")
        print(status)

        for line in status:
            spl = line.split(":")

            if len(spl) > 1:
                key = spl[0].strip()
                value = spl[1].strip()

                self.status[key] = value

                print(key + ":::" + value)

            # get rid of extra whitespace

        return 1

    def getObs(self):
        self.child.send("obs\r\n")

        if self.expectAnswer("get obs") < 0:
            return -1

        if self.expectAnswer("get obs") < 0:
            return -1

        # time to extract information from the obs form

        obs = self.child.before.split("\r\n")

        for line in obs:
            spl = line.split()
            print(spl)

        return 1

rm = RtkManager("/Users/fedorovegor/Documents/RTKLIB/app/rtkrcv/gcc")

if rm.start() > 0:
    rm.restart()

    while(1):
        rm.getStatus()
        rm.getObs()
        time.sleep(1)


