"""JSON transfer, scope/conflict isolation and guest UI; no native/game input."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as overlay
import GameToolOverlayAppearance as looks
import GameToolOverlayAppearanceExchange as appearances
import GameToolKeymapExchange as exchange
import GameToolKeymapBuilder as builder
import GameToolKeymapDocument as maps

spec=importlib.util.spec_from_file_location('sources',Path(__file__).with_name('Test-KeymapBuilder.py'))
sources=importlib.util.module_from_spec(spec);spec.loader.exec_module(sources)


class AppearancePackages(unittest.TestCase):
    def setUp(self):
        self.games=[dict(id='game',label='Game'),dict(id='other',label='Other')]
        value=overlay.empty_store();value['manifest']['games']=self.games
        self.policy=looks.policy(value)
        self.policy,self.global_id=looks.save_preset(self.policy,None,'Global comfort',looks.default_style())
        self.policy,self.game_id=looks.save_preset(self.policy,'game','Game comfort',dict(looks.default_style(),action_text_percent=140))

    def test_all_global_game_and_selected_preset_scopes_roundtrip(self):
        before=copy.deepcopy(self.policy)
        for scope,count in [('all',5),('global',2),('game',2),('preset',1)]:
            value=appearances.export_package(self.policy,self.games,scope,game='game',preset=self.game_id)
            self.assertEqual(len(value['presets']),count)
            self.assertEqual(appearances.validate(overlay.decode(overlay.encode(value))),value)
            if scope=='global':self.assertEqual(value['games'],[])
            if scope in {'game','preset'}:self.assertEqual(value['games'],[self.games[0]])
        self.assertEqual(self.policy,before)

    def test_import_only_library_idempotent_keep_and_explicit_copy_replace(self):
        package=appearances.export_package(self.policy,self.games,'preset',preset=self.game_id)
        package['presets'][0]['style']['key_text_percent']=150
        kept,rows=appearances.import_plan(package,self.policy,{'game','other'})
        self.assertEqual(kept,self.policy);self.assertEqual(rows[0]['action'],'Keep existing')
        copied,rows=appearances.import_plan(package,self.policy,{'game','other'},conflict='copy')
        self.assertEqual(len(copied['presets']),3);self.assertIn('imported',rows[0]['name'])
        replaced,rows=appearances.import_plan(package,self.policy,{'game','other'},conflict='replace')
        self.assertEqual(replaced['presets'][self.game_id]['style']['key_text_percent'],150)
        self.assertEqual(replaced['global'],self.policy['global']);self.assertEqual(replaced['games'],self.policy['games'])

    def test_missing_destination_game_requires_explicit_scope_mapping(self):
        package=appearances.export_package(self.policy,self.games,'preset',preset=self.game_id)
        empty=dict(schema_version=1,**{'global':looks.default_style()},games={},presets={})
        with self.assertRaisesRegex(ValueError,'Destination lacks'):appearances.import_plan(package,empty,set())
        candidate,rows=appearances.import_plan(package,empty,set(),target=None)
        self.assertIsNone(candidate['presets'][rows[0]['id']]['scope'])

    def test_imported_current_snapshots_can_be_exported_again(self):
        package=appearances.export_package(self.policy,self.games,'all')
        candidate,_=appearances.import_plan(package,self.policy,{'game','other'})
        again=appearances.export_package(candidate,self.games,'all')
        self.assertEqual(len(again['presets']),len(package['presets']))

    def test_unknown_fields_bad_sizes_duplicate_and_nonfinite_json_refuse(self):
        valid=appearances.export_package(self.policy,self.games,'global')
        for mutate in (lambda x:x.update(command='run'),lambda x:x['presets'][0]['style'].update(action_text_percent=201),
                       lambda x:x['presets'].append(copy.deepcopy(x['presets'][0])),lambda x:x['presets'][0].update(scope='absent')):
            value=copy.deepcopy(valid);mutate(value)
            with self.assertRaises(ValueError):appearances.validate(value)
        with self.assertRaises(ValueError):overlay.decode(b'{"size": NaN}')
        with self.assertRaises(ValueError):overlay.decode(b'{"a":1,"a":2}')


class KeymapPackages(unittest.TestCase):
    def setUp(self):
        sources.Sources.setUp(self)
        self.documents={'game':self.doc,'other':builder.new_game(self.doc,'Other','other')}
        self.keymaps={'keymap':self.keymap}

    def test_full_game_and_single_map_packages_keep_keys_actions_and_geometry(self):
        original=copy.deepcopy(self.documents)
        for scope,games,count in [('all',2,4),('game',1,2),('map',1,1)]:
            value=exchange.export_keymaps(self.documents,self.keymaps,scope,'game',1)
            self.assertEqual(len(value['documents']),games);self.assertEqual(sum(len(d['maps']) for d in value['documents']),count)
            self.assertEqual(builder.validate_package(overlay.decode(maps.encoded(value))),value)
            for doc in value['documents']:self.assertEqual(doc['buttons'],self.doc['buttons'])
        self.assertEqual(self.documents,original)
        single=exchange.export_keymaps(self.documents,self.keymaps,'map','game',1)['documents'][0]
        self.assertEqual(builder.merge_maps(self.doc,single),self.doc)

    def test_template_defaults_clear_actions_keep_keys_and_can_retain_labels_explicitly(self):
        blank=exchange.make_template(self.doc,self.keymap,'Shared blank')
        labeled=exchange.make_template(self.doc,self.keymap,'Labeled',True)
        self.assertEqual(builder.map_outputs(blank['document']),builder.map_outputs(self.doc))
        self.assertFalse(any(c['action'] for m in blank['document']['maps'] for c in m['cells']))
        self.assertEqual(labeled['document']['maps'],self.doc['maps'])
        game,keymap=exchange.new_game(labeled,'New game')
        self.assertNotEqual(game['game_id'],self.doc['game_id']);self.assertEqual(game['maps'],self.doc['maps']);self.assertEqual(keymap,self.keymap)
        self.assertEqual(self.library.current('game'),self.doc)

    def test_global_template_store_roundtrip_history_stale_and_conflict_choices(self):
        store=exchange.Templates(self.root/'global')
        preset=exchange.make_template(self.doc,self.keymap,'Comfort')
        first=store.add(preset,'absent');value,_=store.load()
        same,expected,rows=store.import_plan(value);self.assertEqual(same,value)
        copied,_,rows=store.import_plan(value,'copy');self.assertEqual(len(copied['presets']),2)
        self.assertNotEqual(copied['presets'][0]['id'],copied['presets'][1]['id'])
        second=store.write(copied,expected);self.assertNotEqual(first,second)
        self.assertTrue((store.directory/('keymap-global-presets-before-'+first+'.json')).is_file())
        with self.assertRaisesRegex(ValueError,'changed'):store.write(value,first)
        self.assertEqual(store.load()[1],second)

    def test_preset_import_refuses_unknown_fields_and_native_contract_collisions(self):
        a=exchange.make_template(self.doc,self.keymap,'A');b=exchange.make_template(self.doc,self.keymap,'B')
        value=dict(schema_version=1,kind='global_keymap_package',presets=[a,b]);exchange.validate_templates(value)
        b['keymap']['outputs_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'collision'):exchange.validate_templates(value)
        value=dict(schema_version=1,kind='global_keymap_package',presets=[a]);value['presets'][0]['command']='run'
        with self.assertRaises(ValueError):exchange.validate_templates(value)

    def test_exports_and_imported_presets_leave_active_registry_and_sources_untouched(self):
        before=self.library.store.load()[1];raw=self.library.path('game').read_bytes()
        store=exchange.Templates(self.library.store.directory)
        preset=exchange.make_template(self.doc,self.keymap,'Global')
        store.add(preset,'absent');exchange.export_keymaps(self.documents,self.keymaps,'all')
        self.assertEqual(self.library.store.load()[1],before);self.assertEqual(self.library.path('game').read_bytes(),raw)


class GuestUI(unittest.TestCase):
    def setUp(self):
        sources.GuestEditor.setUp(self)
        from GameToolOverlayAppearanceUI import Editor
        self.appearance=Editor(self.panel);self.addCleanup(self.appearance.close)
        self.root_ui.update()

    def test_keymap_export_dialog_scopes_are_real_packages_and_do_not_save_drafts(self):
        from GameToolMapExchangeUI import KeymapExport
        window=KeymapExport(self.editor,'all');self.addCleanup(window.window.destroy)
        before=self.library.store.load()[1]
        for scope,count in [('all',2),('game',2),('map',1)]:
            window.scope.select(scope);window.refresh();self.root_ui.update()
            self.assertEqual(sum(len(d['maps']) for d in window.payload()['documents']),count)
        self.assertEqual(self.library.store.load()[1],before)

    def test_appearance_import_review_cancel_and_explicit_commit_do_not_activate(self):
        from GameToolMapExchangeUI import AppearanceImport,AppearanceExport
        export=AppearanceExport(self.appearance);self.addCleanup(export.window.destroy)
        export.scope.select('global');payload=export.payload();path=self.root/'looks.json';builder.write_new(path,payload)
        before=self.library.store.load()[0]
        review=AppearanceImport(self.appearance,path);self.root_ui.update()
        self.assertIsNotNone(review.candidate);self.assertEqual(self.library.store.load()[0],before)
        review.commit();after=self.library.store.load()[0]
        self.assertEqual(after['manifest'],before['manifest'])
        self.assertEqual(after['preferences']['selections'],before['preferences']['selections'])
        self.assertEqual(len(after['preferences']['appearance']['presets']),1)

    def test_global_template_dialog_persists_only_template_library(self):
        from GameToolMapExchangeUI import GlobalTemplates
        from tkinter import ttk
        manager=GlobalTemplates(self.editor);self.addCleanup(manager.window.destroy)
        before=self.library.store.load()[1];dialog=manager.save_current();self.root_ui.update()
        form=dialog.winfo_children()[0];next(w for w in form.winfo_children() if isinstance(w,ttk.Button)).invoke();self.root_ui.update()
        self.assertEqual(len(manager.value['presets']),1)
        self.assertEqual(self.library.store.load()[1],before)
        self.assertEqual(self.library.current('game'),self.doc)

    def test_export_buttons_write_roundtrippable_json_to_selected_files(self):
        from GameToolMapExchangeUI import KeymapExport,AppearanceExport
        dialogs=[KeymapExport(self.editor,'map'),AppearanceExport(self.appearance)]
        for i,dialog in enumerate(dialogs):
            self.addCleanup(dialog.window.destroy)
            target=self.root/('ui-export-'+str(i)+'.json')
            with mock.patch('GameToolMapExchangeUI.filedialog.asksaveasfilename',return_value=str(target)):
                dialog.export()
            saved=overlay.decode(overlay.read(target))
            self.assertEqual(saved,dialog.payload())


if __name__=='__main__':unittest.main()
