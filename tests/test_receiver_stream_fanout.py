from pathlib import Path
from queue import Queue, Empty
import socket
import sys
import time
from threading import Event, Thread
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from receiver_stream_fanout import PassiveFanout


class Input:
    def __init__(self):
        self.queue = Queue()
        self.closed = False

    def read(self):
        try:
            return self.queue.get(timeout=0.05)
        except Empty:
            return b''

    def close(self):
        self.closed = True


class BlockedConnection:
    """Deterministic stalled writer, avoiding OS-dependent socket buffer sizes."""
    def __init__(self):
        self.writing = Event()
        self.released = Event()
        self.closed = False

    def sendall(self, data):
        self.writing.set()
        if not self.released.wait(3):
            raise socket.timeout('simulated write timeout')
        raise OSError('simulated closed connection')

    def shutdown(self, how):
        self.released.set()

    def close(self):
        self.closed = True
        self.released.set()


class FanoutTests(unittest.TestCase):
    def receive(self, client, expected):
        received = b''
        while len(received) < len(expected):
            chunk = client.recv(len(expected) - len(received))
            if not chunk:
                self.fail('Healthy consumer disconnected')
            received += chunk
        self.assertEqual(received, expected)

    def test_saturated_writer_is_disconnected_without_interrupting_healthy_stream(self):
        source = Input(); factory = Mock(return_value=source)
        fanout = PassiveFanout(factory)
        healthy = socket.create_connection(('127.0.0.1', fanout.port), timeout=2)
        stalled = BlockedConnection()
        stalled_queue = Queue(maxsize=fanout.QUEUE_CHUNKS)
        try:
            deadline = time.monotonic() + 2
            while fanout.client_count != 1 and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertEqual(fanout.client_count, 1)
            with fanout.lock:
                fanout.clients[stalled] = stalled_queue
                sender = Thread(target=fanout.send, args=(stalled, stalled_queue), daemon=True)
                fanout.senders.add(sender); sender.start()
            fanout.start_reading()
            first = b'first chunk'
            source.queue.put(first); self.receive(healthy, first)
            self.assertTrue(stalled.writing.wait(1))
            expected_bytes = len(first)
            for index in range(fanout.QUEUE_CHUNKS + 8):
                chunk = index.to_bytes(4, 'big') + bytes(range(256))
                source.queue.put(chunk); self.receive(healthy, chunk)
                expected_bytes += len(chunk)
            deadline = time.monotonic() + 2
            while not stalled.closed and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertTrue(stalled.closed)
            sender.join(1); self.assertFalse(sender.is_alive())
            self.assertEqual(fanout.client_count, 1)
            self.assertEqual(fanout.dropped_clients, 1)
            self.assertLessEqual(stalled_queue.qsize(), fanout.QUEUE_CHUNKS)
            self.assertEqual(fanout.source_bytes, expected_bytes)
            self.assertFalse(source.closed)
            self.assertIsNone(fanout.error)
            factory.assert_called_once()
        finally:
            stalled.close(); healthy.close(); fanout.close()

    def test_two_consumers_receive_identical_bytes_from_single_reader(self):
        source = Input()
        factory = Mock(return_value=source)
        fanout = PassiveFanout(factory)
        clients = [socket.create_connection(('127.0.0.1', fanout.port), timeout=2) for _ in range(2)]
        try:
            deadline = time.monotonic() + 2
            while fanout.client_count != 2 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(fanout.client_count, 2)
            fanout.start_reading()
            clients[0].sendall(b'RECEIVER COMMAND MUST NOT BE FORWARDED')
            data = bytes(range(256)) * 16
            source.queue.put(data)
            for client in clients:
                received = b''
                while len(received) < len(data):
                    received += client.recv(len(data) - len(received))
                self.assertEqual(received, data)
            factory.assert_called_once()
            with self.assertRaises(RuntimeError):
                fanout.start_reading()
        finally:
            for client in clients:
                client.close()
            fanout.close()
        self.assertTrue(source.closed)
        self.assertIsNone(fanout.error)

    def test_failed_source_is_reported_and_cleanup_works(self):
        fanout = PassiveFanout(Mock(side_effect=RuntimeError('port busy')))
        try:
            fanout.start_reading()
            fanout.reader.join(1)
            self.assertEqual(fanout.error, 'port busy')
            self.assertEqual(fanout.source_bytes, 0)
        finally:
            fanout.close()

    def test_failed_source_disconnects_consumers(self):
        fanout = PassiveFanout(Mock(side_effect=RuntimeError('source lost')))
        client = socket.create_connection(('127.0.0.1', fanout.port), timeout=2)
        try:
            deadline = time.monotonic() + 2
            while fanout.client_count != 1 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(fanout.client_count, 1)
            fanout.start_reading()
            self.assertEqual(client.recv(1), b'')
            fanout.reader.join(1)
            self.assertEqual(fanout.error, 'source lost')
        finally:
            client.close()
            fanout.close()
        self.assertEqual(len(fanout.senders), 0)

    def test_reconnections_release_sender_threads(self):
        source = Input()
        fanout = PassiveFanout(Mock(return_value=source))
        fanout.start_reading()
        try:
            for _ in range(20):
                client = socket.create_connection(('127.0.0.1', fanout.port), timeout=2)
                deadline = time.monotonic() + 2
                while fanout.client_count != 1 and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertEqual(fanout.client_count, 1)
                with fanout.lock:
                    accepted = next(iter(fanout.clients))
                fanout.remove(accepted)
                client.close()
                deadline = time.monotonic() + 2
                while fanout.senders and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertEqual(len(fanout.senders), 0)
        finally:
            fanout.close()

    def test_local_ports_are_distinct_and_invalid_ports_rejected(self):
        first = PassiveFanout(Input)
        second = PassiveFanout(Input)
        try:
            self.assertNotEqual(first.port, second.port)
            self.assertEqual(first.listener.getsockname()[0], '127.0.0.1')
            for port in (-1, 65536, True, '5016'):
                with self.assertRaises(ValueError):
                    PassiveFanout(Input, port=port)
            with self.assertRaises(OSError):
                PassiveFanout(Input, port=first.port)
        finally:
            first.close()
            second.close()


if __name__ == '__main__':
    unittest.main()
