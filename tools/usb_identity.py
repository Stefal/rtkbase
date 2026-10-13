"""Read Linux USB identity metadata only; never open a serial device."""
from pathlib import Path
import re


def stable_path(value):
    return isinstance(value, str) and bool(re.fullmatch(
        r'/dev/serial/by-(?:id|path)/[A-Za-z0-9_.:+-]+', value))


def device_key(device):
    """Compare connected aliases without opening ports; retain missing saved paths."""
    try:
        return ('connected', str(Path(device).resolve(strict=True)))
    except (OSError, RuntimeError, ValueError):
        return ('configured', device)


def usb_metadata(device, sys_class=Path('/sys/class/tty')):
    result = {'usb_serial': None, 'usb_location': None,
              'usb_identity_state': 'unavailable', 'usb_serial_scope': 'USB device or adapter'}
    try:
        target = Path(device).resolve(strict=True)
        node = (sys_class / target.name / 'device').resolve(strict=True)
        for parent in (node, *node.parents):
            if (parent / 'bInterfaceNumber').is_file():
                result['usb_interface'] = (parent / 'bInterfaceNumber').read_text().strip()
            if (parent / 'idVendor').is_file() and (parent / 'idProduct').is_file():
                serial_file = parent / 'serial'
                serial = serial_file.read_text(encoding='utf-8').strip() if serial_file.is_file() else ''
                if len(serial) > 256 or any(ord(c) < 32 for c in serial):
                    return result
                result.update(usb_serial=serial or None, usb_location=parent.name,
                              usb_vendor=(parent / 'idVendor').read_text().strip().lower(),
                              usb_identity_state='serial' if serial else 'physical_port')
                return result
    except (OSError, ValueError):
        pass
    return result


def data_links(directory=Path('/dev/serial/by-id'), physical=Path('/dev/serial/by-path')):
    """Prefer serial-backed by-id links; use by-path when USB has no serial."""
    chosen = {}
    for path in sorted(directory.glob('*')):
        if not path.is_symlink() or not path.exists():
            continue
        if 'Septentrio' in path.name and not path.name.endswith('-if02'):
            continue
        chosen.setdefault(path.resolve(), path)
    for path in sorted(physical.glob('*')):
        if not path.is_symlink() or not path.exists():
            continue
        target = path.resolve()
        if not target.name.startswith(('ttyACM', 'ttyUSB')):
            continue
        metadata = usb_metadata(str(path))
        if metadata.get('usb_vendor') == '152a' and metadata.get('usb_interface') != '02':
            continue
        if metadata['usb_identity_state'] == 'physical_port':
            chosen[target] = path
    return sorted(chosen.values())
