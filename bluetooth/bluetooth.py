import time
import pexpect
import subprocess
import sys

class BluetoothError(Exception):
    """This exception is raised, when bluetoothctl fails to start."""
    pass

class Bluetooth:

    def __init__(self):
        out = subprocess.check_output("rfkill unblock bluetooth", shell = True)
        self.child = None

    def initialize(self):
        """Starts a bluetoothctl process. Raise BluetoothError on failure."""
        self.child = pexpect.spawn("bluetoothctl", echo = False)
        # self.child.logfile = sys.stdout

    def get_output(self, command):
        """Run a command in bluetoothctl prompt, return output as a list of lines."""
        self.child.send(command + "\n")
        start_failed = self.child.expect(["bluetooth", pexpect.EOF])

        if start_failed:
            raise BluetoothError("Bluetoothctl failed after running " + command)

        return self.child.before.split("\r\n")

    def start_scan(self):
        try:
            out = self.get_output("scan on")
        except BluetoothError, e:
            print(e)
            return None

    def get_available_devices(self):
        try:
            out = self.get_output("devices")
        except BluetoothError, e:
            print(e)
            return None
        else:
            available_devices = []
            for line in out:
                if line.startswith("Device"):
                    attribute_list = line.split()
                    mac_address = attribute_list[1]
                    name = attribute_list[2]
                    available_devices.append((mac_address, name))

            return available_devices

    def pair(self, mac_address):
        try:
            out = self.get_output("pair " + mac_address)
        except BluetoothError, e:
            print(e)
            return None


def pretty_print(list_to_print):
    print("\nstart")
    for line in list_to_print:
        print([line])
    print("stop")

if __name__ == "__main__":

    print("Init bluetooth...")
    bl = Bluetooth()
    print("Ready!")
    try:
        bl.initialize()
    except BluetoothError, e:
        print(e)
    else:
        print("Successful init!")
        pretty_print(bl.get_output("devices"))
        print("WTF")
        pretty_print(bl.get_output("help"))
        pretty_print(bl.get_output("scan on"))
        time.sleep(5)
        print(bl.get_available_devices())

