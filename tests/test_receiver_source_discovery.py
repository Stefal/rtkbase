import configparser
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from receiver_source_discovery import discover_sources, detected_payload
from ntrip_routing import register_source, source_catalog


def config():
    result = configparser.ConfigParser(interpolation=None)
    result['main'] = {'receiver_format': 'sbf', 'tcp_port': '5015', 'com_port': 'ttyACM1'}
    return result


def usb(name, resolved, exists=True):
    item = Mock()
    item.name = name
    item.is_symlink.return_value = True
    item.exists.return_value = exists
    item.resolve.return_value = Path(resolved).resolve()
    item.__str__ = Mock(return_value='/dev/serial/by-id/' + name)
    item.__lt__ = Mock(side_effect=lambda other: name < other.name)
    return item


class DiscoveryTests(unittest.TestCase):
    def test_identical_um980_register_separately_and_only_registered_port_is_excluded(self):
        cfg = config()
        names = ['usb-FTDI_FT230X_Basic_UART_' + serial + '-if00-port0'
                 for serial in ('ADAPTER_A', 'ADAPTER_B')]
        paths = [usb(name, '/dev/ttyUSB' + str(index)) for index, name in enumerate(names)]
        found = self.candidates(cfg, paths)
        self.assertEqual(len(found), 2)
        identities = []
        for candidate in found:
            # Same model, firmware and baudrate: only the USB port identifies the source.
            candidate.update(model='UM980', firmware='R4.10Build25621')
            payload = detected_payload(cfg, {'detected_device': candidate['device'],
                'label': 'UM980', 'format': 'rtcm3', 'baudrate': '115200'},
                found, lambda port: True)
            identities.append(payload['identity'])
            cfg = register_source(cfg, payload)
        self.assertEqual(len(set(identities)), 2)
        catalog = source_catalog(cfg)
        self.assertNotEqual(catalog[identities[0]].port, catalog[identities[1]].port)
        self.assertEqual([catalog[key].label for key in identities], ['UM980', 'UM980'])
        # Resolve fixture paths as Linux does, including aliases to the first device.
        first_cfg = register_source(config(), {**self.submitted_without_detection(),
            'device': found[0]['device'], 'label': 'UM980', 'format': 'rtcm3'})
        targets = [path.resolve() for path in paths]
        main_target = Path('/dev/ttyACM1').resolve()
        def resolved(path, *args, **kwargs):
            if path.name == 'ttyACM1':
                return main_target
            if names[0] in str(path):
                return targets[0]
            return targets[1]
        with patch.object(Path, 'resolve', autospec=True, side_effect=resolved):
            remaining = self.candidates(first_cfg, paths)
        self.assertEqual([item['device'] for item in remaining], [found[1]['device']])

    def candidates(self, cfg, paths):
        directory = Mock()
        directory.glob.return_value = paths
        physical = Mock()
        physical.glob.return_value = []
        # Fixtures must not mix synthetic by-id links with the host's real USB ports.
        with patch('receiver_source_discovery.usb_metadata', return_value={
                'usb_serial': None, 'usb_location': None, 'usb_identity_state': 'unavailable'}):
            result = discover_sources(cfg, directory, physical)
        physical.glob.assert_called_once_with('*')
        return result

    def submitted(self):
        return {'detected_device': '/dev/serial/by-id/usb-u-blox-X20P',
                'label': 'X20P', 'format': 'ubx', 'baudrate': '115200'}

    def test_main_control_and_disconnected_ports_are_excluded(self):
        items = [usb('usb-Septentrio-X5-if02', '/dev/ttyACM1'),
                 usb('usb-Septentrio-X5-if04', '/dev/ttyACM2'),
                 usb('usb-u-blox-X20P', '/dev/ttyACM0'),
                 usb('usb-FTDI-missing', '/dev/ttyUSB0', False)]
        found = self.candidates(config(), items)
        self.assertEqual([item['device'] for item in found], [self.submitted()['detected_device']])
        self.assertFalse(found[0]['identity_verified'])
        self.assertFalse(found[0]['format_verified'])

    def test_registered_device_alias_is_excluded(self):
        cfg = register_source(config(), {**self.submitted_without_detection(), 'device': '/dev/serial/by-id/alias'})
        from unittest.mock import patch
        with patch.object(Path, 'resolve', autospec=True,
                          side_effect=lambda path, *args, **kwargs: Path(
                              '/dev/ttyACM1' if path.name == 'ttyACM1' else '/dev/ttyUSB0')):
            self.assertEqual(self.candidates(cfg, [usb('usb-FTDI-second-alias', '/dev/ttyUSB0')]), [])

    def submitted_without_detection(self):
        return {'identity': 'existing', 'label': 'Existing', 'format': 'ubx', 'baudrate': '115200', 'port': 5016}

    def test_id_and_free_port_are_assigned_without_changing_existing_config(self):
        cfg = config(); cfg['network'] = {'other_port': '5016'}
        before = {section: dict(cfg[section]) for section in cfg.sections()}
        calls = []
        def available(port):
            calls.append(port)
            return port != 5017
        payload = detected_payload(cfg, self.submitted(), [{'device': self.submitted()['detected_device']}], available)
        self.assertEqual(payload['port'], 5018)
        self.assertEqual(calls, [5017, 5018])
        self.assertTrue(payload['identity'].startswith('usb_'))
        self.assertEqual(before, {section: dict(cfg[section]) for section in cfg.sections()})
        registered = register_source(cfg, payload)
        self.assertEqual(source_catalog(registered)[payload['identity']].label, 'X20P')

    def test_disappeared_receiver_and_forged_device_are_refused(self):
        for device in (self.submitted()['detected_device'], '/tmp/serial', '/dev/ttyUSB0'):
            with self.subTest(device=device), self.assertRaises(ValueError):
                detected_payload(config(), {**self.submitted(), 'detected_device': device}, [], lambda p: True)

    def test_format_must_be_explicit_and_valid(self):
        for fmt in ('', 'unknown'):
            payload = detected_payload(config(), {**self.submitted(), 'format': fmt},
                                       [{'device': self.submitted()['detected_device']}], lambda p: True)
            with self.assertRaises(ValueError):
                register_source(config(), payload)

    def test_client_cannot_choose_port_or_identity_in_detected_mode(self):
        with self.assertRaises(ValueError):
            detected_payload(config(), {**self.submitted(), 'port': 5015}, [], lambda p: True)

    def test_port_exhaustion_is_reported(self):
        with self.assertRaisesRegex(ValueError, 'No local stream port'):
            detected_payload(config(), self.submitted(), [{'device': self.submitted()['detected_device']}], lambda p: False)


if __name__ == '__main__':
    unittest.main()
