"""Offline checks for the imported X20P configuration; no serial port access."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gps.ubx import ubx


class X20PConfigurationTests(unittest.TestCase):
    def test_default_profile_preserves_unrelated_settings(self):
        commands = [line.strip() for line in (ROOT / "receiver_cfg/X20P_RTCM3_OUT.txt").read_text().splitlines()
                    if line.strip() and not line.strip().startswith("#")]
        self.assertNotIn("UBX-FRESET", commands)

    def test_profile_uses_supported_configuration_keys(self):
        keys = {item[0] for item in ubx.cfgs}
        for line in (ROOT / "receiver_cfg/X20P_RTCM3_OUT.txt").read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("CFG-"):
                key, value = line.split(",", 1)
                self.assertIn(key, keys, key)
                int(value)
            else:
                self.assertTrue(line == "UBX-FRESET" or line.startswith("UBX-SURVEY,"), line)

    def convert_position(self, position):
        # Execute the actual Python helper embedded in the Bash configurator.
        script = (ROOT / "tools/set_zed-x20p.sh").read_text()
        helper = script.split("<<'PYFIXED'\n", 1)[1].split("\nPYFIXED", 1)[0]
        return subprocess.run([sys.executable, "-", position], input=helper,
                              text=True, capture_output=True)

    def test_negative_position_preserves_high_precision(self):
        result = self.convert_position("-48.123456789 -2.987654321 -12.3456")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(),
                         ["-481234567", "-89", "-29876543", "-21", "-1234", "-56"])

    def test_zero_position_is_valid(self):
        result = self.convert_position("0 0 0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["0"] * 6)

    def test_invalid_positions_fail(self):
        for position in ("91 0 0", "0 -181 0", "1 2", "bad 2 3"):
            with self.subTest(position=position):
                self.assertNotEqual(self.convert_position(position).returncode, 0)


if __name__ == "__main__":
    unittest.main()
