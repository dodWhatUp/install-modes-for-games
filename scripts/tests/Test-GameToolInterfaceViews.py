"""Observable switching, draft, ownership and fallback checks on fictional data."""
import importlib.util,json,sys,time,tkinter as tk,unittest
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolInterfaceViews import InterfaceViews,InterfacePreference,IntegratedModel
spec=importlib.util.spec_from_file_location('ui_fixture',Path(__file__).with_name('Test-GameToolUIReview.py'));fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class Tests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.Tests();self.f.setUp();self.root=tk.Tk();self.root.geometry('1100x800');self.errors=[];self.root.report_callback_exception=lambda t,v,tr:self.errors.append(str(v))
        self.original=ttk.Frame(self.root);self.original.pack(fill='both',expand=True);self.notebook=ttk.Notebook(self.original);self.notebook.pack(fill='both',expand=True)
        self.banner=ttk.Label(self.root,text='Operational state');self.banner.pack(fill='x');self.root.game_tools_scope_banner=self.banner
        self.tabs=[]
        for name in ['Studio','Controls planner','Mod Controls','Runtime profiles','Other extension']:
            tab=ttk.Frame(self.notebook);self.notebook.add(tab,text=name);self.tabs.append(tab)
        self.original_draft=tk.StringVar(self.root,value='unsaved original');ttk.Entry(self.tabs[0],textvariable=self.original_draft).pack()
        self.status=tk.StringVar(self.root);self.protocol=self.root.register(lambda:None);self.root.protocol('WM_DELETE_WINDOW',self.protocol)
        self.pref=InterfacePreference(self.f.f.base/'interface.json')
        def model(*args,**kwargs):return IntegratedModel(self.f.f.data,self.f.model.root,controls=self.f.f.controls)
        self.views=InterfaceViews(self.root,self.notebook,self.f.f.controls,self.f.f.data,self.status,preference=self.pref,model_factory=model)
        self.root.update()
    def pump(self):
        until=time.monotonic()+15
        while time.monotonic()<until:
            self.root.update()
            if not self.views.app or (not self.views.app.busy and self.views.app.events.empty() and not self.views.app.pending):break
            time.sleep(.02)
        self.root.update();self.assertEqual(self.errors,[])
    def tearDown(self):
        self.pump()
        if self.views.app and self.views.app.finder:
            while self.views.app.finder.jobs:self.root.update();time.sleep(.02)
        self.views.close();self.root.destroy();self.f.tearDown()
    def test_default_does_not_build_new_view_or_apply(self):
        self.assertEqual(self.views.mode,'Existing');self.assertIsNone(self.views.app);self.assertTrue(self.original.winfo_ismapped());self.assertFalse(self.pref.path.exists())
    def test_switches_preserve_original_widgets_and_both_drafts(self):
        self.assertTrue(self.views.show('New'));self.pump();app=self.views.app;app.variables['amount'].set('7.5');self.assertFalse(self.original.winfo_ismapped())
        self.assertTrue(self.views.show('Existing'));self.root.update();self.assertEqual(self.original_draft.get(),'unsaved original');self.assertTrue(self.original.winfo_ismapped())
        self.assertTrue(self.views.show('New'));self.pump();self.assertIs(self.views.app,app);self.assertEqual(app.values()['amount'],7.5);self.assertEqual(self.f.f.path('fixture-one').read_bytes(),self.f.f.initial['fixture-one'])
    def test_operational_banner_and_original_layout_order_survive_switch(self):
        before=[w for w in self.root.pack_slaves() if w is not self.views.bar]
        self.views.show('New');self.pump();self.assertTrue(self.banner.winfo_ismapped());self.views.show('Existing');self.root.update()
        self.assertEqual([w for w in self.root.pack_slaves() if w is not self.views.bar],before)
    def test_all_original_and_later_extension_pages_remain_reachable(self):
        self.views.show('New');self.pump();extra=ttk.Frame(self.notebook);self.notebook.add(extra,text='Later profile extension');self.views.update_tools()
        self.assertEqual(len(self.views.pages()),6);self.assertTrue(self.views.open_tool(str(extra)));self.assertEqual(self.notebook.select(),str(extra));self.assertEqual(self.views.mode,'Existing')
    def test_disabled_pages_are_not_reenabled(self):
        self.notebook.tab(self.tabs[1],state='disabled');self.views.show('New');self.pump();self.assertFalse(self.views.open_tool(str(self.tabs[1])));self.assertEqual(self.notebook.tab(self.tabs[1],'state'),'disabled');self.assertEqual(self.views.mode,'New')
    def test_preference_persists_and_unknown_fields_survive(self):
        self.pref.path.write_text(json.dumps({'schema_version':1,'interface':'Existing','other':{'keep':1}}));self.views.show('New');self.pump();saved=self.pref.read();self.assertEqual(saved['interface'],'New');self.assertEqual(saved['other'],{'keep':1});self.views.show('Existing');self.assertEqual(self.pref.read()['interface'],'Existing')
    def test_wm_close_theme_geometry_and_existing_hotkeys_preserved(self):
        self.root.bind('<Control-f>','set existing_search 1');before=self.root.bind('<Control-f>');style=ttk.Style(self.root);theme=style.theme_use();font=style.lookup('TLabel','font');geometry=self.root.geometry()
        self.views.show('New');self.pump();self.views.app.dark.set(True);self.views.app.restyle();self.assertEqual(self.root.protocol('WM_DELETE_WINDOW'),self.protocol);self.assertEqual(style.theme_use(),theme);self.assertEqual(style.lookup('TLabel','font'),font);self.assertEqual(self.root.geometry(),geometry)
        self.views.show('Existing');self.assertEqual(self.root.bind('<Control-f>'),before)
    def test_new_profiles_use_original_controller_owner(self):
        self.views.show('New');self.pump();state=self.f.f.controls.inspect('fixture-one');self.views.app.model.save_profile('fixture-one','shared-test',{'amount':6},state['revision']);rows=self.f.f.controls.profile_rows('fixture-one');self.assertTrue(any(r['label']=='shared-test' for r in rows));self.assertEqual(self.f.f.path('fixture-one').read_bytes(),self.f.f.initial['fixture-one'])
    def test_optional_view_failure_restores_original(self):
        def broken(*args,**kwargs):raise ValueError('fixture missing optional view')
        self.views.app_factory=broken;self.assertFalse(self.views.show('New'));self.root.update();self.assertTrue(self.original.winfo_ismapped());self.assertEqual(self.views.mode,'Existing');self.assertFalse(self.pref.path.exists())
    def test_close_new_view_does_not_destroy_hub(self):
        self.views.show('New');self.pump();self.assertTrue(self.views.close());self.root.update();self.assertTrue(self.root.winfo_exists());self.assertTrue(self.original.winfo_ismapped());self.views.app=None
    def test_invalid_mode_never_changes_files_or_view(self):
        self.assertFalse(self.views.show('Unknown'));self.assertEqual(self.views.mode,'Existing');self.assertFalse(self.pref.path.exists())

if __name__=='__main__':unittest.main()
