"""Isolated Tk behavior and original-versus-current row measurements."""
import importlib.util
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from test_options import prepared
import switcher


@unittest.skipUnless(os.environ.get('DISPLAY'), 'GUI runs in isolated Linux Xvfb')
class InlineGUI(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from mod_panel import Panel
        self.temp = tempfile.TemporaryDirectory()
        self.game, self.work = prepared(self.temp.name)
        self.root = tk.Tk()
        self.panel = Panel(self.root, switcher.Switcher(self.work, process_check=lambda: []))
        self.root.update()

    def tearDown(self):
        if not self.panel.closed:
            self.panel.close()
        self.temp.cleanup()

    def pump(self):
        deadline = time.monotonic() + 5
        while self.panel.busy and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.02)
        self.assertFalse(self.panel.busy, 'Options transaction timed out')
        self.root.update()

    def test_each_inline_page_and_options_window_are_independent_and_nonmodal(self):
        panel = self.panel
        panel.vars['build-liberator'].set(True)
        for component in panel.service.components:
            for source in ('github', 'nexus'):
                expected = panel.catalog[component['id']].get(source)
                button = panel.row_actions[component['id']][source]
                with patch('mod_panel.webbrowser.open') as opened:
                    button.invoke()
                    if expected:
                        opened.assert_called_once_with(expected)
                    else:
                        self.assertIn('disabled', button.state())
                        opened.assert_not_called()
            panel.row_actions[component['id']]['options'].invoke()
            window = panel.option_windows[component['id']]
            self.root.update()
            self.assertIsNone(self.root.grab_current())
            self.assertEqual(window.window.state(), 'normal')
            window.window.withdraw()
            self.assertIs(window, panel.open_options(component))
        self.assertTrue(panel.vars['build-liberator'].get())
        self.assertFalse(panel.mod_options.path.exists(), 'Opening options must not write')

    def test_save_scopes_one_mod_and_preserves_main_checkbox_draft(self):
        panel = self.panel
        panel.vars['rune-details'].set(True)
        component = next(c for c in panel.service.components if c['id'] == 'wicked-menu')
        window = panel.open_options(component)
        window.vars['MenuHotkey'].set('F12')
        window.window.withdraw()
        self.assertIs(window, panel.open_options(component))
        self.assertEqual(window.vars['MenuHotkey'].get(), 'F12', 'Close retains unsaved draft')
        self.assertFalse(panel.mod_options.path.exists())
        window.save_button.invoke()
        self.pump()
        self.assertEqual(panel.mod_options.path.read_text(), '[WickedMenu]\nMenuHotkey = "F12"\n')
        self.assertTrue(panel.vars['rune-details'].get(), 'Saving options must preserve main choices')
        self.assertFalse((self.game / 'Mods/B.dll').exists(), 'Saving options must not apply main choices')
        self.assertIn('Saved.', window.status.get())

    def test_preview_footer_remains_fully_visible_at_large_text_sizes(self):
        import tkinter as tk
        from mod_panel import Panel
        for scale in (1.0, 1.5, 2.0):
            root = tk.Tk()
            root.tk.call('tk', 'scaling', scale)
            panel = Panel(root, self.panel.service)
            component = next(c for c in panel.service.components if c['id'] == 'rune-details')
            dialog = panel.open_preview(component)
            root.update()
            button = dialog.original_button
            self.assertEqual(button.winfo_height(), button.winfo_reqheight(), f'Clipped footer at {scale}')
            self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                                 dialog.window.winfo_rooty() + dialog.window.winfo_height())
            panel.close()

    def test_original_row_height_and_fit_at_multiple_scales_and_sizes(self):
        import tkinter as tk
        from tkinter import ttk
        from mod_panel import Panel
        baseline_path = Path(__file__).with_name('baseline_panel.py')
        if not baseline_path.is_file():
            self.skipTest('Baseline source transferred only to the isolated lab')
        spec = importlib.util.spec_from_file_location('baseline_panel', baseline_path)
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        measured = []
        for scale in (1.0, 1.5, 2.0):
            for width, height in ((870, 525), (720, 490)):
                sizes = []
                for old in (True, False):
                    root = tk.Tk()
                    root.tk.call('tk', 'scaling', scale)
                    panel = (baseline.Panel if old else Panel)(root, self.panel.service)
                    root.geometry(f'{width}x{height}')
                    root.update()
                    rows = next(w for w in panel.winfo_children() if isinstance(w, ttk.LabelFrame))
                    sizes.append([rows.grid_bbox(row=i, column=0, col2=5, row2=i)[3]
                                  for i in range(len(panel.service.components))])
                    if not old:
                        for actions in panel.row_actions.values():
                            for button in actions.values():
                                self.assertLessEqual(button.winfo_x() + button.winfo_width(), rows.winfo_width(),
                                    f'Button clipped at scaling {scale}, width {width}')
                        for index in range(len(panel.service.components)):
                            checkbox = rows.grid_slaves(row=index, column=0)[0]
                            status = rows.grid_slaves(row=index, column=1)[0]
                            self.assertLessEqual(checkbox.winfo_x() + checkbox.winfo_width(), status.winfo_x(),
                                f'Name overlaps state at scaling {scale}, width {width}')
                        self.assertEqual((root.winfo_width(), root.winfo_height()), (width, height))
                    panel.close()
                self.assertEqual(sizes[0], sizes[1], f'Row size changed at {scale}, {width}')
                measured.append((scale, width, sizes[1]))
        print('Original/current identical row heights:', measured)

    def test_previews_and_existing_options_reopen_beside_current_pointer(self):
        from unittest.mock import patch
        panel = self.panel
        for ident in ('build-liberator', 'rune-details', 'wicked-menu'):
            component = next(c for c in panel.service.components if c['id'] == ident)
            for method in (panel.open_preview, panel.open_options):
                windows = []
                for point in ((100, 100), (1100, 700), (400, 200)):
                    with patch.object(panel.root, 'winfo_pointerxy', return_value=point):
                        dialog = method(component)
                    self.root.update()
                    window = dialog.window
                    windows.append(dialog)
                    self.assertIsNone(window.grab_current())
                    self.assertGreaterEqual(window.winfo_x(), 0)
                    self.assertGreaterEqual(window.winfo_y(), 0)
                    self.assertLessEqual(window.winfo_x() + window.winfo_width(), window.winfo_screenwidth())
                    self.assertLessEqual(window.winfo_y() + window.winfo_height(), window.winfo_screenheight())
                    # Pointer lies beside or just above/below the clamped popup.
                    dx = min(abs(point[0] - window.winfo_x()), abs(point[0] - window.winfo_x() - window.winfo_width()))
                    dy = min(abs(point[1] - window.winfo_y()), abs(point[1] - window.winfo_y() - window.winfo_height()))
                    self.assertLessEqual(min(dx, dy), 20)
                    window.withdraw()
                self.assertIs(windows[0], windows[-1])
        self.assertFalse(panel.mod_options.path.exists())

    def test_gallery_navigation_zoom_and_missing_image_fallback(self):
        import tkinter as tk
        from preview_window import PreviewWindow
        component = self.panel.service.components[2]
        media = self.work / 'media'
        media.mkdir()
        photo = tk.PhotoImage(master=self.root, width=1200, height=600)
        photo.put('#215e70', to=(0, 0, 1200, 600))
        photo.write(str(media / 'fixture.png'), format='png')
        images = [{'file': 'media/fixture.png', 'url': 'https://example.com/image',
                   'caption': 'Disposable fixture', 'credit': 'Test'},
                  {'file': 'media/missing.png', 'url': 'https://example.com/missing',
                   'caption': 'Missing fixture', 'credit': 'Test'}]
        dialog = PreviewWindow(self.panel, component, {'images': images}, media_root=self.work)
        dialog.show((20, 20))
        self.root.update()
        self.assertIsNotNone(dialog.photo)
        self.assertLessEqual(dialog.photo.width(), dialog.canvas.winfo_width())
        dialog.zoom(False)
        self.assertEqual(dialog.photo.width(), 1200)
        dialog.change(1)
        self.assertIsNone(dialog.original)
        self.assertIn('unavailable', dialog.error)
        with patch('preview_window.webbrowser.open') as opened:
            dialog.open_original()
            opened.assert_called_once_with('https://example.com/missing')
        dialog.change(1)
        self.assertEqual(dialog.index, 0)
        dialog.window.destroy()


if __name__ == '__main__':
    unittest.main(verbosity=2)
