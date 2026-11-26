"""Run the installer with an isolated dpkg database and inert system commands."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/install_polkit_rules.sh'


@unittest.skipUnless(shutil.which("dpkg-query") and shutil.which("bash"),
                     "requires Debian dpkg-query and bash")
class PolkitInstallation(unittest.TestCase):
    def run_installer(self, status, install_result=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bindir = root / 'bin'
            bindir.mkdir()
            database = root / 'dpkg'
            database.mkdir()
            record = '' if status is None else (
                'Package: polkitd\nStatus: ' + status + '\n'
                'Architecture: all\nVersion: 1\nDescription: test fixture\n\n')
            (database / 'status').write_text(record)
            log = root / 'actions'
            commands = {
                'apt-cache': '#!/bin/sh\necho "Package: polkitd"\n',
                'dpkg-query': '#!/bin/sh\nexec "' + shutil.which('dpkg-query') +
                              '" --admindir="$TEST_DPKG" "$@"\n',
                'apt-get': '#!/bin/sh\necho install >> "$TEST_ACTIONS"\nexit ' + str(install_result) + '\n',
                'cp': '#!/bin/sh\necho rules >> "$TEST_ACTIONS"\n',
                'groupadd': '#!/bin/sh\necho group >> "$TEST_ACTIONS"\n',
                'usermod': '#!/bin/sh\necho user >> "$TEST_ACTIONS"\n',
            }
            for name, content in commands.items():
                executable = bindir / name
                executable.write_text(content)
                executable.chmod(0o755)
            env = dict(os.environ, PATH=str(bindir) + ':' + os.environ['PATH'],
                       TEST_DPKG=str(database), TEST_ACTIONS=str(log))
            result = subprocess.run(['bash', str(SCRIPT), 'test-user'], env=env,
                                    capture_output=True, text=True)
            actions = log.read_text().splitlines() if log.exists() else []
            return result, actions

    def test_missing_or_removed_packages_are_installed(self):
        for status in (None, 'unknown ok not-installed', 'deinstall ok config-files'):
            with self.subTest(status=status):
                result, actions = self.run_installer(status)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(actions, ['install', 'rules', 'group', 'user'])

    def test_installed_package_is_not_reinstalled(self):
        result, actions = self.run_installer('install ok installed')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(actions, ['rules', 'group', 'user'])

    def test_failed_install_stops_before_system_changes(self):
        result, actions = self.run_installer(None, install_result=100)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(actions, ['install'])


if __name__ == '__main__':
    unittest.main()
