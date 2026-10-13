"""Fixed APT operations, persisted review, and bounded public progress.

Only the root-owned systemd worker executes APT. No command supplied by a
browser is accepted. Debian package changes are not a reversible file patch.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid

from receiver_batch_lock import ReceiverBatchLock

STATE = Path('/var/lib/rtkbase-system-update')
UNIT = 'rtkbase_system_update.service'
APT = ['/usr/bin/apt-get']
PLAN = APT + ['--simulate', '--with-new-pkgs', '--no-remove', 'upgrade']
REFRESH = APT + ['-o', 'APT::Update::Error-Mode=any', 'update']
UPGRADE = APT + ['-y', '--with-new-pkgs', '--no-remove', '-o',
                 'Dpkg::Options::=--force-confdef', '-o',
                 'Dpkg::Options::=--force-confold', 'upgrade']


def redact(line):
    line = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', line)
    line = re.sub(r'\b[a-zA-Z][a-zA-Z0-9+.-]*://\S+', '[repository]', line)
    return ''.join(c for c in line if c.isprintable())[:500]


def parse_plan(output):
    packages = []
    for line in output.splitlines():
        if line.startswith('Remv '):
            raise ValueError('Package removal is forbidden')
        if line.startswith('Inst '):
            match = re.match(r'^Inst ([a-z0-9][a-z0-9+.:\-]*) (?:\[([^\]]+)\] )?\(([^\s)]+)', line)
            if not match:
                raise ValueError('Cannot read the proposed package list')
            packages.append(dict(name=match[1], old=match[2], version=match[3]))
    return sorted(packages, key=lambda p: p['name'])


def digest(packages):
    return hashlib.sha256(json.dumps(packages, sort_keys=True).encode()).hexdigest()


class Store:
    def __init__(self, root=STATE):
        self.root = Path(root)

    def ensure(self):
        if self.root.is_symlink():
            raise ValueError('Unsafe state directory')
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name != 'nt':
            info = self.root.stat()
            if info.st_uid != 0 or info.st_mode & 0o077:
                raise ValueError('State directory must be private and owned by root')

    def read(self, name, default=None):
        path = self.root / (name + '.json')
        if path.is_symlink():
            raise ValueError('Unsafe state file')
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

    def write(self, name, value):
        self.ensure()
        fd, tmp = tempfile.mkstemp(dir=self.root)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(value, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp, self.root / (name + '.json'))
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def run_apt(command, progress):
    env = dict(os.environ, LC_ALL='C', DEBIAN_FRONTEND='noninteractive', NEEDRESTART_MODE='l')
    captured = []
    size = 0
    overflow = False
    with subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, env=env) as process:
        # Fixed-size reads bound memory even when APT emits no newline.
        pending = b''
        while True:
            chunk = process.stdout.read1(4096)
            if not chunk:
                break
            pending += chunk
            while b'\n' in pending or len(pending) > 8192:
                if b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                else:
                    line, pending = pending[:8192], pending[8192:]
                decoded = line.decode('utf-8', errors='replace')
                progress(redact(decoded))
                if command == PLAN:
                    size += len(line)
                    if size <= 4 * 1024 * 1024:
                        captured.append(decoded)
                    else:
                        overflow = True
        if pending:
            decoded = pending.decode('utf-8', errors='replace')
            progress(redact(decoded))
            if command == PLAN:
                captured.append(decoded)
        code = process.wait()
    if code:
        raise RuntimeError('APT failed (exit {}). Check progress; package locks are never removed.'.format(code))
    if overflow:
        raise RuntimeError('Package review exceeds the supported size')
    return '\n'.join(captured)


def worker(store=None, runner=run_apt):
    store = store or Store()
    store.ensure()
    with ReceiverBatchLock(store.root / 'worker.lock'):
        job = store.read('request')
        if not job or job.get('action') not in ('refresh', 'upgrade', 'update'):
            raise ValueError('No valid update request')
        previous = store.read('status', {})
        if previous.get('id') != job.get('id') or previous.get('state') != 'queued':
            raise ValueError('Request was already consumed')
        state = dict(id=job['id'], state='running', action=job['action'], created=time.time(), progress=[])
        store.write('status', state)
        last_write = [0]

        def progress(line):
            state['progress'] = (state['progress'] + [line])[-40:]
            if time.monotonic() - last_write[0] > .5:
                store.write('status', state)
                last_write[0] = time.monotonic()

        try:
            if job['action'] in ('refresh', 'update'):
                # Invalidate the old review before refreshing any repository.
                store.write('review', {})
                runner(REFRESH, progress)
                packages = parse_plan(runner(PLAN, progress))
                if job['action'] == 'update':
                    if packages:
                        runner(UPGRADE, progress)
                        store.write('last-update', {'completed_at': time.time()})
                    state.update(state='succeeded', packages_count=len(packages), reboot_required=Path('/var/run/reboot-required').exists())
                    store.write('status', state)
                    return state
                review = dict(id=uuid.uuid4().hex, created=time.time(),
                              packages=packages, digest=digest(packages))
                store.write('review', review)
                state.update(state='ready', review=review)
            else:
                review = store.read('review', {})
                if review.get('id') != job.get('review_id') or time.time() - review.get('created', 0) > 3600:
                    raise ValueError('Review expired. Check updates again.')
                packages = parse_plan(runner(PLAN, progress))
                if digest(packages) != review['digest']:
                    raise ValueError('Package list changed. Check updates again.')
                # Consume authorization before starting the package manager.
                store.write('review', {})
                runner(UPGRADE, progress)
                store.write('last-update', {'completed_at': time.time()})
                state.update(state='succeeded', reboot_required=Path('/var/run/reboot-required').exists())
        except Exception as error:
            state.update(state='failed', error=redact(str(error)))
        store.write('status', state)
        return state


def systemctl(*args):
    result = subprocess.run(['/bin/systemctl', *args], stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=10, check=False)
    if result.returncode:
        raise RuntimeError('System update service is unavailable')
    return result.stdout.strip()


def status(store=None, control=systemctl):
    store = store or Store()
    if control('show', UNIT, '--property=LoadState', '--value') != 'loaded':
        raise ValueError('System update service is not installed')
    value = store.read('status', {'state': 'idle'})
    if value.get('state') in ('queued', 'running') and time.time() - value.get('created', 0) > 30:
        if control('show', UNIT, '--property=ActiveState', '--value') not in ('active', 'activating', 'deactivating'):
            with ReceiverBatchLock(store.root / 'worker.lock'):
                value = store.read('status', value)
                if value.get('state') in ('queued', 'running'):
                    value.update(state='failed', error='Update worker stopped. Check the package manager before trying again.')
                    store.write('status', value)
    value['last_successful_update'] = store.read('last-update', {}).get('completed_at')
    return value


def queue(action, review_id=None, store=None, control=systemctl):
    if action not in ('refresh', 'upgrade', 'update'):
        raise ValueError('Unknown update action')
    store = store or Store()
    store.ensure()
    with ReceiverBatchLock(store.root / 'request.lock'):
        if control('show', UNIT, '--property=LoadState', '--value') != 'loaded':
            raise ValueError('System update service is not installed')
        active = control('show', UNIT, '--property=ActiveState', '--value')
        prior = status(store, control)
        if active in ('active', 'activating', 'deactivating') or (prior.get('state') == 'queued' and time.time() - prior.get('created', 0) < 30):
            raise ValueError('A system update is already running')
        if action == 'upgrade':
            review = store.read('review', {})
            if not review_id or review.get('id') != review_id or not review.get('packages'):
                raise ValueError('Check and review updates first')
        job = dict(id=uuid.uuid4().hex, action=action, review_id=review_id)
        store.write('request', job)
        store.write('status', dict(id=job['id'], action=action, state='queued', created=time.time(), progress=[]))
        try:
            control('--no-block', 'start', UNIT)
        except Exception:
            store.write('status', dict(id=job['id'], state='failed', error='Cannot start system update service'))
            raise
        return store.read('status')
