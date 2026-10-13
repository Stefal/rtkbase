"""Share one read-only GNSS input among bounded localhost-only consumers."""
from pathlib import Path
from queue import Queue, Full, Empty
from threading import Event, Lock, Thread, current_thread
import os
import socket
import subprocess
from usb_identity import stable_path


class TCPInput:
    def __init__(self, port):
        if not 1 <= port <= 65535:
            raise ValueError('Invalid local source port')
        self.socket = socket.create_connection(('127.0.0.1', port), timeout=2)
        self.socket.settimeout(0.2)

    def read(self):
        try:
            data = self.socket.recv(8192)
        except socket.timeout:
            return b''
        if not data:
            raise ConnectionError('Source disconnected')
        return data

    def close(self):
        self.socket.close()


class SerialInput:
    def __init__(self, path, baudrate=115200):
        if os.geteuid() != 0:
            raise PermissionError('Root required to verify serial ownership')
        stable = Path(path)
        if not stable_path(path) or not stable.is_symlink():
            raise ValueError('A stable USB identity or physical port is required')
        device = stable.resolve(strict=True)
        if device.parent != Path('/dev') or not device.name.startswith(('ttyUSB', 'ttyACM')):
            raise ValueError('Unexpected serial device')
        check = subprocess.run(['fuser', str(device)], capture_output=True, text=True, timeout=3)
        if check.returncode != 1 or check.stdout.strip() or check.stderr.strip():
            raise RuntimeError('Serial port busy or ownership unknown')
        import serial
        import fcntl
        import termios
        self.stream = serial.Serial(port=None, baudrate=baudrate, timeout=0.2, exclusive=True)
        self.stream.dtr = False
        self.stream.rts = False
        self.stream.port = str(stable)
        self.stream.open()
        try:
            fcntl.ioctl(self.stream.fileno(), termios.TIOCEXCL)
            owners = subprocess.run(['fuser', str(device)], capture_output=True, text=True, timeout=3)
            if owners.returncode != 0 or owners.stdout.split() != [str(os.getpid())]:
                raise RuntimeError('Serial ownership changed while opening')
        except Exception:
            self.stream.close()
            raise

    def read(self):
        return self.stream.read(8192)

    def close(self):
        self.stream.close()


class PassiveFanout:
    MAX_CLIENTS = 16
    QUEUE_CHUNKS = 16

    def __init__(self, source_factory, port=0):
        if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
            raise ValueError('Invalid local output port')
        self.factory = source_factory
        self.listener = socket.socket()
        if os.name == "nt":
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.listener.bind(('127.0.0.1', port))
        except Exception:
            self.listener.close()
            raise
        self.port = self.listener.getsockname()[1]
        self.listener.listen(self.MAX_CLIENTS)
        self.listener.settimeout(0.2)
        self.stop = Event()
        self.lock = Lock()
        self.clients = {}
        self.senders = set()
        self.reader = None
        self.source = None
        self.source_bytes = 0
        self.dropped_clients = 0
        self.error = None
        self.acceptor = Thread(target=self.accept, daemon=True)
        self.acceptor.start()

    @property
    def client_count(self):
        with self.lock:
            return len(self.clients)

    def accept(self):
        while not self.stop.is_set():
            try:
                connection, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            connection.settimeout(1)
            queue = Queue(maxsize=self.QUEUE_CHUNKS)
            with self.lock:
                if self.stop.is_set() or self.error is not None or len(self.clients) >= self.MAX_CLIENTS:
                    connection.close()
                    continue
                self.clients[connection] = queue
                sender = Thread(target=self.send, args=(connection, queue), daemon=True)
                self.senders.add(sender)
                sender.start()

    def remove(self, connection):
        with self.lock:
            self.clients.pop(connection, None)
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        connection.close()

    def send(self, connection, queue):
        try:
            while not self.stop.is_set():
                try:
                    data = queue.get(timeout=0.2)
                except Empty:
                    with self.lock:
                        if connection not in self.clients:
                            break
                    continue
                connection.sendall(data)
        except OSError:
            pass
        finally:
            self.remove(connection)
            with self.lock:
                self.senders.discard(current_thread())

    def start_reading(self):
        with self.lock:
            if self.reader is not None:
                raise RuntimeError('Source already started')
            self.reader = Thread(target=self.read, daemon=True)
            self.reader.start()

    def read(self):
        try:
            self.source = self.factory()
            while not self.stop.is_set():
                data = self.source.read()
                if not data:
                    continue
                if len(data) > 8192:
                    raise ValueError('Input chunk exceeds limit')
                self.source_bytes += len(data)
                with self.lock:
                    clients = list(self.clients.items())
                for connection, queue in clients:
                    try:
                        queue.put_nowait(data)
                    except Full:
                        self.dropped_clients += 1
                        self.remove(connection)
        except Exception as error:
            if not self.stop.is_set():
                self.error = str(error)
        finally:
            with self.lock:
                clients = list(self.clients)
            for connection in clients:
                self.remove(connection)
            if self.source:
                self.source.close()

    def close(self):
        self.stop.set()
        self.listener.close()
        with self.lock:
            clients = list(self.clients)
        for connection in clients:
            self.remove(connection)
        self.acceptor.join(2)
        if self.reader:
            self.reader.join(2)
        with self.lock:
            senders = list(self.senders)
        for sender in senders:
            sender.join(2)
        if self.reader and self.reader.is_alive():
            raise RuntimeError('Input reader did not terminate')
