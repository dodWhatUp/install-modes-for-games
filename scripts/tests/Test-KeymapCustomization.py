"""Data/render contracts and isolated Tk controls; no native input experiments."""
import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolKeymapCustomization as custom
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder
import GameToolKeymapExchange as exchange
import GameToolOverlay as overlay
spec=importlib.util.spec_from_file_location('sources',Path(__file__).with_name('Test-KeymapBuilder.py'))
sources=importlib.util.module_from_spec(spec);spec.loader.exec_module(sources)


def customized():
    doc=sources.fixtures.document();b=doc['buttons'][0];c=doc['maps'][0]['cells'][0]
    b['ergonomics']=dict(comfort=5,group='Core combat',action_kind='Combat',tags=['easy'],notes='User preference')
    c['organization']=dict(category='Combat',frequency='Frequent',together=[doc['buttons'][1]['id']])
    c['icon']='★';c['comment']=dict(text='Small hint',color='#79DDF2')
    doc['key_style']=dict(background_color='#123456',background_opacity=40,action_color='#FFAA11')
    return maps.validate(doc)


class Contracts(unittest.TestCase):
    def test_frequent_action_unknown_comfort_is_not_treated_as_easiest(self):
        doc=customized();button=doc['buttons'][0];bid=button['id']
        del button['ergonomics']
        self.assertIn('Frequent action; position comfort is unknown',custom.issues(doc,doc['maps'][0])[bid])
        button['ergonomics']={'comfort':2}
        self.assertIn('Frequent action on a low-comfort position',custom.issues(doc,doc['maps'][0])[bid])
        button['ergonomics']={'comfort':5}
        self.assertFalse(any('comfort' in warning for warning in custom.issues(doc,doc['maps'][0])[bid]))

    def test_roundtrip_export_templates_and_native_output_preservation(self):
        doc=customized();self.assertEqual(maps.validate(overlay.decode(maps.encoded(doc))),doc)
        with tempfile.TemporaryDirectory() as root:
            manifest,_=sources.fixtures.fixtures.fixture(Path(root))
        keymap=manifest['keymaps'][0];keymap['revision']='f'*64
        self.assertEqual(builder.validate_package(builder.package([doc],[keymap]))['documents'][0],doc)
        clean=builder.new_game(doc,'Other game')
        self.assertEqual(clean['buttons'],doc['buttons']);self.assertEqual(clean['key_style'],doc['key_style'])
        self.assertFalse(any('organization' in c or 'icon' in c for m in clean['maps'] for c in m['cells']))
        self.assertEqual(maps.output_matrix(doc),maps.output_matrix(sources.fixtures.document()))
        template=exchange.make_template(doc,keymap,'Preserved',True)
        self.assertEqual(template['document']['maps'],doc['maps'])

    def test_bad_colors_numbers_self_chords_and_unknown_metadata_are_rejected(self):
        for change in [lambda d:d.update(key_style={'background_opacity':True}),lambda d:d.update(key_style={'background_opacity':101}),
                       lambda d:d.update(key_style={'key_color':'red'}),lambda d:d.update(key_style={'command':'run'}),
                       lambda d:d['buttons'][0].update(ergonomics={'comfort':0}),
                       lambda d:d['maps'][0]['cells'][0].update(organization={'together':[d['buttons'][0]['id']]}),
                       lambda d:d['maps'][0]['cells'][0].update(icon='x\n')]:
            doc=customized();change(doc)
            with self.assertRaises(ValueError):maps.validate(doc)

    def test_scope_inheritance_clear_and_advisory_simultaneous_warning(self):
        doc=customized();bid=doc['buttons'][0]['id']
        changed=custom.set_style(doc,0,bid,'map',{'action_color':'#00FF00'})
        changed=custom.set_style(changed,0,bid,'key',{'action_color':'#0000FF'})
        self.assertEqual(custom.style(changed,changed['maps'][0],changed['maps'][0]['cells'][0])['action_color'],'#0000FF')
        cleared=custom.set_style(changed,0,bid,'key',{})
        self.assertEqual(custom.style(cleared,cleared['maps'][0],cleared['maps'][0]['cells'][0])['action_color'],'#00FF00')
        self.assertTrue(custom.issues(doc,doc['maps'][0])[bid]);self.assertEqual(custom.ordered_buttons(doc)[0]['id'],bid)
        self.assertEqual(maps.output_matrix(changed),maps.output_matrix(doc))


class Rendering(unittest.TestCase):
    def test_opacity_compositing_icons_four_views_and_legacy_equivalence_when_no_override(self):
        from PIL import Image
        doc=customized();button=doc['buttons'][0];doc['presentation']['background']='buttons'
        with tempfile.TemporaryDirectory() as folder:
            for view in overlay.VIEWS:
                path=Path(folder)/(view+'.png');maps.render(doc,doc['maps'][0],path,view)
                with Image.open(path) as image:
                    self.assertEqual(image.getpixel((button['x']+button['width']//2,button['y']+button['height']-5))[3],102)
                    self.assertEqual(image.getpixel((0,0))[3],0)
                    self.assertEqual(image.getpixel((button['x'],button['y']+35))[3],255)
            doc['presentation']['background']='opaque';maps.render(doc,doc['maps'][0],path)
            with Image.open(path) as image:self.assertEqual(image.getchannel('A').getextrema(),(255,255))


class GuestUI(unittest.TestCase):
    def setUp(self):sources.GuestEditor.setUp(self)

    def test_preferences_styles_review_preview_and_saved_json(self):
        original=maps.output_matrix(self.editor.document);stored=self.library.store.load()[1]
        dialog=self.editor.customize();dialog.values['comfort'].set('5');dialog.values['group'].set('Combat')
        dialog.values['icon'].set('★');dialog.values['frequency'].set('Frequent');dialog.apply_details();self.root_ui.update()
        dialog.scope.set('All maps of this game');dialog.load_style();dialog.style_values['background_color'].set('#224466')
        dialog.style_values['background_opacity'].set('55');dialog.apply_style();self.root_ui.update()
        self.assertEqual(self.editor.document['key_style']['background_opacity'],55)
        self.assertEqual(len(dialog.table.get_children()),29);dialog.search.set('Combat');self.root_ui.update()
        self.assertEqual(len(dialog.table.get_children()),1)
        image=self.editor._styled_image;self.editor.select_button(self.editor.selected_button);self.root_ui.update()
        self.assertIs(self.editor._styled_image,image)
        self.assertEqual(self.library.store.load()[1],stored)
        for view in overlay.VIEWS:self.editor.view_choices.buttons[view].invoke();self.root_ui.update()
        self.editor.save();self.assertEqual(self.library.current('game')['key_style']['background_opacity'],55)
        self.assertEqual(maps.output_matrix(self.editor.document),original);dialog.window.destroy()
        from types import SimpleNamespace
        b=self.editor.document['buttons'][1];s=self.editor.scale
        self.editor.canvas_down(SimpleNamespace(x=(b['x']+b['width']/2)*s,y=(b['y']+b['height']/2)*s))
        self.assertEqual(self.editor.selected_button,b['id'])

    def test_cancel_bad_value_and_reselection_do_not_mutate(self):
        before=copy.deepcopy(self.editor.document);dialog=self.editor.customize();dialog.values['group'].set('Uncommitted')
        dialog.window.destroy();self.assertEqual(self.editor.document,before)
        dialog=self.editor.customize();dialog.style_values['key_color'].set('invalid')
        with self.assertRaises(ValueError):dialog.apply_style()
        self.assertEqual(self.editor.document,before)
        self.editor.map_index=1
        with self.assertRaises(ValueError):dialog.apply_details()
        self.assertEqual(self.editor.document,before);dialog.window.destroy()


if __name__=='__main__':unittest.main()
