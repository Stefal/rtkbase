import time
import pexpect
import subprocess

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
        print("EXPECTING...")
        start_failed = self.child.expect(["[default]", pexpect.EOF])

        if start_failed:
            raise BluetoothError("Could not start bluetoothctl")

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

