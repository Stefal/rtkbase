"""Discover serial source candidates without opening or querying receivers."""
import hashlib
import socket
from pathlib import Path
from ntrip_routing import source_catalog, value
from usb_identity import data_links, usb_metadata


def discover_sources(config, directory=Path('/dev/serial/by-id'), physical=Path('/dev/serial/by-path')):
    catalog = source_catalog(config)
    used = {Path(source.device).resolve() for source in catalog.values() if source.device}
    main = value(config, 'main', 'com_port', '')
    if main:
        used.add((Path(main) if main.startswith('/') else Path('/dev') / main).resolve())
    result = []
    for path in data_links(directory, physical):
        if not path.is_symlink() or not path.exists() or path.resolve() in used:
            continue
        if 'Septentrio' in path.name and not path.name.endswith('-if02'):
            continue
        label = ('Septentrio receiver' if 'Septentrio' in path.name else
                 'u-blox receiver' if 'u-blox' in path.name else 'USB serial device')
        result.append({'device': str(path), 'label': label, 'usb_name': path.name,
                       'identity_verified': False, 'format_verified': False,
                       **usb_metadata(str(path))})
    return result


def port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        try:
            connection.bind(('127.0.0.1', port))
        except OSError:
            return False
    return True


def detected_payload(config, submitted, candidates, available=port_available):
    if set(submitted) != {'detected_device', 'label', 'format', 'baudrate'}:
        raise ValueError('Unexpected detected receiver settings')
    device = submitted['detected_device']
    if not isinstance(device, str) or device not in {item['device'] for item in candidates}:
        raise ValueError('Receiver is unavailable or already registered; detect again')
    identity = 'usb_' + hashlib.sha256(device.encode()).hexdigest()[:16]
    if config.has_section('receiver_stream_' + identity):
        raise ValueError('Receiver is already registered')
    reserved = {source.port for source in source_catalog(config).values()}
    for section in config.sections():
        for key in config[section]:
            candidate = value(config, section, key)
            if 'port' in key and candidate.isdigit():
                reserved.add(int(candidate))
    port = next((port for port in range(5016, 6000) if port not in reserved and available(port)), None)
    if port is None:
        raise ValueError('No local stream port is available')
    return {'identity': identity, 'device': device, 'label': submitted['label'],
            'format': submitted['format'], 'baudrate': submitted['baudrate'], 'port': port}
