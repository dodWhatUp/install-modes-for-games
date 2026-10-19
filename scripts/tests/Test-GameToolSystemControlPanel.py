"""Real Tk interaction tests. Run under the accepted guest's virtual X server."""
from pathlib import Path
import json
import sys
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from GameToolSystemControlPanel import SystemControlPanel


class PanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            probe = tk.Tk(); probe.destroy()
        except tk.TclError:
            raise unittest.SkipTest("GUI acceptance requires an isolated virtual display.")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="control-ui-")
        self.path = Path(self.tmp.name)
        for name in ("context.example.json", "instructions.example.md", "detail.example.txt"):
            (self.path/name).write_bytes((SCRIPTS.parent/"examples/system-control"/name).read_bytes())
        self.root = tk.Tk(); self.root.geometry("900x760")
        self.panel = SystemControlPanel(self.root, context_path=self.path/"context.example.json")
        self.panel.pack(fill="both", expand=True); self.root.update()

    def tearDown(self):
        self.panel.close(); self.root.destroy(); self.tmp.cleanup()

    def draft(self, text):
        self.panel.draft.delete("1.0", "end"); self.panel.draft.insert("1.0", text)
        self.root.update(); self.panel.review_draft(); self.root.update()

    def test_selector_query_does_not_commit_and_escape_restores_choice(self):
        p = self.panel; p.selector.select("reader"); p.select_node("reader")
        p.selector.variable.set("no match"); self.root.update()
        self.assertEqual(p.selector.selected_id, "reader"); self.assertFalse(p.tree.get_children())
        p.selector.cancel(); self.root.update()
        self.assertEqual(p.selector.selected_id,"reader"); self.assertIn("reader",p.tree.get_children())

    def test_keyboard_selection_and_source_details(self):
        p=self.panel;p.selector.variable.set("reader");p.selector.commit();self.root.update()
        self.assertEqual(p.selector.selected_id,"reader")
        self.assertIn("instructions.example.md",p.details.get("1.0","end"))
        self.assertIn("not_observed",p.details.get("1.0","end"))

    def test_graph_visibility_preserves_data_and_draft(self):
        p=self.panel;p.draft.insert("1.0","Inspect only.");self.root.update()
        revision=p.view["revision"]
        p.show_graph.set(True);p.toggle_graph();self.root.update()
        self.assertTrue(p.graph_box.winfo_ismapped());self.assertTrue(p.canvas.find_all())
        p.show_graph.set(False);p.toggle_graph();self.root.update()
        self.assertEqual(p.view["revision"],revision);self.assertEqual(p.draft.get("1.0","end-1c"),"Inspect only.")

    def test_compare_requires_acceptance_and_keeps_original(self):
        p=self.panel;original="Answer in English.\nInspect the project. Do not install Codex."
        self.draft(original)
        self.assertIsNone(p.accepted_draft);self.assertEqual(p.draft.get("1.0","end-1c"),original)
        p.accept_button.invoke();self.root.update()
        self.assertEqual(p.accepted_draft,"Inspect the project. Do not install Codex.")
        self.assertEqual(p.draft.get("1.0","end-1c"),original)

    def test_edit_invalidates_old_candidate(self):
        self.draft("Answer in English.\nInspect the project.")
        p=self.panel;p.draft.insert("end"," Keep all details.");self.root.update()
        self.assertIsNone(p.result);self.assertTrue(p.accept_button.instate(["disabled"]))

    def test_source_drift_blocks_acceptance(self):
        self.draft("Answer in English.\nInspect the project.")
        p=self.panel;(self.path/"instructions.example.md").write_text("Changed",encoding="utf-8")
        p.accept_candidate();self.assertIsNone(p.accepted_draft)
        self.assertIn("changed",p.status.get())

    def test_browse_cancel_retains_draft_and_context(self):
        p=self.panel;p.draft.insert("1.0","Keep original.");self.root.update()
        before=p.context_path
        with patch("GameToolSystemControlPanel.filedialog.askopenfilename",return_value=""):
            p.choose_context()
        self.assertEqual(p.context_path,before);self.assertEqual(p.draft.get("1.0","end-1c"),"Keep original.")

    def test_missing_context_clears_stale_activity(self):
        p=self.panel;p.context_path=self.path/"missing.json";p.reload();self.root.update()
        self.assertIsNone(p.view);self.assertEqual(p.activity_output.get("1.0","end-1c"),"")
        self.assertTrue(p.accept_button.instate(["disabled"]))

    def test_no_store_detail_is_explicit_and_cleared_on_tab_change(self):
        p=self.panel;p.notebook.select(p.activity_tab);self.root.update();p.resource.set("detail-reference")
        p.read_detail();self.assertEqual(p.detail_output.get("1.0","end-1c"),"")
        p.detail_authorized.set(True);p.read_detail();self.assertIn("Authored detail",p.detail_output.get("1.0","end"))
        p.notebook.select(p.request_tab);self.root.update()
        self.assertEqual(p.detail_output.get("1.0","end-1c"),"");self.assertFalse(p.detail_authorized.get())

    def test_activity_filter_keeps_unknowns_and_can_clear_filter(self):
        p=self.panel;p.activity_filter.set("unknown");self.root.update()
        text=p.activity_output.get("1.0","end")
        self.assertIn("Example computer B",text);self.assertNotIn("Example computer A",text)
        p.activity_filter.set("");self.root.update()
        self.assertIn("Example computer A",p.activity_output.get("1.0","end"))

    def test_narrow_layout_long_labels_and_scaling(self):
        p=self.panel;self.root.geometry("420x760");self.root.tk.call("tk","scaling",1.8);self.root.update()
        for widget in (p.notebook,p.selector,p.tree):
            self.assertLessEqual(widget.winfo_rootx()+widget.winfo_width(),self.root.winfo_rootx()+self.root.winfo_width()+2)
        p.selector.set_choices([("long","A long label "*15)]);p.selector.select("long");self.root.update()
        self.assertEqual(p.selector.selected_id,"long")

    def test_clear_forgets_session_data_and_original_files_unchanged(self):
        original={f.name:f.read_bytes() for f in self.path.iterdir()}
        p=self.panel;p.clear();self.root.update()
        self.assertIsNone(p.context);self.assertIsNone(p.view);self.assertFalse(p.tree.get_children())
        self.assertEqual(original,{f.name:f.read_bytes() for f in self.path.iterdir()})

    def test_intended_outcome_scope_and_device_edits_invalidate_comparison(self):
        p=self.panel;p.intended_outcome.set("Read-only inspection")
        self.draft("Answer in English.\nInspect the project.")
        self.assertEqual(p.result["intended_outcome"],"Read-only inspection")
        p.device.set("other-device");self.root.update()
        self.assertIsNone(p.result);self.assertTrue(p.accept_button.instate(["disabled"]))

    def test_guidance_dialog_cancel_keeps_original_context(self):
        p=self.panel;before=p.context_path
        with patch("GameToolSystemControlPanel.filedialog.askdirectory",return_value=""):
            p.choose_global();p.choose_skills()
        self.assertEqual(p.context_path,before);self.assertFalse(p.skill_roots);self.assertIsNone(p.global_root)

    def test_report_cancel_and_existing_file_preserve_sources(self):
        p=self.panel;target=self.path/"existing.html";target.write_text("keep existing")
        with patch("GameToolSystemControlPanel.filedialog.asksaveasfilename",return_value=""):
            p.save_report()
        with patch("GameToolSystemControlPanel.filedialog.asksaveasfilename",return_value=str(target)):
            p.save_report()
        self.assertEqual(target.read_text(),"keep existing")
        target=self.path/"new-report.html"
        with patch("GameToolSystemControlPanel.filedialog.asksaveasfilename",return_value=str(target)):
            p.save_report()
        self.assertIn("<!doctype html>",target.read_text());self.assertNotIn("Authored detail",target.read_text())

    def test_attachment_bytes_are_released_on_filter_and_failed_read(self):
        import hashlib
        p=self.panel;raw=b"\x00\xffprivate binary";(self.path/"blob.bin").write_bytes(raw)
        p.context["sources"].append({"id":"blob","owner":"selected fixture","locator":"blob.bin","binding":"selected_project",
                                      "sha256":hashlib.sha256(raw).hexdigest(),"availability":"available"})
        p.context["resources"].append({"id":"blob-ref","source_id":"blob","relative":"blob.bin","access":"local_selected","content_type":"attachment"})
        p.notebook.select(p.activity_tab);self.root.update();p.resource.set("blob-ref");p.detail_authorized.set(True);p.read_detail()
        self.assertEqual(p.detail_bytes,raw)
        p.activity_filter.set("unknown");self.root.update();self.assertIsNone(p.detail_bytes)
        p.detail_authorized.set(True);p.read_detail();self.assertEqual(p.detail_bytes,raw)
        (self.path/"blob.bin").write_bytes(b"changed");p.read_detail();self.assertIsNone(p.detail_bytes)
        self.assertEqual(p.detail_output.get("1.0","end-1c"),"")

    def test_activity_controls_fit_narrow_view_and_keyboard_focus(self):
        p=self.panel;self.root.geometry("420x760");p.notebook.select(p.activity_tab);self.root.update()
        for widget in (p.resource_control,p.detail_output):
            self.assertLessEqual(widget.winfo_rootx()+widget.winfo_width(),self.root.winfo_rootx()+self.root.winfo_width()+2)
        p.resource_control.focus_force();self.root.update()
        self.assertEqual(self.root.focus_get(),p.resource_control)
        p.resource_control.event_generate("<Tab>");self.root.update()
        self.assertNotEqual(self.root.focus_get(),p.resource_control)


if __name__ == "__main__":
    unittest.main(verbosity=2)
