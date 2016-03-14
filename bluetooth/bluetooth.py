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
                    attribute_list = line.split(" ", 2)
                    mac_address = attribute_list[1]
                    name = attribute_list[2]
                    available_devices.append((mac_address, name))

            return available_devices

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

    def connect(self, mac_address):
        try:
            out = self.get_output("connect " + mac_address + "\r\n", 2)
        except BluetoothError, e:
            print(e)
            return None
        else:
            return out


if __name__ == "__main__":

    print("Init bluetooth...")
    bl = Bluetooth()
    print("Ready!")
    bl.initialize()
    print("Successful init!")
    pretty_print(bl.get_output("scan on"))
    print("Scan turned on")

    searching_for_air = True
    while searching_for_air:
        print("Scanning...")
        devices = bl.get_available_devices()
        print(devices)
        for mac, name in devices:
            if name == "Galaxy Note3":
                searching_for_air = False
                break

    print("Found air!")

    pretty_print(bl.get_device_info(mac))
    print("Finally pairing...")
    pretty_print(bl.pair(mac))

    time.sleep(3)
    print("Connecting...")
    pretty_print(bl.connect(mac))


















