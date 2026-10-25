"""Withdrawn Tk fixtures: presentation only, with inert existing pages."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("workspace_test_module", ROOT / "GameToolWorkspace.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


def actual_hub_shortcut_handler(root, workspace, notebook=None, selected="tool-page", shortcuts=None):
    """Compile the actual two authored functions, not a mirrored test handler.

    No gui(), mainloop, discovery or panel constructors are executed. The Hub's
    closure dependencies are inert fixtures except the supplied Tk workspace.
    """
    tree=ast.parse((ROOT/"Game-Tool-Hub.py").read_text(encoding="utf-8-sig"))
    shortcut=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="shortcut_key")
    gui=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="gui")
    handler=next(node for node in gui.body if isinstance(node,ast.FunctionDef) and node.name=="handle_shortcut")
    tabs=notebook or mock.Mock()
    if notebook is None: tabs.select.return_value=selected
    environment=dict(root=root,workspace=workspace,tabs=tabs,os=SimpleNamespace(name="nt"),
        tk=tk,ttk=ttk,mod_integration=None,data_tab=None,unified_panel=None,overlay_tab="overlay-page",session_tab="session-page",
        comparison_tab="comparison-page",catalog_tab="catalog-page",overlay_panel=None,session_panel=None,
        comparison_panel=None,catalog_panel=None,status=mock.Mock(),shortcuts=shortcuts or {})
    module=ast.Module(body=[shortcut,handler],type_ignores=[])
    exec(compile(module,str(ROOT/"Game-Tool-Hub.py"),"exec"),environment)
    return environment["handle_shortcut"],environment


class RegistryTests(unittest.TestCase):
    def test_ids_and_domains(self):
        registry = api.FeatureRegistry()
        self.assertEqual(len(registry.features), 13)
        self.assertEqual(registry.get('page.profiles')['route'],'profiles')
        self.assertEqual(len(registry.goals), 8)
        self.assertEqual(set(r["domain"] for r in registry.features), set(api.DOMAINS))

    def test_returned_records_do_not_mutate_registry(self):
        registry = api.FeatureRegistry()
        registry.get("page.comparison")["title"] = "changed"
        self.assertEqual(registry.get("page.comparison")["title"], "Saved-result comparison")

    def test_multi_term_filter_and_empty(self):
        registry = api.FeatureRegistry()
        self.assertEqual([r["id"] for r in registry.records("Goals", "graphics dynamic")], ["goal.graphics-plan"])
        self.assertEqual(registry.records("Features", "no-such-text"), [])

    def test_commands_unknown_domains_duplicate_and_invalid_ids_rejected(self):
        good = dict(api.DEFAULT_FEATURES[0])
        for changes in ({"command": "launch"}, {"domain": "Other"}, {"id": "../escape"}, {"route": "CAPTURE"}):
            bad = {**good, **changes}
            with self.assertRaises(ValueError):
                api.FeatureRegistry([bad], [])
        with self.assertRaises(ValueError):
            api.FeatureRegistry([good], [good])

    def test_scope_words_distinguish_offline_and_runtime(self):
        registry = api.FeatureRegistry()
        self.assertIn("Offline", registry.get("goal.prepare-stability")["scope"])
        self.assertIn("blocked", registry.get("goal.graphics-plan")["summary"])
        self.assertIn("Off", registry.get("page.studio")["scope"])


class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
            root.withdraw()
            root.destroy()
        except tk.TclError as error:
            raise unittest.SkipTest("Tk unavailable: " + str(error))

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.status = tk.StringVar(master=self.root, value="Provider stays stopped")
        self.workspace = api.Workspace(self.root, self.status)
        self.workspace.frame.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(self.workspace.content)
        self.notebook.pack(fill="both", expand=True)
        self.pages = {}
        self.operations = []
        for route in ("tools", "comparison", "sessions", "catalog", "overlays", "reports", "studio", "updates"):
            page = ttk.Frame(self.notebook)
            self.notebook.add(page, text=route.title())
            ttk.Button(page, text="Operation must stay idle", command=lambda: self.operations.append("called")).pack()
            self.pages[route] = page
        self.workspace.attach(self.notebook, self.pages)
        self.root.update()

    def tearDown(self):
        self.workspace.close()
        self.root.destroy()

    def test_search_does_not_navigate_or_operate(self):
        before = self.notebook.select()
        self.workspace.query.set("compare saved")
        self.root.update()
        self.assertEqual(self.notebook.select(), before)
        self.assertEqual(set(self.workspace._rows), {"goal.compare-saved"})
        self.assertEqual(self.operations, [])
        self.assertEqual(self.status.get(), "Provider stays stopped")

    def test_explicit_commit_navigates_only(self):
        self.workspace.query.set("compare saved")
        self.workspace._commit_selector()
        self.root.update()
        self.assertEqual(self.notebook.select(), str(self.pages["comparison"]))
        self.assertIn("Compare saved results", self.workspace.active_label.get())
        self.assertEqual(self.operations, [])

    def test_escape_cancels_without_changing_page(self):
        self.workspace.route("goal.prepare-stability")
        before = self.notebook.select()
        self.workspace.query.set("graphics")
        self.workspace._cancel_search()
        self.root.update()
        self.assertEqual(self.workspace.query.get(), "")
        self.assertEqual(self.notebook.select(), before)
        self.assertEqual(self.workspace.current_route, "sessions")

    def test_unknown_and_missing_routes_keep_page(self):
        before = self.notebook.select()
        self.assertFalse(self.workspace.route("not-a-route"))
        self.assertFalse(self.workspace.route("goal.portable-data"))
        self.assertEqual(self.notebook.select(), before)
        self.assertIn("Unavailable", self.workspace.result_label.get())

    def test_ambiguous_commit_keeps_page(self):
        before = self.notebook.select()
        self.workspace.query.set("")
        self.workspace._commit_selector()
        self.assertEqual(self.notebook.select(), before)
        self.assertIn("Choose one", self.workspace.result_label.get())

    def test_external_tab_selection_updates_route_and_breadcrumb(self):
        self.workspace.route("goal.compare-saved")
        self.root.update()
        self.notebook.select(self.pages["sessions"])
        self.root.update()
        self.assertEqual(self.workspace.current_route, "sessions")
        self.assertIn("Diagnose & stability", self.workspace.active_label.get())

    def test_view_switch_preserves_panel_widgets_and_route(self):
        children = self.pages["comparison"].winfo_children()
        self.workspace.route("goal.compare-saved")
        self.workspace.set_view("Features")
        self.root.update()
        self.assertEqual(self.notebook.select(), str(self.pages["comparison"]))
        self.assertEqual(self.pages["comparison"].winfo_children(), children)
        self.assertEqual(self.operations, [])

    def test_original_tabs_accessible_and_extension_kept(self):
        extra = ttk.Frame(self.notebook)
        self.notebook.add(extra, text="Future page")
        self.workspace.set_view("Original tabs")
        self.assertEqual(len(self.workspace._rows), len(self.notebook.tabs()))
        record = next(r for r in self.workspace._rows.values() if r["title"] == "Future page")
        self.assertTrue(self.workspace.route(record["id"]))
        self.assertEqual(self.notebook.select(), str(extra))
        self.assertEqual(self.notebook.cget("style"), "TNotebook")

    def test_tree_selection_is_explicit_navigation(self):
        self.workspace.tree.selection_set("goal.keymap-display")
        self.workspace._tree_selected()
        self.root.update()
        self.assertEqual(self.notebook.select(), str(self.pages["overlays"]))
        self.assertEqual(self.operations, [])

    def test_disabled_existing_page_never_navigates(self):
        before = self.notebook.select()
        self.notebook.tab(self.pages["comparison"], state="disabled")
        self.assertFalse(self.workspace.route("goal.compare-saved"))
        self.assertEqual(self.notebook.select(), before)

    def test_details_visibility_is_not_feature_enablement(self):
        self.workspace.route("goal.input-pictures")
        self.workspace.show_details.set(True)
        self.workspace._visibility_changed()
        self.assertEqual(self.workspace.details_box.winfo_manager(), "grid")
        self.workspace.show_details.set(False)
        self.workspace._visibility_changed()
        self.assertEqual(self.workspace.details_box.winfo_manager(), "")
        self.assertEqual(self.notebook.select(), str(self.pages["studio"]))
        self.assertEqual(self.operations, [])

    def test_view_roundtrip_is_presentation_only(self):
        self.workspace.restore_view(dict(schema=1, view="Features", show_details=True,
                                         show_navigation=False, show_original_tabs=True))
        saved = self.workspace.export_view()
        before = self.notebook.select()
        self.workspace.reset_view()
        self.workspace.restore_view(saved)
        self.assertEqual(self.workspace.export_view(), saved)
        self.assertEqual(self.notebook.select(), before)
        self.assertEqual(self.operations, [])

    def test_invalid_restore_keeps_view(self):
        before = self.workspace.export_view()
        with self.assertRaises(ValueError):
            self.workspace.restore_view(dict(schema=2, view="Goals"))
        self.assertEqual(self.workspace.export_view(), before)

    def test_ctrl_k_does_not_intercept_studio(self):
        self.workspace.route("goal.input-pictures")
        self.assertIsNone(self.workspace._focus_search())
        self.assertEqual(self.notebook.select(), str(self.pages["studio"]))

    def test_workspace_search_focus_is_presentation_only(self):
        before=self.notebook.select()
        with mock.patch.object(self.root,"focus_get",return_value=self.workspace.tree), \
                mock.patch.object(self.root,"grab_current",return_value=None), \
                mock.patch.object(self.workspace.selector,"focus_set") as focus, \
                mock.patch.object(self.workspace.selector,"selection_range") as selection:
            self.assertEqual(self.workspace._focus_search(),"break")
            focus.assert_called_once()
            selection.assert_called_once_with(0,"end")
        self.assertEqual(self.notebook.select(),before)
        self.assertEqual(self.operations,[])

    def test_workspace_modal_and_other_toplevel_do_not_steal_focus(self):
        other=mock.Mock(); other.winfo_toplevel.return_value=object()
        for focused,modal in ((self.workspace.tree,object()),(other,None)):
            with self.subTest(modal=modal is not None),mock.patch.object(self.root,"focus_get",return_value=focused), \
                    mock.patch.object(self.root,"grab_current",return_value=modal), \
                    mock.patch.object(self.workspace.selector,"focus_set") as focus:
                self.assertIsNone(self.workspace._focus_search())
                focus.assert_not_called()
        self.assertEqual(self.operations,[])

    def test_hub_windows_physical_ctrl_k_survives_hebrew_keysym(self):
        handler,environment=actual_hub_shortcut_handler(self.root,self.workspace,self.notebook)
        self.assertEqual(environment["shortcut_key"](75,"כ",True),"k")
        self.assertEqual(environment["shortcut_key"](75,"כ",False),"כ")
        event=SimpleNamespace(keycode=75,keysym="כ")
        before=self.notebook.select()
        with mock.patch.object(self.root,"focus_get",return_value=self.workspace.tree), \
                mock.patch.object(self.root,"grab_current",return_value=None), \
                mock.patch.object(self.workspace.selector,"focus_set") as focus:
            self.assertEqual(handler(event),"break")
            focus.assert_called_once()
        self.assertEqual(self.notebook.select(),before)
        self.assertEqual(self.operations,[])

    def test_hub_ctrl_k_none_native_modal_and_other_window_guards(self):
        handler,_=actual_hub_shortcut_handler(self.root,self.workspace,self.notebook)
        other=mock.Mock(); other.winfo_toplevel.return_value=object()
        event=SimpleNamespace(keycode=75,keysym="כ")
        for focused,modal in ((None,None),(other,None),(self.workspace.tree,object())):
            with self.subTest(focus_none=focused is None,modal=modal is not None), \
                    mock.patch.object(self.root,"focus_get",return_value=focused), \
                    mock.patch.object(self.root,"grab_current",return_value=modal), \
                    mock.patch.object(self.workspace,"_focus_search") as dispatch:
                self.assertIsNone(handler(event))
                dispatch.assert_not_called()
        self.workspace.route("goal.input-pictures")
        with mock.patch.object(self.root,"focus_get",return_value=self.workspace.tree), \
                mock.patch.object(self.root,"grab_current",return_value=None), \
                mock.patch.object(self.workspace.selector,"focus_set") as focus:
            self.assertIsNone(handler(event))
            focus.assert_not_called()
        self.assertEqual(self.operations,[])

    def test_hub_original_ctrl_1_to_8_routes_are_retained(self):
        actions={str(n):mock.Mock() for n in range(1,9)}
        handler,_=actual_hub_shortcut_handler(self.root,self.workspace,shortcuts=actions)
        with mock.patch.object(self.root,"focus_get",return_value=self.workspace.tree), \
                mock.patch.object(self.root,"grab_current",return_value=None):
            for n in range(1,9):
                self.assertEqual(handler(SimpleNamespace(keycode=48+n,keysym=str(n))),"break")
                actions[str(n)].assert_called_once()
        self.assertEqual(self.operations,[])

    def test_hub_native_text_select_all_and_copy_are_not_replaced(self):
        actions={"a":mock.Mock(),"c":mock.Mock()}
        handler,_=actual_hub_shortcut_handler(self.root,self.workspace,shortcuts=actions)
        for editor in (ttk.Entry(self.root),ttk.Combobox(self.root),tk.Text(self.root)):
            try:
                with mock.patch.object(self.root,"focus_get",return_value=editor), \
                        mock.patch.object(self.root,"grab_current",return_value=None):
                    for key in ("a","c"):
                        self.assertIsNone(handler(SimpleNamespace(keycode=ord(key.upper()),keysym=key)))
            finally:
                editor.destroy()
        actions["a"].assert_not_called(); actions["c"].assert_not_called()
        self.assertEqual(self.operations,[])

    def test_keyboard_bindings_local_and_cleanup(self):
        self.assertTrue(self.root.bind("<Control-k>"))
        self.assertTrue(self.workspace.selector.bind("<Escape>"))
        self.assertTrue(self.workspace.selector.bind("<Return>"))
        self.workspace.close()
        self.assertFalse(self.root.bind("<Control-k>"))
        self.workspace.close()  # Host cleanup is safe to repeat.

    def test_narrow_resize_keeps_readable_wrap(self):
        class Event:
            widget = self.workspace.frame
            width = 760
        self.workspace._resize(Event())
        self.assertGreaterEqual(int(self.workspace.scope_widget.cget("wraplength")), 500)
        self.assertEqual(self.operations, [])

    def test_compact_titles_keep_full_active_label(self):
        self.assertEqual(self.workspace.tree.item("goal.graphics-plan", "text"), "Plan graphics comparison")
        self.workspace.route("goal.graphics-plan")
        self.assertIn("Plan graphics comparison · read-only", self.workspace.active_label.get())
        self.assertEqual(self.workspace.horizontal_scroll.winfo_manager(), "grid")

    def test_unavailable_status_is_visible_prefix_and_scrollable(self):
        self.assertTrue(self.workspace.tree.item("goal.portable-data", "text").startswith("Unavailable · "))
        self.assertFalse(self.workspace.sidebar.grid_propagate())
        self.assertEqual(self.workspace.tree.column("#0", "stretch"), 0)
        self.assertTrue(self.workspace.tree.cget("xscrollcommand"))

    def test_sidebar_fits_normal_labels_at_current_font_scale(self):
        self.assertLessEqual(int(self.workspace.sidebar.cget("width")),290)
        self.assertTrue(self.workspace.tree.cget("xscrollcommand"))
        self.assertIn("goal.input-pictures",self.workspace._rows)

    def test_attach_validates_existing_widgets(self):
        other = api.Workspace(self.root)
        try:
            with self.assertRaises(ValueError):
                other.attach(self.notebook, {"outside": ".not-a-page"})
        finally:
            other.close()

    def test_sidebar_toggle_preserves_widgets_draft_route_and_operations(self):
        draft = tk.StringVar(self.root, value="unsaved working value")
        entry = ttk.Entry(self.pages["comparison"], textvariable=draft)
        entry.pack()
        self.workspace.route("goal.compare-saved")
        panels = self.notebook.tabs()
        self.workspace.toggle_navigation()
        self.assertNotIn(str(self.workspace.sidebar), self.workspace.splitter.panes())
        self.assertEqual(self.workspace.navigation_button.cget("text"), "Show sidebar")
        self.workspace.toggle_navigation()
        self.assertIn(str(self.workspace.sidebar), self.workspace.splitter.panes())
        self.assertEqual(self.notebook.tabs(), panels)
        self.assertTrue(entry.winfo_exists())
        self.assertEqual(draft.get(), "unsaved working value")
        self.assertEqual(self.workspace.current_route, "comparison")
        self.assertEqual(self.operations, [])

    def test_explicit_show_works_after_automatic_collapse(self):
        self.workspace._resize(SimpleNamespace(widget=self.workspace.frame, width=640))
        self.assertNotIn(str(self.workspace.sidebar), self.workspace.splitter.panes())
        self.assertTrue(self.workspace.show_navigation.get())
        self.workspace.navigation_button.invoke()
        self.assertIn(str(self.workspace.sidebar), self.workspace.splitter.panes())
        self.assertTrue(self.workspace.show_navigation.get())
        self.workspace.navigation_button.invoke()
        self.assertFalse(self.workspace.show_navigation.get())
        self.workspace._resize(SimpleNamespace(widget=self.workspace.frame, width=1400))
        self.assertNotIn(str(self.workspace.sidebar), self.workspace.splitter.panes())

    def test_sidebar_width_roundtrip_and_legacy_preference(self):
        self.workspace.set_sidebar_width(170)
        saved = self.workspace.export_view()
        self.assertEqual(saved["sidebar_width"], 170)
        self.workspace.reset_view()
        self.workspace.restore_view(saved)
        self.assertEqual(self.workspace.sidebar_width, 170)
        saved.pop("sidebar_width")
        self.workspace.restore_view(saved)
        self.assertEqual(self.workspace.sidebar_width, api.SIDEBAR_DEFAULT)

    def test_invalid_width_restore_is_atomic(self):
        before = self.workspace.export_view()
        for width in (True, 149, 521, "256", 170.5):
            with self.subTest(width=width), self.assertRaises(ValueError):
                self.workspace.restore_view(dict(before, view="Features", sidebar_width=width))
            self.assertEqual(self.workspace.export_view(), before)

    def test_narrow_toolbar_reflows_without_recreating_search(self):
        search = self.workspace.selector
        for width, row in ((760, 1), (1300, 0), (640, 1)):
            self.workspace._resize(SimpleNamespace(widget=self.workspace.frame, width=width))
            self.assertEqual(int(search.grid_info()["row"]), row)
            self.assertIs(self.workspace.selector, search)
            self.assertEqual(self.workspace.view_menu.master.grid_info()["row"], row)

    def test_resize_and_filter_do_not_overwrite_preferred_width(self):
        self.workspace.set_sidebar_width(310)
        self.workspace.query.set("graphics")
        self.workspace._resize(SimpleNamespace(widget=self.workspace.frame, width=750))
        self.root.update_idletasks()
        self.assertEqual(self.workspace.export_view()["sidebar_width"], 310)
        self.assertEqual(self.operations, [])

    def test_hover_uses_full_public_route_title_and_stays_local(self):
        self.workspace._tip_row = "goal.graphics-plan"
        with mock.patch.object(self.workspace.tree, "winfo_ismapped", return_value=True):
            self.workspace._show_route_tip("goal.graphics-plan")
        self.assertIsNotNone(self.workspace._tip)
        label = self.workspace._tip.winfo_children()[0]
        self.assertIn("Plan graphics comparison · read-only", label.cget("text"))
        self.assertEqual(self.operations, [])
        self.workspace._hide_route_tip()
        self.assertIsNone(self.workspace._tip)
        self.assertIsNone(self.workspace._tip_row)

    def test_stale_or_hidden_hover_is_not_shown(self):
        self.workspace._tip_row = "goal.graphics-plan"
        self.workspace._show_route_tip("goal.keymap-display")
        self.assertIsNone(self.workspace._tip)
        self.workspace._show_route_tip("goal.graphics-plan")
        self.assertIsNone(self.workspace._tip)

    def test_sash_records_width_and_clamps_excessive_drag(self):
        for width, expected in ((170,170),(70,150),(700,520)):
            with mock.patch.object(self.workspace.splitter,"sashpos",return_value=width):
                self.workspace._sash_released(SimpleNamespace(x=width,y=20))
            self.assertEqual(self.workspace.sidebar_width, expected)
        self.assertEqual(self.operations, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
