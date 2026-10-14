"""Own headless Tk callbacks using synthetic text fixtures. No screenshot."""
import gc,json,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).absolute().parents[2]))
import tkinter as tk
from test_extensibility import Base
from game_keybind_ops.panel import Panel
from game_keybind_ops import pack_panel
from game_keybind_ops.packs import import_pack_local,inspect_pack,load_pin

class PackUI(Base):
    def setUp(self):
        super().setUp();self.window=tk.Tk();self.window.withdraw();self.p=Panel(self.window,self.root/'state',self.s);self.p.pack();self.folder=self.sample()
    def tearDown(self):
        if self.p.working:self.p.cancel.set();self.wait()
        self.window.destroy();self.p=None;self.window=None;gc.collect();super().tearDown()
    def wait(self):
        stop=time.monotonic()+5
        while self.p.working and time.monotonic()<stop:self.window.update();time.sleep(.01)
        self.assertFalse(self.p.working)
    def import_ui(self,allow=True):
        with patch.object(pack_panel.filedialog,'askdirectory',return_value=str(self.folder)),patch.object(pack_panel.messagebox,'askyesno',return_value=allow):pack_panel.review_import(self.p);self.wait()
    def bind_ui(self):
        self.import_ui();pack=load_pin(self.s,self.p.pack_pin);self.file=self.root/'input.json';self.file.write_bytes((self.folder/pack['fixtures'][0]['before']).read_bytes())
        with patch.object(pack_panel.simpledialog,'askstring',return_value='ui-game'),patch.object(pack_panel.filedialog,'askopenfilename',return_value=str(self.file)),patch.object(pack_panel.messagebox,'askyesno',return_value=True):pack_panel.bind_files(self.p);self.wait()
    def test_pack_controls_added_same_backend(self):
        labels=[b.cget('text') for b in self.p.controls];self.assertIn('Review / import game pack…',labels);self.assertIs(self.p.service,self.s)
    def test_import_review_confirmation_required(self):
        self.import_ui(False);self.assertIsNone(self.p.pack_pin);self.assertFalse((self.s.root/'packs').exists())
    def test_import_pin_no_game_activation(self):
        self.import_ui();self.assertIsNotNone(self.p.pack_pin);self.assertIsNone(self.p.instance_id);self.assertFalse((self.s.root/'instances').exists())
    def test_bind_selected_current_file(self):
        self.bind_ui();self.assertEqual(self.p.instance_id,'ui-game');self.assertIsNone(self.p.preview)
    def test_semantic_ui_existing_stage_approve_and_undo(self):
        self.bind_ui();before=self.file.read_bytes();intent=self.root/'intent.json';intent.write_text(json.dumps({'changes':[{'action':'use','context':'gameplay','key':'F'}]}))
        with patch.object(pack_panel.filedialog,'askopenfilename',return_value=str(intent)):pack_panel.semantic_preview(self.p);self.wait()
        self.assertTrue(self.p.items);self.assertEqual(self.file.read_bytes(),before);self.p.stage();self.wait()
        with patch('game_keybind_ops.panel.messagebox.askyesno',return_value=True):self.p.apply();self.wait()
        self.assertNotEqual(self.file.read_bytes(),before);self.p.undo();self.wait()
        with patch('game_keybind_ops.panel.messagebox.askyesno',return_value=True):self.p.apply();self.wait()
        self.assertEqual(self.file.read_bytes(),before)
    def test_new_game_scaffold_in_ui(self):
        with patch.object(pack_panel.filedialog,'askdirectory',return_value=str(self.root)),patch.object(pack_panel.simpledialog,'askstring',side_effect=['new-game','Another game','ini']):pack_panel.new_draft(self.p);self.wait()
        p=json.loads((self.root/'new-game/pack.json').read_text());self.assertEqual(p['evidence']['stage'],'draft');self.assertFalse(p['files'][0]['fields'])
    def test_cancel_file_picker_no_effect(self):
        with patch.object(pack_panel.filedialog,'askdirectory',return_value=''):pack_panel.review_import(self.p)
        self.assertFalse(self.p.working);self.assertFalse((self.s.root/'packs').exists())
    def test_pack_operations_use_existing_busy_guard(self):
        self.p.busy_guard=lambda:True
        with patch.object(pack_panel.filedialog,'askdirectory',return_value=str(self.folder)):self.failcode('ACTION_BUSY',lambda:pack_panel.review_import(self.p))
    def test_native_difference_stays_local(self):
        a=self.root/'before.json';b=self.root/'after.json';a.write_text('{"key":"E"}');b.write_text('{"key":"F"}')
        with patch.object(pack_panel.filedialog,'askopenfilename',side_effect=[str(a),str(b)]),patch.object(pack_panel.simpledialog,'askstring',return_value='json'):pack_panel.learn(self.p);self.wait()
        text=self.p.out.get('1.0','end');self.assertIn('NOT_INFERRED',text);self.assertIn('"private_values_included": true',text);self.assertFalse((self.s.root/'automation').exists())

if __name__=='__main__':unittest.main(verbosity=2)
