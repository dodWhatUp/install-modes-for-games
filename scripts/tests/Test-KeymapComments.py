"""Scoped annotation persistence, bounded rendering and isolated Tk authoring."""
import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolKeymapComments as notes
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder
import GameToolKeymapExchange as exchange
import GameToolOverlay as overlay
spec=importlib.util.spec_from_file_location('sources',Path(__file__).with_name('Test-KeymapBuilder.py'))
sources=importlib.util.module_from_spec(spec);spec.loader.exec_module(sources)


class Contracts(unittest.TestCase):
    def setUp(self): self.doc=sources.fixtures.document()

    def test_key_map_and_all_maps_are_independent_and_do_not_edit_keys_actions(self):
        bid=self.doc['maps'][0]['cells'][0]['button_id'];old=copy.deepcopy(self.doc)
        changed=notes.set_key(self.doc,0,bid,'Tap once','Cyan')
        changed=notes.set_header(changed,0,'map','Only this map','Pink')
        changed=notes.set_header(changed,0,'all','Every map','Amber')
        self.assertEqual(maps.output_matrix(changed),maps.output_matrix(old));self.assertEqual(self.doc,old)
        self.assertEqual([c['text'] for c in notes.headers(changed,changed['maps'][0])],['Every map','Only this map'])
        self.assertEqual([c['text'] for c in notes.headers(changed,changed['maps'][1])],['Every map'])
        self.assertEqual(changed['maps'][0]['cells'][0]['action'],old['maps'][0]['cells'][0]['action'])
        self.assertEqual(changed['maps'][0]['cells'][0]['evidence'],old['maps'][0]['cells'][0]['evidence'])
        removed=notes.set_key(changed,0,bid,'')
        self.assertNotIn('comment',removed['maps'][0]['cells'][0]);self.assertIn('comment',changed['maps'][0]['cells'][0])

    def test_comment_validation_colors_limits_and_unknown_fields(self):
        for color in ('Amber','Cyan','#abc123'):self.assertRegex(notes.color(color),r'^#[A-F0-9]{6}$')
        for value in (dict(text='x',color='red'),dict(text='x\ny',color='#123456'),dict(text='x'*161,color='#123456'),dict(text='x',color='#123456',command='run')):
            with self.assertRaises(ValueError):notes.validate(value,160)
        with self.assertRaises(ValueError):notes.color([])
        self.assertEqual(maps.validate(overlay.decode(maps.encoded(self.doc))),self.doc)

    def test_json_and_global_templates_preserve_or_explicitly_clear_annotations(self):
        doc=notes.set_header(self.doc,0,'all','Shared note')
        doc=notes.set_key(doc,0,doc['maps'][0]['cells'][0]['button_id'],'Key hint')
        doc=notes.set_header(doc,0,'map','Map hint')
        self.assertEqual(maps.validate(overlay.decode(maps.encoded(doc))),doc)
        cleared=builder.new_game(doc,'Another game')
        self.assertNotIn('comment',cleared)
        self.assertFalse(any('comment' in m or any('comment' in c for c in m['cells']) for m in cleared['maps']))
        context=copy.deepcopy(doc);builder.add_context(context,'BASIC','inventory')
        self.assertIn('comment',context);self.assertNotIn('comment',context['maps'][-1])
        self.assertFalse(any('comment' in c for c in context['maps'][-1]['cells']))


class Rendering(unittest.TestCase):
    def font(self,size,bold=False):
        from PIL import ImageFont
        root=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
        candidates=[root/('segoeuib.ttf' if bold else 'segoeui.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
        return ImageFont.truetype(str(next(p for p in candidates if p.is_file())),size)

    def test_all_views_keep_note_small_colored_inside_button_and_separate_from_main_text(self):
        from PIL import Image,ImageDraw
        draw=ImageDraw.Draw(Image.new('RGB',(10,10)))
        cell=dict(sources.fixtures.document()['maps'][0]['cells'][0],display_key='K',display_action='Jump')
        notes.set_value(cell,'Optional hint in a different color','Cyan',160)
        for height in (60,86,113,150):
            for width in (60,146,180):
                button=dict(width=width,height=height)
                for view in overlay.VIEWS:
                    for scale in (.5,1,2):
                        runs,_,_=notes.cell_layout(cell,button,view,lambda t,s,b:draw.textlength(t,font=self.font(s,b)),scale,scale,
                                                  line_height=lambda s,b:self.font(s,b).getbbox('Agjy')[3]+2)
                        boxes=[]
                        for run in runs:
                            box=draw.textbbox((run['x'],run['y']),run['text'],font=self.font(run['size'],run['bold']),stroke_width=1)
                            self.assertGreaterEqual(box[0],2);self.assertGreaterEqual(box[1],2)
                            self.assertLessEqual(box[2],width-2);self.assertLessEqual(box[3],height-2)
                            boxes.append((run['role'],box))
                            if run['role']=='comment':self.assertLessEqual(run['size'],12);self.assertEqual(run['color'],notes.COLORS['Cyan'])
                        self.assertEqual(any(r['role']=='key' for r in runs),view!='Actions')
                        self.assertEqual(any(r['role']=='action' for r in runs),view!='Keys')
                        for role,box in boxes:
                            if role=='comment':
                                for other,main in boxes:
                                    if other!='comment':self.assertLessEqual(main[3],box[1],f'{width}x{height} {view} {scale}: {runs}')

    def test_render_headers_below_subtitle_and_comments_remain_visible_in_all_views(self):
        from PIL import ImageDraw
        doc=sources.fixtures.document();bid=doc['maps'][0]['cells'][0]['button_id']
        doc=notes.set_key(doc,0,bid,'Hint','Cyan');doc=notes.set_header(doc,0,'all','Shared note','Amber');doc=notes.set_header(doc,0,'map','Layer note','Pink')
        original=ImageDraw.ImageDraw.text
        with tempfile.TemporaryDirectory() as folder:
            for view in overlay.VIEWS:
                seen=[]
                def capture(draw,xy,text,*args,**kwargs):
                    seen.append((text,xy,kwargs.get('fill'),kwargs.get('font')))
                    return original(draw,xy,text,*args,**kwargs)
                with mock.patch.object(ImageDraw.ImageDraw,'text',capture):maps.render(doc,doc['maps'][0],Path(folder)/(view+'.png'),view)
                hint=next(row for row in seen if row[0]=='Hint');self.assertEqual(hint[2],notes.COLORS['Cyan']);self.assertLessEqual(hint[3].size,12)
                shared=next(row for row in seen if row[0]=='Shared note');specific=next(row for row in seen if row[0]=='Layer note')
                self.assertGreater(shared[1][1],53);self.assertLess(shared[1][1],specific[1][1]);self.assertLess(specific[1][1],114)

    def test_empty_comments_do_not_change_unannotated_pixels(self):
        doc=sources.fixtures.document();empty=copy.deepcopy(doc)
        empty['comment']=dict(text='',color=notes.DEFAULT_COLOR)
        empty['maps'][0]['comment']=dict(text='',color=notes.DEFAULT_COLOR)
        empty['maps'][0]['cells'][0]['comment']=dict(text='',color=notes.DEFAULT_COLOR)
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/'a.png',Path(folder)/'b.png'
            for view in overlay.VIEWS:
                maps.render(doc,doc['maps'][0],a,view);maps.render(empty,empty['maps'][0],b,view)
                self.assertEqual(a.read_bytes(),b.read_bytes())


class Persistence(unittest.TestCase):
    def setUp(self): sources.Sources.setUp(self)

    def test_save_publish_exports_and_templates_keep_comment_separate_from_native_bindings(self):
        doc=notes.set_header(self.doc,0,'all','Shared comment')
        doc=notes.set_key(doc,0,doc['maps'][0]['cells'][0]['button_id'],'Hint','Cyan')
        before,sha=self.library.store.load();native=copy.deepcopy(before['manifest']['keymaps'])
        self.library.save_source(doc,self.keymap,self.saved)
        result=self.library.publish(doc,self.keymap,sha)
        value,_=self.library.store.load();self.assertEqual(value['manifest']['keymaps'],native)
        self.assertFalse(result['native_changes']);self.assertEqual(self.library.current('game'),doc)
        data=exchange.export_keymaps({'game':doc},{'keymap':self.keymap},'map','game',0)
        self.assertEqual(builder.validate_package(overlay.decode(maps.encoded(data))),data)
        preset=exchange.make_template(doc,self.keymap,'With notes',True)
        self.assertEqual(preset['document']['comment'],doc['comment'])
        self.assertEqual(preset['document']['maps'],doc['maps'])
        blank=exchange.make_template(doc,self.keymap,'Clean template')
        self.assertNotIn('comment',blank['document'])
        self.assertEqual(maps.output_matrix(doc),maps.output_matrix(self.doc))


class GuestUI(unittest.TestCase):
    def setUp(self):sources.GuestEditor.setUp(self)

    def fill(self,dialog,text,color='Cyan'):
        from tkinter import ttk
        form=dialog.winfo_children()[0]
        entry=next(w for w in form.winfo_children() if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox))
        entry.delete(0,'end');entry.insert(0,text)
        combo=next(w for w in form.winfo_children() if isinstance(w,ttk.Combobox));combo.set(color)
        next(w for w in form.winfo_children() if isinstance(w,ttk.Button)).invoke();self.root_ui.update()

    def test_key_comment_dialog_draft_preview_save_and_json_color_persistence(self):
        before=self.library.store.load()[1];bid=self.editor.selected_button
        dialog=self.editor.comment_editor('key');self.fill(dialog,'Tap once')
        self.assertEqual(self.library.store.load()[1],before);self.assertNotIn('comment',self.library.current('game')['maps'][0]['cells'][0])
        for view in overlay.VIEWS:
            self.editor.view_choices.buttons[view].invoke();self.root_ui.update()
            texts=[self.editor.canvas.itemcget(i,'text') for i in self.editor.canvas.find_withtag('key-comment')]
            self.assertTrue(texts)
            for item in self.editor.canvas.find_withtag('key-comment'):self.assertEqual(self.editor.canvas.itemcget(item,'fill'),notes.COLORS['Cyan'])
        self.editor.save();stored=self.library.current('game')
        cell=next(c for c in stored['maps'][0]['cells'] if c['button_id']==bid)
        self.assertEqual(cell['comment'],dict(text='Tap once',color=notes.COLORS['Cyan']))

    def test_header_comment_scopes_cancel_and_reselection_guard(self):
        dialog=self.editor.comment_editor('all');self.fill(dialog,'Common header','Amber')
        dialog=self.editor.comment_editor('map');self.fill(dialog,'This layer','Pink')
        self.assertEqual(len(self.editor.canvas.find_withtag('header-comment')),2)
        self.editor.map_index=1;self.editor.select_button(self.editor.selected_button);self.root_ui.update()
        self.assertEqual(len(self.editor.canvas.find_withtag('header-comment')),1)
        dialog=self.editor.comment_editor('key');self.editor.map_index=0;self.editor.select_button(self.editor.selected_button)
        self.fill(dialog,'Wrong target');self.assertTrue(dialog.winfo_exists());dialog.destroy()
        self.assertFalse(any('comment' in c for m in self.editor.document['maps'] for c in m['cells']))
        self.assertNotIn('comment',self.library.current('game'))

    def test_invalid_color_and_cancel_keep_the_document_unchanged(self):
        before=copy.deepcopy(self.editor.document)
        dialog=self.editor.comment_editor('key');self.fill(dialog,'Hint','not-a-color')
        self.assertTrue(dialog.winfo_exists());self.assertEqual(self.editor.document,before);dialog.destroy()


if __name__=='__main__':unittest.main()
