"""Appearance contracts and isolated Tk checks; no game/device input."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as overlay
import GameToolOverlayAppearance as looks
import GameToolKeymapDocument as maps

spec = importlib.util.spec_from_file_location('sources', Path(__file__).with_name('Test-KeymapBuilder.py'))
sources = importlib.util.module_from_spec(spec); spec.loader.exec_module(sources)


class Policies(unittest.TestCase):
    def setUp(self):
        self.value = overlay.empty_store()
        self.value['manifest']['games'] = [dict(id='game', label='Game'), dict(id='other', label='Other')]
        self.policy = looks.policy(self.value)

    def test_legacy_store_and_independent_override_inheritance(self):
        overlay.validate_store(self.value)
        style = looks.default_style(); style.update(action_text_percent=140, key_text_percent=75, view='Actions')
        global_policy = looks.set_scope(self.policy, None, style, all_games=True)
        self.assertEqual(looks.effective(global_policy, 'game'), style)
        game = looks.set_scope(global_policy, 'game', dict(style, key_text_percent=160))
        self.assertEqual(looks.effective(game, 'other'), style)
        restored = looks.set_scope(game, 'game', style, inherit=True)
        self.assertEqual(restored, global_policy)
        self.assertEqual(self.policy['global']['key_text_percent'], 100)

    def test_presets_copy_move_are_snapshots_not_live_settings(self):
        saved, first = looks.save_preset(self.policy, None, 'Comfort', looks.default_style())
        copied, second = looks.transfer_preset(saved, first, 'game', 'Comfort')
        moved, third = looks.transfer_preset(copied, second, 'other', 'Large', move=True)
        self.assertEqual(second, third); self.assertNotEqual(first, second)
        looks.validate_policy(moved, {'game','other'})
        moved['presets'][first]['style']['key_text_percent'] = 150
        self.assertEqual(moved['presets'][second]['style']['key_text_percent'], 100)
        self.assertEqual(moved['games'], self.policy['games'])
        self.assertEqual(moved['global'], self.policy['global'])
        self.assertEqual(copied['presets'][second]['scope'], 'game')

    def test_invalid_sizes_scopes_fields_and_name_collisions_refuse(self):
        for field, bad in [('action_text_percent', True), ('key_text_percent', 201), ('action_text_percent', 49), ('key_text_percent', 90.5)]:
            with self.assertRaises(ValueError): looks.validate_style(dict(looks.default_style(), **{field:bad}))
        saved, first = looks.save_preset(self.policy, None, 'Comfort', looks.default_style())
        saved, _ = looks.save_preset(saved, None, 'comfort', looks.default_style())
        with self.assertRaisesRegex(ValueError, 'already exists'): looks.validate_policy(saved, {'game','other'})
        for bad in ('absent', [], True):
            value, _ = looks.save_preset(self.policy, bad, 'Test', looks.default_style())
            with self.assertRaises(ValueError): looks.validate_policy(value, {'game'})


class Transactions(unittest.TestCase):
    def setUp(self):
        sources.Sources.setUp(self)
        value, sha = self.library.store.load()
        self.library.publish(self.doc, self.keymap, sha)
        self.service = looks.Service(self.library.store.directory)

    def test_apply_commits_fonts_geometry_view_and_preserves_source_native_and_associations(self):
        before, sha, policy = self.service.load(); source_bytes = self.library.path('game').read_bytes()
        new = looks.set_scope(policy, 'game', dict(looks.effective(policy,'game'), action_text_percent=150, key_text_percent=70, view='ActionFirst', background='buttons', size_value=40))
        receipt = self.service.apply(new, sha)
        after, fresh, saved = self.service.load()
        self.assertFalse(receipt['native_changes']); self.assertGreater(receipt['rendered_images'], 0)
        self.assertEqual(saved, new); self.assertNotEqual(fresh, sha)
        self.assertEqual(after['manifest']['keymaps'], before['manifest']['keymaps'])
        self.assertEqual(after['manifest']['associations'], before['manifest']['associations'])
        self.assertEqual(self.library.path('game').read_bytes(), source_bytes)
        self.assertEqual(after['preferences']['selections']['game']['view'], 'ActionFirst')
        self.assertTrue(all(g['rendering']['size_value']==40 for g in after['manifest']['groups']))
        self.assertTrue((self.service.store.directory/('overlay-before-'+sha+'.json')).is_file())
        # Republishing a map must keep the saved appearance rather than reset it.
        hashes = {a['id']: a['sha256'] for a in after['manifest']['assets']}
        self.library.publish(self.doc, self.keymap, fresh)
        value, _ = self.library.store.load()
        self.assertTrue(all(a['sha256']==hashes[a['id']] for a in value['manifest']['assets'] if a['id'].startswith('map-image-')))

    def test_cancel_stale_and_source_drift_preserve_registry(self):
        value, sha, policy = self.service.load()
        new = looks.set_scope(policy, 'game', dict(looks.effective(policy,'game'), action_text_percent=120))
        with self.assertRaisesRegex(ValueError, 'cancelled'): self.service.apply(new, sha, cancelled=lambda: True)
        self.assertEqual(self.service.store.load()[1], sha)
        with self.assertRaisesRegex(ValueError, 'changed'): self.service.apply(new, '0'*64)
        calls = [0]
        original = self.service.documents
        def drifting():
            docs = original(); calls[0]+=1
            if calls[0]>1: docs['game']['title'] = 'Changed source'
            return docs
        with mock.patch.object(self.service, 'documents', drifting):
            with self.assertRaisesRegex(ValueError, 'source changed'): self.service.apply(new, sha)
        self.assertEqual(self.service.store.load()[1], sha)

    def test_preset_library_only_and_quick_view_sync(self):
        value, sha, policy = self.service.load()
        candidate, pid = looks.save_preset(policy, None, 'Portable', dict(looks.default_style(), key_text_percent=160))
        self.service.save_library(candidate, sha)
        value, sha, saved = self.service.load()
        self.assertEqual(value['manifest'], self.library.store.load()[0]['manifest'])
        self.assertEqual(looks.effective(saved,'game'), looks.effective(policy,'game'))
        self.service.store.update('selection',dict(game_id='game', layer='BASIC',context='gameplay',view='Actions'),sha)
        value, _, saved = self.service.load()
        self.assertEqual(looks.effective(saved,'game')['view'],'Actions')
        self.assertEqual(saved['presets'][pid]['style']['key_text_percent'],160)


class Fonts(unittest.TestCase):
    def test_default_output_and_hidden_role_size_do_not_change_pixels(self):
        doc = sources.fixtures.document()
        with tempfile.TemporaryDirectory() as folder:
            a,b = Path(folder)/'a.png',Path(folder)/'b.png'
            for view in overlay.VIEWS:
                maps.render(doc,doc['maps'][0],a,view)
                maps.render(doc,doc['maps'][0],b,view,looks.default_style())
                self.assertEqual(a.read_bytes(),b.read_bytes())
            for view, field in [('Actions','key_text_percent'),('Keys','action_text_percent')]:
                maps.render(doc,doc['maps'][0],a,view)
                maps.render(doc,doc['maps'][0],b,view,dict(looks.default_style(),**{field:150}))
                self.assertEqual(a.read_bytes(),b.read_bytes())

    def test_both_font_roles_change_and_stay_inside_cells(self):
        from PIL import ImageDraw
        doc = sources.fixtures.document(); cell=doc['maps'][0]['cells'][0]
        cell.update(display_key='K',display_action='Leap')
        original=ImageDraw.ImageDraw.text
        sizes=[]
        def capture(draw,xy,text,*args,**kwargs):
            if text in {'K','Leap'}: sizes.append((text,kwargs['font'].size,xy))
            return original(draw,xy,text,*args,**kwargs)
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(ImageDraw.ImageDraw,'text',capture):
            style=dict(looks.default_style(),action_text_percent=70,key_text_percent=150)
            maps.render(doc,doc['maps'][0],Path(folder)/'x.png','ActionFirst',style)
        key=next(r for r in sizes if r[0]=='K'); action=next(r for r in sizes if r[0]=='Leap')
        self.assertGreater(key[1],17); self.assertLess(action[1],24)
        self.assertLess(action[2][1],key[2][1])


class GuestUI(unittest.TestCase):
    def setUp(self):
        sources.GuestEditor.setUp(self)
        from GameToolOverlayAppearanceUI import Editor
        self.appearance = Editor(self.panel); self.addCleanup(self.appearance.close)
        self.root_ui.update()

    def pump(self, predicate, seconds=10):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline and not predicate():
            self.root_ui.update(); time.sleep(.02)
        self.assertTrue(predicate())

    def test_sizes_and_layout_are_drafts_then_worker_apply_persists(self):
        editor=self.appearance; before=editor.service.store.load()[1]
        editor.variables['action_text_percent'].set('130'); editor.variables['key_text_percent'].set('75')
        editor.views.buttons['ActionFirst'].invoke(); self.root_ui.update()
        self.assertEqual(editor.service.store.load()[1],before)
        # Avoid expensive guest PNG rendering here; real render/transaction
        # coverage is in Transactions. Exercise the asynchronous UI boundary.
        real=editor.service.apply
        def quick(candidate,expected,**kwargs):
            value,current=editor.service.store.load(); self.assertEqual(current,expected)
            value['preferences']['appearance']=candidate
            return editor.service.store.write(value,expected)
        with mock.patch.object(editor.service,'apply',quick):
            editor.apply_button.invoke(); self.assertTrue(editor.busy)
            self.assertIn('disabled',editor.scope.state())
            self.pump(lambda: not editor.busy)
        _,_,saved=editor.service.load(); style=looks.effective(saved,'game')
        self.assertEqual((style['action_text_percent'],style['key_text_percent'],style['view']),(130,75,'ActionFirst'))

    def test_inheritance_presets_and_narrow_layout_do_not_apply(self):
        editor=self.appearance; before=editor.service.store.load()[1]
        editor.inherit.set(True); editor.inheritance()
        self.assertTrue(all('disabled' in w.state() for w in editor.edit_controls))
        editor.inherit.set(False); editor.inheritance()
        self.assertTrue(all('disabled' not in w.state() for w in editor.edit_controls))
        editor.window.geometry('640x500'); self.root_ui.update()
        self.assertEqual(int(editor.preview_frame.grid_info()['column']),0)
        self.assertEqual(editor.service.store.load()[1],before)
        editor.scope.select('appearance-global-defaults'); editor.change_scope(editor.scope.selected_id)
        self.assertEqual(str(editor.all_button.winfo_manager()),'grid')
        self.assertIn('disabled',editor.inherit_button.state())

    def test_real_image_preview_completes_on_tk_thread(self):
        self.pump(lambda: hasattr(self.appearance, 'photo'), seconds=15)
        self.assertGreater(self.appearance.photo.width(), 0)
        self.assertLessEqual(self.appearance.photo.width(), 440)

    def test_real_preset_dialog_saves_duplicates_and_moves_without_applying(self):
        from tkinter import ttk
        from GameToolCompactUI import Selector
        editor=self.appearance
        before=editor.service.store.load()[0]
        def dialog_controls(title):
            self.root_ui.update()
            dialog=next(w for w in editor.window.winfo_children() if hasattr(w,'title') and w.title()==title)
            widgets=dialog.winfo_children()[0].winfo_children()
            return widgets
        editor.variables['action_text_percent'].set('145'); editor.save_new()
        widgets=dialog_controls('Save appearance preset')
        name=next(w for w in widgets if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox))
        name.insert(0,'Comfort'); next(w for w in widgets if isinstance(w,ttk.Button)).invoke()
        first=editor.preset.selected_id
        self.assertIn(first,editor.policy['presets'])
        editor.transfer(False); widgets=dialog_controls('Duplicate preset')
        destination=next(w for w in widgets if isinstance(w,Selector)); destination.select('appearance-global-defaults')
        next(w for w in widgets if isinstance(w,ttk.Button)).invoke(); self.root_ui.update()
        second=editor.preset.selected_id
        self.assertNotEqual(first,second); self.assertIsNone(editor.policy['presets'][second]['scope'])
        editor.transfer(True); widgets=dialog_controls('Move preset')
        destination=next(w for w in widgets if isinstance(w,Selector)); destination.select('game')
        name=next(w for w in widgets if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox))
        name.delete(0,'end'); name.insert(0,'Moved comfort')
        next(w for w in widgets if isinstance(w,ttk.Button)).invoke(); self.root_ui.update()
        self.assertEqual(editor.preset.selected_id,second)
        self.assertEqual(editor.policy['presets'][second]['scope'],'game')
        after=editor.service.store.load()[0]
        self.assertEqual(after['manifest'],before['manifest'])
        self.assertEqual(after['preferences']['selections'],before['preferences']['selections'])
        self.assertEqual(editor.policy['presets'][second]['style']['action_text_percent'],145)


if __name__ == '__main__': unittest.main()
