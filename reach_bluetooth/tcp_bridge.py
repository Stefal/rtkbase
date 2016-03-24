import bluetooth
import subprocess
import multiprocessing
import socket
import time

class TCPConnectionError(Exception):
    pass

class RFCOMMServer:
    """A bluetooth SPP RFCOMM server."""

    def __init__(self, buffer_size=1024):
        out = subprocess.check_output("rfkill unblock bluetooth", shell = True)

        self.server_socket = None
        self.client_socket = None
        self.buffer_size = buffer_size

    def initialize(self):
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

    def accept_connection(self):
        self.client_socket, client_info = self.server_socket.accept()
        return client_info

    def kill_connection(self):
        self.client_socket.close()
        self.server_socket.close()

    def read(self):
        return self.client_socket.recv(self.buffer_size)

    def write(self, data):
        return self.client_socket.send(data)


class TCPServer():
    """A wrapper around TCP server."""

    def __init__(self, tcp_port, buffer_size=1024):
        self.server_socket = None
        self.client_socket = None
        self.address = ("localhost", tcp_port)
        self.buffer_size = buffer_size

    def initialize(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(self.address)
        self.server_socket.listen(5)

    def accept_connection(self):
        self.client_socket, client_info = self.server_socket.accept()
        return client_info

    def kill_connection(self):
        self.client_socket.close()
        self.server_socket.close()

    def read(self):
        return self.client_socket.recv(self.buffer_size)

    def write(self, data):
        return self.client_socket.send(data)


class TCPtoRFCOMMBridge:
    """A bridge that reads a tcp socket and sends data to a RFCOMMServer."""

    def __init__(self, tcp_port=8143):
        self.rfcomm_server = RFCOMMServer()
        self.tcp_server = TCPServer(tcp_port)

        self.bridge_not_interrupted = True
        self.bridge_process = None

    def kill_connections(self):
        print("Killing all bridge connections...")
        self.rfcomm_server.kill_connection()
        self.tcp_server.kill_connection()

    def run_bridge(self):
        self.rfcomm_server.initialize()
        self.tcp_server.initialize()
        print("Waiting for incoming TCP connection...")
        print("{}:{} connected".format(*self.tcp_server.accept_connection()))
        print("Waiting for incoming bluetooth connection...")
        print("{} connected".format(self.rfcomm_server.accept_connection()))
        while self.bridge_not_interrupted:
            print("Starting the connection bridge...")
            try:
                while True:
                    network_data_received = self.tcp_server.read()
                    if not network_data_received:
                        raise TCPConnectionError("External connection shutdown")
                    self.rfcomm_server.write(network_data_received)
            except IOError, e:
                print(e)
                print("Bluetooth connection killed, reinitializing...")
                self.rfcomm_server.kill_connection()
                self.rfcomm_server.initialize()
                print("Waiting for incoming bluetooth connection...")
                print("{} connected".format(self.rfcomm_server.accept_connection()))
            except TCPConnectionError, e:
                print(e)
                print("TCP connection killed, reinitializing all...")
                self.kill_connections()
                self.rfcomm_server.initialize()
                self.tcp_server.initialize()
                print("Waiting for incoming TCP connection...")
                print("{}:{} connected".format(*self.tcp_server.accept_connection()))
                print("Waiting for incoming bluetooth connection...")
                print("{} connected".format(self.rfcomm_server.accept_connection()))

        print("Bridge stopped from outside, killing connections...")
        self.kill_connection()

    def start(self):
        """Run the bridge in a separate process."""
        self.bridge_not_interrupted = True
        self.bridge_process = multiprocessing.Process(target = self.run_bridge)
        self.bridge_process.start()

    def stop(self):
        self.bridge_not_interrupted = False
        if self.bridge_process is not None:
            self.bridge_process.terminate()
            self.bridge_process.join()
            self.bridge_process = None


if __name__ == "__main__":
    bridge = TCPtoRFCOMMBridge(8000)
    bridge.start()

    for i in range(0, 30):
        print(i)
        time.sleep(1)

    print("Time is up, stopping...")
    bridge.stop()







