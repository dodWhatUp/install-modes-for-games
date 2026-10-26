"""Guest-only Tk tests. No native devices, game state or host input."""
from pathlib import Path
import copy
import os
import sys
import tempfile
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolControllerRoutingUI as ui


SNAPSHOT = {"devices": [{"id": "physical-private-digest", "label": "Vader 5 Pro", "kind": "physical", "present": True, "eligible_primary": True},
                         {"id": "virtual-private-digest", "label": "Xbox output", "kind": "virtual", "present": True, "eligible_primary": True}],
            "relationships": [], "xinput": [{"index": 0, "present": True}, {"index": 1, "present": True}],
            "warnings": ["Physical-to-virtual correlation remains unverified."]}


class ControllerGUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = tk.Tk()
        self.root.geometry("920x740")
        self.addCleanup(self.root.destroy)
        self.native = Mock()
        self.inventory = Mock()
        profiles = Mock()
        profiles.load.return_value = ({"profiles": [{"id": "native-profile", "name": "Vader baseline", "provider": "rewasd"}]}, "pin")
        profiles.games.return_value = {"doom": "DOOM: The Dark Ages", "shadow": "Shadow of War"}
        self.panel = ui.ControllersPanel(self.root, self.temp.name, profiles=profiles, open_native=self.native,
                                        inventory=self.inventory, auto_refresh=False)
        self.addCleanup(self.panel.close)
        self.root.update()

    def choose(self):
        self.panel.set_snapshot(copy.deepcopy(SNAPSHOT))
        self.panel.controller.select("physical-private-digest")
        self.panel.preview()

    def test_open_and_filtering_cannot_save_or_apply(self):
        self.choose()
        self.panel.controller.focus_force()
        self.panel.controller.event_generate("<Button-1>", x=18, y=8)
        self.root.update()
        popup = self.panel.controller.game_tools_editable_list
        self.assertTrue(popup.visible)
        self.panel.controller.delete(0, "end")
        self.panel.controller.insert(0, "Vader")
        self.root.update()
        self.assertTrue(popup.visible)
        self.assertIn("Vader 5 Pro", self.panel.controller.cget("values")[0])
        self.assertFalse(self.panel.store.root.exists())
        self.inventory.snapshot.assert_not_called()
        self.native.assert_not_called()
        self.panel.controller.event_generate("<Escape>")
        self.root.update()
        self.assertFalse(popup.visible)

    def test_private_machine_ids_are_not_choice_labels(self):
        self.choose()
        self.assertFalse(any("private-digest" in str(x) for x in self.panel.controller.cget("values")))

    def test_explicit_save_and_native_review_are_separate(self):
        self.choose()
        self.panel.native.select("native-profile")
        self.panel.save()
        self.assertEqual(len(self.panel.store.load()[0]["preferences"]), 1)
        self.native.assert_not_called()
        self.panel.native_controls()
        self.native.assert_called_once_with("native-profile")

    def test_game_scope_is_searchable_and_scope_changes_clear_acceptance(self):
        self.choose()
        self.panel.scope.set("game")
        self.panel.scope_changed()
        self.panel.scope_choice.select("doom")
        self.panel.accepted.set(True)
        self.panel.save()
        row = self.panel.store.load()[0]["preferences"][0]
        self.assertEqual(row["scope_value"], "doom")
        self.assertEqual(row["evidence"]["state"], "user-reported")
        self.panel.route.set(ui.api.ROUTE_LABELS["native"])
        self.panel.edited()
        self.assertFalse(self.panel.accepted.get())

    def test_automatic_display_never_opens_native_controls(self):
        self.choose()
        self.panel.automatic.set(True)
        self.panel.save()
        before = self.panel.store.load()[1]
        self.assertEqual(self.panel.observe_game("doom")["state"], "preferred")
        self.assertIn("unverified", self.panel.match_text.get())
        self.assertEqual(self.panel.store.load()[1], before)
        self.native.assert_not_called()

    def test_cancel_add_scope_does_not_create_or_save(self):
        self.panel.scope.set("group")
        self.panel.scope_changed()
        with patch.object(ui.simpledialog, "askstring", return_value=None):
            self.panel.add_scope()
        self.assertEqual(self.panel.scope_choice.records, {})
        self.assertFalse(self.panel.store.root.exists())

    def test_stale_or_metadata_only_endpoint_cannot_be_saved(self):
        self.choose()
        self.panel.snapshot["devices"][0]["present"] = None
        self.panel.save()
        self.assertIn("no longer", self.panel.feedback.get())
        self.assertFalse(self.panel.store.root.exists())

    def test_missing_saved_controller_is_diagnosed_and_not_auto_applied(self):
        self.choose()
        self.panel.automatic.set(True)
        self.panel.save()
        self.panel.set_snapshot({"devices": [], "xinput": [], "relationships": [], "warnings": []})
        self.assertIn("missing", self.panel.feedback.get() if "missing" in self.panel.feedback.get() else self.panel.details_text.get().lower())
        self.panel.observe_game("doom")
        self.assertIn("absent", self.panel.match_text.get())
        self.native.assert_not_called()

    def test_narrow_scaled_content_keeps_main_controls_reachable(self):
        self.choose()
        self.root.geometry("720x640")
        self.root.tk.call("tk", "scaling", 1.65)
        self.root.update()
        self.assertGreater(self.panel.controller.winfo_width(), 150)
        self.assertLessEqual(self.panel.controller.winfo_rootx() + self.panel.controller.winfo_width(),
                             self.panel.scroll.body.winfo_rootx() + self.panel.scroll.body.winfo_width() + 2)
        self.assertIs(self.panel.heading.master, self.panel.scroll.body)
        if os.environ.get("CONTROLLERS_SCREENSHOT"):
            import subprocess
            subprocess.run(["import", "-window", str(self.root.winfo_id()), os.environ["CONTROLLERS_SCREENSHOT"]], check=True)


if __name__ == "__main__":
    unittest.main()
