"""Focused capture behavior and native-output preservation; no host key injection."""
import importlib.util
from pathlib import Path
import sys
import tkinter as tk
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolKeyCapture as api


class Names(unittest.TestCase):
    def test_windows_keys_survive_hebrew_text_layout(self):
        self.assertEqual(api.key_name("hebrew_shin",65,"win32"),"A")
        self.assertEqual(api.key_name("exclam",49,"win32"),"1")
        self.assertEqual(api.key_name("NoSymbol",135,"win32"),"F24")
        self.assertEqual(api.key_name("Return",13,"win32",state=0x40000),"Numpad Enter")

    def test_special_keys_and_numpad_are_distinct(self):
        for key,want in (("Prior","Page Up"),("KP_Enter","Numpad Enter"),("KP_End","Numpad 1"),
                         ("Control_R","Right Ctrl"),("XF86AudioPlay","Media Play/Pause")):
            self.assertEqual(api.key_name(key,0,"linux"),want)
        self.assertEqual(api.key_name("1",97,"win32"),"Numpad 1")
        self.assertIsNone(api.key_name("unknown-key",0,"linux"))

    def test_numlock_is_not_an_alt_chord(self):
        self.assertEqual(api.chord("A",8,"win32"),"A")
        self.assertEqual(api.chord("A",16,"win32"),"Alt+A")
        self.assertEqual(api.chord("A",0x20000,"win32"),"Alt+A")
        self.assertEqual(api.chord("A",16,"linux"),"A")
        self.assertEqual(api.chord("A",13,"linux"),"Ctrl+Alt+Shift+A")


class Dialog(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.root.geometry("500x300");self.addCleanup(self.root.destroy)
        self.values=[];self.dialog=api.CaptureDialog(self.root,self.values.append)
        self.root.update();self.dialog.pad.focus_force();self.root.update()

    def press(self,key,state=0):
        self.dialog.pad.event_generate("<KeyPress>",keysym=key,state=state);self.root.update()

    def test_capture_repeat_and_explicit_commit(self):
        self.press("q",4);self.press("q",4)
        self.assertEqual(self.dialog.preview.get(),"Ctrl+Q");self.assertEqual(self.values,[])
        self.dialog.pad.event_generate("<KeyRelease>",keysym="q");self.root.update()
        self.assertEqual(self.dialog.value,"Ctrl+Q")
        self.dialog.use();self.assertEqual(self.values,["Ctrl+Q"]);self.assertTrue(self.dialog.closed)

    def test_tab_enter_are_captured_without_committing(self):
        # Xvfb has no physical F24 keycode. Its Windows VK path is tested above;
        # unexposed system keys remain available in the editable special-key list.
        for key,want in (("Tab","Tab"),("Return","Enter"),("KP_Enter","Numpad Enter"),("F12","F12")):
            self.press(key);self.assertEqual(self.dialog.value,want);self.assertFalse(self.values)
            self.assertEqual(self.root.focus_get(),self.dialog.pad)

    def test_focus_outside_capture_does_not_collect_typing(self):
        self.press("q");entry=tk.Entry(self.root);entry.pack();entry.focus_force();self.root.update()
        entry.event_generate("<KeyPress>",keysym="x");self.root.update()
        self.assertEqual(self.dialog.value,"Q");self.assertEqual(entry.get(),"x")
        self.dialog.cancel();self.assertFalse(self.values)
        self.assertFalse(self.root.bind_all("<KeyPress>"))

    def test_escape_and_window_close_cancel(self):
        self.press("q");self.press("Escape");self.assertTrue(self.dialog.closed);self.assertFalse(self.values)
        second=api.CaptureDialog(self.root,self.values.append);self.root.update();second.cancel()
        self.assertTrue(second.closed);self.assertFalse(self.values)


if __name__=="__main__":unittest.main()
