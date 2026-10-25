"""Automated synthetic native-log transitions; no physical input or game test."""
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolAzeronLayer as provider
import GameToolOverlay as overlay

spec = importlib.util.spec_from_file_location("overlay_fixtures", Path(__file__).with_name("Test-GameToolOverlay.py"))
fixtures = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixtures)


class LayerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="AzeronLayerFixture-"); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); manifest, source = fixtures.fixture(self.root)
        self.native = self.root / "native/device/ProfileStorage"; self.native.mkdir(parents=True)
        self.ids = {name: str(uuid.uuid4()) for name in ("BASIC", "NUMBERS", "MENUS", "TOOLS", "NAV", "SYMBOLS")}
        layers = []
        for layer, id_ in self.ids.items():
            raw = json.dumps({"id": id_, "name": layer, "inputs": [{"key": "unchanged"}]}).encode()
            (self.native / ("profile_" + id_ + ".json")).write_bytes(raw)
            layers.append({"id": layer, "profile_id": id_, "profile_sha256": hashlib.sha256(raw).hexdigest()})
        manifest["keymaps"][0]["layers"] = layers
        manifest["keymaps"][0]["blank_masks"] = {name: [] for name in self.ids}
        basic = copy.deepcopy(manifest["assets"])
        manifest["assets"] = [{**asset, "id": asset["id"] + "-" + layer.lower(), "layer": layer, "profile_id": id_}
                              for layer, id_ in self.ids.items() for asset in basic]
        for group in manifest["groups"]:
            group["asset_ids"] = [a["id"] for a in manifest["assets"]]
        source.write_bytes(overlay.encode(manifest))
        self.store = overlay.Store(self.root / "store"); self.store.import_manifest(source, "absent")
        self.value, _ = self.store.load(); self.value["preferences"].update(enabled=True, display=True)
        self.value["preferences"]["selections"]["game"] = {"layer": "BASIC", "view": "Combined", "context": "gameplay"}
        self.log = self.root / "native.log"; self.log.write_bytes(b"")
        self.mono = 10.; self.wall = 1800000000.; self.identity = (1, 123)
        self.reader = provider.LayerFollower(self.log, self.root / "native", probe=lambda: self.identity,
                                            clock=lambda: self.mono, wall=lambda: self.wall)
        self.reader.poll(self.value["manifest"])
        self.before = {p: p.read_bytes() for p in self.native.glob("*.json")}
        self.store_before = self.store.path.read_bytes()

    def emit(self, layer, *, delay=0, message=None, split=False):
        msg = message or "Switch layer on toggle hold: " + self.ids[layer]
        stamp = datetime.fromtimestamp(self.wall - delay, timezone.utc).isoformat()
        data = json.dumps({"level": "info", "message": msg, "timestamp": stamp}).encode() + b"\n"
        with self.log.open("ab") as stream: stream.write(data[:len(data)//2] if split else data)
        self.reader.poll(self.value["manifest"])
        return data

    def select(self):
        return overlay.checked_selection(self.store, self.value, {"exe": "Gameplay.exe", "at": self.mono, "own": False},
                                         now=self.mono, native=self.reader.snapshot())

    def test_hold_all_five_banks_then_release_returns_base(self):
        self.emit("BASIC")
        for layer in ("NUMBERS", "MENUS", "TOOLS", "NAV", "SYMBOLS"):
            self.wall += .1; self.mono += .1; self.emit(layer)
            self.assertEqual(self.select()["layer"], layer)
            self.assertEqual(self.select()["asset_id"], "asset-combined-" + layer.lower())
            self.assertEqual(self.select()["layer_state"], "Event-tracked")
            self.wall += 5; self.mono += 5; self.reader.poll(self.value["manifest"])
            self.assertEqual(self.select()["layer"], layer, "Quiet held interval must not revert to selected BASIC")
            self.wall += .1; self.mono += .1; self.emit("BASIC")
            self.assertEqual(self.select()["layer"], "BASIC")
        self.assertEqual(self.store.path.read_bytes(), self.store_before)
        self.assertEqual({p: p.read_bytes() for p in self.before}, self.before)

    def test_historical_log_never_establishes_current_layer(self):
        self.emit("NAV"); new = provider.LayerFollower(self.log, self.root / "native", probe=lambda: self.identity,
                          clock=lambda: self.mono, wall=lambda: self.wall)
        new.poll(self.value["manifest"]); self.assertFalse(new.snapshot()["available"])

    def test_stale_observation_hides_not_manual_fallback(self):
        self.emit("NAV"); self.mono += 1
        self.assertFalse(self.select()["render"]); self.assertEqual(self.select()["layer_state"], "Stale")

    def test_disconnected_process_resets_until_new_event(self):
        self.emit("NAV"); self.identity = None; self.reader.poll(self.value["manifest"])
        self.assertFalse(self.select()["render"])
        self.identity = (2, 456); self.reader.poll(self.value["manifest"])
        self.assertFalse(self.select()["render"])
        self.emit("BASIC"); self.assertEqual(self.select()["layer"], "BASIC")

    def test_disconnect_and_mode_notifications_invalidate(self):
        for message in ("Normal disconnect - clearing activeDevicePid", "Hardware mode", "Device connected: fixture",
                        "Switch Profile: unknown", "Sleep disconnect detected"):
            self.emit("NAV"); self.emit("NAV", message=message); self.assertFalse(self.select()["render"])

    def test_delayed_event_refused(self):
        self.emit("NAV", delay=1); self.assertFalse(self.select()["render"])

    def test_future_event_refused(self):
        self.emit("NAV", delay=-1); self.assertFalse(self.select()["render"])

    def test_out_of_order_event_refused(self):
        self.emit("NAV"); self.wall -= .1; self.emit("BASIC")
        self.assertFalse(self.select()["render"])

    def test_unknown_layer_message_clears_previous_state(self):
        self.emit("NAV"); self.emit("NAV", message="Switch layer: unrecognized")
        self.assertFalse(self.select()["render"])

    def test_multiple_native_profile_files_are_ambiguous(self):
        self.emit("NAV")
        other = self.root / "native/other/ProfileStorage"; other.mkdir(parents=True)
        (other / ("profile_" + self.ids["NAV"] + ".json")).write_bytes(
            (self.native / ("profile_" + self.ids["NAV"] + ".json")).read_bytes())
        self.reader.poll(self.value["manifest"]); self.assertFalse(self.select()["render"])

    def test_replacement_log_discards_previous_state(self):
        self.emit("NAV"); new = self.root / "new.log"; new.write_bytes(b"{}\n")
        new.replace(self.log); self.reader.poll(self.value["manifest"])
        self.assertFalse(self.select()["render"])

    def test_background_lifecycle_stops_without_native_writes(self):
        self.reader.start(lambda: self.value["manifest"])
        self.assertTrue(self.reader.thread.is_alive()); self.reader.stop()
        self.assertIsNone(self.reader.thread)
        self.assertEqual({p: p.read_bytes() for p in self.before}, self.before)

    def test_unknown_profile_refused(self):
        self.emit("NAV", message="Switch layer: " + str(uuid.uuid4())); self.assertFalse(self.select()["render"])

    def test_profile_drift_hides_stale_labels(self):
        self.emit("NAV"); path = self.native / ("profile_" + self.ids["NAV"] + ".json")
        path.write_bytes(b'{"changed":true}'); self.reader.poll(self.value["manifest"])
        self.assertFalse(self.select()["render"]); self.assertIn("revision", self.select()["reason"])

    def test_retained_old_revision_does_not_block_exact_current_profile(self):
        old = copy.deepcopy(self.value["manifest"]["keymaps"][0]); old["id"] = "old-keymap"
        for layer in old["layers"]: layer["profile_sha256"] = "a" * 64
        old["outputs_sha256"] = "b" * 64
        self.value["manifest"]["keymaps"].append(old)
        self.emit("NAV")
        self.assertTrue(self.reader.snapshot()["available"])
        self.assertEqual(self.select()["layer"], "NAV")

    def test_conflicting_outputs_for_same_current_profile_still_fail_closed(self):
        other = copy.deepcopy(self.value["manifest"]["keymaps"][0]); other["id"] = "conflicting-keymap"
        other["outputs_sha256"] = "b" * 64
        self.value["manifest"]["keymaps"].append(other)
        self.emit("NAV")
        self.assertFalse(self.reader.snapshot()["available"])

    def test_partial_line_waits_for_newline(self):
        data = self.emit("NAV", split=True); self.assertFalse(self.select()["render"])
        with self.log.open("ab") as stream: stream.write(data[len(data)//2:])
        self.reader.poll(self.value["manifest"]); self.assertEqual(self.select()["layer"], "NAV")

    def test_truncation_discards_previous_state(self):
        self.emit("NAV"); self.log.write_bytes(b""); self.reader.poll(self.value["manifest"])
        self.assertFalse(self.select()["render"])

    def test_malformed_event_fails_closed(self):
        self.emit("NAV")
        with self.log.open("ab") as stream: stream.write(b"{invalid}\n")
        self.reader.poll(self.value["manifest"]); self.assertFalse(self.select()["render"])

    def test_backlog_fails_closed(self):
        self.emit("NAV")
        with self.log.open("ab") as stream: stream.write(b" " * (provider.MAX_BATCH + 1))
        self.reader.poll(self.value["manifest"]); self.assertFalse(self.select()["render"])

    def test_unsupported_version_no_tracking(self):
        self.reader.version = "future"; self.emit("NAV"); self.assertFalse(self.select()["render"])

    def test_manual_mode_retains_existing_selection(self):
        self.emit("NAV")
        result = overlay.choose(self.value, {"exe": "Gameplay.exe", "at": self.mono}, now=self.mono)
        self.assertEqual(result["layer"], "BASIC"); self.assertEqual(result["layer_state"], "Selected")

    def test_stop_clears_tracked_state(self):
        self.emit("NAV"); self.reader.stop(); self.assertFalse(self.reader.snapshot()["available"])


class PanelWiringTests(unittest.TestCase):
    def test_panel_switches_assets_and_release_without_profile_write(self):
        # Inert Tk root and mocked renderer: never displays or takes desktop focus.
        import tkinter as tk
        from GameToolOverlayPanel import OverlayPanel
        fixture = LayerTests(); fixture.setUp()
        root = tk.Tk(); root.withdraw(); renderer = mock.Mock()
        # Fixture polling is deterministic; the panel must consume its snapshot.
        fixture.reader.start = mock.Mock()
        panel = None
        try:
            panel = OverlayPanel(root, fixture.store.directory, renderer_factory=lambda *_: renderer,
                                 layer_factory=lambda: fixture.reader)
            panel.value = fixture.value
            panel.foreground = lambda: {"exe": "Gameplay.exe", "at": fixture.mono, "own": False}
            # tick normally loads the store. Supply the fixture's unsaved display state.
            with mock.patch.object(panel.store, "load", return_value=(fixture.value, panel.fingerprint)), \
                    mock.patch.object(overlay.time, "monotonic", side_effect=lambda: fixture.mono), \
                    mock.patch.object(overlay, "relay"):
                panel.tick(False); self.assertFalse(panel.result["render"])
                fixture.emit("NAV"); panel.tick(False)
                self.assertEqual(renderer.show.call_args.args[0]["layer"], "NAV")
                fixture.emit("BASIC"); panel.tick(False)
                self.assertEqual(renderer.show.call_args.args[0]["layer"], "BASIC")
                panel.follow_layer.set(False); panel.tick(False)
                self.assertEqual(panel.result["layer_state"], "Selected")
            self.assertEqual(fixture.store.path.read_bytes(), fixture.store_before)
            self.assertEqual({p: p.read_bytes() for p in fixture.before}, fixture.before)
        finally:
            if panel: panel.close()
            root.destroy(); fixture.doCleanups()


if __name__ == "__main__":
    unittest.main()
