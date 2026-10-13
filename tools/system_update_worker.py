#!/usr/bin/env python3
"""Root systemd entry point; accepts no browser or shell arguments."""
from system_updates import worker

if __name__ == '__main__':
    result = worker()
    raise SystemExit(1 if result['state'] == 'failed' else 0)
