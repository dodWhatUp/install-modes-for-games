"""Real isolated Tk acceptance for shared standalone presentation; no games."""
import json,sys,tempfile,tkinter as tk,unittest
from pathlib import Path
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolAppMenus import AppMenus
from GameToolEditableLists import install

class Menus(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=tk.Tk();self.root.geometry('900x600')
        self.calls=[];self.errors=[];self.root.report_callback_exception=lambda *a:self.errors.append(str(a[1]))
        install(self.root)
        self.header=ttk.Frame(self.root);self.header.pack(fill='x')
        self.title=ttk.Label(self.header,text='Fictional controls',font=('Segoe UI',19,'bold'));self.title.pack(side='left')
        self.old=ttk.Button(self.header,text='Original controls',command=lambda:self.calls.append('old'));self.old.pack(side='right')
        self.body=ttk.Frame(self.root);self.body.pack(fill='both',expand=True);self.body.columnconfigure(0,weight=1)
        self.var=tk.StringVar(self.root,'Original value');self.combo=ttk.Combobox(self.body,textvariable=self.var,width=60,values=('Original value','Other choice'));self.combo.grid(sticky='ew')
        self.fixed=ttk.Combobox(self.body,values=('Fixed',),width=50,state='readonly');self.fixed.grid(sticky='ew')
        self.entry=ttk.Entry(self.body,width=60);self.entry.grid(sticky='ew');self.entry.insert(0,'ordinary path / unchanged')
        self.help=ttk.Label(self.body,text='Help');self.help.grid(sticky='w')
        self.path=Path(self.tmp.name)/'ui-chrome.json';tools=tk.Menu(self.root,tearoff=False);tools.add_command(label='Explicit action',command=lambda:self.calls.append('tool'))
        self.chrome=AppMenus(self.header,root=self.root,preference=self.path,title=self.title,original_controls=(self.old,),tools_menu=tools,status=self.calls.append)
        self.visible=self.chrome.visibility('Show help',(self.help,),'help');self.root.update()
    def tearDown(self):
        self.chrome.close();self.root.destroy();self.tmp.cleanup()
    def test_open_and_cancel_menus_are_inert_and_startup_writes_nothing(self):
        for menu in (self.chrome.view,self.chrome.layout,self.chrome.tools):menu.post(10,10);self.root.update();menu.unpost()
        self.assertFalse(self.path.exists());self.assertEqual(self.calls,[]);self.assertEqual(self.var.get(),'Original value');self.assertEqual(self.errors,[])
    def test_compact_and_original_roundtrip_keep_widget_value_caret_and_handlers(self):
        self.combo.icursor(3);original_widget=str(self.combo)
        self.assertLess(self.combo.winfo_width(),500);self.assertFalse(self.old.winfo_ismapped())
        self.chrome.layout.invoke(1);self.root.update()
        self.assertTrue(self.old.winfo_ismapped());self.assertEqual(int(self.combo.cget('width')),60)
        self.assertEqual(self.combo.grid_info()['sticky'],'ew');self.assertEqual(self.combo.index('insert'),3)
        self.chrome.layout.invoke(0);self.root.update()
        self.assertEqual(str(self.combo),original_widget);self.assertEqual(self.var.get(),'Original value');self.assertEqual(self.combo.index('insert'),3)
        self.assertEqual(self.calls,[]);self.assertFalse(json.loads(self.path.read_text())['original_toolbar'])
    def test_fixed_choices_and_ordinary_text_are_not_shortened(self):
        self.assertEqual(int(self.fixed.cget('width')),50);self.assertEqual(self.fixed.grid_info()['sticky'],'ew')
        self.assertEqual(self.entry.get(),'ordinary path / unchanged');self.assertEqual(int(self.entry.cget('width')),60)
    def test_typing_with_choices_open_filters_without_committing(self):
        choices=self.combo.game_tools_editable_list;self.combo.focus_force();choices.open();self.root.update()
        self.var.set('Other');self.root.update();self.assertTrue(choices.visible);self.assertEqual(choices.rows,['Other choice'])
        self.assertEqual(self.var.get(),'Other');choices.escape(None);self.root.update();self.assertEqual(self.var.get(),'Original value');self.assertEqual(self.calls,[])
    def test_visibility_is_only_ui_state(self):
        self.chrome.view.invoke(0);self.root.update();self.assertFalse(self.help.winfo_ismapped());self.assertEqual(self.var.get(),'Original value')
        self.chrome.view.invoke(0);self.root.update();self.assertTrue(self.help.winfo_ismapped());self.assertEqual(self.calls,[])
    def test_existing_choices_and_later_fields_keep_same_callbacks(self):
        field=ttk.Combobox(self.body,width=70,values=('Later',));field.grid(sticky='ew');field.insert(0,'Later');self.root.update()
        self.assertLessEqual(int(field.cget('width')),28);self.assertEqual(field.get(),'Later');self.assertEqual(field.cget('values'),('Later',));self.assertEqual(self.calls,[])
    def test_original_choice_survives_restart_without_startup_save(self):
        self.chrome.layout.invoke(1);raw=self.path.read_bytes();self.chrome.close()
        self.chrome=AppMenus(self.header,root=self.root,preference=self.path,original_controls=())
        self.root.update();self.assertTrue(self.chrome.original.get());self.assertEqual(self.path.read_bytes(),raw)
    def test_newer_ui_file_is_not_overwritten(self):
        raw=b'{"schema_version":1,"original_toolbar":true,"visibility":{},"other_window":"retained"}'
        self.path.write_bytes(raw);self.chrome.layout.invoke(1);self.root.update()
        self.assertEqual(self.path.read_bytes(),raw);self.assertIn('another window',self.calls[-1])

if __name__=='__main__':unittest.main()
