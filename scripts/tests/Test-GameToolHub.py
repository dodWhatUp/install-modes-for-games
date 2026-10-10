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


def rtss_fixture(version=0x20015, stride=9344):
    raw = bytearray(128 + stride)
    hub.RTSS_HEADER.pack_into(raw, 0, 0x52545353, version, stride, 128, 1, 512, 36, 0, 1)
    def put(name, value):
        struct.pack_into("<I", raw, 128 + getattr(hub.RtssApp, name).offset, value)
    put("pid", 123)
    raw[132:145] = b"synthetic.exe"
    put("time1", 1000)
    put("stat_count", 25)
    put("average", 555)
    if stride >= 9184:
        put("low_1", 425)
        put("low_01", 310)
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

    def test_rtss_wire_offsets(self):
        # Independently checked against installed SDK's Windows packing-8 prefix.
        self.assertEqual(hub.RtssApp.average.offset, 308)
        self.assertEqual(hub.RtssApp.low_1.offset, 9176)
        self.assertEqual(hub.RtssApp.latency_marker.offset, 9216)
        self.assertEqual(hub.RtssApp.instrumentation.offset, 9232)

    def test_rtss_uses_provider_results(self):
        app = hub.decode_rtss(rtss_fixture(), 1100)["applications"][0]
        self.assertEqual(app["values"]["average"], {"raw": 555, "fps": 55.5})
        self.assertEqual(app["values"]["low_1"], {"raw": 425, "fps": 42.5})
        self.assertEqual(app["values"]["low_01"]["fps"], 31.0)
        self.assertEqual(app["process_id"], 123)
        self.assertTrue(app["fresh"])
        self.assertIsNone(app["latency_ms"])
        self.assertIsNone(app["run_association"])
        self.assertFalse(app["statistics_recording"])

    def test_rtss_no_statistics_does_not_invent_lows(self):
        raw = rtss_fixture()
        struct.pack_into("<I", raw, 128 + hub.RtssApp.stat_count.offset, 0)
        app = hub.decode_rtss(raw, 1100)["applications"][0]
        self.assertIsNone(app["values"]["low_1"]["fps"])
        self.assertEqual(app["values"]["low_1"]["raw"], 425)

    def test_rtss_version_and_stride_gate_new_fields(self):
        for version, stride in ((0x2000C, 9344), (0x20015, 316)):
            app = hub.decode_rtss(rtss_fixture(version, stride), 1100)["applications"][0]
            self.assertIsNone(app["values"]["low_1"]["raw"])
            self.assertEqual(app["latency_endpoints_present"], [])

    def test_rtss_instrumentation_is_not_latency(self):
        raw = rtss_fixture()
        struct.pack_into("<Q", raw, 128 + hub.RtssApp.instrumentation.offset, 999)
        app = hub.decode_rtss(raw, 1100)["applications"][0]
        self.assertEqual(app["latency_endpoints_present"], ["input_sample"])
        self.assertIsNone(app["latency_ms"])

    def test_rtss_stale_live_counter_and_tick_wrap(self):
        raw = rtss_fixture()
        struct.pack_into("<I", raw, 128 + hub.RtssApp.buffer_fps.offset, 600)
        self.assertIsNone(hub.decode_rtss(raw, 4001)["applications"][0]["values"]["buffer_fps"]["fps"])
        struct.pack_into("<I", raw, 128 + hub.RtssApp.time1.offset, 0xFFFFFFF0)
        self.assertEqual(hub.decode_rtss(raw, 16)["applications"][0]["update_age_ms"], 32)

    def test_rtss_invalid_layout_and_truncation(self):
        with self.assertRaises(ValueError):
            hub.decode_rtss(rtss_fixture()[:-1])
        for offset, value in ((0, 0xDEAD), (4, 0x30000), (8, 12), (12, 0), (16, 4097)):
            raw = rtss_fixture()
            struct.pack_into("<I", raw, offset, value)
            with self.assertRaises(ValueError):
                hub.decode_rtss(raw)

    def test_presentmon_preserves_cells_and_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.csv"
            payload = ("Application,ProcessID,SwapChainAddress,CPUStartTime,FrameType,MsGPULatency,MsAllInputToPhotonLatency,InstrumentedLatency\r\n"
                       "synthetic.exe,123,0x1,0.00,Application,1.250,NA,\r\n").encode()
            path.write_bytes(payload)
            folder = hub.import_report(path, Path(temporary) / "imports", "PresentMon 2.6.0 synthetic fixture", "Not measured")
            receipt = json.loads((folder / "receipt.json").read_text())
            preview = receipt["preview"]
            self.assertEqual(preview["samples"][0]["MsGPULatency"], "1.250")
            self.assertEqual(preview["samples"][0]["MsAllInputToPhotonLatency"], "NA")
            self.assertEqual(preview["samples"][0]["InstrumentedLatency"], "")
            self.assertFalse(preview["latency_and_gpu_fields"][1]["available_in_preview"])
            self.assertTrue(preview["frame_type_column_present"])
            self.assertFalse(preview["metrics_recalculated"])
            self.assertEqual((folder / "original.csv").read_bytes(), payload)

    def test_preview_is_bounded_and_opaque_for_other_provider(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.csv"
            path.write_text("Application,ProcessID,SwapChainAddress,CPUStartQPC,DisplayLatency\n" +
                            "synthetic.exe,123,0x1,42,0\n" * 10)
            self.assertEqual(len(hub.report_preview(path, "PresentMon")["samples"]), 5)
            self.assertEqual(hub.report_preview(path, "Other tool")["schema"], "opaque")
            path.write_text("Application,ProcessID,SwapChainAddress,CPUStartTime\nshort,row\n")
            self.assertEqual(hub.report_preview(path, "PresentMon")["schema"], "opaque")

    def test_collectors_cannot_be_relabelled_to_launch(self):
        for name in ("PresentMon-2.6.0-x64.exe", "PresentMon_x64.exe", "RTSSHooksLoader64.exe"):
            self.assertFalse(hub.launch_allowed({"id": "custom", "path": name, "open_allowed": True}))
        self.assertTrue(hub.launch_allowed({"id": "rtss", "path": "RTSS.exe", "open_allowed": True}))

    def test_registration_preserves_registry_and_rejects_collectors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = root / "tools.json"
            registry.write_text("[]")
            tools = []
            interface = root / "existing.exe"
            interface.write_bytes(b"synthetic fixture; never executed")
            with self.assertRaises(ValueError):
                hub.register_tool(registry, tools, interface, "Example", False)
            self.assertEqual(registry.read_text(), "[]")
            self.assertTrue(hub.register_tool(registry, tools, interface, "Example", True))
            self.assertEqual(len(tools), 1)
            self.assertEqual(next(root.glob("tools-before-*.json")).read_text(), "[]")
            self.assertFalse(hub.register_tool(registry, tools, interface, "Duplicate", True))
            collector = root / "PresentMon_x64.exe"
            collector.write_bytes(b"never executed")
            with self.assertRaises(ValueError):
                hub.register_tool(registry, tools, collector, "Relabelled", True)

    def test_shortcuts_preserve_physical_letters_across_layout(self):
        self.assertEqual(hub.shortcut_key(84, "Hebrew_aleph", True), "t")
        self.assertEqual(hub.shortcut_key(49, "1", True), "1")
        self.assertEqual(hub.shortcut_key(28, "Return", True), "return")

    def test_form_draft_never_supplies_action_or_confirmation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "draft.json"
            draft = {"report": {"path": "existing.csv", "provider": "PresentMon"}}
            path.write_text(json.dumps(draft))
            self.assertEqual(hub.read_form_file(path), draft)
            for invalid in ({"capture": True}, {"tool": {"confirmed": True}}, {"report": {"path": 123}}):
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):
                    hub.read_form_file(path)


if __name__ == "__main__":
    unittest.main()
