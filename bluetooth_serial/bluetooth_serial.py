import bluetooth
import subprocess
import multiprocessing
import socket
import time

class BluetoothConnectionError(Exception):
    pass

class BluetoothSerial:

    def __init__(self, buffer_size=1024):
        out = subprocess.check_output("rfkill unblock bluetooth", shell = True)

        self.server_socket = None
        self.client_socket = None
        self.buffer_size = buffer_size

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

        print("Initialized bluetooth serial server")
        print("Waiting for connection on RFCOMM channel " + str(port))

    def accept_connection(self):
        self.client_socket, client_info = self.server_socket.accept()
        print("Accepted connection from " + str(client_info))

    def kill_connection(self):
        self.client_socket.close()
        self.server_socket.close()
        self.client_socket = None
        self.server_socket = None

    def read(self):
        return self.client_socket.recv(self.buffer_size)

    def write(self, data):
        return self.client_socket.send(data)

class BluetoothTCPBridge:

    def __init__(self, tcp_port=8143):
        self.tcp_port = tcp_port
        self.socket = None
        self.bluetooth_serial = BluetoothSerial()

        self.bridge_not_interrupted = True
        self.bridge_process = None

    def connect_tcp(self):
        self.socket = socket.create_connection(("localhost", self.tcp_port))

    def kill_connections(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.bluetooth_serial.kill_connection()

    def run_bridge(self):
        while self.bridge_not_interrupted:
            print("Initializing bluetooth server...")
            self.bluetooth_serial.initialize_server()
            self.bluetooth_serial.accept_connection()
            self.connect_tcp()

            try:
                while self.bridge_not_interrupted:
                    print(self.bridge_not_interrupted)
                    data_received = self.socket.recv(1024)
                    print("Received data via tcp: " + str(data_received))
                    self.bluetooth_serial.write(data_received)
            except IOError, e:
                print(e)
                self.kill_connections()
                print("Bluetooth connection broken, reinitializing...")

        print("Bridge interrupted, shutting down..")
        self.kill_connections()
        sys.stdout.close()

    def start(self):
        self.bridge_not_interrupted = True
        self.bridge_process = multiprocessing.Process(target = self.run_bridge)
        self.bridge_process.start()

    def stop(self):
        self.bridge_not_interrupted = False
        if self.bridge_process is not None:
            self.bridge_process.terminate()
            self.bridge_process.join()
            self.bridge_process = None


class STOPITALREADY(Exception):
    pass

if __name__ == "__main__":
    bl = BluetoothTCPBridge()
    bl.start()
    i = 0
    try:
        while True:
            print(i)
            time.sleep(1)
            i += 1
            if i == 30:
                raise STOPITALREADY
    except STOPITALREADY:
        print("Caught STOPITALREADY, killing the bridge")
        bl.stop()
        print("Bridge stopped")

    print("Program exiting...")









