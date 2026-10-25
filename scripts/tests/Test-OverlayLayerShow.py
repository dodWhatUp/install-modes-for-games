"""Native-event to visibility relay, saved choices and real Tk editor contracts."""
import copy, importlib.util, json, sys, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as api
import GameToolOverlayLayerShow as feature
spec = importlib.util.spec_from_file_location("layer_fixtures", Path(__file__).with_name("Test-GameToolAzeronLayer.py"))
layers = importlib.util.module_from_spec(spec); spec.loader.exec_module(layers)


class Core(unittest.TestCase):
    emit = layers.LayerTests.emit

    def setUp(self):
        layers.LayerTests.setUp(self)
        keymap = self.value["manifest"]["keymaps"][0]
        base = next(l for l in keymap["layers"] if l["id"] == "BASIC")
        path = self.native / ("profile_" + base["profile_id"] + ".json")
        data = json.loads(path.read_bytes())
        data["inputs"] = [{"id": button, "types": ["24", "11", "11"], "isToggleOnHold": True, "layeringProfileId": self.ids[name]} for button, name in [(2,"NUMBERS"),(1,"MENUS"),(36,"TOOLS"),(28,"NAV"),(30,"SYMBOLS")]]
        path.write_bytes(api.encode(data)); base["profile_sha256"] = api.sha(path.read_bytes())
        self.value["preferences"]["display_target"] = "studio"
        self.store.write(self.value, self.store.load()[1])
        self.profiles = self.root / "native"
        self.rules = feature.choices(self.store, self.profiles)
        self.selected = next(r for r in self.rules.values() if r["layer"] == "NUMBERS")
        self.originals = {p: p.read_bytes() for p in self.native.glob("*.json")}
        self.registry = self.store.path.read_bytes()

    def select(self):
        return api.checked_selection(self.store, self.value, {"exe":"Gameplay.exe", "at":self.mono, "own":False}, now=self.mono, native=self.reader.snapshot())

    def fields(self):
        return feature.relay_fields(self.store, self.select(), self.profiles)

    def enable(self, rules=None):
        return feature.save(self.store, [self.selected] if rules is None else rules, feature.read(self.store.directory)[1], self.profiles)

    def test_only_actual_momentary_buttons_are_offered(self):
        self.assertEqual({r["button_id"] for r in self.rules.values()}, {1,2,28,30,36})
        self.assertNotIn("BASIC", {r["layer"] for r in self.rules.values()})
        base = self.native / ("profile_" + self.ids["BASIC"] + ".json")
        base.write_bytes(base.read_bytes() + b" ")
        self.assertEqual(feature.choices(self.store, self.profiles), {})

    def test_default_off_and_selected_hold_release_flow(self):
        self.emit("NUMBERS"); self.assertEqual(self.fields(), {"LayerShow":"0"})
        self.enable(); first = self.fields()
        self.assertEqual(first["LayerShow"], "1"); self.assertEqual(len(first["LayerHoldKey"]), 64)
        self.wall += 10; self.mono += 10; self.reader.poll(self.value["manifest"])
        self.assertEqual(self.fields(), first, "Quiet hold retains visibility, without timer/key replay")
        self.emit("BASIC"); self.assertEqual(self.fields(), {"LayerShow":"0"})
        self.wall += .1; self.emit("NUMBERS")
        self.assertNotEqual(self.fields()["LayerHoldKey"], first["LayerHoldKey"])
        self.assertEqual(self.store.path.read_bytes(), self.registry)
        self.assertEqual({p:p.read_bytes() for p in self.originals}, self.originals)

    def test_unselected_layers_and_normal_profile_switch_do_not_open(self):
        self.enable(); self.emit("MENUS"); self.assertEqual(self.fields()["LayerShow"], "0")
        self.emit("NUMBERS", message="Switch layer: " + self.ids["NUMBERS"])
        self.assertEqual(self.select()["layer"], "NUMBERS"); self.assertEqual(self.fields()["LayerShow"], "0")
        self.emit("NUMBERS"); self.assertEqual(self.fields()["LayerShow"], "1")

    def test_disable_and_native_unknown_stale_and_revision_changes_withdraw(self):
        self.enable(); self.emit("NUMBERS"); self.assertEqual(self.fields()["LayerShow"], "1")
        self.mono += 1; self.assertEqual(self.fields()["LayerShow"], "0")
        self.reader.poll(self.value["manifest"]); self.assertEqual(self.fields()["LayerShow"], "1")
        self.enable([]); self.assertEqual(self.fields()["LayerShow"], "0")
        self.enable(); self.identity = None; self.reader.poll(self.value["manifest"])
        self.assertEqual(self.fields()["LayerShow"], "0")

    def test_wrong_native_base_revision_refuses_auto_without_disabling_dedicated_route(self):
        self.enable(); self.emit("NUMBERS")
        path = self.native / ("profile_" + self.ids["BASIC"] + ".json"); path.write_bytes(path.read_bytes()+b" ")
        self.assertTrue(self.select()["render"]); self.assertEqual(self.fields()["LayerShow"], "0")

    def test_saved_choices_are_atomic_recoverable_and_stale_edit_is_refused(self):
        _, saved = self.enable()
        with self.assertRaises(ValueError): feature.save(self.store, [], None, self.profiles)
        self.enable([])
        recovery = self.store.directory / ("overlay-layer-show-before-" + api.sha(saved) + ".json")
        self.assertEqual(recovery.read_bytes(), saved)
        with self.assertRaises(ValueError): self.enable([{**self.selected, "button_id":19}])
        self.assertEqual(self.store.path.read_bytes(), self.registry)

    def test_malformed_optional_file_disables_auto_only(self):
        self.emit("NUMBERS")
        (self.store.directory/"overlay-layer-show.json").write_bytes(b'{"commands":[]}')
        self.assertTrue(self.select()["render"]); self.assertEqual(self.fields(), {"LayerShow":"0"})

    def test_relay_roundtrip_carries_guarded_auto_intent_and_never_a_key(self):
        self.enable(); self.emit("NUMBERS")
        with mock.patch.object(feature, "choices", return_value=self.rules):
            api.relay(self.store, self.select(), self.root/"relay", now=100)
        raw = (self.root/"relay/overlay-selection.ini").read_text()
        for item in ("LayerShow = 1", "LayerHoldKey = ", "ExpiresUnixMs = 101000", "Exe = gameplay.exe", "SHA256 = "):
            self.assertIn(item.lower(), raw.lower())
        self.assertNotIn("button_id", raw); self.assertNotIn("Send", raw)


class Editor(unittest.TestCase):
    def setUp(self):
        Core.setUp(self)
        import tkinter as tk
        self.tk = tk.Tk(); self.tk.withdraw(); self.addCleanup(self.tk.destroy)
        self.saved = mock.Mock(); self.editor = feature.LayerShowEditor(self.tk, self.store, self.saved, self.profiles)
        self.tk.update()

    def test_select_cancel_and_default_make_no_changes(self):
        self.assertTrue(all(not flag.get() for flag in self.editor.selected.values()))
        next(iter(self.editor.selected.values())).set(True); self.editor.window.destroy()
        self.assertFalse((self.store.directory/"overlay-layer-show.json").exists()); self.assertFalse(self.saved.called)

    def test_save_multiple_then_clear_keeps_registry_and_native_profiles(self):
        selected = list(self.editor.selected)[:2]
        for identity in selected: self.editor.selected[identity].set(True)
        self.editor.commit(); self.assertTrue(self.saved.called)
        self.assertEqual(len(feature.read(self.store.directory)[0]["rules"]), 2)
        editor = feature.LayerShowEditor(self.tk, self.store, profiles=self.profiles)
        for flag in editor.selected.values(): flag.set(False)
        editor.commit(); self.assertEqual(feature.read(self.store.directory)[0]["rules"], [])
        self.assertEqual(self.store.path.read_bytes(), self.registry)
        self.assertEqual({p:p.read_bytes() for p in self.originals}, self.originals)

    def test_concurrent_editor_save_preserves_later_selection(self):
        second = feature.LayerShowEditor(self.tk, self.store, profiles=self.profiles)
        next(iter(second.selected.values())).set(True); second.commit()
        self.editor.commit(); self.assertIn("changed", self.editor.message.get()); self.assertFalse(self.saved.called)

    def test_large_text_keeps_save_and_cancel_inside_the_window(self):
        self.editor.window.destroy(); self.tk.tk.call("tk", "scaling", 2.0)
        editor = feature.LayerShowEditor(self.tk, self.store, profiles=self.profiles)
        editor.window.geometry("500x430"); self.tk.update()
        bar = editor.window.winfo_children()[0].winfo_children()[-1]
        for button in bar.winfo_children():
            bottom = button.winfo_rooty() + button.winfo_height() - editor.window.winfo_rooty()
            self.assertLessEqual(bottom, editor.window.winfo_height())


if __name__ == "__main__": unittest.main()
