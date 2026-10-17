"""Controlled fixtures, NOT game/native-device acceptance."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as api


def fixture(root):
    from PIL import Image
    buf = io.BytesIO(); Image.new("RGB", (16, 12), (2, 8, 14)).save(buf, format="PNG")
    pixels = buf.getvalue(); (root / "fixture.png").write_bytes(pixels)
    value = api.empty_store()["manifest"]
    value["games"] = [{"id": "game", "label": "Long synthetic game label — fixture only"}]
    value["keymaps"] = [{"id": "keymap", "label": "Fixture SPARSE6", "revision": "fixture-1", "outputs_sha256": "a" * 64,
        "geometry_sha256": "b" * 64, "atlas_revision": "fixture-Atlas", "family": "SPARSE6",
        "layers": [{"id": layer, "profile_id": "installed-" + layer, "profile_sha256": "c" * 64} for layer in ("BASIC", "MENUS")],
        "visible_positions": sorted(api.R8_POSITIONS), "hidden_positions": [19],
        "blank_masks": {"BASIC": [], "MENUS": [7, 11, 16]}, "joystick_drawn": False}]
    value["assets"] = [{"id": "asset-" + view.lower(), "label": view + " fixture", "path": "fixture.png", "sha256": api.sha(pixels),
        "keymap_id": "keymap", "layer": "BASIC", "context": "gameplay", "view": view,
        "profile_id": "installed-BASIC", "evidence": "unknown"} for view in api.VIEWS]
    render = {"size_mode": "Screen width %", "size_value": 30, "opacity": 85, "monitor": 1,
              "anchor": "TopRight", "offset_x": 0, "offset_y": 0}
    value["groups"] = [{"id": "group-" + n, "label": "Fixture group " + n, "game_id": "game", "keymap_id": "keymap",
                        "asset_ids": [a["id"] for a in value["assets"]], "rendering": copy.deepcopy(render)} for n in ("a", "b")]
    value["associations"] = [{"id": "assoc", "game_id": "game", "executables": ["Gameplay.exe"],
        "excluded_executables": ["Launcher.exe"], "keymap_id": "keymap", "default_group": "group-a",
        "cycle_groups": ["group-a", "group-b"], "cycle_enabled": True, "priority": 0}]
    path = root / "manifest.json"; path.write_bytes(api.encode(value))
    return value, path


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="OverlayContractFixture-")
        self.root = Path(self.temp.name); self.addCleanup(self.temp.cleanup)
        self.m, self.source = fixture(self.root)
        self.store = api.Store(self.root / "private")
        self.store.import_manifest(self.source, "absent")
        self.value, self.hash = self.store.load()
        self.value["preferences"].update(enabled=True, display=True)
        self.value["preferences"]["selections"]["game"] = {"layer": "BASIC", "context": "gameplay", "view": "Combined"}
        self.fg = {"exe": "C:\\Games\\Gameplay.exe", "pid": 12, "at": 10, "own": False}

    def choose(self, fg=None, **kwargs):
        return api.choose(self.value, self.fg if fg is None else fg, now=10, **kwargs)

    def test_auto_exact_selection(self):
        result = self.choose()
        self.assertEqual(result["asset_id"], "asset-combined"); self.assertTrue(result["render"])
        self.assertEqual(result["layer_state"], "Selected"); self.assertFalse(result["native_mismatch"])

    def test_pid_restart_does_not_change_association(self):
        old = self.choose(); self.fg["pid"] = 912
        self.assertEqual(self.choose()["asset_id"], old["asset_id"])

    def test_actual_path_overrides_basename(self):
        other = copy.deepcopy(self.value["manifest"]["associations"][0]); other.update(id="exact", executables=[self.fg["exe"]], default_group="group-b")
        self.value["manifest"]["associations"].append(other)
        self.assertEqual(self.choose()["group_id"], "group-b")

    def test_equal_ambiguity_refuses(self):
        other = copy.deepcopy(self.value["manifest"]["associations"][0]); other.update(id="other", default_group="group-b")
        self.value["manifest"]["associations"].append(other)
        self.assertIsNone(self.choose()["asset_id"]); self.assertIn("Ambiguous", self.choose()["reason"])

    def test_priority_resolves_ambiguity(self):
        other = copy.deepcopy(self.value["manifest"]["associations"][0]); other.update(id="other", priority=1, default_group="group-b")
        self.value["manifest"]["associations"].append(other)
        self.assertEqual(self.choose()["group_id"], "group-b")

    def test_launcher_never_selected(self):
        self.fg["exe"] = "Launcher.exe"; self.assertIsNone(self.choose()["game_id"])

    def test_background_game_not_selection(self):
        self.fg["exe"] = "Browser.exe"; self.assertIsNone(self.choose()["asset_id"])

    def test_own_app_window_hides(self):
        self.fg["own"] = True; self.assertFalse(self.choose()["render"])

    def test_focus_loss_exit_missing_hides(self):
        self.assertFalse(api.choose(self.value, None, now=10)["render"])

    def test_stale_future_fg_refuses(self):
        for at in (8, 11):
            self.fg["at"] = at; self.assertFalse(self.choose()["render"])

    def test_rapid_changes_never_reuse_old_asset(self):
        self.assertTrue(self.choose()["render"])
        self.fg["exe"] = "Other.exe"; self.assertFalse(self.choose()["render"])
        self.fg["exe"] = "Gameplay.exe"; self.assertTrue(self.choose()["render"])

    def test_unknown_layer_no_old_action_fallback(self):
        self.value["preferences"]["selections"]["game"]["layer"] = "Unknown"
        self.assertIsNone(self.choose()["asset_id"])

    def test_context_matching(self):
        self.value["preferences"]["selections"]["game"]["context"] = "inventory"
        self.assertIsNone(self.choose()["asset_id"])

    def test_all_view_variants(self):
        for view in api.VIEWS:
            self.value["preferences"]["selections"]["game"]["view"] = view
            self.assertEqual(self.choose()["asset_id"], "asset-" + view.lower())

    def test_layer_matching(self):
        self.value["preferences"]["selections"]["game"]["layer"] = "MENUS"
        self.assertIsNone(self.choose()["asset_id"])

    def test_native_fresh_fixture_observed(self):
        result = self.choose(native={"at": 10, "provider": "fixture-only", "profile_id": "installed-BASIC",
            "profile_sha256": "c" * 64, "outputs_sha256": "a" * 64})
        self.assertEqual(result["layer_state"], "Observed"); self.assertTrue(result["render"])

    def test_native_stale_fixture_refuses_even_with_selection(self):
        result = self.choose(native={"at": 8, "provider": "fixture-only"})
        self.assertEqual(result["layer_state"], "Stale"); self.assertFalse(result["render"])

    def test_observed_native_mismatch_refuses(self):
        for field in ("profile_id", "profile_sha256", "outputs_sha256"):
            native = {"at": 10, "provider": "fixture-only", "profile_id": "installed-BASIC", "profile_sha256": "c" * 64, "outputs_sha256": "a" * 64}
            native[field] = "mismatch"
            self.assertTrue(self.choose(native=native)["native_mismatch"]); self.assertFalse(self.choose(native=native)["render"])

    def test_no_native_provider_claimed(self):
        self.assertIn("unsupported", api.capabilities()["native_observation"])

    def test_manual_override_return_auto(self):
        self.value["preferences"]["overrides"]["game"] = "group-b"
        self.assertEqual(self.choose()["group_id"], "group-b"); self.assertTrue(self.choose()["manual_override"])
        self.value["preferences"]["overrides"].clear(); self.assertEqual(self.choose()["group_id"], "group-a")

    def test_cycle_and_persistence(self):
        self.store.update("cycle", {"game_id": "game", "group_id": ""}, self.hash)
        value, hashed = api.Store(self.store.directory).load()
        self.assertEqual(value["preferences"]["overrides"]["game"], "group-b")
        self.store.update("cycle", {"game_id": "game", "group_id": ""}, hashed)
        self.assertEqual(self.store.load()[0]["preferences"]["overrides"]["game"], "group-a")

    def test_display_hidden_vs_disabled(self):
        self.value["preferences"]["display"] = False
        self.assertIsNotNone(self.choose()["asset_id"]); self.assertFalse(self.choose()["render"])
        self.value["preferences"]["enabled"] = False; self.assertIsNone(self.choose()["asset_id"])

    def test_visibility_does_not_disable_feature(self):
        self.value["preferences"]["visibility"]["overlay"] = {"details": False, "associations": False}
        self.assertTrue(self.choose()["render"])

    def test_state_optimistic_concurrency(self):
        self.store.update("visibility", {"details": True, "associations": False}, self.hash)
        with self.assertRaises(api.OverlayError):
            self.store.update("visibility", {"details": False, "associations": True}, self.hash)

    def test_before_copy_is_byte_identical(self):
        old = api.read(self.store.path)
        self.store.update("visibility", {"details": True, "associations": True}, self.hash)
        self.assertEqual(api.read(self.store.directory / ("overlay-before-" + self.hash + ".json")), old)

    def test_empty_store_does_not_create_directories(self):
        path = self.root / "untouched"; value, hashed = api.Store(path).load()
        self.assertFalse(path.exists()); self.assertEqual(hashed, "absent"); self.assertFalse(value["preferences"]["enabled"])

    def test_additive_import_retains_existing(self):
        other = copy.deepcopy(self.m); other["groups"].append({**copy.deepcopy(other["groups"][0]), "id": "group-c"})
        self.source.write_bytes(api.encode(other)); self.store.import_manifest(self.source, self.hash)
        self.assertEqual(len(self.store.load()[0]["manifest"]["groups"]), 3)

    def test_conflict_stop_keep_replace(self):
        self.m["groups"][0]["label"] = "Changed explicit label"; self.source.write_bytes(api.encode(self.m))
        with self.assertRaises(api.OverlayError): self.store.import_manifest(self.source, self.hash)
        self.assertEqual(self.store.load()[1], self.hash)
        self.store.import_manifest(self.source, self.hash, "keep"); _, hashed = self.store.load()
        self.assertEqual(self.store.load()[0]["manifest"]["groups"][0]["label"], "Fixture group a")
        self.store.import_manifest(self.source, hashed, "replace")
        self.assertEqual(self.store.load()[0]["manifest"]["groups"][0]["label"], "Changed explicit label")

    def test_missing_corrupt_changed_asset_refuses(self):
        path = self.store.directory / self.store.load()[0]["manifest"]["assets"][0]["path"]
        path.write_bytes(b"corrupt")
        with self.assertRaises(api.OverlayError): self.store.asset(self.store.load()[0]["manifest"]["assets"][0])
        path.unlink()
        with self.assertRaises(FileNotFoundError): self.store.asset(self.store.load()[0]["manifest"]["assets"][0])

    def test_missing_image_before_import(self):
        (self.root / "fixture.png").unlink()
        with self.assertRaises(FileNotFoundError): self.store.validate_import(self.source)

    def test_export_roundtrip(self):
        result = api.export_manifest(self.store, self.root / "export", self.hash)
        other = api.Store(self.root / "new-store"); other.import_manifest(result["path"], "absent")
        self.assertEqual(other.load()[0]["manifest"], self.store.load()[0]["manifest"])

    def test_no_export_overwrite(self):
        with self.assertRaises(api.OverlayError): api.export_manifest(self.store, self.root, self.hash)

    def test_relay_active_hash_foreground_and_expiry(self):
        result = self.choose(); result["foreground_exe"] = self.fg["exe"]; result["display_target"] = "studio"
        api.relay(self.store, result, self.root / "relay", now=100)
        text = (self.root / "relay/overlay-selection.ini").read_text()
        self.assertIn("ExpiresUnix = 101", text); self.assertIn("Active = 1", text); self.assertIn("Exe = C:", text)
        api.relay(self.store, {"render": False}, self.root / "relay", now=101)
        self.assertIn("Active = 0", (self.root / "relay/overlay-selection.ini").read_text())

    def test_payload_is_not_mutated(self):
        obj = {"game_id": "game", "layer": "BASIC", "context": "gameplay", "view": "Keys"}
        self.store.update("selection", obj, self.hash); self.assertIn("game_id", obj)

    def test_duplicate_nonfinite_deep_json_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'[' * 30 + b'0' + b']' * 30):
            with self.assertRaises(api.OverlayError): api.decode(raw)

    def test_invalid_contract_cases(self):
        cases = [lambda m: m.update(schema_version=2), lambda m: m.update(command="run"),
                 lambda m: m["keymaps"][0].update(joystick_drawn=True),
                 lambda m: m["keymaps"][0].update(hidden_positions=[]),
                 lambda m: m["keymaps"][0]["visible_positions"].remove(36),
                 lambda m: m["keymaps"][0]["visible_positions"].remove(37),
                 lambda m: m["keymaps"][0]["visible_positions"].remove(41),
                 lambda m: m["assets"][0].update(path="../evil.png"),
                 lambda m: m["assets"][0].update(profile_id="candidate-not-installed"),
                 lambda m: m["groups"][0].update(keymap_id="missing"),
                 lambda m: m["groups"][0]["asset_ids"].append("asset-keys"),
                 lambda m: m["associations"][0].update(executables=[]),
                 lambda m: m["associations"][0].update(executables=["*.exe"]),
                 lambda m: m["associations"][0].update(priority=True),
                 lambda m: m["associations"][0].update(default_group="missing"),
                 lambda m: m["groups"][0]["rendering"].update(opacity=0),
                 lambda m: m["groups"][0]["rendering"].update(size_value=float("inf"))]
        for index, change in enumerate(cases):
            with self.subTest(case=index):
                value = copy.deepcopy(self.m); change(value)
                with self.assertRaises(api.OverlayError): api.manifest(value)

    def test_geometry_all_modes_anchors_monitors_dpi(self):
        for mode in ("Pixels", "Screen width %", "Screen height %", "Original %"):
            for anchor in ("TopLeft", "TopRight", "Center", "BottomLeft", "BottomRight"):
                for scale in (1, 1.25, 1.5, 2):
                    r = copy.deepcopy(self.m["groups"][0]["rendering"]); r.update(size_mode=mode, anchor=anchor)
                    x, y, w, h = api.geometry(r, 800, 400, (-1920, 0, int(800 * scale), int(600 * scale)))
                    self.assertGreater(w, 0); self.assertGreater(h, 0); self.assertGreaterEqual(x, -1920)
                    self.assertLessEqual(x + w, -1920 + 800 * scale)

    def test_structured_cli_refuses_without_expected_hash(self):
        script = Path(__file__).resolve().parents[1] / "Game-Tool-Hub.py"
        result = subprocess.run([sys.executable, "-B", str(script), "overlay", "--directory", str(self.store.directory),
                                 "visibility", "--source", str(self.source)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2); self.assertIn("require", result.stdout)

    def test_cli_list_gui_store_contract_agreement(self):
        script = Path(__file__).resolve().parents[1] / "Game-Tool-Hub.py"
        result = subprocess.run([sys.executable, "-B", str(script), "overlay", "--directory", str(self.store.directory), "list"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["manifest"], self.store.load()[0]["manifest"])


class PanelTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from GameToolOverlayPanel import OverlayPanel
        self.root = tk.Tk(); self.root.withdraw(); self.addCleanup(self.root.destroy)
        self.root.update()
        self.temp = tempfile.TemporaryDirectory(prefix="OverlayUIFixture-"); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name); self.m, self.path = fixture(self.folder)
        self.renderer = mock.Mock()
        self.panel = OverlayPanel(self.root, self.folder / "private", foreground=lambda: None,
                                  renderer_factory=lambda *args: self.renderer)
        self.panel.follow_layer.set(False)  # Existing explicit/manual selection fixtures.
        self.addCleanup(self.panel.close)
        self.panel.store.import_manifest(self.path, "absent")
        self.panel.value, self.panel.fingerprint = self.panel.store.load(); self.panel.reload_choices()

    def test_selector_search_no_save(self):
        before = self.panel.store.load()[1]
        sel = self.panel.selectors["game"]; sel.variable.set("Long")
        self.assertEqual(len(sel.cget("values")), 2)  # match + explicit Add
        self.assertEqual(self.panel.store.load()[1], before)

    def test_selector_cancel_restores_id(self):
        sel = self.panel.selectors["game"]; sel.select("game"); sel.variable.set("query"); sel.cancel()
        self.assertEqual(sel.selected_id, "game"); self.assertIn("game", sel.variable.get())

    def test_unknown_enter_does_not_create(self):
        before = self.panel.store.load()[1]; sel = self.panel.selectors["game"]
        sel.variable.set("not-created"); sel.commit(); self.assertEqual(self.panel.store.load()[1], before)

    def test_explicit_keyboard_commit_saves_selection(self):
        sel = self.panel.selectors["layer"]; sel.variable.set("BASIC"); sel.commit()
        self.assertEqual(self.panel.store.load()[0]["preferences"]["selections"]["game"]["layer"], "BASIC")

    def test_view_visibility_reset_not_enablement(self):
        self.panel.save_visibility({"details": False, "associations": False})
        self.assertFalse(self.panel.value["preferences"]["enabled"])
        self.panel.visibility.reset(self.panel.save_visibility)
        self.assertTrue(self.panel.value["preferences"]["visibility"]["overlay"]["associations"])

    def test_start_stop_calls_owned_renderer_only(self):
        self.panel.enabled.set(True); self.panel.save_flags()
        self.assertIn("Foreground unavailable", self.panel.note.get())
        self.panel.enabled.set(False); self.panel.save_flags(); self.assertIn("stopped", self.panel.note.get())
        self.panel.close(); self.renderer.close.assert_called_once()

    def test_close_cancels_timer_and_is_idempotent(self):
        self.assertIsNotNone(self.panel.timer); self.panel.close(); self.panel.close()
        self.assertIsNone(self.panel.timer); self.renderer.close.assert_called_once()

    def test_peek_release_does_not_pin(self):
        self.panel.selectors["layer"].variable.set("BASIC"); self.panel.selectors["layer"].commit()
        self.panel.peek_down(); self.assertTrue(self.panel.peek_held)
        self.renderer.show.assert_called_once(); self.panel.peek_up(); self.assertFalse(self.panel.peek_held)

    def test_explore_is_explicit_pinned_snapshot(self):
        self.panel.selectors["layer"].variable.set("BASIC"); self.panel.selectors["layer"].commit()
        self.panel.explore(); self.assertTrue(self.renderer.show.call_args.kwargs["pinned"])
        self.assertIn("preview", self.renderer.show.call_args.args[0]["reason"])

    def test_missing_asset_clears_result_hides_no_stale_map(self):
        self.panel.enabled.set(True); self.panel.display.set(True); self.panel.save_flags()
        self.panel.selectors["layer"].variable.set("BASIC"); self.panel.selectors["layer"].commit()
        self.panel.foreground = lambda: {"exe": "Gameplay.exe", "at": __import__('time').monotonic(), "own": False}
        self.panel.tick(reschedule=False); self.assertIsNotNone(self.panel.result["asset_id"])
        asset = self.panel.value["manifest"]["assets"][0]; (self.panel.store.directory / asset["path"]).unlink()
        self.panel.tick(reschedule=False); self.assertIsNone(self.panel.result["asset_id"]); self.renderer.hide.assert_called()

    def test_narrow_long_labels_keyboard_scaling(self):
        for scale in (1, 1.25, 1.5, 2):
            self.root.tk.call("tk", "scaling", scale)
            self.root.geometry("760x600"); self.root.update_idletasks()
            for sel in self.panel.selectors.values():
                self.assertEqual(str(sel.cget("state")), "normal")
                self.assertTrue(sel.bind("<Return>")); self.assertTrue(sel.bind("<Escape>"))
                self.assertGreater(sel.winfo_reqwidth(), 50)
        from types import SimpleNamespace
        self.panel.reflow(SimpleNamespace(width=480))
        self.assertEqual({c.grid_info()["column"] for c in self.panel.top_controls}, {0})
        self.assertLessEqual(max(c.grid_info()["column"] for c in self.panel.action_buttons), 1)

    def test_explicit_add_game_and_cancel(self):
        from tkinter import simpledialog
        before = self.panel.store.load()[1]
        with mock.patch.object(simpledialog, "askstring", return_value=None): self.panel.add_entity("game")
        self.assertEqual(self.panel.store.load()[1], before)
        with mock.patch.object(simpledialog, "askstring", return_value="New fixture game"): self.panel.add_entity("game")
        games = self.panel.store.load()[0]["manifest"]["games"]
        self.assertEqual(len(games), 2); self.assertEqual(games[0]["id"], "game")

    def test_explicit_add_group_shares_assets_geometry(self):
        from tkinter import simpledialog
        original = self.panel.value["manifest"]["groups"][0]
        with mock.patch.object(simpledialog, "askstring", return_value="New shared fixture"): self.panel.add_entity("group")
        added = self.panel.store.load()[0]["manifest"]["groups"][-1]
        self.assertEqual(added["asset_ids"], original["asset_ids"]); self.assertEqual(added["rendering"], original["rendering"])
        self.assertNotEqual(added["id"], original["id"])

    def test_external_cli_state_reload_visible(self):
        value, hashed = self.panel.store.load()
        self.panel.store.update("display", {"enabled": True, "display": False, "display_target": "studio"}, hashed)
        self.panel.tick(reschedule=False)
        self.assertTrue(self.panel.enabled.get()); self.assertTrue(self.panel.studio_target.get())


@unittest.skipUnless(os.name == "nt", "Windows passive-render integration only")
class NativeRenderTests(unittest.TestCase):
    def test_supported_foreground_read_and_passive_noactivate(self):
        import ctypes
        import tkinter as tk
        from GameToolOverlayPanel import Renderer
        temp = tempfile.TemporaryDirectory(prefix="OverlayPassiveFixture-")
        root = tk.Tk(); root.withdraw(); root.update()
        renderer = None
        try:
            folder = Path(temp.name); value, source = fixture(folder)
            store = api.Store(folder / "private"); store.import_manifest(source, "absent")
            renderer = Renderer(root, store)
            user = ctypes.WinDLL("user32"); user.GetForegroundWindow.restype = ctypes.c_void_p
            user.GetParent.argtypes = [ctypes.c_void_p]; user.GetParent.restype = ctypes.c_void_p
            user.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
            before = user.GetForegroundWindow()
            renderer.show({"asset_id": "asset-combined", "group_id": "group-a"})
            root.update()
            hwnd = user.GetParent(renderer.passive.winfo_id()) or renderer.passive.winfo_id()
            style = user.GetWindowLongW(hwnd, -20)
            self.assertTrue(style & 0x08000000); self.assertTrue(style & 0x20)
            self.assertEqual(user.GetForegroundWindow(), before, "Foreground changed; no no-focus acceptance")
            self.assertIsNotNone(api.foreground_windows())
            renderer.hide(); self.assertIsNone(renderer.passive)
        finally:
            if renderer: renderer.close()
            root.destroy(); temp.cleanup()


if __name__ == "__main__":
    unittest.main()
