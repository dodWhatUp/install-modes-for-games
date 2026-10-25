"""Alternate images, scoped settings and isolated editor tests; no global input."""
import copy,importlib.util,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as api
import GameToolOverlayAlternate as alt
import GameToolOverlayAppearance as looks
import GameToolKeymapDocument as maps
spec=importlib.util.spec_from_file_location('builder_sources',Path(__file__).with_name('Test-KeymapBuilder.py'))
sources=importlib.util.module_from_spec(spec);spec.loader.exec_module(sources)


class Contracts(unittest.TestCase):
    def setUp(self):sources.Sources.setUp(self)

    def test_strict_inputs_timing_and_scopes(self):
        value=alt.defaults();self.assertEqual(alt.effective(value,'game')['window_ms'],300)
        value['games']['game']=dict(alt.rule(),double_press=False,chord=['Ctrl','XButton1'])
        self.assertFalse(alt.effective(value,'game')['double_press']);self.assertTrue(alt.effective(value,'other')['double_press'])
        self.assertEqual(alt.validate(api.decode(api.encode(value))),value)
        for updates in ({'window_ms':149},{'window_ms':601},{'window_ms':True},{'chord':['Ctrl']},{'chord':['Ctrl','Ctrl']},{'chord':['Ctrl','WheelUp']},{'chord':['Ctrl','Run script']},{'behavior':'run'}):
            with self.assertRaises(ValueError):alt.validate_rule(dict(alt.rule(),**updates))

    def test_view_save_and_exact_layer_context_relay_never_changes_normal_selection(self):
        original,sha=self.library.store.load();settings=alt.defaults();settings['global_rule']['target']['view']='Keys'
        saved,raw=alt.save(self.library.store,settings,None)
        self.assertEqual(self.library.store.load(),(original,sha));self.assertEqual(self.library.current('game'),self.doc)
        self.library.publish(self.doc,self.keymap,sha)
        value,_=self.library.store.load();index=api.validate_store(value)
        group=next(g for g in index['groups'].values() if g['id'].startswith('builder-'))
        asset=next(index['assets'][aid] for aid in group['asset_ids'] if index['assets'][aid]['view']=='Combined')
        result=dict(game_id='game',group_id=group['id']);fields=alt.relay_fields(self.library.store,index,result,asset)
        expected=next(index['assets'][aid] for aid in group['asset_ids'] if all(index['assets'][aid][k]==asset[k] for k in ('layer','context')) and index['assets'][aid]['view']=='Keys')
        self.assertEqual(fields['AltSHA256'],expected['sha256']);self.assertEqual(fields['AltWindowMs'],'300')
        self.assertEqual(fields['AltChord'],'');self.assertEqual(fields['AltBehavior'],'hold')
        self.assertEqual(saved,alt.read(self.library.store.directory)[0])
        self.assertEqual(asset['view'],'Combined')

    def test_preset_snapshot_preparation_and_source_drift_refusal(self):
        value,sha=self.library.store.load();self.library.publish(self.doc,self.keymap,sha)
        value,sha=self.library.store.load();index=api.validate_store(value)
        setting=alt.defaults();style=looks.default_style();style.update(view='ActionFirst',action_text_percent=125,key_text_percent=75,background='buttons')
        setting['global_rule']['target']=dict(kind='preset',name='Readable',style=style)
        saved,raw=alt.save(self.library.store,setting,None)
        self.assertTrue(saved['prepared'])
        for gid in {r['group'] for r in saved['prepared']}:
            expected={(index['assets'][aid]['layer'],index['assets'][aid]['context']) for aid in index['groups'][gid]['asset_ids']}
            self.assertEqual({(r['layer'],r['context']) for r in saved['prepared'] if r['group']==gid},expected)
        self.assertEqual(self.library.store.load(),(value,sha));self.assertEqual(self.library.current('game'),self.doc)
        row=saved['prepared'][0];asset=next(a for a in index['assets'].values() if a['layer']==row['layer'] and a['context']==row['context'])
        result=dict(game_id='game',group_id=row['group'])
        fields=alt.relay_fields(self.library.store,index,result,asset)
        self.assertEqual(fields['AltEnabled'],'1');self.assertEqual(fields['Alt_opacity'],'100')
        self.assertTrue(Path(fields['AltFile']).is_file())
        doc=copy.deepcopy(self.doc);doc['title']='Changed source';self.library.save_source(doc,self.keymap,maps.fingerprint(self.doc))
        self.assertEqual(alt.relay_fields(self.library.store,index,result,asset),{'AltEnabled':'0'})

    def test_stale_cancelled_and_bad_optional_settings_preserve_normal_data(self):
        setting=alt.defaults();before=self.library.store.load()
        saved,raw=alt.save(self.library.store,setting,None)
        with self.assertRaises(ValueError):alt.save(self.library.store,setting,None)
        with self.assertRaises(ValueError):alt.save(self.library.store,setting,raw,cancelled=lambda:True)
        self.assertEqual(alt.read(self.library.store.directory)[1],raw);self.assertEqual(self.library.store.load(),before)
        path=self.library.store.directory/'overlay-alternate.json';path.write_text('{broken')
        self.assertEqual(alt.relay_fields(self.library.store,api.validate_store(before[0]),dict(game_id='game',group_id='x'),{}),{'AltEnabled':'0'})


@unittest.skipUnless(os.name=='nt','Headless Windows AHK handlers')
class ActualHost(unittest.TestCase):
    def test_actual_handlers_with_inert_rendering_and_clock_key_state_fixtures(self):
        root=Path(__file__).resolve().parents[2]
        host=(root/'examples/game-input/AzeronOverlayStudio.integrated.ahk').read_text(encoding='utf-8-sig')
        methods=host[host.index('    KeyDown(i, *) {'):host.index('    ShowSlot(i, resolvedSlot := 0) {')]
        text=Path(__file__).with_suffix('.ahk').read_text(encoding='utf-8-sig')
        text=text.replace('    WriteLog(*) {',methods+'    WriteLog(*) {')
        text=text.replace('host.Route := this','host.Route := this, host.GroupRoute := this, host.TotalEvents := 0, host.Slots[1].Key := "F24", host.Slots[1].Name := "inert", host.Pictures := AltPictures(this)')
        text=text.replace('route.Down()','route.Host.KeyDown(1)').replace('route.Up()','route.Host.KeyUp(1)')
        text=text.replace('RunAltChecks(normal,alternate) {','class AltPictures {\n    __New(route) {\n        this.Route := route\n    }\n    ResolveSlot(i,unused,active) => this.Route.Resolve(i,this.Route.Host.Slots[i])\n}\nRunAltChecks(normal,alternate) {')
        text=text.replace('%A_ScriptDir%\\..\\..\\examples\\game-input\\',str(root/'examples/game-input')+'\\')
        ahk=Path(os.environ['LOCALAPPDATA'])/'Programs/AutoHotkey/v2/AutoHotkey64.exe'
        if not ahk.is_file():self.skipTest('AHK unavailable')
        from PIL import Image
        with tempfile.TemporaryDirectory(prefix='ActualAltHost-') as folder:
            folder=Path(folder);script=folder/'check.ahk';script.write_text(text,encoding='utf-8')
            a,b=folder/'normal.png',folder/'alternate.png';Image.new('RGBA',(16,16),'red').save(a);Image.new('RGBA',(16,16),'blue').save(b)
            result=subprocess.run([str(ahk),'/ErrorStdOut',str(script),str(a),str(b)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('PASS 23',result.stdout)


class GuestUI(unittest.TestCase):
    def setUp(self):
        sources.GuestEditor.setUp(self)
        from GameToolOverlayAlternateUI import AlternateEditor
        self.ui=AlternateEditor(self.root_ui,self.library.store);self.root_ui.update()

    def test_keyboard_and_mouse_combination_scope_save_worker_and_normal_overlay_preserved(self):
        before=self.library.store.load();self.ui.chord[0].set('Ctrl');self.ui.chord[1].set('Mouse Back')
        self.ui.window_ms.set('350');self.ui.commit();deadline=time.monotonic()+20
        while self.ui.busy and time.monotonic()<deadline:self.root_ui.update();time.sleep(.02)
        self.assertFalse(self.ui.busy);saved,_=alt.read(self.library.store.directory)
        self.assertEqual(saved['global_rule']['chord'],['Ctrl','XButton1']);self.assertEqual(saved['global_rule']['window_ms'],350)
        self.assertEqual(self.library.store.load(),before)
        self.ui.scope.set(next(label for label,g in self.ui.scopes.items() if g=='game'));self.ui.load_scope()
        self.assertTrue(self.ui.inherit.get());self.assertEqual(str(self.ui.speed.cget('state')),'disabled')
        self.ui.inherit.set(False);self.ui.refresh();self.ui.window_ms.set('400')
        candidate=self.ui.candidate();self.assertEqual(candidate['games']['game']['window_ms'],400);self.assertEqual(candidate['global_rule']['window_ms'],350)

    def test_invalid_combination_and_close_do_not_save(self):
        self.ui.chord[0].set('Wheel Up');self.ui.commit();self.root_ui.update()
        self.assertFalse(self.ui.busy);self.assertIn('lists',self.ui.message.get())
        self.ui.close();self.assertIsNone(alt.read(self.library.store.directory)[1])

if __name__=='__main__':unittest.main()
