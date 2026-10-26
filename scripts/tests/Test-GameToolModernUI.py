"""Offline presentation tests. No AHK, input dispatch, games or providers."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
import unittest
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolWorkspace as workspace_api
import GameToolAppearance as appearance_api
import GameToolModernUI as modern_api
from GameToolCompactUI import FlowToolbar


class DesignContract(unittest.TestCase):
    def test_text_contrast(self):
        c = modern_api.COLORS
        for ink, surface in (("ink", "background"), ("muted", "background"),
                             ("accent", "surface"), ("rail_text", "rail"),
                             ("rail_muted", "rail"), ("rail_text", "selected")):
            self.assertGreaterEqual(modern_api.contrast(c[ink], c[surface]), 4.5)

    def test_unique_task_domains(self):
        self.assertEqual(len(modern_api.CATEGORIES), 4)
        self.assertIn("Modern", appearance_api.MODES)
        self.assertEqual(len(workspace_api.DEFAULT_FEATURES), 13)
        self.assertEqual(len(workspace_api.DEFAULT_GOALS), 8)


class ModernUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk(); root.withdraw(); root.destroy()
        except tk.TclError as error:
            raise unittest.SkipTest(str(error))

    def setUp(self):
        self.private = tempfile.TemporaryDirectory()
        self.root = tk.Tk(); self.root.withdraw()
        self.root.geometry("1360x880")
        self.root.report_callback_exception = lambda *args: self.fail(str(args))
        self.status = tk.StringVar(self.root, "Stopped")
        self.header = ttk.Frame(self.root); self.header.pack(fill="x")
        ttk.Label(self.header, text="GameTools").pack(side="left")
        self.w = workspace_api.Workspace(self.root, self.status)
        self.w.frame.pack(fill="both", expand=True)
        self.tabs = ttk.Notebook(self.w.content); self.tabs.pack(fill="both", expand=True)
        self.pages = {}
        self.operations = []
        for record in self.w.registry.features:
            page = ttk.Frame(self.tabs)
            self.tabs.add(page, text=record["route"])
            ttk.Button(page, text="Never invoke", command=lambda: self.operations.append("called")).pack()
            self.pages[record["route"]] = page
        self.entry = ttk.Entry(self.pages["comparison"]); self.entry.pack()
        self.entry.insert(0, "unsaved fixture")
        self.text = tk.Text(self.pages["comparison"]); self.text.pack()
        self.text.insert("1.0", "original fixture text")
        self.original_colors = self.text.cget("background"), self.text.cget("foreground")
        self.actions = FlowToolbar(self.pages["comparison"]); self.actions.pack(fill="x")
        for number in range(6):
            self.actions.add("Fixture action " + str(number), lambda n=number: self.operations.append(n))
        self.w.attach(self.tabs, self.pages)
        self.path = Path(self.private.name)/"ui-preferences.json"
        self.a = appearance_api.Appearance(self.root, self.header, self.w, self.status, self.path, "fixture")
        self.root.update()
        self.a.change("Modern", persist=False)
        self.root.update()
        self.m = self.w.modern

    def tearDown(self):
        self.a.preview_only = True
        self.a.close(); self.w.close()
        self.root.update_idletasks(); self.root.destroy()
        self.private.cleanup()

    def test_home_has_four_task_groups_and_eight_routes(self):
        self.assertTrue(self.w.home_visible)
        self.assertEqual(len(self.m.cards), 4)
        self.assertEqual(len(self.m.links), 8)
        self.assertEqual(self.operations, [])

    def test_compact_top_keeps_search_and_reclaims_editor_space(self):
        self.root.deiconify()
        self.w.route('page.profiles')
        self.root.update()
        self.assertFalse(self.header.winfo_ismapped())
        self.assertTrue(self.w.selector.winfo_ismapped())
        self.assertTrue(self.w.view_menu.master.winfo_ismapped())
        self.assertLess(self.w.content.winfo_rooty()-self.root.winfo_rooty(), 150)
        self.assertEqual(self.operations, [])

    def test_profiles_explanation_never_expands_pinned_header(self):
        self.root.deiconify()
        self.w.route('page.profiles')
        self.w.show_details.set(False);self.w._visibility_changed();self.root.update()
        height=self.w.breadcrumb.winfo_height()
        self.w.show_details.set(True);self.w._visibility_changed();self.root.update()
        self.assertEqual(self.w.breadcrumb.winfo_height(),height)
        self.assertEqual(self.m.page_title.cget('text'),'Game profiles')
        self.assertFalse(self.w.scope_widget.winfo_ismapped())
        self.assertFalse(self.m.detail.winfo_ismapped())
        self.assertFalse(self.m.detail_button.winfo_ismapped())
        self.assertTrue(self.w.show_details.get())
        self.assertEqual(self.operations,[])

    def test_profiles_short_heading_stays_on_one_row_at_narrow_scaled_widths(self):
        self.w.route('page.profiles');self.root.deiconify()
        for scaling in (1.0,1.8):
            self.root.tk.call('tk','scaling',scaling)
            for width in (720,1000,1300):
                self.root.geometry(f'{width}x700');self.root.update()
                self.assertEqual(int(self.m.page_title.grid_info()['row']),0)
                self.assertLess(self.w.breadcrumb.winfo_height(),75)
                self.assertTrue(self.w.selector.winfo_ismapped())
                self.assertEqual(self.operations,[])

    def test_profiles_header_switch_preserves_other_page_details_and_modes(self):
        for mode in ('Modern','Classic','Professional','Compact','Modern'):
            self.a.change(mode,persist=False)
            # Each layout retains its own existing saved detail preference.
            self.w.show_details.set(True);self.w._visibility_changed()
            self.w.route('page.profiles');self.root.update()
            self.assertFalse(self.w.scope_widget.winfo_ismapped())
            self.w.route('page.comparison');self.root.update()
            self.assertTrue(self.w.show_details.get())
            self.assertEqual(self.w.scope_label.get(),self.w.registry.get('page.comparison')['scope'])
            self.assertEqual(self.entry.get(),'unsaved fixture')
        self.root.deiconify();self.root.update()
        self.assertTrue(self.w.scope_widget.winfo_ismapped())
        self.assertTrue(self.m.detail.winfo_ismapped())
        self.assertTrue(self.m.detail_button.winfo_ismapped())
        self.assertEqual(self.operations,[])

    def test_expanded_controls_are_reachable_without_changing_edits_or_settings(self):
        self.root.deiconify()
        self.w.route('page.comparison')
        self.root.update()
        compact = self.a.compact_header
        before = self.path.read_bytes() if self.path.exists() else None
        compact.expanded.set(True); compact.refresh(); self.root.update()
        self.assertTrue(self.a.selector.winfo_ismapped())
        compact.expanded.set(False); compact.refresh(); self.root.update()
        self.assertFalse(self.header.winfo_ismapped())
        self.assertEqual(self.entry.get(), 'unsaved fixture')
        self.assertEqual(self.w.current_route, 'comparison')
        self.assertEqual(self.path.read_bytes() if self.path.exists() else None, before)
        self.assertEqual(self.operations, [])

    def test_new_interface_keeps_global_view_menu_with_expanded_controls(self):
        compact=self.a.compact_header;original=compact.interface;bar=ttk.Frame(self.root)
        try:
            compact.interface=SimpleNamespace(mode='New',bar=bar)
            compact.expanded.set(True);compact.refresh();self.root.deiconify();self.root.update()
            self.assertTrue(compact.new_bar.winfo_ismapped())
            self.assertTrue(compact.new_menu_button.winfo_ismapped())
            self.assertTrue(compact.new_layout_button.winfo_ismapped())
            self.assertTrue(compact.new_tools_button.winfo_ismapped())
            self.assertEqual(self.operations,[])
        finally:
            compact.interface=original;bar.destroy()

    def test_compact_menu_keeps_layout_and_identification_owners(self):
        compact = self.a.compact_header
        labels = [self.w.view_menu.entrycget(i, 'label') for i in range(self.w.view_menu.index('end')+1)
                  if self.w.view_menu.type(i) != 'separator']
        self.assertNotIn('Layout', labels)
        self.assertNotIn('Identify UI', labels)
        self.assertEqual(len(labels),7)
        self.assertEqual([compact.tools_menu.entrycget(i,'label') for i in range(compact.tools_menu.index('end')+1)
                          if compact.tools_menu.type(i)!='separator'],['Browse by','Identify UI','Hide window · reopen from taskbar','Close application'])
        self.assertIn('Show expanded app controls', labels)
        self.assertIn('Show field icons', labels)
        target = next(i for i in range(compact.layout_menu.index('end')+1)
                      if compact.layout_menu.entrycget(i, 'label') == 'Compact')
        self.w.route('page.comparison')
        compact.layout_menu.invoke(target); self.root.update()
        self.assertEqual(self.a.mode.get(), 'Compact')
        self.assertEqual(self.w.current_route, 'comparison')
        self.assertEqual(self.entry.get(), 'unsaved fixture')
        self.assertEqual(self.operations, [])

    def test_three_header_menus_open_without_changing_work_or_preferences(self):
        compact=self.a.compact_header
        self.root.deiconify();self.w.route('page.comparison');self.root.update()
        before=self.path.read_bytes() if self.path.exists() else None
        view=self.w.export_view();selection=self.tabs.select()
        for menu in (compact.menu,compact.layout_menu,compact.tools_menu):
            menu.post(20,20);self.root.update();self.assertTrue(menu.winfo_ismapped())
            menu.unpost();self.root.update()
        self.assertEqual(self.w.export_view(),view)
        self.assertEqual(self.tabs.select(),selection)
        self.assertEqual(self.entry.get(),'unsaved fixture')
        self.assertEqual(self.path.read_bytes() if self.path.exists() else None,before)
        self.assertEqual(self.operations,[])

    def test_shorter_search_and_all_three_menus_fit_resized_header(self):
        compact=self.a.compact_header
        self.root.deiconify();self.w.route('page.comparison');self.root.update()
        search=self.w.selector;self.w.query.set('report');search.icursor(2)
        for width in (1360,1000,720,620):
            self.root.geometry(f'{width}x740');self.root.update()
            self.assertIs(self.w.selector,search)
            self.assertEqual(int(search.cget('width')),28)
            self.assertEqual(search.index('insert'),2)
            self.assertEqual(self.w.query.get(),'report')
            for button in (self.w.view_menu.master,compact.layout_button,compact.tools_button):
                self.assertTrue(button.winfo_ismapped())
                self.assertLessEqual(button.winfo_x()+button.winfo_width(),self.w.toolbar.winfo_width())
            if width==1360:self.assertLess(search.winfo_width(),width*.45)
            if width<880:
                self.assertFalse(self.w.navigation_button.winfo_ismapped())
                self.assertGreater(search.winfo_width(),150)
            self.assertEqual(bool(compact.window_controls.winfo_ismapped()),width>=950)
        self.assertEqual(self.w.current_route,'comparison')
        self.assertEqual(self.operations,[])

    def test_browse_menu_keeps_existing_navigation_owner_and_draft(self):
        self.w.route('page.comparison');self.root.update()
        target=next(i for i in range(self.w.browse_menu.index('end')+1)
                    if self.w.browse_menu.entrycget(i,'label')=='Goals')
        self.w.browse_menu.invoke(target);self.root.update()
        self.assertEqual(self.w.view.get(),'Goals')
        self.assertEqual(self.w.current_route,'comparison')
        self.assertEqual(self.entry.get(),'unsaved fixture')
        self.assertEqual(self.operations,[])

    def test_categories_are_view_only_and_all_features_remain_reachable(self):
        before = self.tabs.select()
        count = 0
        for i, button in enumerate(self.m.domain_buttons):
            button.invoke(); self.root.update()
            count += len(self.m.links)
            self.assertEqual(self.tabs.select(), before)
            self.assertEqual(self.operations, [])
            self.assertEqual(self.m.domain, i)
        self.assertEqual(count, 13)

    def test_task_opens_existing_page_without_operation(self):
        children = self.pages["comparison"].winfo_children()
        self.m.links[0].invoke(); self.root.update()
        self.assertFalse(self.w.home_visible)
        self.assertEqual(self.tabs.select(), str(self.pages["comparison"]))
        self.assertEqual(self.pages["comparison"].winfo_children(), children)
        self.assertEqual(self.entry.get(), "unsaved fixture")
        self.assertEqual(self.operations, [])

    def test_search_on_home_filters_without_navigating(self):
        before = self.tabs.select()
        self.w.query.set("saved-result"); self.root.update()
        self.assertEqual(len(self.m.cards), 1)
        self.assertEqual(self.tabs.select(), before)
        self.assertTrue(self.w.home_visible)
        self.w._commit_selector(); self.root.update()
        self.assertFalse(self.w.home_visible)
        self.assertEqual(self.tabs.select(), str(self.pages["comparison"]))

    def test_search_on_page_keeps_editor_until_explicit_commit(self):
        self.w.route("page.comparison"); self.root.update()
        self.w.query.set("updates"); self.root.update()
        self.assertFalse(self.w.home_visible)
        self.assertEqual(self.tabs.select(), str(self.pages["comparison"]))
        self.assertEqual(self.entry.get(), "unsaved fixture")
        self.w._commit_selector(); self.root.update()
        self.assertEqual(self.tabs.select(), str(self.pages["updates"]))

    def test_empty_search_and_escape_keep_underlying_page(self):
        before = self.tabs.select()
        self.w.query.set("NO-SUCH-TASK"); self.root.update()
        self.assertEqual(len(self.m.cards), 0)
        self.assertEqual(self.m.empty.winfo_manager(), "grid")
        self.w._cancel_search(); self.root.update()
        self.assertEqual(len(self.m.cards), 4)
        self.assertEqual(self.tabs.select(), before)

    def test_all_layouts_keep_profiles_editors_commands_and_text(self):
        ids = self.tabs.tabs()
        for mode in ("Classic", "Modern", "Compact", "Modern", "Professional", "Modern"):
            self.a.change(mode, persist=False); self.root.update()
            self.assertEqual(self.tabs.tabs(), ids)
            self.assertEqual(self.entry.get(), "unsaved fixture")
            self.assertEqual(self.text.get("1.0", "end-1c"), "original fixture text")
            self.assertEqual(self.operations, [])

    def test_raw_display_colors_restore_exactly(self):
        self.assertEqual(self.text.cget("background"), modern_api.COLORS["surface"])
        self.a.change("Classic", persist=False); self.root.update()
        self.assertEqual((self.text.cget("background"), self.text.cget("foreground")), self.original_colors)

    def test_secondary_action_disclosure_keeps_callbacks_and_disabled_states(self):
        self.assertTrue(self.actions.disclosure)
        self.actions.buttons[2].state(["disabled"])
        self.actions._refresh_more()
        self.assertEqual(self.actions.more_menu.entrycget(0, "state"), "disabled")
        self.actions.more_menu.invoke(0)
        self.assertEqual(self.operations, [])
        self.actions.more_menu.invoke(1)
        self.assertEqual(self.operations, [3])
        self.a.change("Compact", persist=False)
        self.assertFalse(self.actions.disclosure)
        self.assertEqual(len(self.actions.buttons), 6)

    def test_details_is_disclosure_not_feature_enable(self):
        self.w.route("page.sessions"); self.root.update()
        self.m.detail_button.invoke(); self.root.update()
        self.assertEqual(self.m.detail.winfo_manager(), "pack")
        self.m.detail_button.invoke()
        self.assertEqual(self.m.detail.winfo_manager(), "")
        self.assertEqual(self.operations, [])

    def test_reflow_uses_font_width_and_keeps_every_link(self):
        self.m.reflow(1050); self.assertEqual(self.m.columns, 2)
        self.m.reflow(480); self.assertEqual(self.m.columns, 1)
        self.assertEqual(len(self.m.links), 8)
        for i, card in enumerate(self.m.cards):
            self.assertEqual(int(card.grid_info()["row"]), i)

    def test_page_owned_wrapping_is_not_overridden_by_generic_layout(self):
        labels = [self.m.title, self.m.subtitle, self.m.note, self.m.empty,
                  self.m.page_title, self.m.detail,
                  *(label for card in self.m.cards for label in card.game_tools_labels)]
        before = {str(label): label.master.bind("<Configure>") for label in labels}
        appearance_api.wrap_labels(self.m.body)
        for label in labels:
            self.assertTrue(label.game_tools_wrap_managed)
            self.assertEqual(label.master.bind("<Configure>"), before[str(label)])

    def test_wrap_is_idempotent_without_changing_profile_or_text(self):
        label = self.m.title
        modern_api.ModernSurface._set_wrap(label, 390)
        with mock.patch.object(label, "configure", wraps=label.configure) as configure:
            modern_api.ModernSurface._set_wrap(label, 390)
            configure.assert_not_called()
        self.assertFalse(self.path.exists())
        self.assertEqual(self.entry.get(), "unsaved fixture")

    def test_narrow_layout_collapses_rail_without_changing_preference(self):
        self.w._resize(SimpleNamespace(widget=self.w.frame, width=620))
        self.assertNotIn(str(self.w.sidebar), self.w.splitter.panes())
        self.assertTrue(self.w.show_navigation.get())
        self.w.toggle_navigation()
        self.assertIn(str(self.w.sidebar), self.w.splitter.panes())
    def test_saved_page_header_reflows_when_home_was_never_mapped(self):
        self.w.route('page.profiles');self.w.show_details.set(True);self.w._visibility_changed()
        self.root.geometry('1000x700');self.root.deiconify();self.root.update()
        self.assertFalse(self.m.dashboard.winfo_ismapped())
        self.assertGreater(int(self.m.page_title.cget('wraplength')),400)
        self.assertGreater(self.w.content.winfo_height(),self.w.frame.winfo_height()*.55)
        self.assertLess(self.w.breadcrumb.winfo_height(),180)
        self.assertEqual(self.entry.get(),'unsaved fixture');self.assertEqual(self.operations,[])
    def test_active_page_resizes_at_large_text_without_revisiting_home(self):
        self.w.route('page.profiles');self.w.show_details.set(True);self.w._visibility_changed()
        self.root.tk.call('tk','scaling',1.8);self.root.deiconify()
        for width,height in ((1300,850),(720,650),(1000,700)):
            self.root.geometry(f'{width}x{height}');self.root.update()
            self.assertGreater(self.w.content.winfo_height(),self.w.frame.winfo_height()*.45)
            self.assertLess(self.w.breadcrumb.winfo_height(),220)
            self.assertEqual(self.tabs.select(),str(self.pages['profiles']))
            self.assertEqual(self.entry.get(),'unsaved fixture')

    def test_feedback_on_tasks_text_and_sections_has_stable_ids(self):
        first = {label: identifier for _, identifier, label in self.m.identifiers}
        self.m.refresh()
        second = {label: identifier for _, identifier, label in self.m.identifiers}
        self.assertEqual(first, second)
        self.a.set_identification(True, 15)
        target = self.m.links[0]
        badge = self.a.markers.records[str(target)][1]
        badge.invoke()
        self.assertEqual(self.root.clipboard_get(), "UI-007.goal-compare-saved")
        self.assertTrue(self.w.home_visible)
        self.assertEqual(self.operations, [])

    def test_repeated_search_does_not_leak_retired_markers(self):
        original = len(self.a.markers.records)
        for _ in range(15):
            self.w.query.set("reports"); self.w.query.set("")
        self.assertEqual(len(self.a.markers.records), original)

    def test_home_can_focus_search_even_when_studio_selected_behind_it(self):
        self.w.route("page.studio"); self.root.update()
        self.m.show_home()
        with mock.patch.object(self.w.selector, "focus_set") as focus:
            self.assertEqual(self.w._focus_search(), "break")
            focus.assert_called_once()

    def test_external_tab_navigation_reveals_original_page(self):
        self.tabs.select(self.pages["sessions"]); self.root.update()
        self.assertFalse(self.w.home_visible)
        self.assertIn("sessions", self.w.current_route)
        self.m.show_home(); self.w.reveal_selected_page()
        self.assertFalse(self.w.home_visible)

    def test_preview_does_not_replace_saved_compact_layout(self):
        self.a.change("Compact")
        raw = self.path.read_bytes()
        self.a.preview("Modern")
        self.a.save()
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(json.loads(raw)["mode"], "Compact")
        self.a.change("Modern")
        value = json.loads(self.path.read_bytes())
        self.assertEqual(value["mode"], "Modern")
        self.assertIn("Compact", value["views"])

    def test_home_blocks_hidden_tools_shortcuts(self):
        test_path = Path(__file__).with_name("Test-GameToolWorkspace.py")
        spec = importlib.util.spec_from_file_location("shortcut_fixture", test_path)
        fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
        actions = {k: mock.Mock() for k in "rocasi"}
        handler, _ = fixture.actual_hub_shortcut_handler(self.root, self.w, self.tabs, shortcuts=actions)
        with mock.patch.object(self.root, "focus_get", return_value=self.m.home_button):
            for key in actions:
                self.assertEqual(handler(SimpleNamespace(keycode=ord(key.upper()), keysym=key)), "break")
        for callback in actions.values():
            callback.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
