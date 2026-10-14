"""Cross-game and hostile-pack regression tests using only fictional local files."""
from __future__ import annotations
import copy,hashlib,io,json,os,shutil,stat,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
SCRIPTS=Path(__file__).absolute().parents[2];ROOT=SCRIPTS.parent
sys.path.insert(0,str(SCRIPTS))
from game_keybind_ops.core import Service,sha,compile_changes
from game_keybind_ops.documents import Document
from game_keybind_ops.deps import Error,object_hash
from game_keybind_ops.packs import *
from game_keybind_ops.effective import inspect_instance,intent_preview,instance,key_overlap,resolved
from game_keybind_ops.pack_transport import export_pack_local,inspect_archive,unpack_pack_local
from game_keybind_ops.authoring import scaffold,learn_difference,inventory,planner_bridge,troubleshoot
from game_keybind_ops.store_discovery import steam_installations,epic_installations
from game_keybind_ops.key_codec import canonical_chord,encode,unreal_chords
from game_keybind_ops.adapter_registry import Adapter,register_adapter,capabilities

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.s=Service(self.root/'state',process_reader=lambda:set());self.n=0
    def tearDown(self):self.tmp.cleanup()
    def failcode(self,code,fn):
        with self.assertRaises(Error) as c:fn()
        self.assertEqual(c.exception.code,code)
    def sample(self,kind='json'):
        self.n+=1;dest=self.root/('author-'+str(self.n));shutil.copytree(ROOT/'game-packs/format-examples'/('sample-'+kind),dest);return dest
    def write_pack(self,folder,p): (folder/'pack.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def import_(self,folder):
        report=inspect_pack(folder)
        return import_pack_local(self.s,folder,report['pack_sha256'],authorize=lambda _:True)['pin']
    def binding(self,folder,ident='installation',overrides=None):
        pin=self.import_(folder);p=load_pin(self.s,pin);game=self.root/(ident+'-native');game.mkdir();bindings={};hashes={};paths={}
        for f in p['files']:
            data=next((folder/ff['before']).read_bytes() for ff in p['fixtures'] if ff['file_id']==f['id'])
            data=(overrides or {}).get(f['id'],data);file=game/f['locations'][0]['pattern'];file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
            bindings[f['id']]={'root':str(game),'relative':file.relative_to(game).as_posix()};hashes[f['id']]=sha(data);paths[f['id']]=file
        state=bind_instance_local(self.s,pin,ident,p['variants'][0]['id'],bindings,hashes,authorize=lambda _:True,evidence='Test fixture active owner; no real game installed.')
        return state,paths,pin
    def view(self,ident='installation',changes=None):
        state=inspect_instance(self.s,ident)
        return intent_preview(self.s,ident,changes or [{'action':'use','context':'gameplay','key':'F'}],state['revision'])
    def apply(self,v):
        p=self.s.prepare(v['items_request'],v['preview_sha256']);r=self.s.apply_local(p['plan_id'],p['plan_sha256'],authorize=lambda _:True)
        self.assertEqual(r['status'],'APPLIED_FILES_RUNTIME_UNVERIFIED');return p
    def roundtrip(self,kind):
        folder=self.sample(kind);state,paths,pin=self.binding(folder);before=paths['input'].read_bytes()
        p=self.apply(self.view());after=paths['input'].read_bytes();self.assertNotEqual(before,after)
        self.assertEqual(inspect_pack(folder)['fixtures'][0]['status'],'PASS')
        self.assertTrue(inspect_instance(self.s,'installation')['gameplay_verified'] is False)
        inverse=self.s.exact_rollback_preview(p['plan_id']);undo=self.s.prepare_rollback(p['plan_id'],inverse['preview_sha256'])
        self.s.apply_local(undo['plan_id'],undo['plan_sha256'],authorize=lambda _:True);self.assertEqual(paths['input'].read_bytes(),before)

class RoundTrips(Base):pass
for kind in ('json','jsonc','ini','ini-sparse','ue-ini','ue-chord','xml','cfg-bind','keyvalues','colon-lines'):
    def run(self,k=kind):self.roundtrip(k)
    setattr(RoundTrips,'test_full_'+kind.replace('-','_'),run)

class Packs(Base):
    def test_scaffold_not_supported(self):
        dest=self.root/'new';scaffold(dest,'new-game','New game');r=inspect_pack(dest);self.assertFalse(r['eligible_for_local_review'])
    def test_scaffold_does_not_overwrite(self):
        dest=self.root/'new';scaffold(dest,'new-game','New game');self.failcode('DEST_EXISTS',lambda:scaffold(dest,'new-game','Again'))
    def test_completely_new_game_needs_no_core_edit(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());p['id']=p['game_id']='never-seen-before';p['title']='Entirely new fictional game';self.write_pack(folder,p)
        before={f.relative_to(SCRIPTS).as_posix():sha(f.read_bytes()) for f in SCRIPTS.rglob('*.py')}
        self.binding(folder);self.apply(self.view());after={f.relative_to(SCRIPTS).as_posix():sha(f.read_bytes()) for f in SCRIPTS.rglob('*.py')}
        self.assertEqual(before,after)
    def test_no_approval_no_import(self):
        folder=self.sample();r=inspect_pack(folder);self.failcode('LOCAL_APPROVAL_REQUIRED',lambda:import_pack_local(self.s,folder,r['pack_sha256'],authorize=lambda _:False));self.assertFalse((self.s.root/'packs').exists())
    def test_changed_review_digest(self):
        folder=self.sample();r=inspect_pack(folder);(folder/'NOTES.md').write_text('Later work');self.failcode('PACK_CHANGED',lambda:import_pack_local(self.s,folder,r['pack_sha256'],authorize=lambda _:True))
    def test_same_import_idempotent(self):
        folder=self.sample();a=self.import_(folder);r=import_pack_local(self.s,folder,a['sha256'],authorize=lambda _:True);self.assertEqual(r['status'],'ALREADY_IMPORTED_NOT_ACTIVATED')
    def test_exact_version_cannot_be_overwritten(self):
        folder=self.sample();self.import_(folder);(folder/'NOTES.md').write_text('A different revision');self.failcode('PACK_CHANGED',lambda:self.import_(folder))
    def test_pinned_payload_drift(self):
        folder=self.sample();pin=self.import_(folder);(stored_folder(self.s,pin)/'payload'/'NOTES.md').write_text('Unexpected change');self.failcode('PACK_CHANGED',lambda:load_pin(self.s,pin))
    def test_new_revision_keeps_old_pin(self):
        folder=self.sample();a=self.import_(folder);p=json.loads((folder/'pack.json').read_text());p['version']='2.0.0';self.write_pack(folder,p);b=self.import_(folder)
        self.assertEqual(load_pin(self.s,a)['version'],'1.0.0');self.assertEqual(load_pin(self.s,b)['version'],'2.0.0');self.assertEqual(len(list_packs(self.s)),2)
    def test_draft_cannot_bind(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());p['evidence']['stage']='draft';self.write_pack(folder,p);pin=self.import_(folder)
        self.failcode('PACK_DRAFT',lambda:bind_instance_local(self.s,pin,'instance','keyboard',{}, {},authorize=lambda _:True,evidence='No'))
    def test_false_inventory_not_ready(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());p['files'][0]['inventory_complete']=False;p['fixtures']=[];self.write_pack(folder,p);self.assertFalse(inspect_pack(folder)['eligible_for_local_review'])
    def test_missing_adapter_is_explicit(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());p['files'][0]['adapter']='unresolved-native';self.write_pack(folder,p);r=inspect_pack(folder);self.assertEqual(r['missing_adapters'],['unresolved-native']);self.assertFalse(r['eligible_for_local_review'])
    def test_new_schema_refused(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());p['schema_version']=999;self.write_pack(folder,p);self.failcode('PACK_SCHEMA',lambda:inspect_pack(folder))
    def test_executable_hook_field_refused(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());p['run']='python evil.py';self.write_pack(folder,p);self.failcode('PACK_INVALID',lambda:inspect_pack(folder))
    def test_executable_payload_refused(self):
        folder=self.sample();(folder/'hook.py').write_text('raise Exception()');self.failcode('PACK_EXECUTABLE_BLOCKED',lambda:inspect_pack(folder))
    def test_case_alias_blocked(self):
        folder=self.sample();(folder/'PACK.JSON').write_bytes((folder/'pack.json').read_bytes());self.failcode('PACK_DUPLICATE',lambda:inspect_pack(folder))
    def test_symlink_blocked(self):
        folder=self.sample();(folder/'linked.txt').symlink_to(folder/'pack.json')
        with self.assertRaises(Error):inspect_pack(folder)
    def test_hostile_paths_blocked(self):
        for p in ('../file.json','/file.ini','c:/a.json','a\\b.ini','a/*x.ini','x\x01.json','NUL.txt','a./file.json'):
            with self.subTest(path=p),self.assertRaises(Error):portable_path(p)
    def test_recursive_discovery_blocked(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());p['files'][0]['locations'][0]['pattern']='**/*.json';self.failcode('UNSAFE_PATTERN',lambda:validate_pack(p))
    def test_fixture_must_match_exact_bytes(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());(folder/p['fixtures'][0]['after']).write_text('{}');self.failcode('FIXTURE_FAILED',lambda:inspect_pack(folder))
    def test_original_catalog_research_drafts_all_unready(self):
        dirs=list((ROOT/'game-packs/research-drafts').iterdir());self.assertEqual(len(dirs),17)
        for folder in dirs:
            with self.subTest(game=folder.name):self.assertFalse(inspect_pack(folder)['eligible_for_local_review'])
    def test_discover_many_profiles_no_autoselection(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());p['files'][0]['locations'][0]['pattern']='*/input.json'
        for name in ('user-a','user-b'):
            d=self.root/'configs'/name;d.mkdir(parents=True);(d/'input.json').write_bytes((folder/p['fixtures'][0]['before']).read_bytes())
        r=discover_pack(p,{'GAME_CONFIG':self.root/'configs'});self.assertEqual(len(r['candidates']),2);self.assertTrue(all(not x['active_verified'] for x in r['candidates']))
    def test_missing_root_no_fulldisk_search(self):
        r=discover_pack(json.loads((self.sample()/'pack.json').read_text()),{});self.assertFalse(r['candidates']);self.assertEqual(r['warnings'][0]['status'],'ROOT_UNRESOLVED')
    def test_fingerprint_failure_is_candidate_not_active(self):
        folder=self.sample();p=json.loads((folder/'pack.json').read_text());game=self.root/'game';game.mkdir();f=p['files'][0];path=game/f['locations'][0]['pattern'];path.write_bytes((folder/p['fixtures'][0]['before']).read_bytes())
        f['fingerprints']=[{'selector':{'pointer':'/schema'},'equals':'different'}]
        r=discover_pack(p,{'GAME_CONFIG':game});self.assertNotEqual(r['candidates'][0]['status'],'CANDIDATE_NOT_ACTIVE')
    def test_duplicate_native_owner_blocked(self):
        folder=self.sample();state,paths,pin=self.binding(folder)
        self.failcode('FILE_ALREADY_OWNED',lambda:bind_instance_local(self.s,pin,'another','keyboard',{'input':{'root':str(paths['input'].parent),'relative':paths['input'].name}},{'input':sha(paths['input'].read_bytes())},authorize=lambda _:True,evidence='Another owner'))

class Transport(Base):
    def archive(self,entries):
        p=self.root/'bad.zip'
        with zipfile.ZipFile(p,'w') as z:
            for name,data in entries:z.writestr(name,data)
        return p
    def test_export_import_roundtrip(self):
        folder=self.sample();path=self.root/'pack.zip';r=export_pack_local(folder,path);m,b=inspect_archive(path);self.assertEqual(m['pack_sha256'],r['pack_sha256'])
        rr=unpack_pack_local(path,self.root/'unpacked',m['pack_sha256']);self.assertEqual(rr['pack_sha256'],inspect_pack(folder)['pack_sha256']);self.assertFalse(rr['activated'])
    def test_existing_destination_preserved(self):
        folder=self.sample();p=self.root/'pack.zip';p.write_bytes(b'existing');self.failcode('DEST_EXISTS',lambda:export_pack_local(folder,p));self.assertEqual(p.read_bytes(),b'existing')
    def test_zip_traversal(self):self.failcode('UNSAFE_PATH',lambda:inspect_archive(self.archive([('../evil.json','{}')])))
    def test_zip_executable(self):self.failcode('PACK_EXECUTABLE_BLOCKED',lambda:inspect_archive(self.archive([('hook.py','pass')])))
    def test_zip_duplicate(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');p=self.archive([('pack.json','{}'),('pack.json','{}')])
        self.failcode('PACK_DUPLICATE',lambda:inspect_archive(p))
    def test_zip_symlink(self):
        info=zipfile.ZipInfo('evil.json');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16
        self.failcode('PACK_UNSAFE',lambda:inspect_archive(self.archive([(info,'elsewhere')])))
    def test_zip_nonregular(self):
        info=zipfile.ZipInfo('evil.json');info.create_system=3;info.external_attr=(stat.S_IFIFO|0o600)<<16
        self.failcode('PACK_UNSAFE',lambda:inspect_archive(self.archive([(info,'nothing')])))
    def test_zip_manifest_tamper(self):
        folder=self.sample();p=self.root/'good.zip';export_pack_local(folder,p)
        with zipfile.ZipFile(p) as z:entries=[(i.filename,b'{}' if i.filename=='pack.json' else z.read(i)) for i in z.infolist()]
        self.failcode('PACK_CORRUPT',lambda:inspect_archive(self.archive(entries)))
    def test_zip_invalid_crc_format(self):
        p=self.root/'bad.zip';p.write_bytes(b'not a zip');self.failcode('PACK_CORRUPT',lambda:inspect_archive(p))
    def test_zip_wrong_review_hash_no_output(self):
        folder=self.sample();p=self.root/'good.zip';export_pack_local(folder,p);out=self.root/'unpacked';self.failcode('PACK_CHANGED',lambda:unpack_pack_local(p,out,'0'*64));self.assertFalse(out.exists())

class Formats(Base):
    def test_jsonc_keep_comments_and_trailing_comma(self):
        raw=b'{/* local */"bind": "E", "other":"https://example/",}'
        d=Document(raw,'jsonc');out=d.render([({'pointer':'/bind'},'F')]);self.assertEqual(out,raw.replace(b'"E"',b'"F"'))
    def test_jsonc_not_json5(self):
        with self.assertRaises(Error):Document(b"{'bind':'E'}",'jsonc')
    def test_jsonc_unclosed_comment(self):self.failcode('FORMAT_INVALID',lambda:Document(b'{/*','jsonc'))
    def test_json_identity_survives_reorder(self):
        sel={'json_match':{'array':'/bindings','where':{'/name':'jump','/device':'keyboard'},'value':'/key'}}
        rows=[{'name':'jump','device':'keyboard','key':'Space'},{'name':'shoot','device':'mouse','key':'MouseLeft'}]
        for seq in (rows,list(reversed(rows))):
            d=Document(json.dumps({'bindings':seq}).encode(),'json');self.assertEqual(d.select(sel).value,'Space')
    def test_json_identity_duplicate_refused(self):
        d=Document(b'{"bindings":[{"name":"jump","key":"E"},{"name":"jump","key":"F"}]}','json')
        self.failcode('SELECTOR_AMBIGUOUS',lambda:d.select({'json_match':{'array':'/bindings','where':{'/name':'jump'},'value':'/key'}}))
    def test_json_pointer_escapes(self):
        d=Document(b'{"a/b":[{"~id":"use","key":"E"}]}','json');self.assertEqual(d.select({'json_match':{'array':'/a~1b','where':{'/~0id':'use'},'value':'/key'}}).value,'E')
    def test_xml_identity(self):
        d=Document(b'<root><bind name="use" key="E"/><bind name="fire" key="M1"/></root>','xml');c=d.select({'xml_match':{'tag':'bind','where':{'name':'use'},'attribute':'key'}});self.assertEqual(c.value,'E');self.assertIn(b'name="fire" key="M1"',d.render([(c.selector,'F')]))
    def test_xml_identity_duplicate(self):
        d=Document(b'<root><bind name="use" key="E"/><bind name="use" key="G"/></root>','xml');self.failcode('SELECTOR_AMBIGUOUS',lambda:d.select({'xml_match':{'tag':'bind','where':{'name':'use'},'attribute':'key'}}))
    def test_utf16_comment_preserved(self):
        raw=b'\xff\xfe'+('{/* הערה */ "bind": "E",}').encode('utf-16-le');d=Document(raw,'jsonc');out=d.render([({'pointer':'/bind'},'F')]);self.assertEqual(out,b'\xff\xfe'+('{/* הערה */ "bind": "F",}').encode('utf-16-le'))
    def test_keyvalues_duplicate_occurrence(self):
        d=Document(b'"Keys" { "Use" "E" "Use" "F" }','keyvalues');self.assertEqual(d.select({'kv_path':[['Keys',0],['Use',1]]}).value,'F')
    def test_keyvalues_includes_unsupported(self):self.failcode('FORMAT_UNSUPPORTED',lambda:Document(b'#include "other.vdf"','keyvalues'))
    def test_colon_duplicate(self):
        d=Document(b'use:E\nuse:F\n# ignored\n','colon-lines');self.assertEqual(d.select({'key':'use','occurrence':1}).value,'F')
    def test_chord_preserves_unrelated_tokens(self):
        raw=b'[Input]\n+ActionMappings=(ActionName="Use",bShift=False,bCtrl=False,bAlt=False,bCmd=False,Key=E) ; comment\n';d=Document(raw,'ue-chord');c=d.cells[0];v={**c.value,'ctrl':True,'key':'F'};out=d.render([(c.selector,v)]);self.assertEqual(out,raw.replace(b'bCtrl=False',b'bCtrl=True').replace(b'Key=E',b'Key=F'))
    def test_unreal_negative_directive_refused(self):self.failcode('EFFECTIVE_OWNER_REQUIRED',lambda:Document(b'[Input]\n!ActionMappings=ClearArray\n','ue-chord'))
    def test_unreal_partial_flags_refused(self):self.failcode('FORMAT_UNSUPPORTED',lambda:Document(b'[Input]\n+ActionMappings=(ActionName="Use",Key=E)\n','ue-chord'))
    def test_sided_modifiers_not_collapsed(self):
        self.assertEqual(canonical_chord('F',['LCtrl']),'LCtrl+F');self.failcode('KEY_UNSUPPORTED',lambda:unreal_chords({'F':'F'},[['LCtrl']]))
    def test_generic_and_sided_modifiers_refused(self):
        for mods in (['Ctrl','LCtrl'],['Alt','RAlt'],['Shift','LShift']):
            with self.subTest(mods=mods):self.failcode('KEY_AMBIGUOUS',lambda:canonical_chord('F',mods))
    def test_multiple_sparse_insertions(self):
        raw=b'[Keys]\nOther=R\n';d=Document(raw,'ini-sparse')
        sel=lambda k:{'section':'Keys','key':k,'occurrence':0,'part':'value','optional':True}
        out=d.render([(sel('Use'),'E'),(sel('Jump'),'Space')]);self.assertEqual(Document(out,'ini-sparse').select(sel('Use')).value,'E');self.assertEqual(Document(out,'ini-sparse').select(sel('Jump')).value,'Space');self.assertIn(b'Other=R',out)
    def test_sparse_no_new_section(self):
        d=Document(b'[Other]\nx=R\n','ini-sparse');self.failcode('SELECTOR_AMBIGUOUS',lambda:d.select({'section':'Keys','key':'Use','occurrence':0,'part':'value','optional':True}))
    def test_sparse_comment_cannot_be_deleted(self):
        d=Document(b'[Keys]\nUse = E ; keep\n','ini-sparse');c=d.select({'section':'Keys','key':'Use','occurrence':0,'part':'value','optional':True});self.failcode('SPARSE_REMOVE_COMMENT',lambda:d.render([(c.selector,'__GT_INHERIT__')]))
    def test_sparse_duplicate_blocked(self):
        d=Document(b'[Keys]\nUse=E\nUse=F\n','ini-sparse');self.failcode('SELECTOR_AMBIGUOUS',lambda:d.select({'section':'Keys','key':'Use','occurrence':0,'part':'value','optional':True}))

class AuthoringAndStores(Base):
    def test_compare_does_not_infer_action(self):
        a=self.root/'before.json';b=self.root/'after.json';a.write_bytes(b'{"bind":"E","volume":50}');b.write_bytes(b'{"bind":"F","volume":50}')
        r=learn_difference(a,b,'json');self.assertEqual(len(r['candidate_changes']),1);self.assertEqual(r['action_attribution'],'NOT_INFERRED');self.assertNotIn('before',r['candidate_changes'][0])
    def test_inventory_pagination_private_opt_in(self):
        a=self.root/'input.json';a.write_bytes(b'{"one":"E","two":"F"}');r=inventory(a,'json',limit=1);self.assertEqual(r['next_offset'],1);self.assertNotIn('native_value',r['items'][0]);self.assertIn('native_value',inventory(a,'json',include_values=True)['items'][0])
    def test_planner_explicit_translation_only(self):
        v={'assignments':[{'label':'Walk','target_key':'Ctrl'},{'label':'Use','target_key':'F'}]};x=[{'source_action':'Use','action':'interact','context':'gameplay','slot':'primary','keys':{'F':'F'}}]
        r=planner_bridge(v,x);self.assertEqual(len(r['intents']),1);self.assertEqual(r['unresolved'][0]['source_key'],'Ctrl');self.assertFalse(r['auto_apply'])
    def test_same_plan_uncertainty_stays_data(self):
        r=troubleshoot('DEPENDENCY_CHANGED');self.assertFalse(r['automatic_retry']);self.assertEqual(r['effects'],'NONE')
    def test_steam_explicit_metadata(self):
        root=self.root/'Steam';(root/'steamapps/common/Fictional').mkdir(parents=True);(root/'steamapps/appmanifest_123.acf').write_text('"AppState" { "appid" "123" "installdir" "Fictional" "buildid" "42" }')
        r=steam_installations(root,'123');self.assertEqual(r['candidates'][0]['build_id'],'42');self.assertFalse(r['candidates'][0]['active_config_verified'])
    def test_steam_second_library(self):
        root=self.root/'Steam';second=self.root/'Other';(root/'steamapps').mkdir(parents=True);(second/'steamapps/common/Fictional').mkdir(parents=True)
        (root/'steamapps/libraryfolders.vdf').write_text('"libraryfolders" { "1" { "path" '+json.dumps(str(second))+' } }');(second/'steamapps/appmanifest_123.acf').write_text('"AppState" { "appid" "123" "installdir" "Fictional" }')
        r=steam_installations(root,'123');self.assertEqual(len(r['candidates']),1);self.assertIn('Other',r['candidates'][0]['install_root'])
    def test_steam_traversal_manifest_refused(self):
        root=self.root/'Steam';(root/'steamapps').mkdir(parents=True);(root/'steamapps/appmanifest_123.acf').write_text('"AppState" { "appid" "123" "installdir" "../../outside" }')
        with self.assertRaises(Error):steam_installations(root,'123')
    def test_epic_exact_app_name(self):
        root=self.root/'manifests';root.mkdir();game=self.root/'EpicGame';game.mkdir();(root/'a.item').write_text(json.dumps({'AppName':'Exact123','InstallLocation':str(game),'AppVersionString':'fixture'}));self.assertEqual(len(epic_installations(root,'Exact123')['candidates']),1);self.assertFalse(epic_installations(root,'Other')['candidates'])


class AdapterSDK(Base):
    def test_trusted_module_adds_format_without_core_edits(self):
        import importlib.util
        path=ROOT/'examples/adapter-sdk/named_tokens.py';spec=importlib.util.spec_from_file_location('fixture_sdk',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.register()
        doc=Document(b'# untouched\nmap use E\nmap fire M1\n','ext-named-tokens');out=doc.render([({'action':'use','occurrence':0},'F')])
        self.assertEqual(out,b'# untouched\nmap use F\nmap fire M1\n');self.assertTrue(any(r['id']=='ext-named-tokens' for r in capabilities()))
    def test_no_loaded_adapter_replacement(self):
        self.failcode('ADAPTER_INVALID',lambda:register_adapter(Adapter('json',1,('.json',),lambda d:None,lambda d,c,v:[])))
    def test_binary_extension_not_implicitly_supported(self):
        self.failcode('FILE_ROLE_UNSUPPORTED',lambda:register_adapter(Adapter('ext-binary-save',1,('.sav',),lambda d:None,lambda d,c,v:[])))
    def test_extension_cannot_return_outside_spans(self):
        from game_keybind_ops.documents import Cell
        def parse(d):d.add(Cell({'id':'use'},d.text,0,len(d.text),'extension'))
        register_adapter(Adapter('ext-invalid-spans',1,('.conf',),parse,lambda d,c,v:[(-1,999,v)]))
        with self.assertRaises(Error):Document(b'E','ext-invalid-spans').render([({'id':'use'},'F')])

if __name__=='__main__':unittest.main(verbosity=2)
