"""Compile pinned upstream EX sources privately; no installation or receiver IO."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import tarfile
import tempfile

SOURCE_SHA256 = 'ad8e56f64dd2b71e2eb8098c27925a65b027b161eae366cf5afb71402348d2e1'


def unpack(archive, directory):
    with tarfile.open(archive, 'r:gz') as source:
        members = source.getmembers()
        if len(members) > 20000 or sum(item.size for item in members) > 500 * 1024 * 1024:
            raise ValueError('Source archive exceeds limits')
        names = set()
        for member in members:
            path = PurePosixPath(member.name)
            if (not path.parts or path.parts[0] != 'RTKLIB-2.5.1' or path.is_absolute()
                    or '..' in path.parts or '\\' in member.name or ':' in member.name
                    or not (member.isfile() or member.isdir()) or member.name in names):
                raise ValueError('Unsafe source archive')
            names.add(member.name)
        for member in members:
            target = directory.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as incoming, target.open('xb') as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)


def build(archive, output):
    if platform.system() != 'Linux':
        raise ValueError('Build requires Linux with make and a C compiler')
    if output.exists():
        raise ValueError('Use a new output directory')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('Source fingerprint differs from the previously validated EX 2.5.1 build')
    if not shutil.which('make') or not shutil.which('cc'):
        raise ValueError('Install the build toolchain before this private compilation')
    output.mkdir(mode=0o700)
    report = {'installed': False, 'receiver_commands_sent': False, 'services_changed': False,
              'source_sha256': SOURCE_SHA256, 'architecture': platform.machine(), 'tools': {}}
    with tempfile.TemporaryDirectory(prefix='ex251-build-', dir=output) as work:
        unpack(archive, Path(work))
        for name in ('str2str', 'rtkrcv', 'convbin'):
            directory = Path(work) / 'RTKLIB-2.5.1/app/consapp' / name / 'gcc'
            with (output / (name + '-build.log')).open('wb') as log:
                subprocess.run(['make', '-C', str(directory)], stdout=log,
                               stderr=subprocess.STDOUT, check=True, timeout=1800)
            binary = directory / name
            answer = subprocess.run([str(binary), '--version'], capture_output=True, text=True, timeout=10)
            version = (answer.stdout + answer.stderr).strip()
            if answer.returncode != 0 or 'RTKLIB EX 2.5.1' not in version:
                raise ValueError('Unexpected binary version: ' + name)
            target = output / name
            shutil.copy2(binary, target)
            target.chmod(0o755)
            report['tools'][name] = {'version': version, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    report['build_passed'] = True
    (output / 'build-manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.source_archive, args.output), indent=2))
