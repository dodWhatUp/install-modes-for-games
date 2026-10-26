"""Bounded native-source/draft tests; no mapper, game or live Overlay writes."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolControllerKeymaps as k
import GameToolControlsPlanner as p


def native_fixture():
    return {'schemaVersion':3.0,'appVersion':'9.5.0','config':{'appName':'GENERAL'},
        'devices':{'hardware':[{'id':1,'name':'gamepad','convertToVirtual':True}], 'virtual':{'gamepads':[{'id':1,'type':'360'}]}},
        'shifts':[{'id':2,'type':'default','description':'Face buttons'}],
        'masks':[{'id':1,'set':[{'deviceId':1,'buttonId':29,'description':'XB: LeftUpperPaddle / Flydigi: M4'}]},
                 {'id':2,'set':[{'deviceId':1,'buttonId':13,'description':'Flydigi: Back'}]}],
        'mappings':[{'condition':{'mask':{'id':1,'activator':{'type':'single','mode':'hold_until_release'}}},'macros':[{'gamepad':{'id':1,'buttonId':33,'description':'DpadUp'}}]},
                    {'condition':{'mask':{'id':2,'activator':{'type':'single','mode':'hold_until_release'}}},'jumpToLayer':{'layer':2}},
                    {'condition':{'shiftId':2,'mask':{'id':1,'activator':{'type':'single','mode':'hold_until_release'}}},'macros':[{'gamepad':{'id':1,'buttonId':1,'description':'XB: A'}}]}]}


def workbook():
    source={'kind':'target','id':'fixture','snapshot':{'game_id':'doom-the-dark-ages','action_fields':[]}}
    source['revision']=p.maps.fingerprint(source['snapshot'])
    return {'kind':'game_controls_workbook','schema_version':1,'game_id':'doom-the-dark-ages','id':'fixture-controls','revision':1,'policy':p.POLICY,
        'baseline':{'map_sha256':'0'*64,'keymap_revision':'1'*64,'rules_revision':p.RULES},'sources':[source],
        'actions':[p._action('offhand','Off-hand swap','bindset-0','JOY_DPAD_UP',urgency=[3],frequency=[2]),p._action('jump','Jump','bindset-0','JOY1')],
        'exclusive_contexts':[],'pending_shared_changes':[],'change_log':[],'extensions':{}}


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.native=self.root/'native';self.path=self.native/'GENERAL/Controller/Test.rewasd';self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps(native_fixture()),encoding='utf-8');self.original=self.path.read_bytes()
    def draft(self,**kwargs):return k.draft_from_profile(self.path,'doom-the-dark-ages','DOOM',root=self.native,**kwargs)
    def test_saved_outputs_layers_and_unknown_geometry(self):
        d=self.draft();self.assertEqual(len(d['bindings']),3);self.assertEqual(d['layers'][1]['id'],'shift-2')
        self.assertEqual(d['bindings'][0]['controls'][0]['label'],'Flydigi M4')
        self.assertEqual(d['bindings'][0]['outputs'][0]['label'],'DpadUp');self.assertFalse(d['device']['physical_acceptance'])
        self.assertEqual(d['bindings'][0]['annotations'],{});self.assertEqual(self.original,self.path.read_bytes())
    def test_only_named_direction_crosswalk_seeds_game_action_and_icon(self):
        d=self.draft(workbook=workbook());a=d['bindings'][0]['annotations']['gameplay']
        self.assertEqual(a['label'],'Off-hand swap');self.assertEqual(a['icon'],'swap');self.assertEqual(a['evidence'],'semantic_crosswalk')
        self.assertEqual(d['bindings'][2]['annotations'],{});self.assertIn('Jump',[a['label']for a in d['action_catalog']])
        self.assertIn('Saved game action catalog (2 rows)',k.preview_html(d))
    def test_direction_id_without_exact_description_is_not_assumed(self):
        v=native_fixture();v['mappings'][0]['macros'][0]['gamepad']['description']='Unknown';self.path.write_text(json.dumps(v))
        self.assertEqual(self.draft(workbook=workbook())['bindings'][0]['annotations'],{})
    def test_bundle_labels_and_source_unknowns_are_retained(self):
        w=workbook();w['actions'].append(p._action('second','Unresolved support (?)','bindset-0','JOY_DPAD_UP'))
        a=self.draft(workbook=w)['bindings'][0]['annotations']['gameplay'];self.assertIn('Unresolved support (?)',a['label']);self.assertEqual(len(a['action_ids']),2)
    def test_radial_sector_is_native_menu_evidence_not_game_action(self):
        v=native_fixture();v['shifts'].append({'id':3,'type':'radialMenu'});v['masks'].append({'id':3,'radialMenuSet':[{'circleId':1,'sectorId':2}]})
        v['mappings'].append({'condition':{'shiftId':3,'mask':{'id':3}},'macros':[{'keyboard':{'buttonId':23,'description':'DIK_I'}}]})
        self.path.write_text(json.dumps(v));d=self.draft();row=d['bindings'][-1]
        self.assertEqual(row['controls'][0]['label'],'reWASD radial circle 1 / sector 2')
        self.assertNotIn('gameplay',row['annotations']);self.assertEqual(row['annotations']['rewasd-radial']['evidence'],'saved_config')
    def test_foreign_game_research_rejected(self):
        w=workbook();w['game_id']='other'
        with self.assertRaises(ValueError):self.draft(workbook=w)
    def test_duplicate_native_mask_and_missing_layer_refused(self):
        v=native_fixture();v['masks'].append(copy.deepcopy(v['masks'][0]));self.path.write_text(json.dumps(v))
        with self.assertRaises(ValueError):self.draft()
        v=native_fixture();v['mappings'][0]['condition']['shiftId']=9;self.path.write_text(json.dumps(v))
        with self.assertRaises(ValueError):self.draft()
    def test_annotation_changes_no_native_output_or_mapping(self):
        d=self.draft();new=k.annotate(d,d['bindings'][0]['id'],'gameplay','Custom action','attack')
        self.assertEqual(d['bindings'][0]['native_mapping'],new['bindings'][0]['native_mapping']);self.assertEqual(self.original,self.path.read_bytes())
        self.assertEqual(d['bindings'][0]['annotations'],{});self.assertEqual(new['bindings'][0]['annotations']['gameplay']['evidence'],'user_label')
    def test_stale_source_export_refused_without_creating_output(self):
        d=self.draft();self.path.write_bytes(self.original+b' ');out=self.root/'export'
        with self.assertRaises(ValueError):k.export_bundle(d,out,self.native)
        self.assertFalse(out.exists());self.assertEqual(k.source_status(d,self.native)['state'],'changed')
    def test_source_path_cannot_escape_native_root(self):
        d=self.draft();d['source']['config_reference']='../escape.rewasd'
        with self.assertRaises(ValueError):k.validate(d)
    def test_draft_cannot_alter_native_inventory_under_valid_hash(self):
        d=self.draft();d['bindings'][0]['outputs'][0]['label']='Different output'
        with self.assertRaises(ValueError):k.export_bundle(d,self.root/'export',self.native)
        self.assertFalse((self.root/'export').exists())
    def test_research_needs_fresh_owner_before_export(self):
        d=self.draft(workbook=workbook())
        with self.assertRaises(ValueError):k.export_bundle(d,self.root/'export',self.native)
        self.assertFalse((self.root/'export').exists())
    def test_save_history_drift_and_explicit_exports(self):
        d=self.draft();lib=k.DraftLibrary(self.root/'app',self.native);pin=lib.save(d)
        new=k.annotate(d,d['bindings'][0]['id'],'gameplay','Changed','use');lib.save(new,pin)
        self.assertTrue((lib.root/'history'/d['id']/(pin+'.json')).exists())
        with self.assertRaises(ValueError):lib.save(d,pin)
        out=self.root/'export';r=k.export_bundle(new,out,self.native);self.assertFalse(r['overlay_published'])
        self.assertTrue((out/'controller-preview.html').is_file());self.assertEqual(self.original,self.path.read_bytes())
        with self.assertRaises(ValueError):k.export_bundle(new,out,self.native)
    def test_preview_escapes_labels_and_uses_neutral_controller(self):
        d=self.draft();d=k.annotate(d,d['bindings'][0]['id'],'gameplay','<script>alert(1)</script>','unknown')
        text=k.preview_html(d);self.assertIn('&lt;script&gt;',text);self.assertNotIn('<script>alert',text)
        self.assertIn('STANDARD FRONT',text);self.assertIn('REAR',text);self.assertIn('positions unverified',text)


if __name__=='__main__':unittest.main(verbosity=2)
