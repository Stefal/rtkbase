import pexpect

class RtkManager:

    def __init__(self, path_to_rtkrcv):
        self.bin_path = path_to_rtkrcv
        self.child = 0
    
    def start(self, config_name = "rtk.conf"):
        print("./rtkrcv -o ../" + config_name)
        self.child = pexpect.spawn("./rtkrcv -o ../" + config_name, cwd = self.bin_path)
        r = self.child.expect(["rtkrcv> ", pexpect.EOF])
        if r == 0:
            print("good")
        else:
            print("got EOF while waiting for rtkrcv> . Shutting down")
            print("output before exception: " + str(self.child))
            return -1

        print("launched rtklib")
        self.child.send("start\r\n")
        r = self.child.expect(["rtkrcv> ", "error", pexpect.EOF])
        if r == 0:
            print("good")
        else:
            print("r=", r)
            print("got EOF while waiting for rtkrcv> . Shutting down")
            print("output before exception: " + str(self.child))
            return -1

        print("after start")

        if "rtk server start error" in self.child.before:
            print("too bad: something wrong about the config you specified")
            return -1

        self.child.sendline("status\r\n")
        self.child.expect("rtkrcv>")

        print("current status: " + self.child.before)

        return 1

    def restart(self):
        self.child.sendline("restart\r\n")
        self.child.expect("rtkrcv>")

        if self.child.before == "rtk server start error":
            print("too bad: something wrong about the config you specified")
            return -1

        print("output = " + self.child.before)
        return 1

#    def loadConfig(self, config_name):

#    def stop(self):


rm = RtkManager("/Users/fedorovegor/Documents/RTKLIB/app/rtkrcv/gcc")
if rm.start() > 0:
    rm.restart()

