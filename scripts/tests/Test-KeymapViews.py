"""Four view roles, persisted routing and guest-only one-click UI checks."""
import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolKeymapDocument as maps
import GameToolOverlay as overlay


def fixture_module(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


sources = fixture_module('Test-KeymapBuilder')
panels = fixture_module('Test-GameToolOverlay')


class Rendering(unittest.TestCase):
    def test_four_views_draw_only_the_requested_roles_and_emphasis(self):
        from PIL import ImageDraw
        document = sources.fixtures.document()
        cell = document['maps'][0]['cells'][0]
        cell.update(display_key='F24', display_action='Leap')
        original = ImageDraw.ImageDraw.text
        with tempfile.TemporaryDirectory() as folder:
            for view in overlay.VIEWS:
                seen = []
                def capture(draw, xy, text, *args, **kwargs):
                    seen.append((text, kwargs.get('font'), xy))
                    return original(draw, xy, text, *args, **kwargs)
                with mock.patch.object(ImageDraw.ImageDraw, 'text', capture):
                    maps.render(document, document['maps'][0], Path(folder)/(view+'.png'), view)
                key = [row for row in seen if row[0] == 'F24']
                action = [row for row in seen if row[0] == 'Leap']
                self.assertEqual(bool(key), view != 'Actions')
                self.assertEqual(bool(action), view != 'Keys')
                if view == 'ActionFirst':
                    self.assertGreater(action[0][1].size, key[0][1].size)
                    self.assertLess(action[0][2][1], key[0][2][1])
                    self.assertIn('Bold', action[0][1].getname()[1])
                if view == 'Actions':
                    self.assertFalse(any(row[0] == '#'+str(cell['button_id']) for row in seen))


class Persistence(unittest.TestCase):
    def setUp(self):
        sources.Sources.setUp(self)

    def test_publish_retains_saved_view_and_only_explicit_choice_changes_it(self):
        before = maps.encoded(self.doc)
        other = copy.deepcopy(self.library.store.load()[0]['preferences'])
        _, fingerprint = self.library.store.load()
        first = self.library.publish(self.doc, self.keymap, fingerprint, selected_view='Actions')
        value, fingerprint = self.library.store.load()
        self.assertEqual(value['preferences']['selections']['game']['view'], 'Actions')
        self.library.publish(self.doc, self.keymap, fingerprint)
        value, fingerprint = self.library.store.load()
        self.assertEqual(value['preferences']['selections']['game']['view'], 'Actions')
        self.library.publish(self.doc, self.keymap, fingerprint, selected_view='ActionFirst')
        value, _ = self.library.store.load()
        selected = copy.deepcopy(value); selected['preferences']['enabled'] = True
        result = overlay.choose(selected, {'exe':'Gameplay.exe', 'at':10, 'own':False}, now=10)
        asset = next(a for a in value['manifest']['assets'] if a['id'] == result['asset_id'])
        self.assertEqual(asset['view'], 'ActionFirst')
        self.assertEqual(maps.encoded(self.doc), before)
        self.assertEqual(value['preferences']['enabled'], other['enabled'])
        self.assertEqual(first['native_changes'], False)


class GuestUI(unittest.TestCase):
    def setUp(self):
        panels.PanelTests.setUp(self)

    def test_each_single_button_click_persists_and_reloads_the_view(self):
        for view in ('Combined','ActionFirst','Actions','Keys'):
            self.panel.selectors['view'].buttons[view].invoke()
            self.root.update()
            value, _ = self.panel.store.load()
            self.assertEqual(value['preferences']['selections']['game']['view'], view)
            self.panel.reload_choices()
            self.assertEqual(self.panel.selectors['view'].selected_id, view)
        self.assertEqual([b.cget('text') for b in self.panel.selectors['view'].buttons.values()],
                         ['Key first','Action first','Action only','Key only'])

    def test_choices_wrap_and_retain_selection_at_large_scaling(self):
        import tkinter as tk
        from GameToolCompactUI import ChoiceButtons
        window = tk.Toplevel(self.root); self.addCleanup(window.destroy)
        window.geometry('320x300'); self.root.tk.call('tk','scaling',2.0)
        buttons = ChoiceButtons(window, overlay.VIEW_CHOICES); buttons.pack(fill='x')
        buttons.select('ActionFirst'); self.root.update()
        self.assertEqual(buttons.selected_id, 'ActionFirst')
        self.assertGreater(max(int(b.grid_info()['row']) for b in buttons.buttons.values()), 0)
        for button in buttons.buttons.values():
            self.assertLessEqual(button.winfo_x()+button.winfo_width(), buttons.winfo_width()+1)

    def test_stale_choice_does_not_overwrite_newer_settings(self):
        value, fingerprint = self.panel.store.load()
        self.panel.store.update('selection', {'game_id':'game','layer':'BASIC','context':'gameplay','view':'Actions'}, fingerprint)
        self.panel.selectors['view'].buttons['Keys'].invoke()
        self.assertEqual(self.panel.store.load()[0]['preferences']['selections']['game']['view'], 'Actions')


class GuestBuilder(unittest.TestCase):
    def setUp(self):
        sources.GuestEditor.setUp(self)

    def test_all_four_builder_previews_fit_and_only_show_requested_content(self):
        self.root_ui.tk.call('tk','scaling',2.0)
        self.editor.window.geometry('860x620'); self.root_ui.update()
        cell = self.editor.document['maps'][0]['cells'][0]
        cell.update(display_key='F24',display_action='Leap')
        before = maps.encoded(self.editor.document)
        for view in ('Combined','ActionFirst','Actions','Keys'):
            self.editor.view_choices.buttons[view].invoke(); self.root_ui.update()
            texts = [self.editor.canvas.itemcget(i,'text') for i in self.editor.canvas.find_all() if self.editor.canvas.type(i)=='text']
            self.assertEqual('F24' in texts,view!='Actions')
            self.assertEqual('Leap' in texts,view!='Keys')
            for button in self.editor.document['buttons']:
                items=self.editor.canvas.find_withtag('button-'+str(button['id']))
                rectangle=next(i for i in items if self.editor.canvas.type(i)=='rectangle')
                x,y,right,bottom=self.editor.canvas.coords(rectangle)
                for item in items:
                    if self.editor.canvas.type(item)=='text':
                        left,top,r,bottom_text=self.editor.canvas.bbox(item)
                        self.assertGreaterEqual(left,x-2); self.assertGreaterEqual(top,y-2)
                        self.assertLessEqual(r,right+2); self.assertLessEqual(bottom_text,bottom+2)
        self.assertEqual(maps.encoded(self.editor.document),before)


if __name__ == '__main__':
    unittest.main()
