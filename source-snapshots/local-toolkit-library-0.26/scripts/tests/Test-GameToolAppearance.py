"""Test-owned UI fixtures: no games, profiles, providers or live key injection."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolAppearance as UI
import GameToolWorkspace as WS
import GameToolUnifiedPanel as Native
from tkinter import ttk


class Preferences(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"views.json"

    def test_missing_has_session_defaults_without_creating_file(self):
        p=UI.ViewPreferences(self.path)
        self.assertEqual(p.value["mode"],"Professional"); self.assertFalse(self.path.exists())

    def test_roundtrip_separate_from_user_profiles(self):
        profile=self.path.with_name("settings.ini"); profile.write_bytes(b"user profile unchanged")
        p=UI.ViewPreferences(self.path); p.save("Compact",{"Compact":{"schema":1}})
        self.assertEqual(UI.ViewPreferences(self.path).value["mode"],"Compact")
        self.assertEqual(profile.read_bytes(),b"user profile unchanged")
        self.assertEqual(list(self.path.parent.glob(".ui-view-*")),[])

    def test_unknown_fields_preserved(self):
        self.path.write_text(json.dumps({"schema_version":1,"mode":"Classic","future_note":{"keep":True},"views":{}}))
        p=UI.ViewPreferences(self.path); p.save("Professional",{})
        self.assertEqual(json.loads(self.path.read_text())["future_note"],{"keep":True})

    def test_future_schema_never_overwritten(self):
        original=b'{"schema_version":99,"mode":"future-layout"}'
        self.path.write_bytes(original); p=UI.ViewPreferences(self.path)
        self.assertTrue(p.read_only)
        with self.assertRaises(ValueError): p.save("Classic",{})
        self.assertEqual(self.path.read_bytes(),original)

    def test_malformed_file_retained(self):
        self.path.write_bytes(b"invalid original")
        p=UI.ViewPreferences(self.path)
        with self.assertRaises(ValueError): p.save("Professional",{})
        self.assertEqual(self.path.read_bytes(),b"invalid original")

    def test_concurrent_change_and_deletion_retained(self):
        for newer in (b"newer owner",None):
            self.path.write_text('{"schema_version":1,"mode":"Classic","views":{}}')
            p=UI.ViewPreferences(self.path)
            if newer is None: self.path.unlink()
            else: self.path.write_bytes(newer)
            with self.assertRaises(ValueError): p.save("Compact",{})
            self.assertEqual(self.path.read_bytes() if self.path.exists() else None,newer)

    def test_invalid_modes_do_not_write(self):
        p=UI.ViewPreferences(self.path)
        with self.assertRaises(ValueError): p.save("arbitrary",{})
        self.assertFalse(self.path.exists())


class Feedback(unittest.TestCase):
    def test_ids_unique_fixed_and_studio_and_import_addressable(self):
        ids=[r[0] for r in UI.ITEMS]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertIn(("UI-103","Studio / Picture buttons / image and preview","studio"),UI.ITEMS)
        self.assertIn(("UI-202","Comparison / saved-report import adapters","comparison"),UI.ITEMS)

    def test_multi_id_metadata_only(self):
        raw=UI.feedback_text(["UI-103","UI-202"],"Compact","studio","test")
        self.assertIn("Layout: Compact",raw)
        self.assertIn("UI-103",raw); self.assertIn("UI-202",raw)
        self.assertNotIn("source_path",raw)

    def test_unknown_and_empty_ids_rejected(self):
        for ids in ([],["999"],["UI-103","unknown"]):
            with self.assertRaises(ValueError): UI.feedback_text(ids,"Professional","studio","test")


class Layout(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=UI.tk.Tk(); self.root.withdraw()
        self.status=UI.tk.StringVar(self.root)
        header=ttk.Frame(self.root); header.pack()
        self.workspace=WS.Workspace(self.root,self.status); self.workspace.frame.pack()
        self.tabs=ttk.Notebook(self.workspace.content); self.tabs.pack()
        self.pages={}
        for route in ("studio","comparison","catalog","sessions"):
            page=ttk.Frame(self.tabs); self.tabs.add(page,text=route); self.pages[route]=page
        self.entry=ttk.Entry(self.pages["comparison"]); self.entry.insert(0,"unsaved original input")
        self.workspace.attach(self.tabs,self.pages)
        self.appearance=UI.Appearance(self.root,header,self.workspace,self.status,Path(self.temp.name)/"views.json","fixture")
    def tearDown(self):
        self.appearance.close(); self.workspace.close(); self.root.update_idletasks(); self.root.destroy()

    def test_three_layouts_reuse_same_pages_and_unsaved_field(self):
        pages=self.tabs.tabs(); self.workspace.route("goal.compare-saved")
        for mode in UI.MODES:
            self.appearance.change(mode)
            self.assertEqual(self.tabs.tabs(),pages)
            self.assertEqual(self.tabs.select(),str(self.pages["comparison"]))
            self.assertEqual(self.entry.get(),"unsaved original input")

    def test_distinct_navigation_defaults_and_heading_position(self):
        self.appearance.change("Compact")
        self.assertEqual(self.workspace.view.get(),"Features")
        self.assertFalse(self.workspace.show_navigation.get())
        self.assertEqual(int(self.workspace.breadcrumb.grid_info()["row"]),2)
        self.appearance.change("Classic")
        self.assertEqual(self.workspace.view.get(),"Original tabs")
        self.assertEqual(self.tabs.cget("style"),"TNotebook")
        self.appearance.change("Professional")
        self.assertEqual(int(self.workspace.breadcrumb.grid_info()["row"]),1)

    def test_hidden_tabs_survive_native_and_modern_theme_switches(self):
        for mode in ("Compact","Classic","Professional","Classic","Compact"):
            self.appearance.change(mode)
            style=ttk.Style(self.root)
            self.assertEqual(style.layout(self.workspace._hidden_style+".Tab"),[("null",{"sticky":"nswe"})])
            self.assertEqual(self.tabs.cget("style")=="TNotebook",mode=="Classic")

    def test_query_survives_mode_switches(self):
        self.workspace.query.set("comparison")
        for mode in UI.MODES:
            self.appearance.change(mode); self.assertEqual(self.workspace.query.get(),"comparison")

    def test_per_layout_visibility_is_remembered(self):
        self.workspace.show_details.set(True)
        self.appearance.change("Compact"); self.assertFalse(self.workspace.show_details.get())
        self.appearance.change("Professional"); self.assertTrue(self.workspace.show_details.get())

    def test_unknown_per_layout_extension_is_retained(self):
        self.appearance.views["Professional"]={"extension":{"preserve":123}}
        self.appearance.change("Compact")
        saved=json.loads(self.appearance.preferences.path.read_text())
        self.assertEqual(saved["views"]["Professional"]["extension"],{"preserve":123})

    def test_wrapping_handles_empty_native_default_and_narrow_parent(self):
        box=ttk.Frame(self.root)
        label=ttk.Label(box,text="An explanatory sentence",wraplength=900)
        ttk.Label(box,text="Default wrap length is empty")
        UI.wrap_labels(box)
        box.event_generate("<Configure>",width=350,height=100)
        self.assertLessEqual(int(label.cget("wraplength")),350)

    def test_close_drains_theme_work_before_destroying_fixture(self):
        self.root.update_idletasks()
        self.assertFalse(self.root.winfo_viewable())

    def test_adaptive_sidebar_does_not_change_saved_preference_or_route(self):
        self.workspace.route("goal.compare-saved"); before=self.tabs.select()
        self.workspace._resize(SimpleNamespace(widget=self.workspace.frame,width=640))
        self.assertNotIn(str(self.workspace.sidebar), self.workspace.splitter.panes())
        self.assertTrue(self.workspace.show_navigation.get())
        self.workspace._resize(SimpleNamespace(widget=self.workspace.frame,width=1300))
        self.assertIn(str(self.workspace.sidebar), self.workspace.splitter.panes())
        self.assertEqual(self.tabs.select(),before)

    def test_feedback_is_nonmodal_and_reuses_one_dialog(self):
        self.appearance.feedback(); first=self.appearance.dialog
        self.appearance.feedback(); self.assertIs(first,self.appearance.dialog)
        self.assertIsNone(self.root.grab_current())
        self.appearance.change("Compact")
        self.assertTrue(first.winfo_exists())

    def test_feedback_select_multiple_copy_uses_current_mode(self):
        self.appearance.feedback(); tree=self.appearance.feedback_tree
        tree.selection_set(("UI-103","UI-202")); self.appearance.change("Compact")
        def buttons(widget):
            result=[]
            for child in widget.winfo_children():
                if isinstance(child,ttk.Button): result.append(child)
                result+=buttons(child)
            return result
        copy=next(b for b in buttons(self.appearance.dialog) if b.cget("text")=="Copy feedback + layout")
        with mock.patch.object(self.root,"clipboard_clear"),mock.patch.object(self.root,"clipboard_append") as append:
            copy.invoke(); raw=append.call_args.args[0]
            self.assertIn("Layout: Compact",raw); self.assertIn("UI-103",raw); self.assertIn("UI-202",raw)
            self.assertNotIn(self.entry.get(),raw)


class NativeScrolling(unittest.TestCase):
    def test_bounded_requests_and_absent_values(self):
        engine=Native.NativeStudio.__new__(Native.NativeStudio)
        engine.child=10; engine.process=mock.Mock(); engine.process.poll.return_value=None
        engine.lease=None; engine.viewport=mock.Mock(); engine.viewport.winfo_id.return_value=200
        engine.user=mock.Mock()
        engine.user.RemovePropW.side_effect=[32768+120,32768-240]
        self.assertEqual(engine.scroll_requests(),(120,-240))
        engine.user.RemovePropW.side_effect=[999999,None]
        self.assertEqual(engine.scroll_requests(),(0,0))
        engine.process.poll.return_value=0
        self.assertEqual(engine.scroll_requests(),(0,0))

    def test_studio_wheel_fraction_and_axes(self):
        panel=Native.UnifiedPanel.__new__(Native.UnifiedPanel)
        panel._scroll_remainder=[0,0]; panel.canvas=mock.Mock()
        for _ in range(3): panel.scroll(1,30)
        panel.canvas.yview_scroll.assert_not_called()
        panel.scroll(1,30); panel.canvas.yview_scroll.assert_called_once_with(-3,"units")
        panel.scroll(0,-120); panel.canvas.xview_scroll.assert_called_once_with(3,"units")

    def test_identification_is_bounded_boolean_on_owned_viewport_only(self):
        engine=Native.NativeStudio.__new__(Native.NativeStudio)
        engine.child=10; engine.process=mock.Mock(); engine.process.poll.return_value=None
        engine.lease=None; engine.viewport=mock.Mock(); engine.viewport.winfo_id.return_value=200
        engine.user=mock.Mock()
        engine.set_identification(True)
        engine.user.SetPropW.assert_called_once_with(200,"GameTools.Studio.Identify",1)
        engine.set_identification(False)
        self.assertEqual(engine.user.SetPropW.call_args.args,(200,"GameTools.Studio.Identify",2))
        engine.child=0; engine.user.reset_mock(); engine.set_identification(True)
        engine.user.SetPropW.assert_not_called()


class ComponentIdentification(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=UI.tk.Tk(); self.root.withdraw()
        self.status=UI.tk.StringVar(self.root)
        self.header=ttk.Frame(self.root); self.header.pack()
        self.appearance=UI.Appearance(self.root,self.header,None,self.status,
            Path(self.temp.name)/"ui.json","fixture")
        self.frame=ttk.Frame(self.root); self.frame.pack(fill="both",expand=True)
        self.command=mock.Mock()
        self.button=ttk.Button(self.frame,text="Export HTML",command=self.command); self.button.pack()
        self.value=UI.tk.StringVar(self.root,value="private unsaved file path")
        self.field=ttk.Entry(self.frame,textvariable=self.value); self.field.pack()
    def tearDown(self):
        self.root.update_idletasks(); self.appearance.close(); self.root.destroy()

    def test_top_help_offers_all_and_hide_without_opening_list(self):
        self.appearance.register_panel(self.frame,"UI-201")
        with mock.patch.object(self.appearance.marker_menu,"post") as post:
            self.appearance.help_button.invoke(); post.assert_called_once()
        self.assertFalse(self.appearance.markers.enabled)
        self.appearance.marker_menu.invoke(0)
        self.assertTrue(self.appearance.markers.enabled)
        self.assertIsNone(self.appearance.dialog)
        self.appearance.marker_menu.invoke(1)
        self.assertFalse(self.appearance.markers.enabled)

    def test_badge_copies_actual_component_not_original_command(self):
        self.appearance.register_panel(self.frame,"UI-201")
        target,badge,identifier,label=self.appearance.markers.records[str(self.button)]
        with mock.patch.object(self.root,"clipboard_clear"),mock.patch.object(self.root,"clipboard_append") as copy:
            badge.invoke(); self.assertEqual(copy.call_args.args,("UI-201.action-export-html",))
        self.assertIs(target,self.button); self.assertIn("Export HTML",label)
        self.command.assert_not_called()
        self.assertIn(identifier,self.status.get())

    def test_original_control_command_and_edits_untouched(self):
        self.appearance.register_panel(self.frame,"UI-201")
        self.appearance.toggle_identification(); self.appearance.toggle_identification()
        self.button.invoke(); self.command.assert_called_once()
        self.assertEqual(self.value.get(),"private unsaved file path")

    def test_declared_field_role_never_reads_private_value(self):
        panel=SimpleNamespace(selected_source=self.value,source_entry=self.field)
        self.appearance.register_panel(self.frame,"UI-406",panel)
        target,badge,identifier,label=self.appearance.markers.records[str(self.field)]
        self.assertEqual(identifier,"UI-406.source-entry")
        self.assertNotIn(self.value.get(),label)
        with mock.patch.object(self.root,"clipboard_clear"),mock.patch.object(self.root,"clipboard_append") as copy:
            badge.invoke(); self.assertNotIn(self.value.get(),copy.call_args.args[0])

    def test_variable_button_caption_is_not_used_for_identity(self):
        private=ttk.Button(self.frame,textvariable=self.value); private.pack()
        self.appearance.register_panel(self.frame,"UI-201")
        self.assertNotIn(str(private),self.appearance.markers.records)

    def test_original_geometry_manager_and_children_retained(self):
        original=self.button.pack_info()
        badge=self.appearance.markers.register(self.button,"UI-201.export","Export")
        self.appearance.markers.set_enabled(True)
        self.assertEqual(self.button.pack_info(),original)
        self.assertEqual(badge.place_info()["in"],self.button)
        self.appearance.markers.set_enabled(False)
        self.assertEqual(badge.winfo_manager(),"")

    def test_duplicate_registration_and_explicit_feature_override(self):
        a=self.appearance.markers.register(self.button,"UI-201.export","Export")
        b=self.appearance.markers.register(self.button,"UI-201.export","Export")
        self.assertIs(a,b)
        c=self.appearance.markers.register(self.button,"UI-202","Import",replace=True)
        self.assertFalse(a.winfo_exists()); self.assertIsNot(c,a)
        self.assertEqual(self.appearance.markers.records[str(self.button)][2],"UI-202")

    def test_new_owned_dialog_inherits_mode_and_close_is_clean(self):
        self.appearance.toggle_identification()
        dialog=UI.tk.Toplevel(self.root); dialog.withdraw()
        button=ttk.Button(dialog,text="Preview contract"); button.pack()
        self.appearance.register_panel(dialog,"UI-304")
        self.assertEqual(self.appearance.markers.records[str(button)][1].winfo_manager(),"place")
        dialog.destroy(); self.appearance.markers.set_enabled(False)
        self.assertNotIn(str(button),self.appearance.markers.records)

    def test_roles_independent_of_layout_and_badges_not_persisted(self):
        self.appearance.register_panel(self.frame,"UI-201")
        records=[r[2] for r in self.appearance.markers.records.values()]
        for mode in UI.MODES:
            self.appearance.change(mode); self.appearance.toggle_identification()
            self.assertEqual(records,[r[2] for r in self.appearance.markers.records.values()])
        raw=self.appearance.preferences.path.read_text()
        self.assertNotIn("private unsaved",raw); self.assertNotIn("identification",raw)

    def test_id_validation_no_positional_or_unknown_codes(self):
        self.assertEqual(UI.component_id("UI-103","Preview current edits"),"UI-103.preview-current-edits")
        for base,role in (("UI-999","known"),("UI-103",""),("UI-103","x"*100)):
            with self.assertRaises(ValueError): UI.component_id(base,role)

    def test_scrolled_target_is_owned_by_scrolled_body_not_root(self):
        from GameToolCompactUI import ScrollableFrame
        scroller=ScrollableFrame(self.frame); scroller.pack()
        target=ttk.Button(scroller.body,text="Preview"); target.pack()
        badge=self.appearance.markers.register(target,"UI-103.preview","Preview")
        self.appearance.toggle_identification()
        self.assertIs(badge.master,scroller.body)
        self.assertIs(badge.place_info()["in"],target)
        scroller.close()

    def test_native_mode_callback_gets_boolean_not_input_payload(self):
        self.appearance.native_feedback=callback=mock.Mock()
        self.appearance.toggle_identification(); self.appearance.toggle_identification()
        self.assertEqual(callback.call_args_list,[mock.call(True),mock.call(False)])

    def test_text_and_status_and_table_registered_without_reading_values(self):
        label=ttk.Label(self.frame,text="Review your saved reports"); label.pack()
        status=ttk.Label(self.frame,textvariable=self.value); status.pack()
        table=ttk.Treeview(self.frame,columns=("field",)); table.pack()
        table.insert("","end",values=("private row",))
        self.appearance.register_panel(self.frame,"UI-201")
        records=self.appearance.markers.records
        for target in (label,status,table): self.assertIn(str(target),records)
        with mock.patch.object(self.root,"clipboard_clear"),mock.patch.object(self.root,"clipboard_append") as copy:
            records[str(status)][1].invoke()
            self.assertNotIn("private",copy.call_args.args[0])
        self.assertEqual(self.value.get(),"private unsaved file path")

    def test_each_type_preset_filters_without_removing_records_or_fields(self):
        label=ttk.Label(self.frame,text="Explanation"); label.pack()
        table=ttk.Treeview(self.frame); table.pack()
        section=ttk.LabelFrame(self.frame,text="Optional"); section.pack()
        for target,role in ((self.button,"button"),(label,"label"),(table,"table"),(section,"section")):
            self.appearance.markers.register(target,"UI-201."+role,role)
        before=set(self.appearance.markers.records)
        for mask in (1,2,4,8,3,15,0):
            self.appearance.set_identification(True,mask)
            for key,(target,badge,_,_) in self.appearance.markers.records.items():
                self.assertEqual(badge.winfo_manager()=="place",bool(mask & self.appearance.markers.kinds[key]))
            self.assertEqual(set(self.appearance.markers.records),before)
            self.assertEqual(self.value.get(),"private unsaved file path")

    def test_custom_uncheck_all_turns_display_off_only(self):
        self.appearance.set_identification(True,15)
        for var in self.appearance.filter_vars.values(): var.set(False)
        self.appearance.apply_marker_filters()
        self.assertFalse(self.appearance.markers.enabled)
        self.button.invoke(); self.command.assert_called_once()

    def test_invalid_masks_fail_before_changing_current_filter(self):
        self.appearance.set_identification(True,2)
        for invalid in (-1,16,True,"all",None):
            with self.assertRaises(ValueError): UI.marker_mask(invalid)
        for invalid in (-1,16,True,"all"):
            with self.assertRaises(ValueError): self.appearance.set_identification(True,invalid)
        self.assertEqual(self.appearance.markers.mask,2)

    def test_labels_reserve_gutter_only_when_visible_and_restore_exact_padding(self):
        label=ttk.Label(self.frame,text="An explanation",padding=(3,4,5,6)); label.pack()
        original=label.cget("padding")
        self.appearance.markers.register(label,"UI-201.explanation","Explanation")
        self.appearance.set_identification(True,2)
        self.assertNotEqual(label.cget("padding"),original)
        self.appearance.set_identification(True,1)
        self.assertEqual(label.cget("padding"),original)
        self.appearance.set_identification(True,2); self.appearance.set_identification(False)
        self.assertEqual(label.cget("padding"),original)

    def test_copy_failure_has_selectable_id_and_does_not_activate_original(self):
        self.appearance.register_panel(self.frame,"UI-201")
        _,badge,identifier,_=self.appearance.markers.records[str(self.button)]
        with mock.patch.object(self.root,"clipboard_clear",side_effect=UI.tk.TclError("busy")):
            badge.invoke()
        self.assertIn("Could not copy",self.status.get())
        self.assertTrue(self.appearance.markers.notice.winfo_exists())
        self.assertIsNone(self.root.grab_current())
        self.command.assert_not_called()
        entry=next(w for w in self.appearance.markers.notice.winfo_children()[0].winfo_children() if isinstance(w,ttk.Entry))
        self.assertEqual(entry.get(),identifier)
        self.assertEqual(str(entry.cget("state")),"readonly")

    def test_new_dialog_inherits_filter_not_all(self):
        self.appearance.set_identification(True,2)
        dialog=UI.tk.Toplevel(self.root); dialog.withdraw()
        label=ttk.Label(dialog,text="Review before saving"); label.pack()
        button=ttk.Button(dialog,text="Save new copy"); button.pack()
        self.appearance.register_panel(dialog,"UI-304")
        self.assertEqual(self.appearance.markers.records[str(label)][1].winfo_manager(),"place")
        self.assertEqual(self.appearance.markers.records[str(button)][1].winfo_manager(),"")
        dialog.destroy()

    def test_filter_callback_is_bounded_metadata_and_separate_from_enable(self):
        self.appearance.native_filter=callback=mock.Mock()
        self.appearance.set_identification(True,6)
        callback.assert_called_once_with(6)
        self.assertNotIn("private",str(callback.call_args))

    def test_filter_is_session_only_and_original_id_stays_stable(self):
        self.appearance.register_panel(self.frame,"UI-201")
        before=self.appearance.markers.records[str(self.button)][2]
        self.appearance.set_identification(True,2); self.appearance.change("Classic")
        self.appearance.set_identification(True,15)
        self.assertEqual(self.appearance.markers.records[str(self.button)][2],before)
        self.assertNotIn("identification",self.appearance.preferences.path.read_text())

    def test_native_display_filter_uses_only_owned_property_and_rejects_payloads(self):
        engine=Native.NativeStudio.__new__(Native.NativeStudio)
        engine.child=10; engine.process=mock.Mock(); engine.process.poll.return_value=None
        engine.lease=None; engine.viewport=mock.Mock(); engine.viewport.winfo_id.return_value=200
        engine.user=mock.Mock()
        engine.set_identification_filter(2)
        engine.user.SetPropW.assert_called_once_with(200,"GameTools.Studio.IdentifyFilter",18)
        for invalid in (-1,16,True,"text"):
            with self.assertRaises(ValueError): engine.set_identification_filter(invalid)
        engine.child=0; engine.user.reset_mock(); engine.set_identification_filter(15)
        engine.user.SetPropW.assert_not_called()


if __name__=="__main__": unittest.main(verbosity=2)
