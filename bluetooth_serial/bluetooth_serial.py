import bluetooth
import subprocess
import threading

class BluetoothSerial:

    def __init__(self):
        out = subprocess.check_output("rfkill unblock bluetooth", shell = True)
        self.server_socket = None

    def scan(self):
        return bluetooth.discover_devices(lookup_names = True)

    def initialize_server(self):
        self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_socket.bind(("",bluetooth.PORT_ANY))
        self.server_socket.listen(1)

        port = self.server_socket.getsockname()[1]

        uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

        bluetooth.advertise_service(
            self.server_socket,
            "ReachBluetoothSocket",
            service_id = uuid,
            service_classes = [uuid, bluetooth.SERIAL_PORT_CLASS],
            profiles = [bluetooth.SERIAL_PORT_PROFILE],
        )

        print("Waiting for connection on RFCOMM channel " + str(port))

    def accept_connection(self):
        client_socket, client_info = self.server_socket.accept()
        print("Accepted connection from " + str(client_info))

        try:
            while True:
                data = client_socket.recv(1024)
                if len(data) == 0: break
                print("received [%s]" % data)
        except IOError:
            pass

        print("disconnected")

        client_socket.close()
        self.server_socket.close()
        print("all done")

if __name__ == "__main__":
    bl = BluetoothSerial()
    bl.initialize_server()
    bl.accept_connection()
