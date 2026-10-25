"""Withdrawn test-owned Tk component tests; no desktop input or launches."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True


SOURCE = Path(__file__).resolve().parents[1] / "GameToolCompactUI.py"
sys.path.insert(0,str(SOURCE.parent))
spec = importlib.util.spec_from_file_location("compact_ui_fixture", SOURCE)
UI = importlib.util.module_from_spec(spec); spec.loader.exec_module(UI)


class ScrollableWorkspace(unittest.TestCase):
    def setUp(self):
        self.root = UI.tk.Tk(); self.root.withdraw()
        self.frame = UI.ScrollableFrame(self.root); self.frame.pack(fill="both", expand=True)
        self.outside = UI.ttk.Label(self.root, text="Outside this workspace")
        self.outside.pack()

    def tearDown(self):
        self.frame.close(); self.root.update_idletasks(); self.root.destroy()

    def event(self, widget, delta):
        return SimpleNamespace(widget=widget, delta=delta)

    def test_initial_structure_and_owned_root_binding(self):
        self.assertIs(self.frame.root, self.root)
        self.assertIs(self.frame.body.master, self.frame.canvas)
        self.assertIs(self.frame.canvas.master, self.frame)
        self.assertTrue(self.frame.binding)
        self.assertIn(self.frame.binding, self.root.bind("<MouseWheel>"))
        self.assertEqual(self.frame.canvas.itemcget(self.frame.item, "anchor"), "nw")
        self.assertEqual(str(self.frame.scrollbar.cget("orient")), "vertical")

    def test_canvas_configure_sets_body_width_narrow_and_wide(self):
        for width in (220, 540, 1000):
            with self.subTest(width=width):
                self.frame.canvas.event_generate("<Configure>", width=width, height=150)
                self.assertEqual(int(float(self.frame.canvas.itemcget(self.frame.item, "width"))), width)
        self.assertFalse(self.root.winfo_viewable())

    def test_body_configuration_updates_scrollregion_to_exact_bbox(self):
        for i in range(25):
            UI.ttk.Label(self.frame.body, text="A readable long workspace line " + str(i)).grid(row=i, sticky="w")
        self.root.update_idletasks()
        self.frame.body.event_generate("<Configure>")
        region = tuple(int(float(x)) for x in self.frame.canvas.cget("scrollregion").split())
        self.assertEqual(region, self.frame.canvas.bbox("all"))
        self.assertGreater(region[3] - region[1], 200)
        self.assertFalse(self.root.winfo_viewable())

    def test_wheel_on_body_and_canvas_honors_delta_magnitude(self):
        with patch.object(self.frame.canvas, "yview_scroll") as scroll:
            self.assertEqual(self.frame.wheel(self.event(self.frame.body, 120)), "break")
            scroll.assert_called_once_with(-3, "units")
            scroll.reset_mock()
            self.assertEqual(self.frame.wheel(self.event(self.frame.canvas, -240)), "break")
            scroll.assert_called_once_with(6, "units")

    def test_descendant_label_entry_button_wheel_is_owned(self):
        nested = UI.ttk.Frame(self.frame.body)
        widgets = (UI.ttk.Label(nested, text="label"), UI.ttk.Entry(nested), UI.ttk.Button(nested, text="button"))
        with patch.object(self.frame.canvas, "yview_scroll") as scroll:
            for widget in widgets:
                with self.subTest(widget=type(widget).__name__):
                    self.assertEqual(self.frame.wheel(self.event(widget, -120)), "break")
            self.assertEqual(scroll.call_count, len(widgets))

    def test_direct_text_and_treeview_keep_native_scrolling(self):
        text = UI.tk.Text(self.frame.body)
        tree = UI.ttk.Treeview(self.frame.body)
        with patch.object(self.frame.canvas, "yview_scroll") as scroll:
            self.assertIsNone(self.frame.wheel(self.event(text, 120)))
            self.assertIsNone(self.frame.wheel(self.event(tree, -120)))
            scroll.assert_not_called()

    def test_zero_delta_never_scrolls_or_consumes_event(self):
        child = UI.ttk.Entry(self.frame.body)
        with patch.object(self.frame.canvas, "yview_scroll") as scroll:
            for widget in (child, self.frame.body, self.frame.canvas):
                self.assertIsNone(self.frame.wheel(self.event(widget, 0)))
            scroll.assert_not_called()

    def test_outside_widget_and_root_not_intercepted(self):
        with patch.object(self.frame.canvas, "yview_scroll") as scroll:
            self.assertIsNone(self.frame.wheel(self.event(self.outside, 120)))
            self.assertIsNone(self.frame.wheel(self.event(self.root, 120)))
            scroll.assert_not_called()

    def test_similarly_named_sibling_not_descendant(self):
        # Body is named !frame; !frame2 shares the textual prefix but is not a
        # descendant. The separator boundary must prevent interception.
        sibling = UI.ttk.Frame(self.frame.canvas)
        outside = UI.ttk.Label(sibling, text="Sibling outside body")
        self.assertTrue(str(sibling).startswith(str(self.frame.body)))
        with patch.object(self.frame.canvas, "yview_scroll") as scroll:
            self.assertIsNone(self.frame.wheel(self.event(outside, -120)))
            scroll.assert_not_called()

    def test_two_separate_workspaces_do_not_scroll_one_another(self):
        other = UI.ScrollableFrame(self.root)
        try:
            other_label = UI.ttk.Label(other.body, text="Other workspace")
            with patch.object(self.frame.canvas, "yview_scroll") as first, patch.object(other.canvas, "yview_scroll") as second:
                self.assertIsNone(self.frame.wheel(self.event(other_label, -120)))
                first.assert_not_called()
                self.assertEqual(other.wheel(self.event(other_label, -120)), "break")
                second.assert_called_once_with(3, "units")
        finally:
            other.close()

    def test_nested_inner_workspace_scroll_is_not_stolen_by_outer(self):
        inner = UI.ScrollableFrame(self.frame.body)
        try:
            inner_label = UI.ttk.Label(inner.body, text="Inner workspace")
            inner_text = UI.tk.Text(inner.body)
            with patch.object(self.frame.canvas, "yview_scroll") as outer_scroll, patch.object(inner.canvas, "yview_scroll") as inner_scroll:
                self.assertIsNone(self.frame.wheel(self.event(inner_label, -120)))
                self.assertEqual(inner.wheel(self.event(inner_label, -120)), "break")
                inner_scroll.assert_called_once_with(3, "units"); outer_scroll.assert_not_called()
                inner_scroll.reset_mock()
                self.assertIsNone(self.frame.wheel(self.event(inner_text, 120)))
                self.assertIsNone(inner.wheel(self.event(inner_text, 120)))
                inner_scroll.assert_not_called(); outer_scroll.assert_not_called()
        finally:
            inner.close()

    def test_after_close_wheel_does_not_act_even_when_directly_called(self):
        child = UI.ttk.Label(self.frame.body, text="Former child")
        self.frame.close()
        with patch.object(self.frame.canvas, "yview_scroll") as scroll:
            for widget in (child, self.frame.body, self.frame.canvas):
                self.assertIsNone(self.frame.wheel(self.event(widget, -120)))
            scroll.assert_not_called()

    def test_close_removes_only_own_binding_and_is_idempotent(self):
        extra = self.root.bind("<MouseWheel>", lambda _: None, add="+")
        own = self.frame.binding
        self.assertIn(extra, self.root.bind("<MouseWheel>"))
        self.frame.close()
        self.assertIsNone(self.frame.binding)
        script = self.root.bind("<MouseWheel>")
        self.assertNotIn(own, script); self.assertIn(extra, script)
        self.frame.close(); self.assertEqual(script, self.root.bind("<MouseWheel>"))
        self.root.unbind("<MouseWheel>", extra)

    def test_close_after_child_destroy_is_safe_while_root_exists(self):
        self.frame.destroy(); self.frame.close(); self.frame.close()
        self.assertIsNone(self.frame.binding)

    def test_small_deltas_accumulate_and_shift_uses_horizontal_axis(self):
        with patch.object(self.frame.canvas,"yview_scroll") as vertical, patch.object(self.frame.canvas,"xview_scroll") as horizontal:
            for _ in range(3): self.frame.wheel(self.event(self.frame.body,30))
            vertical.assert_not_called()
            self.frame.wheel(self.event(self.frame.body,30)); vertical.assert_called_once_with(-3,"units")
            self.frame.wheel(SimpleNamespace(widget=self.frame.body,delta=-120,state=1))
            horizontal.assert_called_once_with(3,"units")

    def test_list_and_value_controls_are_not_intercepted(self):
        with patch.object(self.frame.canvas,"yview_scroll") as scroll:
            for widget in (UI.tk.Listbox(self.frame.body),UI.ttk.Combobox(self.frame.body),UI.ttk.Spinbox(self.frame.body)):
                self.assertIsNone(self.frame.wheel(self.event(widget,120)))
            scroll.assert_not_called()

    def test_minimum_width_retains_horizontal_reach(self):
        frame=UI.ScrollableFrame(self.root,min_width=620)
        try:
            frame.canvas.event_generate("<Configure>",width=300,height=100)
            self.assertEqual(int(float(frame.canvas.itemcget(frame.item,"width"))),620)
            self.assertTrue(frame.canvas.cget("xscrollcommand"))
        finally: frame.close()

    def test_flow_toolbar_wraps_without_replacing_callbacks(self):
        bar=UI.FlowToolbar(self.frame.body); action=Mock()
        buttons=[bar.add("A long original action "+str(i),action) for i in range(4)]
        self.root.update_idletasks()
        bar.reflow(SimpleNamespace(widget=bar,width=300))
        self.assertGreater(int(buttons[-1].grid_info()["row"]),0)
        bar.reflow(SimpleNamespace(widget=bar,width=2000))
        self.assertEqual(int(buttons[-1].grid_info()["row"]),0)
        buttons[1].invoke(); action.assert_called_once()

    def test_responsive_field_grid_reflows_and_keeps_edits(self):
        grid=UI.ResponsiveGrid(self.frame.body,max_columns=4,min_cell=190)
        variable=UI.tk.StringVar(self.root,value="unsaved selection")
        cells=[UI.ttk.Frame(grid) for _ in range(7)]
        entry=UI.ttk.Combobox(cells[0],textvariable=variable,width=20); entry.pack(fill="x")
        for cell in cells: grid.add(cell)
        self.root.update_idletasks()
        grid.reflow(SimpleNamespace(widget=grid,width=350))
        self.assertEqual(cells[-1].grid_info()["row"],6)
        grid.reflow(SimpleNamespace(widget=grid,width=1600))
        self.assertEqual(cells[-1].grid_info()["row"],1)
        self.assertTrue(entry.winfo_exists())
        self.assertEqual(variable.get(),"unsaved selection")
        self.assertEqual(grid.grid_columnconfigure(3)["weight"],1)
        grid.reflow(SimpleNamespace(widget=grid,width=350))
        self.assertEqual(grid.grid_columnconfigure(3)["weight"],0)

    def test_responsive_grid_rejects_foreign_widget(self):
        grid=UI.ResponsiveGrid(self.frame.body)
        with self.assertRaises(ValueError): grid.add(self.outside)


class SelectorAndVisibility(unittest.TestCase):
    def setUp(self):
        self.root = UI.tk.Tk(); self.root.withdraw()
        self.selected = Mock(); self.added = Mock()
        self.selector = UI.Selector(self.root,
            choices=(("alpha", "Same label"), ("beta", "Same label"), ("long", "Readable long choice")),
            on_select=self.selected, on_add=self.added)
        self.selector.pack()

    def tearDown(self):
        self.root.update_idletasks(); self.root.destroy()

    def test_selector_startup_and_programmatic_selection_do_not_commit(self):
        self.assertEqual(str(self.selector.cget("state")), "normal")
        self.selected.assert_not_called(); self.added.assert_not_called()
        self.selector.select("alpha")
        self.assertEqual(self.selector.selected_id, "alpha")
        self.assertEqual(self.selector.variable.get(), "Same label [alpha]")
        self.selected.assert_not_called()

    def test_typing_filters_but_does_not_select_or_create(self):
        self.selector.select("alpha"); self.selector.variable.set("readable")
        self.assertEqual(tuple(self.selector.cget("values")), ("Readable long choice [long]", "Add new…"))
        self.assertEqual(self.selector.selected_id, "alpha")
        self.selected.assert_not_called(); self.added.assert_not_called()

    def test_exact_stable_id_commit_uses_callback_once(self):
        self.selector.variable.set("BETA")
        self.assertEqual(self.selector.commit(), "break")
        self.assertEqual(self.selector.selected_id, "beta")
        self.selected.assert_called_once_with("beta")
        self.added.assert_not_called()

    def test_duplicate_labels_remain_distinguishable_by_stable_id(self):
        self.assertNotEqual(self.selector.records["alpha"], self.selector.records["beta"])
        self.selector.variable.set(self.selector.records["beta"]); self.selector.commit()
        self.selected.assert_called_once_with("beta")

    def test_cancel_restores_prior_selection_without_callback(self):
        self.selector.select("alpha"); self.selector.variable.set("unsaved query")
        self.assertEqual(self.selector.cancel(), "break")
        self.assertEqual(self.selector.variable.get(), "Same label [alpha]")
        self.assertEqual(self.selector.selected_id, "alpha")
        self.selected.assert_not_called(); self.added.assert_not_called()

    def test_unknown_query_commit_does_not_create_or_replace(self):
        self.selector.select("alpha"); self.selector.variable.set("unknown new text")
        self.selector.commit()
        self.assertEqual(self.selector.selected_id, "alpha")
        self.assertEqual(self.selector.variable.get(), "unknown new text")
        self.selected.assert_not_called(); self.added.assert_not_called()

    def test_add_new_is_explicit_and_restores_prior_selection(self):
        self.selector.select("beta"); self.selector.variable.set("Add new…")
        self.selector.commit()
        self.added.assert_called_once_with(); self.selected.assert_not_called()
        self.assertEqual(self.selector.variable.get(), "Same label [beta]")

    def test_visibility_menu_toggle_changes_view_only_on_invocation(self):
        callback = Mock()
        menu = UI.VisibilityMenu(self.root, {"associations": True, "advanced": False}, callback)
        self.assertEqual(menu.values(), {"associations": True, "advanced": False})
        callback.assert_not_called()
        menu.menu.invoke(1)
        self.assertEqual(menu.values(), {"associations": True, "advanced": True})
        callback.assert_called_once_with({"associations": True, "advanced": True})
        self.assertEqual(str(menu.cget("takefocus")), "1")

    def test_visibility_reset_uses_existing_associations_baseline(self):
        callback = Mock()
        menu = UI.VisibilityMenu(self.root, {"associations": False, "advanced": True, "details": True}, callback)
        menu.reset(callback)
        self.assertEqual(menu.values(), {"associations": True, "advanced": False, "details": False})
        callback.assert_called_once_with(menu.values())
        self.assertEqual(self.selector.selected_id, None)


class TablePresentation(unittest.TestCase):
    def setUp(self):
        self.root = UI.tk.Tk(); self.root.withdraw()
        self.tree = UI.ttk.Treeview(self.root, columns=("name", "value"), show="headings")
        self.tree.heading("name", text="Name"); self.tree.heading("value", text="Value")
        self.tree.column("name", width=300, minwidth=150)
        self.tree.column("value", width=180, minwidth=80)
        self.tree.insert("", "end", iid="one", values=("An existing readable value", "17"))
        self.tree.selection_set("one")
        self.layout = UI.TableLayout(self.tree)

    def tearDown(self):
        self.layout.close(); self.root.destroy()

    def test_fit_window_distributes_width_and_preserves_rows_selection(self):
        for width in (200, 500, 1200):
            with patch.object(self.tree, "winfo_width", return_value=width): self.layout.fit_window()
            self.assertLessEqual(sum(self.tree.column(c,"width") for c in ("name","value")), width)
            self.assertEqual(self.tree.item("one","values"),("An existing readable value","17"))
            self.assertEqual(self.tree.selection(),("one",))

    def test_manual_separator_press_keeps_native_binding_and_width_on_resize(self):
        with patch.object(self.tree,"identify_region",return_value="separator"):
            self.assertIsNone(self.layout._press(SimpleNamespace(x=100,y=10)))
        self.assertFalse(self.layout.automatic)
        self.tree.column("name",width=321)
        self.layout._configure(SimpleNamespace(widget=self.tree))
        self.assertIsNone(self.layout._job)
        self.assertEqual(self.tree.column("name","width"),321)

    def test_heading_sort_callback_is_not_replaced_or_invoked(self):
        action=Mock(); self.tree.heading("name",command=action)
        command=self.tree.heading("name","command")
        self.layout.fit_text("name"); self.layout.fit_window(); self.layout.reset()
        self.assertEqual(self.tree.heading("name","command"),command)
        action.assert_not_called()

    def test_fit_text_measures_column_and_never_changes_values(self):
        before=self.tree.item("one","values")
        self.layout.fit_text("name")
        self.assertFalse(self.layout.automatic)
        self.assertGreater(self.tree.column("name","width"),100)
        self.assertEqual(self.tree.item("one","values"),before)

    def test_reset_restores_exact_original_widths(self):
        self.layout.fit_text("value"); self.layout.reset()
        self.assertEqual(self.tree.column("name","width"),300)
        self.assertEqual(self.tree.column("name","minwidth"),150)
        self.assertEqual(self.tree.column("value","width"),180)
        self.assertFalse(self.layout.automatic)

    def test_display_order_is_respected(self):
        self.tree.configure(displaycolumns=("value","name"))
        with patch.object(self.tree,"identify_column",return_value="#1"):
            self.assertEqual(self.layout.column_at(25),"value")
        with patch.object(self.tree,"identify_column",return_value="#0"):
            self.assertIsNone(self.layout.column_at(0))

    def test_double_separator_fits_without_selecting_or_sorting(self):
        with patch.object(self.tree,"identify_region",return_value="separator"), \
                patch.object(self.tree,"identify_column",return_value="#1"):
            self.assertEqual(self.layout._double(SimpleNamespace(x=100,y=10)),"break")
        self.assertEqual(self.tree.selection(),("one",))

    def test_context_menu_is_heading_only_and_keyboard_reachable(self):
        with patch.object(self.layout.menu,"post") as post, patch.object(self.tree,"identify_region",return_value="cell"):
            self.assertIsNone(self.layout._context(SimpleNamespace(x=25,y=50)))
            post.assert_not_called()
        with patch.object(self.layout.menu,"post") as post:
            self.assertEqual(self.layout._keyboard_menu(SimpleNamespace()),"break")
            post.assert_called_once()
        self.assertEqual(self.layout.menu.entrycget(0,"state"),"disabled")

    def test_enhance_is_idempotent_and_skips_navigation(self):
        self.tree.pack(); navigation=UI.ttk.Treeview(self.root,show="tree"); navigation.pack()
        layouts=UI.enhance_tables(self.root)
        self.assertEqual(layouts,[self.layout])
        self.assertEqual(UI.enhance_tables(self.root),layouts)
        self.assertFalse(hasattr(navigation,"game_tools_column_layout"))

    def test_close_removes_only_own_bindings(self):
        extra=self.tree.bind("<Configure>",lambda _:None,add="+")
        self.layout.close(); self.layout.close()
        self.assertIn(extra,self.tree.bind("<Configure>"))
        self.assertFalse(self.layout.bindings)

    def test_first_run_window_fits_small_and_large_screen(self):
        self.assertEqual(UI.window_bounds(1920,1080),(1360,880,620,430))
        self.assertEqual(UI.window_bounds(800,600),(720,500,620,430))
        self.assertEqual(UI.window_bounds(480,320),(400,240,400,240))


if __name__ == "__main__":
    unittest.main(verbosity=2)
