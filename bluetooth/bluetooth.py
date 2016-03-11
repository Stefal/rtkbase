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
        self.child.logfile = sys.stdout

    def get_output(self, command, pause = 0):
        """Run a command in bluetoothctl prompt, return output as a list of lines."""
        self.child.send(command + "\n")
        time.sleep(pause)
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

    # def pair(self, mac_address):
    #     self.child.send("pair " + mac_address + "\r\n")
    #     time.sleep(3)
    #     start_failed = self.child.expect(["#", pexpect.EOF])

    #     if start_failed:
    #         raise BluetoothError("Bluetoothctl failed after running pair " + mac_address)

    #     return self.child.before.split("\r\n")

    def pair(self, mac_address):
        try:
            out = self.get_output("pair " + mac_address + "\r\n", 3)
        except BluetoothError, e:
            print(e)
            return None
        else:
            return out

    def get_device_info(self, mac_address):
        try:
            out = self.get_output("info " + mac_address)
        except BluetoothError, e:
            print(e)
            return None
        else:
            return out


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
        time.sleep(8)
        devices = bl.get_available_devices()
        pretty_print(devices)
        target_mac = ""
        for dev in devices:
            if dev[1] == "Galaxy":
                target_mac = dev[0]

        print("pairing with " + target_mac)
        pretty_print(bl.get_device_info(target_mac))
        print("Finally")
        pretty_print(bl.pair(target_mac))


















