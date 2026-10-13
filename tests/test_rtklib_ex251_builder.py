"""Exercise the actual compiler coordinator with simulated compiler results."""
import hashlib
import io
from pathlib import Path
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_rtklib_ex251 as builder


class BuilderTests(unittest.TestCase):
    def fixture(self, root):
        archive=root/'source.tar.gz'
        with tarfile.open(archive,'w:gz') as target:
            for name in ('str2str','rtkrcv','convbin'):
                member=tarfile.TarInfo('RTKLIB-2.5.1/app/consapp/'+name+'/gcc/Makefile')
                member.size=4
                target.addfile(member,io.BytesIO(b'fake'))
        return archive

    def test_non_linux_platform_refused_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.platform,'system',return_value='Darwin'), self.assertRaisesRegex(ValueError,'Linux'):
                builder.build(root/'missing.tar.gz',root/'output')
            self.assertFalse((root/'output').exists())

    def test_wrong_source_fingerprint_refused_before_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=self.fixture(root)
            with patch.object(builder.platform,'system',return_value='Linux'), \
                 patch.object(builder.subprocess,'run') as commands, self.assertRaisesRegex(ValueError,'fingerprint'):
                builder.build(archive,root/'output')
            commands.assert_not_called()
            self.assertFalse((root/'output').exists())

    def test_wrong_binary_version_never_produces_success_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=self.fixture(root)
            def simulate(command,**kwargs):
                if command[0]=='make':
                    directory=Path(command[2]);name=directory.parent.name
                    (directory/name).write_bytes(b'fake compiled tool')
                    return SimpleNamespace(returncode=0)
                return SimpleNamespace(returncode=0,stdout='RTKLIB 2.5.0',stderr='')
            with patch.object(builder.platform,'system',return_value='Linux'), \
                 patch.object(builder,'SOURCE_SHA256',hashlib.sha256(archive.read_bytes()).hexdigest()), \
                 patch.object(builder.shutil,'which',return_value='tool'), \
                 patch.object(builder.subprocess,'run',side_effect=simulate), \
                 self.assertRaisesRegex(ValueError,'Unexpected binary version'):
                builder.build(archive,root/'output')
            self.assertFalse((root/'output/build-manifest.json').exists())
            self.assertFalse((root/'output/str2str').exists())

    def test_compiler_failure_never_produces_success_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=self.fixture(root)
            with patch.object(builder.platform,'system',return_value='Linux'), \
                 patch.object(builder,'SOURCE_SHA256',hashlib.sha256(archive.read_bytes()).hexdigest()), \
                 patch.object(builder.shutil,'which',return_value='tool'), \
                 patch.object(builder.subprocess,'run',side_effect=RuntimeError('compiler failed')), \
                 self.assertRaisesRegex(RuntimeError,'compiler failed'):
                builder.build(archive,root/'output')
            self.assertFalse((root/'output/build-manifest.json').exists())


if __name__=='__main__':unittest.main()
