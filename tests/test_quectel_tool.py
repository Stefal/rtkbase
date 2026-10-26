import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import quectel_tool


class FakeSerial:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.writes = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def reset_input_buffer(self):
        pass

    def write(self, data):
        self.writes.append(data)

    def readline(self):
        if self.responses:
            return self.responses.pop(0)
        return b""


class QuectelToolTests(unittest.TestCase):
    def test_nmea_sentence_adds_checksum_and_line_ending(self):
        self.assertEqual(
            quectel_tool.nmea_sentence("PQTMSAVEPAR"),
            b"$PQTMSAVEPAR*5A\r\n",
        )

    def test_get_firmware_recognizes_supported_receiver(self):
        serial = FakeSerial([b"$PQTMVERNO,LG290P03AANR01A06S,2024*00\r\n"])
        with mock.patch.object(quectel_tool, "open_serial", return_value=serial):
            firmware = quectel_tool.get_firmware("/dev/ttyACM0", 460800)

        self.assertEqual(firmware, "LG290P03AANR01A06S")
        self.assertEqual(serial.writes, [b"$PQTMVERNO*58\r\n"])

    def test_config_file_requires_acknowledgements_and_reboots_last(self):
        serial = FakeSerial(
            [
                b"$PQTMCFGRCVRMODE,OK*00\r\n",
                b"$PQTMSAVEPAR,OK*00\r\n",
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "receiver.cfg"
            config.write_text(
                "# Receiver setup\n"
                "PQTMCFGRCVRMODE,W,2\n"
                "PQTMSAVEPAR\n"
                "PQTMSRR\n",
                encoding="utf-8",
            )
            with mock.patch.object(
                quectel_tool, "open_serial", return_value=serial
            ):
                with mock.patch.object(quectel_tool.time, "sleep") as sleep:
                    quectel_tool.send_config_file("/dev/ttyACM0", 460800, config)

        self.assertEqual(
            serial.writes,
            [
                quectel_tool.nmea_sentence("PQTMCFGRCVRMODE,W,2"),
                quectel_tool.nmea_sentence("PQTMSAVEPAR"),
                quectel_tool.nmea_sentence("PQTMSRR"),
            ],
        )
        sleep.assert_called_once_with(5)


if __name__ == "__main__":
    unittest.main()
