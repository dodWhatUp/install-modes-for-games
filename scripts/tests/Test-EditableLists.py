"""Real guest Tk events; no host input and no configuration writers."""
import gc,os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tkinter as tk
from tkinter import ttk
import GameToolEditableLists as lists
from GameToolCompactUI import Selector

class EditableLists(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.root.geometry('640x340+40+40');self.events=[]
        self.value=tk.StringVar(self.root,value='Alpha')
        self.combo=ttk.Combobox(self.root,textvariable=self.value,values=['Alpha','Beta','Gamma'],width=30)
        self.combo.pack(pady=16);self.other=ttk.Entry(self.root);self.other.pack()
        self.combo.bind('<<ComboboxSelected>>',lambda e:self.events.append(self.value.get()))
        self.manager=lists.install(self.root);self.root.update();self.root.focus_force();self.root.update()
        self.addCleanup(self.root.destroy)
        self.callback_errors=[];self.root.report_callback_exception=lambda *args:self.callback_errors.append(args)
    def tearDown(self):
        self.assertEqual(self.callback_errors,[])
    def click(self,x=20):
        self.combo.event_generate('<ButtonPress-1>',x=x,y=10)
        self.combo.event_generate('<ButtonRelease-1>',x=x,y=10);self.root.update()
        return self.combo.game_tools_editable_list
    def test_click_text_opens_all_choices_and_keeps_editing_focus_without_commit(self):
        popup=self.click();self.assertTrue(popup.visible);self.assertTrue(popup.popup.winfo_viewable())
        self.assertEqual(popup.rows,['Alpha','Beta','Gamma']);self.assertIs(self.root.focus_get(),self.combo)
        self.assertIsNone(self.root.grab_current());self.assertEqual(self.events,[]);self.assertEqual(self.value.get(),'Alpha')
    def test_typing_filters_visible_list_and_preserves_caret(self):
        popup=self.click();self.combo.delete(0,'end');self.combo.insert(0,'be')
        self.combo.event_generate('<KeyRelease-e>');self.root.update()
        self.assertTrue(popup.visible);self.assertEqual(popup.rows,['Beta'])
        self.assertEqual(self.combo.get(),'be');self.assertEqual(self.combo.index('insert'),2)
        self.assertIs(self.root.focus_get(),self.combo);self.assertEqual(self.events,[])
    def test_arrow_and_keyboard_commit_dispatch_existing_selection_once(self):
        popup=self.click(self.combo.winfo_width()-6)
        self.combo.event_generate('<Down>');self.root.update();self.combo.event_generate('<Return>');self.root.update()
        self.assertEqual(self.events,['Beta']);self.assertFalse(popup.visible);self.assertEqual(self.value.get(),'Beta')
    def test_list_mouse_selection_dispatches_once_without_leaving_list_open(self):
        popup=self.click();box=popup.listbox;self.root.update()
        x,y,w,h=box.bbox(2);box.event_generate('<ButtonPress-1>',x=x+3,y=y+h//2);self.root.update()
        self.assertEqual(self.events,['Gamma']);self.assertFalse(popup.visible)
        self.assertIs(self.root.focus_get(),self.combo)
    def test_escape_restores_value_and_tab_closes_without_commit(self):
        popup=self.click();self.combo.set('draft');self.combo.event_generate('<Escape>');self.root.update()
        self.assertEqual(self.value.get(),'Alpha');self.assertFalse(popup.visible);self.assertEqual(self.events,[])
        self.click();self.combo.set('another draft');self.combo.event_generate('<Tab>');self.root.update()
        self.assertFalse(popup.visible);self.assertEqual(self.events,[]);self.assertEqual(self.value.get(),'another draft')
    def test_no_match_and_pasted_unicode_stay_editable_without_creating_choice(self):
        popup=self.click();self.combo.set('שלום');self.combo.event_generate('<<Paste>>');self.root.update()
        popup.refresh();self.assertEqual(popup.rows,[]);self.assertTrue(popup.visible)
        self.combo.event_generate('<Return>');self.root.update();self.assertEqual(self.events,[])
        self.assertEqual(tuple(self.combo.cget('values')),('Alpha','Beta','Gamma'))
    def test_readonly_and_disabled_controls_retain_native_state(self):
        self.combo.configure(state='disabled');popup=self.click();self.assertFalse(popup.visible)
        self.combo.configure(state='readonly');self.assertIsNone(popup.toggle());self.assertFalse(popup.visible)
        self.assertEqual(self.value.get(),'Alpha')
    def test_dynamic_dialog_and_plain_combo_are_attached_without_duplicate_callbacks(self):
        win=tk.Toplevel(self.root);choice=ttk.Combobox(win,values=['One','Two']);choice.pack();self.root.update()
        self.assertTrue(hasattr(choice,'game_tools_editable_list'))
        self.assertIs(lists.install(win),self.manager)
        old=choice.bindtags();self.manager.scan(win);self.assertEqual(choice.bindtags(),old)
    def test_outside_click_and_owner_unmap_close_popup(self):
        popup=self.click();self.other.event_generate('<ButtonPress-1>',x=5,y=5);self.root.update()
        self.assertFalse(popup.visible)
        self.click();self.combo.pack_forget();self.root.update();self.assertFalse(popup.visible)
    def test_one_open_popup_and_shared_variable_survives_destroyed_transient_field(self):
        first=self.click();second=ttk.Combobox(self.root,textvariable=self.value,values=['Alpha','Beta']);second.pack();self.root.update()
        second.event_generate('<ButtonPress-1>',x=12,y=10);self.root.update()
        self.assertFalse(first.visible);self.assertTrue(second.game_tools_editable_list.visible)
        second.destroy();del second;gc.collect();self.root.update();self.assertEqual(self.value.get(),'Alpha')
    def test_existing_selector_add_cancel_and_stable_ids_are_preserved(self):
        selected=[];added=[];selector=Selector(self.root,[('a','Same'),('b','Same')],on_select=selected.append,on_add=lambda:added.append(True))
        selector.pack();selector.select('a');self.root.update();selector.event_generate('<ButtonPress-1>',x=10,y=10);self.root.update()
        popup=selector.game_tools_editable_list;self.assertEqual(len(popup.rows),3)
        selector.set('new');selector.event_generate('<Escape>');self.root.update();self.assertEqual(selector.selected_id,'a')
        self.assertEqual(selected,[]);self.assertEqual(added,[])
        selector.event_generate('<ButtonPress-1>',x=10,y=10);self.root.update()
        x,y,w,h=popup.listbox.bbox(2);popup.listbox.event_generate('<ButtonPress-1>',x=x+2,y=y+h//2);self.root.update()
        self.assertEqual(added,[True]);self.assertEqual(selected,[]);self.assertEqual(selector.selected_id,'a')
    def test_live_values_and_screen_edge_popup_fit(self):
        popup=self.click();self.combo.configure(values=['New','Long option '*20]);popup.refresh()
        self.assertEqual(popup.rows,['New','Long option '*20])
        self.assertGreaterEqual(popup.popup.winfo_rooty(),0)
        self.assertLessEqual(popup.popup.winfo_rootx()+popup.popup.winfo_width(),self.root.winfo_screenwidth())
        if os.environ.get('EDITABLE_LIST_SCREENSHOT'):
            import subprocess
            subprocess.run(['import','-window','root',os.environ['EDITABLE_LIST_SCREENSHOT']],check=True)
    def test_adapter_does_not_change_validation_or_readonly_callbacks(self):
        before=self.combo.cget('values');self.combo.configure(validate='key',validatecommand=(self.root.register(lambda text:len(text)<20),'%P'))
        self.click();self.combo.delete(0,'end');self.combo.insert(0,'x'*25);self.root.update()
        self.assertEqual(self.combo.get(),'');self.assertEqual(self.combo.cget('values'),before);self.assertEqual(self.events,[])
    def test_standalone_launcher_keeps_app_arguments_and_installs_without_changing_files(self):
        import tempfile,subprocess
        with tempfile.TemporaryDirectory()as folder:
            app=Path(folder)/'fixture.py';result=Path(folder)/'result.txt'
            app.write_text("import sys,tkinter as tk\nfrom tkinter import ttk\nr=tk.Tk();w=ttk.Combobox(r,values=['One']);w.pack();r.update()\nassert hasattr(w,'game_tools_editable_list')\nassert sys.argv[1:]==['--demo','--name','unchanged']\nr.destroy()\n")
            before=app.read_bytes()
            p=subprocess.run([sys.executable,'-B',str(Path(lists.__file__)),'--app',str(app),'--demo','--name','unchanged'],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(app.read_bytes(),before)
    def test_opening_native_readonly_list_closes_editable_list_without_focus_errors(self):
        popup=self.click();fixed=ttk.Combobox(self.root,values=['Fixed','Other'],state='readonly');fixed.pack();self.root.update()
        try:
            fixed.event_generate('<ButtonPress-1>',x=fixed.winfo_width()-5,y=10);self.root.update()
            self.assertFalse(popup.visible);self.assertEqual(self.callback_errors,[])
        finally:self.root.tk.call('ttk::combobox::Unpost',str(fixed))
    def test_native_tab_bindings_keep_supported_windows_and_x11_variants(self):
        self.assertEqual(lists.tab_events('win32'),('<Tab>','<Shift-Tab>'))
        self.assertEqual(lists.tab_events('aqua'),('<Tab>','<Shift-Tab>'))
        self.assertIn('<ISO_Left_Tab>',lists.tab_events('x11'))
        popup=self.combo.game_tools_editable_list
        for event in lists.tab_events(str(self.root.tk.call('tk','windowingsystem'))):
            self.assertTrue(self.root.bind_class(popup.tag,event))

if __name__=='__main__':unittest.main()
