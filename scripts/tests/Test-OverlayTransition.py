"""Private preference and actual editor behavior; GUI checks require a guest display."""
import configparser
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolOverlayTransition as transition


class Settings(unittest.TestCase):
    def test_default_off_and_save_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            value, raw = transition.read(directory)
            self.assertEqual(value, {"enabled": False, "duration_ms": 120})
            self.assertIsNone(raw)
            value, raw = transition.save(directory, True, 160, raw)
            self.assertEqual(value, {"enabled": True, "duration_ms": 160})
            value, _ = transition.save(directory, False, 160, raw)
            self.assertEqual(value, {"enabled": False, "duration_ms": 160})

    def test_validation_and_concurrent_edit_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            _, raw = transition.save(directory, True, 120, None)
            for duration in [-1, 0, 19, 401, True, 120.0]:
                with self.assertRaises(ValueError):
                    transition.save(directory, True, duration, raw)
                self.assertEqual(transition.read(directory)[1], raw)
            with self.assertRaises(ValueError):
                transition.save(directory, False, 120, None)
            self.assertEqual(transition.read(directory)[1], raw)

    def test_unknown_fields_retained_unknown_schema_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "overlay-transition.ini"
            path.write_text("[Transition]\nSchema=1\nEnabled=1\nDurationMs=120\nFuture=keep\n[Other]\nValue=keep\n")
            _, raw = transition.read(directory)
            transition.save(directory, False, 200, raw)
            config = configparser.ConfigParser(); config.read(path)
            self.assertEqual(config["Transition"]["Future"], "keep")
            self.assertEqual(config["Other"]["Value"], "keep")
            raw = path.read_bytes().replace(b"schema = 1", b"schema = 2")
            path.write_bytes(raw)
            with self.assertRaises(ValueError):
                transition.save(directory, True, 120, raw)
            self.assertEqual(path.read_bytes(), raw)


class Editor(unittest.TestCase):
    def test_real_controls_save_cancel_validation_and_reopen(self):
        import tkinter as tk
        root = tk.Tk(); root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                calls = []
                editor = transition.TransitionEditor(root, directory, lambda: calls.append("saved"))
                root.update()
                self.assertEqual(str(editor.spin.cget("state")), "disabled")
                editor.enabled.set(True); editor.refresh()
                self.assertEqual(str(editor.spin.cget("state")), "normal")
                editor.duration.set("invalid"); editor.commit()
                self.assertTrue(editor.window.winfo_exists())
                self.assertIsNone(transition.read(directory)[1])
                editor.duration.set("180"); editor.commit(); root.update()
                self.assertEqual(calls, ["saved"])
                self.assertEqual(transition.read(directory)[0], {"enabled": True, "duration_ms": 180})
                editor = transition.TransitionEditor(root, directory)
                root.update()
                self.assertTrue(editor.enabled.get()); self.assertEqual(editor.duration.get(), "180")
                before = transition.read(directory)[1]
                editor.duration.set("300"); editor.window.destroy(); root.update()
                self.assertEqual(transition.read(directory)[1], before)
                editor = transition.TransitionEditor(root, directory)
                editor.enabled.set(False); editor.refresh(); editor.commit(); root.update()
                self.assertFalse(transition.read(directory)[0]["enabled"])
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
