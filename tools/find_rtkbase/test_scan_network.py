from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("scan_network.py")
SPEC = importlib.util.spec_from_file_location("scan_network_under_test", MODULE_PATH)
scan_network = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(scan_network)


class FakeService:
    def __init__(self, name, port, server, address_bytes):
        self.name = name
        self.port = port
        self.server = server
        self.addresses = [address_bytes]


class FakeZeroconf:
    def __init__(self, services):
        self.services = services
        self.closed = False

    def get_service_info(self, service_type, name):
        return self.services[name]

    def close(self):
        self.closed = True


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class ScanNetworkTests(unittest.TestCase):
    def test_zeroconf_scan_returns_results_sorted_by_server_name(self):
        fake_services = {
            "svc-b": FakeService(
                "RTKBase Web Server Beta",
                80,
                "beta.local.",
                bytes([192, 168, 1, 20]),
            ),
            "svc-a": FakeService(
                "RTKBase Web Server Alpha",
                80,
                "alpha.local.",
                bytes([192, 168, 1, 10]),
            ),
        }
        fake_zeroconf = FakeZeroconf(fake_services)

        def fake_browser(zeroconf, service_type, listener):
            listener.add_service(zeroconf, service_type, "svc-b")
            listener.add_service(zeroconf, service_type, "svc-a")
            return object()

        with (
            mock.patch.object(scan_network, "Zeroconf", return_value=fake_zeroconf),
            mock.patch.object(scan_network, "ServiceBrowser", side_effect=fake_browser),
            mock.patch.object(scan_network.time, "sleep", return_value=None),
        ):
            results = scan_network.zeroconf_scan("RTKBase Web Server", "_http._tcp.local.")

        self.assertEqual(["alpha.local", "beta.local"], [item["SERVER"] for item in results])
        self.assertTrue(fake_zeroconf.closed)

    def test_get_rtkbase_infos_retries_ip_before_server_name(self):
        calls = []

        def fake_get(url, timeout):
            calls.append(url)
            if len(calls) < 3:
                raise scan_network.requests.exceptions.ConnectionError("network")
            return FakeResponse(
                200,
                {"app": "RTKBase", "app_version": "2.0.0", "fqdn": "alpha.local"},
            )

        host_list = [{"IP": "10.0.0.5", "SERVER": "alpha.local", "PORTS": [80]}]
        with mock.patch.object(scan_network.requests, "get", side_effect=fake_get):
            results = scan_network.get_rtkbase_infos(host_list)

        self.assertEqual(
            [
                "http://10.0.0.5:80/api/v1/infos",
                "http://10.0.0.5:80/api/v1/infos",
                "http://alpha.local:80/api/v1/infos",
            ],
            calls,
        )
        self.assertEqual("alpha.local", results[0]["server"])
        self.assertEqual("10.0.0.5", results[0]["ip"])

    def test_get_rtkbase_infos_stops_after_successful_ip_retry(self):
        calls = []

        def fake_get(url, timeout):
            calls.append(url)
            if len(calls) == 1:
                raise scan_network.requests.exceptions.ConnectionError("network")
            return FakeResponse(
                200,
                {"app": "RTKBase", "app_version": "2.0.0", "fqdn": "alpha.local"},
            )

        host_list = [{"IP": "10.0.0.5", "SERVER": "alpha.local", "PORTS": [80]}]
        with mock.patch.object(scan_network.requests, "get", side_effect=fake_get):
            results = scan_network.get_rtkbase_infos(host_list)

        self.assertEqual(
            [
                "http://10.0.0.5:80/api/v1/infos",
                "http://10.0.0.5:80/api/v1/infos",
            ],
            calls,
        )
        self.assertEqual(1, len(results))


if __name__ == "__main__":
    unittest.main()
