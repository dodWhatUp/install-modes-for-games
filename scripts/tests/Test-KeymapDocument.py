"""Portable display-map contracts. Synthetic fixtures; no native/game acceptance."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolKeymapDocument as maps
import GameToolOverlay as overlay

spec = importlib.util.spec_from_file_location("overlay_fixtures", Path(__file__).with_name("Test-GameToolOverlay.py"))
fixtures = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixtures)


def document():
    return {"schema_version": 1, "kind": "keymap_document", "id": "fixture-map", "game_id": "game",
        "keymap_id": "keymap", "keymap_revision": "f" * 64, "title": "Synthetic game map",
        "canvas": {"width": 1252, "height": 858},
        "buttons": [{"id": bid, "position": f"P{i}", "finger": "fixture", "x": 20 + i % 6 * 180,
            "y": 150 + i // 6 * 125, "width": 146, "height": 113, "guidance": "Synthetic geometry, not a hardware claim"}
            for i, bid in enumerate(sorted(overlay.R8_POSITIONS))],
        "maps": [{"layer": layer, "context": "gameplay", "cells": [{"button_id": bid, "output": "K",
            "action": "Known fixture action", "display_action": "Fixture action", "evidence": "user_label", "source": "Synthetic fixture"}
            for bid in sorted(overlay.R8_POSITIONS)]} for layer in ("BASIC", "MENUS")],
        "guidance": [{"id": "display-only", "text": "No input execution", "evidence": "contract", "source": "fixture"}],
        "presentation": {"background": "opaque", "width_percent": 35}}


class DocumentTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.library = maps.Library(self.root / "data")
        manifest, source = fixtures.fixture(self.root)
        manifest["keymaps"][0]["revision"] = "f" * 64
        source.write_bytes(overlay.encode(manifest))
        self.library.store.import_manifest(source, "absent")
        self.document = document(); self.saved = self.library.save(self.document)

    def test_history_keeps_original_and_stale_save_refuses(self):
        change = copy.deepcopy(self.document); change["maps"][0]["cells"][0]["action"] = "New label"
        self.library.save(change, self.saved)
        history = self.library.root / "history/game" / (self.saved + ".json")
        self.assertEqual(maps.load(history), self.document)
        with self.assertRaisesRegex(ValueError, "Map changed"):
            self.library.save(self.document, self.saved)
        self.assertEqual(self.library.current("game"), change)

    def test_opaque_and_buttons_alpha(self):
        from PIL import Image
        path = self.root / "render.png"
        maps.render(self.document, self.document["maps"][0], path)
        with Image.open(path) as im:
            self.assertEqual(im.getchannel("A").getextrema(), (255, 255))
        change = copy.deepcopy(self.document); change["presentation"]["background"] = "buttons"
        maps.render(change, change["maps"][0], path)
        with Image.open(path) as im:
            self.assertEqual(im.getpixel((0, 0))[3], 0)
            self.assertEqual(im.getpixel((80, 248))[3], 255)
            self.assertEqual(im.getpixel((180, 250))[3], 0)

    def test_apply_changes_display_and_preserves_other_assets(self):
        before, oldhash = self.library.store.load()
        oldkeys = next(a for a in before["manifest"]["assets"] if a["view"] == "Keys")
        receipt = self.library.apply(self.document, oldhash)
        self.assertFalse(receipt["native_changes"])
        after, _ = self.library.store.load()
        self.assertTrue((self.library.store.directory / oldkeys["path"]).is_file())
        self.assertEqual(self.library.store.asset(oldkeys)[1]["width"], 16)
        self.assertEqual(after["manifest"]["keymaps"], before["manifest"]["keymaps"])
        for g in after["manifest"]["groups"]:
            self.assertEqual((g["rendering"]["anchor"], g["rendering"]["opacity"], g["rendering"]["size_value"]), ("Center", 100, 35))
        self.assertTrue((self.library.store.directory / ("overlay-before-" + oldhash + ".json")).is_file())

    def test_changed_outputs_fail_before_registry_write(self):
        _, oldhash = self.library.store.load()
        changed = copy.deepcopy(self.document); changed["maps"][0]["cells"][0]["output"] = "UnexpectedKey"
        with self.assertRaisesRegex(ValueError, "cannot change emitted keys"):
            self.library.apply(changed, oldhash)
        self.assertEqual(self.library.store.load()[1], oldhash)

    def test_changed_native_revision_and_stale_store_refused(self):
        _, oldhash = self.library.store.load()
        changed = copy.deepcopy(self.document); changed["keymap_revision"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "revision changed"):
            self.library.apply(changed, oldhash)
        with self.assertRaisesRegex(ValueError, "registry changed"):
            self.library.apply(self.document, "a" * 64)
        self.assertEqual(self.library.store.load()[1], oldhash)

    def test_reserved_duplicate_and_out_of_bounds_positions_rejected(self):
        for field, value in (("id", 19), ("id", self.document["buttons"][1]["id"]), ("x", 1252)):
            changed = copy.deepcopy(self.document); changed["buttons"][0][field] = value
            with self.assertRaises(ValueError): maps.validate(changed)

    def test_untrusted_data_has_no_execution_fields(self):
        changed = copy.deepcopy(self.document); changed["command"] = "anything"
        with self.assertRaises(ValueError): maps.validate(changed)
        with self.assertRaises(ValueError): self.library.path("../escape")
        changed = copy.deepcopy(self.document); changed["guidance"][0]["text"] = "An external instruction remains text"
        self.assertEqual(maps.validate(changed), changed)

    def test_document_size_and_width_limits(self):
        changed = copy.deepcopy(self.document); changed["schema_version"] = True
        with self.assertRaises(ValueError): maps.validate(changed)
        changed = copy.deepcopy(self.document); changed["presentation"]["background"] = []
        with self.assertRaises(ValueError): maps.validate(changed)
        for value in (0, 19, 71, "35"):
            changed = copy.deepcopy(self.document); changed["presentation"]["width_percent"] = value
            with self.assertRaises(ValueError): maps.validate(changed)
        changed = copy.deepcopy(self.document); changed["maps"][0]["cells"][0]["action"] = "x" * 241
        with self.assertRaises(ValueError): maps.validate(changed)


if __name__ == "__main__":
    unittest.main()
