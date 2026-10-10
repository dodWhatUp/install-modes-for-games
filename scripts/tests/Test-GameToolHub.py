"""Contract tests; fixtures are synthetic tool output, never game measurements."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("tool_hub", Path(__file__).parents[1] / "Game-Tool-Hub.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)


def fixture(value=42.5, source_id=0x55):
    raw = bytearray(32 + 1324)
    hub.HEADER.pack_into(raw, 0, 0x4D41484D, 0x20000, 32, 1, 1324, 1, 1, 1304)
    raw[32:32 + 17] = b"Framerate 1% Low\0"
    raw[292:296] = b"FPS\0"
    struct.pack_into("<3f3I", raw, 32 + 1300, value, 0, 1000, 1, 0xFFFFFFFF, source_id)
    return raw


class Contracts(unittest.TestCase):
    def test_provider_low_is_preserved(self):
        row = hub.decode_mahm(fixture())["rows"][0]
        self.assertEqual(row["value"], 42.5)
        self.assertEqual(row["source_id"], 0x55)
        self.assertEqual(row["units"], "FPS")
        self.assertIn("unscoped", row["scope"])

    def test_unavailable_is_null(self):
        self.assertIsNone(hub.decode_mahm(fixture(3.402823466e38))["rows"][0]["value"])
        self.assertIsNone(hub.decode_mahm(fixture(float("nan")))["rows"][0]["value"])

    def test_zero_not_invented_missing(self):
        self.assertEqual(hub.decode_mahm(fixture(0))["rows"][0]["value"], 0)

    def test_truncated_buffer_rejected(self):
        with self.assertRaises(ValueError):
            hub.decode_mahm(fixture()[:-1])

    def test_invalid_layout_rejected(self):
        for offset, value in ((0, 0xDEAD), (4, 0x30000), (8, 16), (12, 10001), (16, 24)):
            raw = fixture()
            struct.pack_into("<I", raw, offset, value)
            with self.assertRaises(ValueError):
                hub.decode_mahm(raw)

    def test_import_preserves_bytes_and_definition(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "provider.csv"
            payload = b"1% low,0.1% low,latency\r\n42.50,N/A,Unknown\r\n"
            original.write_bytes(payload)
            folder = hub.import_report(original, root / "imports", "Example program", "Provider method v1")
            self.assertEqual((folder / "original.csv").read_bytes(), payload)
            receipt = json.loads((folder / "receipt.json").read_text())
            self.assertEqual(receipt["sha256"], hub.hashlib.sha256(payload).hexdigest())
            self.assertEqual(receipt["definition"], "Provider method v1")
            self.assertFalse(receipt["metrics_recalculated"])
            self.assertIsNone(receipt["run_association"])
            self.assertEqual(original.read_bytes(), payload)
            self.assertNotEqual(hub.import_report(original, root / "imports", "Example program"), folder)

    def test_snapshot_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "evidence.json"
            hub.exclusive_json(target, {"kept": True})
            with self.assertRaises(FileExistsError):
                hub.exclusive_json(target, {"kept": False})
            self.assertTrue(json.loads(target.read_text())["kept"])

    def test_binary_program_not_imported(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "program.exe"
            source.write_bytes(b"test")
            with self.assertRaises(ValueError):
                hub.import_report(source, Path(temporary) / "imports", "Test")

    def test_no_capture_launcher(self):
        console = next(t for t in hub.default_tools() if t["id"] == "presentmon-console")
        self.assertFalse(console["open_allowed"])


if __name__ == "__main__":
    unittest.main()
