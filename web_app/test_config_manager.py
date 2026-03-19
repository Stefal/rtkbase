from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import sys


WEB_APP_DIR = Path(__file__).resolve().parent
if str(WEB_APP_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_APP_DIR))

from RTKBaseConfigManager import RTKBaseConfigManager


class RTKBaseConfigManagerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.default_settings = WEB_APP_DIR.parent / "settings.conf.default"
        self.user_settings = Path(self.tempdir.name) / "settings.conf"
        shutil.copy(self.default_settings, self.user_settings)
        self.config = RTKBaseConfigManager(str(self.default_settings), str(self.user_settings))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_get_all_ntrip_settings_lists_existing_sections(self):
        ntrip_sections = [section["source_section"] for section in self.config.get_all_ntrip_settings()]
        self.assertEqual(["ntrip_A", "ntrip_B"], ntrip_sections)

    def test_add_ntrip_settings_creates_next_available_section(self):
        new_section = self.config.add_ntrip_settings()

        self.assertEqual("ntrip_C", new_section)
        self.assertIn("ntrip_C", self.config.sections())

        ntrip_settings = self.config.get_ntrip_settings("ntrip_C")
        self.assertTrue(ntrip_settings["can_remove"])
        self.assertEqual("svr_addr_C", ntrip_settings["svr_addr"]["name"])
        self.assertEqual("caster.centipede.fr", ntrip_settings["svr_addr"]["value"])
        self.assertEqual("2101", ntrip_settings["svr_port"]["value"])

    def test_builtin_ntrip_sections_cannot_be_removed(self):
        with self.assertRaises(ValueError):
            self.config.remove_ntrip_settings("ntrip_A")

    def test_remove_ntrip_settings_deletes_dynamic_section(self):
        new_section = self.config.add_ntrip_settings()

        self.config.remove_ntrip_settings(new_section)

        self.assertNotIn(new_section, self.config.sections())
        ntrip_sections = [section["source_section"] for section in self.config.get_all_ntrip_settings()]
        self.assertEqual(["ntrip_A", "ntrip_B"], ntrip_sections)


if __name__ == "__main__":
    unittest.main()
