import time
import bluetooth
import subprocess
import multiprocessing
import threading

class BluetoothSerial:

    def __init__(self, socketio):
        out = subprocess.check_output("rfkill unblock bluetooth", shell = True)
        self.server_socket = None
        self.socketio = socketio
        self.scan_thread = None

    def scan(self, queue):
        print("Starting the actual scan")
        devices = bluetooth.discover_devices(lookup_names = True)
        print(devices)
        devices_dict = {}
        i = 0
        for device in devices:
            dev_dict = {
                "mac_address": device[0],
                "name": device[1]
            }
            devices_dict.update({i: dev_dict})
            i += 1

        print("Sending available bluetooth devices: ")
        print(devices_dict)
        queue.put(devices_dict)

    def capture_scan_results(self):
        print("Init queue")
        scan_queue = multiprocessing.Queue()
        scan_process = multiprocessing.Process(target = self.scan, args = (scan_queue, ))
        scan_process.start()
        devices_dict = scan_queue.get()
        print("Got devices dict from queue")
        print(devices_dict)
        scan_process.join()
        self.socketio.emit("bluetooth scan results", devices_dict, namespace="/test")

    def start_scan_thread(self):
        print("Starting capture scan results thread...")
        self.scan_thread = threading.Thread(target = self.capture_scan_results)
        self.scan_thread.start()
        print("Capture scan results thread started")
        
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
    bl = BluetoothSerial(0)
    bl.start_scan_thread()
    for i in range(0, 20):
        print(i)
        time.sleep(1)
    print("Started scanning thread")
