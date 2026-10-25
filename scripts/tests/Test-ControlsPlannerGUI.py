"""Run only inside the accepted isolated GUI lab."""
import importlib.util
from pathlib import Path
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location("builder_tests", Path(__file__).with_name("Test-KeymapBuilder.py"))
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
import GameToolControlsPlanner as api


@unittest.skipUnless(os.environ.get("DISPLAY"), "Requires isolated guest display")
class PlannerGUI(unittest.TestCase):
    def setUp(self):
        f.GuestEditor.setUp(self)
        self.planner = self.editor.controls_planner(); self.root_ui.update()

    def test_navigation_filter_save_and_live_data_isolation(self):
        p = self.planner; before, sha = self.library.store.load()
        self.assertEqual(len(p.tabs.tabs()), 3)
        self.assertTrue(p.table.get_children())
        p.search.set("nothing-matches"); self.root_ui.update(); self.assertFalse(p.table.get_children())
        p.search.set(""); p.filter.set("Changed"); p.refresh_rows(); self.assertFalse(p.table.get_children())
        p.filter.set("All"); p.refresh_rows(); p.review(); p.save()
        self.assertEqual(self.library.store.load()[1], sha)
        self.assertEqual(self.library.current("game"), self.doc)
        self.assertEqual(self.planner.library.load("game"), self.planner.workbook)

    def test_current_and_proposed_map_use_existing_four_view_renderer(self):
        for view in ("Keys", "Actions", "Combined", "ActionFirst"):
            self.editor.view.set(view); self.planner.map_preview(); self.root_ui.update()
        self.assertFalse(any(r["changed"] for r in api.preview(self.planner.workbook, self.doc)["rows"]))

    def test_builder_edits_and_saved_map_drift_refused(self):
        self.editor.document["title"] = "Another unsaved edit"
        with self.assertRaisesRegex(ValueError, "Builder draft changed"): self.planner.current()
        self.editor.document["title"] = self.doc["title"]
        changed = __import__("copy").deepcopy(self.doc); changed["title"] = "Concurrent disk edit"
        self.library.save_source(changed, self.keymap, self.saved)
        with self.assertRaisesRegex(ValueError, "Saved map changed"): self.planner.current()

    def test_keyboard_action_edit_and_compact_layout(self):
        p = self.planner; p.tabs.select(p.actions_tab)
        p.window.geometry("820x600"); self.root_ui.update()
        first = p.table.get_children()[0]; p.table.selection_set(first); p.table.focus(first)
        p.edit(); self.root_ui.update()
        self.assertTrue(p.table.winfo_ismapped())
        self.assertGreater(p.table.winfo_width(), 600)
        from tkinter import font
        heading_font = font.nametofont("TkHeadingFont", root=self.root_ui)
        self.assertLess(heading_font.measure(p.table.heading("priority", "text")), p.table.column("priority", "width") - 8)
        if os.environ.get("CONTROLS_SCREENSHOT"):
            import subprocess
            # Close only the owned editor dialog for a clear main workspace view.
            for child in p.window.winfo_children():
                if child.winfo_class() == "Toplevel": child.destroy()
            self.root_ui.update()
            subprocess.run(["import", "-window", str(p.window.winfo_id()), os.environ["CONTROLS_SCREENSHOT"]], check=True)

    def test_v2_import_projects_classifications_and_keeps_original_graph(self):
        spec=importlib.util.spec_from_file_location("workbook_fixture",Path(__file__).with_name("Test-ControlsWorkbook.py"))
        fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
        value=fixture.workbook(self.planner.workbook);path=self.root/"external-v2.json"
        path.write_bytes(__import__("GameToolKeymapDocument").encoded(value));_,registry=self.library.store.load()
        with mock.patch("tkinter.filedialog.askopenfilename",return_value=str(path)),mock.patch("tkinter.messagebox.askyesno",return_value=True):
            self.planner.import_response()
        self.assertEqual(self.planner.workbook["actions"][0]["urgency"],[5])
        self.assertEqual(self.planner.workbook["extensions"]["workbook_v2"]["original"],value)
        self.assertEqual(self.library.store.load()[1],registry)

    def test_review_preparation_does_not_apply_or_bypass_unknown_native_state(self):
        _,registry=self.library.store.load()
        with mock.patch("tkinter.messagebox.askyesno",return_value=True):self.planner.prepare_plan()
        self.assertIsNotNone(self.planner.prepared)
        self.assertIsNone(self.planner.prepared["game_plan"])
        with self.assertRaisesRegex(ValueError,"Native profile"):self.planner.load_candidate()
        self.assertEqual(self.library.store.load()[1],registry)

    def test_scoped_rule_editor_keeps_scope_and_leaves_other_records_unchanged(self):
        self.planner.rule_editor();self.root_ui.update()
        dialogs=[w for w in self.planner.window.winfo_children() if w.winfo_class()=="Toplevel"]
        dialog=dialogs[-1];entries=[w for w in dialog.winfo_children() if w.winfo_class()=="TEntry"]
        entries[1].insert(0,"4, 8");entries[2].insert(0,"Local fixture rule")
        check=next(w for w in dialog.winfo_children() if w.winfo_class()=="TCheckbutton");check.invoke()
        button=next(w for w in dialog.winfo_children() if w.winfo_class()=="TButton")
        with mock.patch("tkinter.messagebox.showerror",side_effect=AssertionError("Rule editor failed")):button.invoke()
        self.root_ui.update();rule=self.planner.workbook["extensions"]["rules"][0]
        self.assertEqual(rule["scope"],{"level":"game","target_ids":["game"]})
        self.assertEqual(rule["value"],[4,8]);self.assertFalse((self.planner.library.root/"shared-rules.json").exists())


if __name__ == "__main__": unittest.main()
