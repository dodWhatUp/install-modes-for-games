"""Choice-icon presentation, editing, persistence and value-owner regressions."""
import json,sys,tempfile,unittest
from pathlib import Path
import tkinter as tk
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolChoiceIcons as icons
from GameToolCompactUI import Selector


class ChoiceIcons(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.path=Path(self.folder.name)/'icons.json'
        self.root=tk.Tk();self.root.geometry('700x400+30+30')
        self.root.game_tools_icon_path=self.path;self.root.game_tools_icon_namespace='fixture'
        self.errors=[];self.root.report_callback_exception=lambda *a:self.errors.append(a)
        self.selected=[];self.added=[]
        self.field=Selector(self.root,[('one','Same'),('two','Same')],on_select=self.selected.append,on_add=lambda:self.added.append(True))
        self.field.pack(fill='x',padx=20,pady=20);self.field.select('one')
        icons.context(self.field,'saved-profile','Profile');self.root.update()
        self.manager=self.root.game_tools_choice_icons;self.icon=self.field.game_tools_choice_icon
    def tearDown(self):
        self.root.destroy();self.folder.cleanup();self.assertEqual(self.errors,[])
    def button(self,text):
        stack=[self.manager.picker]
        while stack:
            w=stack.pop();stack.extend(w.winfo_children())
            if isinstance(w,(ttk.Button,ttk.Radiobutton))and w.cget('text')==text:return w
        raise AssertionError(text)
    def choose(self,name,position=None):
        self.icon.button.invoke();self.root.update();self.button(name).invoke()
        if position:self.button(position).invoke()
        self.button('Save icon').invoke();self.root.update()
    def test_relevant_icon_reserves_space_without_replacing_text_or_values(self):
        self.assertTrue(self.icon.button.winfo_ismapped())
        self.assertEqual(self.field.get(),'Same [one]')
        self.assertIn('profile',self.icon.button.cget('text'))
        self.assertFalse(self.path.exists());self.assertEqual(self.selected,[])
        self.assertIn('arrow',self.field.identify(self.field.winfo_width()-5,self.field.winfo_height()//2))
    def test_tcl_pixel_objects_and_dimensions_use_tk_pixel_conversion(self):
        class Pixel:
            def __init__(self,value):self.value=value
            def __str__(self):return self.value
            def __int__(self):raise TypeError('Native Tcl pixel object is not a Python integer')
        self.assertEqual(icons.padding_pixels(self.root,(Pixel('2p'),Pixel('3'))),
                         [self.root.winfo_pixels('2p'),3])
    def test_picker_cancel_and_palette_do_not_write_or_commit(self):
        before=self.field.get(),self.field.selected_id,self.field.cget('values')
        self.icon.button.invoke();self.root.update();self.button('Favorite').invoke();self.button('Cancel').invoke();self.root.update()
        self.assertFalse(self.path.exists());self.assertEqual((self.field.get(),self.field.selected_id,self.field.cget('values')),before)
        self.assertEqual(self.selected,[]);self.assertEqual(self.added,[])
    def test_explicit_save_changes_only_icon_preferences(self):
        self.choose('Favorite');value=json.loads(self.path.read_text())
        self.assertEqual(next(iter(value['icons'].values())),{'icon':'star','position':'start'})
        self.assertEqual(self.field.get(),'Same [one]');self.assertEqual(self.field.selected_id,'one')
        self.assertEqual(self.selected,[]);self.assertEqual(self.added,[])
        self.assertNotIn('Same',self.path.read_text());self.assertIn('favorite',self.icon.button.cget('text'))
    def test_duplicate_names_and_renaming_keep_stable_item_icon_identity(self):
        first=self.icon.context()[0];self.choose('Favorite')
        self.field.select('two');self.root.update();self.assertNotEqual(first,self.icon.context()[0])
        self.assertIn('profile',self.icon.button.cget('text'))
        self.field.set_choices([('one','Renamed'),('two','Same')]);self.field.select('one');self.root.update()
        self.assertEqual(self.icon.context()[0],first);self.assertIn('favorite',self.icon.button.cget('text'))
    def test_empty_and_uncommitted_queries_have_quiet_addable_slot(self):
        icons.context(self.field,'custom-choice','Unknown');self.field.set('');self.root.update()
        self.assertIn('no icon',self.icon.button.cget('text'));self.assertTrue(self.icon.button.winfo_ismapped())
        self.choose('Folder');self.field.set('draft search');self.root.update()
        self.assertIn('folder',self.icon.button.cget('text'));self.assertEqual(self.field.selected_id,'one')
        self.assertEqual(self.added,[]);self.assertEqual(self.selected,[])
    def test_remove_icon_keeps_placeholder_and_auto_restores_relevant_default(self):
        self.choose('No icon');self.assertIn('no icon',self.icon.button.cget('text'))
        self.choose('Automatic');self.assertEqual(json.loads(self.path.read_text())['icons'],{})
        self.assertIn('profile',self.icon.button.cget('text'))
    def test_end_position_keeps_native_arrow_and_text_separate(self):
        self.choose('Automatic','End');w=self.field;middle=w.winfo_height()//2
        self.assertIn('arrow',w.identify(w.winfo_width()-5,middle))
        arrow=[x for x in range(w.winfo_width()-1,w.winfo_width()-80,-1)if'arrow'in w.identify(x,middle)]
        self.assertLessEqual(self.icon.button.winfo_rootx()+self.icon.button.winfo_width(),w.winfo_rootx()+min(arrow))
        self.assertEqual(next(iter(json.loads(self.path.read_text())['icons'].values()))['icon'],'auto')
    def test_style_changes_and_small_fields_remain_usable(self):
        ttk.Style(self.root).configure('Fixture.TCombobox',padding=(5,3))
        self.field.configure(style='Fixture.TCombobox');self.icon.queue();self.root.update()
        self.assertIn('Fixture.TCombobox',self.field.cget('style'))
        small=ttk.Combobox(self.root,values=['100','125'],width=4);small.pack();self.root.update()
        self.assertFalse(small.game_tools_choice_icon.button.winfo_ismapped())
    def test_search_and_keyboard_commit_keep_raw_values(self):
        self.root.focus_force();self.field.event_generate('<ButtonPress-1>',x=60,y=10);self.root.update()
        popup=self.field.game_tools_editable_list
        self.field.set('two');self.root.update();self.assertTrue(popup.visible)
        self.assertEqual(popup.rows,['Same [two]'])
        self.field.event_generate('<Down>');self.field.event_generate('<Return>');self.root.update()
        self.assertEqual(self.selected,['two']);self.assertEqual(self.field.get(),'Same [two]')
    def test_selection_change_while_picker_open_rejects_stale_save(self):
        self.icon.button.invoke();self.root.update();self.button('Favorite').invoke()
        self.field.select('two');self.button('Save icon').invoke();self.root.update()
        self.assertFalse(self.path.exists());self.assertTrue(self.manager.picker.winfo_exists())
        self.button('Cancel').invoke()
    def test_icon_preferences_conflict_or_future_format_never_overwritten(self):
        key=self.icon.context()[0];store=icons.IconStore(self.path)
        self.path.write_text('{"schema_version":99,"icons":{}}')
        before=self.path.read_bytes()
        with self.assertRaises(ValueError):store.save(key,'star','start')
        future=icons.IconStore(self.path)
        with self.assertRaises(ValueError):future.save(key,'star','start')
        self.assertEqual(self.path.read_bytes(),before)
    def test_readonly_field_keeps_original_value_and_selection_events(self):
        events=[];fixed=ttk.Combobox(self.root,values=['On','Off'],state='readonly');fixed.set('On');fixed.pack()
        fixed.bind('<<ComboboxSelected>>',lambda _:events.append(True));self.root.update()
        fixed.game_tools_choice_icon.button.invoke();self.root.update();self.button('Cancel').invoke()
        self.assertEqual(fixed.get(),'On');self.assertEqual(events,[])
    def test_late_owned_variable_updates_icons_after_programmatic_selection(self):
        fixed=ttk.Combobox(self.root,values=['On','Off'],state='readonly');fixed.set('On');fixed.pack()
        self.root.update();decorator=fixed.game_tools_choice_icon
        key=decorator.context()[0];self.manager.store.save(key,'star','start');decorator.queue();self.root.update()
        self.assertIn('favorite',decorator.button.cget('text'))
        fixed.set('Off');self.root.update()
        self.assertIn('no icon',decorator.button.cget('text'))

if __name__=='__main__':unittest.main(verbosity=2)
