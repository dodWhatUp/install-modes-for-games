"""Data-only extension and manager contract tests. All game/files are synthetic.
No provider connections, third-party execution, real game folders or installs.
"""
from __future__ import annotations
import copy,importlib.util,io,json,os,sys,tempfile,threading,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S));sys.dont_write_bytecode=True
from game_mod_ops.support import *
from game_mod_ops.definitions import *
from game_mod_ops.managers import inspect_archive,inspect_game,compare_installed
from game_mod_ops.workflow import Job,import_archive,stage
from game_mod_ops.recipes import plan
from game_mod_ops.handoff import export_handoff
from GameToolGameWorkspaces import GameWorkspaces,WorkspaceAI
from GameToolAI import Endpoint,tools


def make_pack(ident='other-game',adapter='directory',mode='default'):
 p=scaffold(ident,ident.replace('-',' ').title(),adapter,'bin/My Game.exe')
 p['recipe']={'schema_version':1,'kind':'game_mod_recipe','game_id':ident,'manager_id':p['definition']['manager_id'],
  'name':p['definition']['name'],'items':[{'id':'test-mod','name':'Test mod','kind':'mod','source':{'kind':'manual'},
  'download_page':'https://example.invalid/test-mod','display_version':'test-only','max_download_bytes':1048576,
  'sha256':None,'requires':[],'conflicts':[]}],'presets':{mode:['test-mod']}}
 if adapter=='umm':p['recipe']['items'][0]['mod_id']='Test.Mod'
 if adapter=='smapi':p['recipe']['items'][0]['mod_id']='Test.Mod'
 return validate_pack(p)


class SupportTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.data=self.root/'profile';self.r=SupportRegistry(self.data,builtin=self.root/'no-shipped');self.p=make_pack()
 def save(self,p=None,name='support.json'):
  target=self.root/name;target.write_text(json.dumps(p or self.p),encoding='utf-8');return target
 def add(self,p=None,expected=None):
  p=p or self.p;return self.r.import_pack(self.save(p),reviewed_sha256=object_hash(p),expected_revision=expected,confirmed=True)
 def z(self,files,name='mod.zip'):
  path=self.root/name
  with zipfile.ZipFile(path,'w') as z:
   for k,v in files.items():z.writestr(k,json.dumps(v) if isinstance(v,dict) else v)
  return path
 def installed(self,adapter='smapi',files=None):
  d=default_definition('other-game','Other game',adapter,'bin/My Game.exe');root=self.root/'game'
  for rel,body in {'bin/My Game.exe':'not an executable',**(files or {})}.items():
   q=root/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(body) if isinstance(body,dict) else body)
  return root,d
 def test_schema_and_template_are_nonmutating(self):
  self.assertEqual(schema()['installation_authority'],False);self.assertEqual(self.r.rows(),{})
  scaffold('another-game','Another game');self.assertFalse(self.data.exists())
 def test_named_noncombat_presets(self):
  p=make_pack(mode='quality-of-life');r=compose_recipe(p);q=plan(r,mode='quality-of-life')
  self.assertEqual(q['mode'],'quality-of-life');self.assertEqual(q['game_definition']['executable_any'],['bin/My Game.exe'])
 def test_relative_spaces_not_fixed_executable_slug(self):
  self.assertEqual(validate_definition(self.p['definition'])['executable_any'],['bin/My Game.exe'])
 def test_unknown_adapter_cannot_execute_data(self):
  self.p['definition']['adapter']='exec-shell'
  with self.assertRaises(ModError):validate_pack(self.p)
 def test_relative_traversal_and_windows_aliases(self):
  for rel in ['../outside','/etc/passwd','a/../../oops','C:/Windows','mods\\evil','mods/CON']:
   p=copy.deepcopy(self.p);p['definition']['mods_relative']=rel
   with self.subTest(rel=rel),self.assertRaises(ModError):validate_pack(p)
 def test_code_and_credentials_rejected(self):
  for key in ['shell','command','script','password','token','api_key','python']:
   p=copy.deepcopy(self.p);p['recipe'][key]='do-not-execute'
   with self.subTest(key=key),self.assertRaises(ModError):validate_pack(p)
 def test_unknown_pack_and_definition_fields(self):
  for place in ('top','definition'):
   p=copy.deepcopy(self.p);(p if place=='top' else p['definition'])['typo']='x'
   with self.subTest(place=place),self.assertRaises(ModError):validate_pack(p)
 def test_signed_urls_and_account_credentials_rejected(self):
  for url in ['https://a.test/file?token=secret','https://u:p@a.test/file','file:///home/me','http://x.test']:
   p=copy.deepcopy(self.p);p['sources'][0]['url']=url
   with self.subTest(url=url),self.assertRaises(ModError):validate_pack(p)
 def test_recipe_identity_must_match(self):
  self.p['recipe']['game_id']='wrong-game'
  with self.assertRaises(ModError):validate_pack(self.p)
 def test_review_digest_and_confirmation_required(self):
  path=self.save()
  with self.assertRaises(ModError):self.r.import_pack(path,reviewed_sha256=object_hash(self.p))
  with self.assertRaises(ModError):self.r.import_pack(path,reviewed_sha256='0'*64,confirmed=True)
  self.assertFalse(self.data.exists())
 def test_single_json_registration_then_readback(self):
  out=self.add();self.assertEqual(out['status'],'REGISTERED_NOT_INSTALLED')
  r=self.r.get('other-game');self.assertEqual(r['pack'],self.p)
  self.assertEqual(read_json(self.r.recipe_path('other-game')),compose_recipe(self.p))
 def test_idempotent_same_pack(self):
  self.add();self.assertEqual(self.add()['status'],'ALREADY_REGISTERED')
 def test_revision_update_retains_old_source(self):
  first=self.add();old=self.r.get('other-game')['path'];p=copy.deepcopy(self.p);p['pack_version']='0.2.0';p['notes']=['new']
  self.add(p,first['revision']);self.assertTrue(old.is_file());self.assertEqual(read_pack(old)[0],self.p)
  self.assertEqual(self.r.get('other-game')['pack']['notes'],['new'])
 def test_unreviewed_replace_refused(self):
  self.add();p=copy.deepcopy(self.p);p['notes']=['changed']
  with self.assertRaises(ModError):self.add(p)
  self.assertEqual(self.r.get('other-game')['pack'],self.p)
 def test_mutated_immutable_pack_refused(self):
  self.add();path=self.r.get('other-game')['path'];p=copy.deepcopy(self.p);p['notes']=['mutated'];path.write_text(json.dumps(p))
  with self.assertRaises(ModError):self.r.rows()
 def test_mutated_derived_recipe_refused(self):
  self.add();path=self.r.recipe_path('other-game');path.write_text('{}')
  with self.assertRaises(ModError):self.r.recipe_path('other-game')
 def test_corrupt_pointer_refused(self):
  self.add();(self.r.root/'other-game/current.json').write_text('{"schema_version":1,"revision":"../x"}')
  with self.assertRaises(ModError):self.r.rows()
 def test_support_zip_rejects_code_or_extra_payloads(self):
  p=self.z({'game-support.json':self.p,'plugin.py':'print("unsafe")'},'pack.zip')
  with self.assertRaises(ModError):read_pack(p)
 def test_support_zip_and_json_export_roundtrip(self):
  self.add()
  for extension in ['.json','.zip']:
   p=self.root/('export'+extension);out=self.r.export('other-game',p);self.assertEqual(read_pack(p)[0],self.p)
   self.assertEqual(out['status'],'EXPORTED_DATA_ONLY')
   with self.assertRaises(FileExistsError):self.r.export('other-game',p)
 def test_duplicate_json_keys_rejected(self):
  p=self.root/'bad.json';p.write_text('{"kind":"game_support_pack","kind":"something"}')
  with self.assertRaises(ModError):read_pack(p)
 def test_symlink_support_refused(self):
  path=self.save();link=self.root/'link.json';link.symlink_to(path)
  with self.assertRaises(ModError):read_pack(link)
 def test_shipped_coverage_is_honest_and_nonmutating(self):
  w=GameWorkspaces(self.data);rows=w.catalog.game_rows();ready={r['id'] for r in rows if r['recipe_available']}
  self.assertEqual(ready,{'pathfinder-kingmaker','stardew-valley'})
  self.assertTrue(all(r['installation']=='unknown' for r in rows));self.assertFalse(self.data.exists())
  for row in rows:
   if not row['recipe_available'] and 'adapter_capabilities' in row:self.assertFalse(row['adapter_capabilities']['plan'])
 def test_stardew_default_plan_preserves_dependencies(self):
  w=GameWorkspaces(self.data);j=w.new_plan('stardew-valley')
  self.assertEqual(list(j.items),['smapi','content-patcher']);self.assertEqual(j.plan['mode'],'default')
  self.assertFalse(j.plan['installation_authorized'])
 def test_new_game_end_to_end_by_data_only_all_three_layouts(self):
  source_hash=digest(S/'GameToolGameWorkspaces.py');w=GameWorkspaces(self.data)
  for adapter in ['directory','umm','smapi']:
   ident='extension-'+adapter;p=make_pack(ident,adapter);q=self.save(p,ident+'.json')
   w.catalog.import_support(q,reviewed_sha256=object_hash(p),confirmed=True)
   j=w.new_plan(ident)
   if adapter=='directory':files={'folder/readme.txt':'hello'}
   elif adapter=='umm':files={'Test/Info.json':{'Id':'Test.Mod','Version':'1.0','AssemblyName':'stub.dll'},'Test/stub.dll':'TEXT ONLY'}
   else:files={'Test/manifest.json':{'UniqueID':'Test.Mod','Version':'1.0','EntryDll':'stub.dll'},'Test/stub.dll':'TEXT ONLY'}
   z=self.z(files,ident+'.zip');w.import_zip(ident,j.path.name,w.revision(j),'test-mod',z,True)
   out=w.prepare(ident,j.path.name,w.revision(j),['test-mod']);self.assertEqual(out['items'][0]['status'],'STAGED_NOT_INSTALLED')
   self.assertIn(ident,{r['id'] for r in w.catalog.game_rows()})
  self.assertEqual(source_hash,digest(S/'GameToolGameWorkspaces.py'))
 def test_old_job_retains_old_definition_when_pack_updates(self):
  w=GameWorkspaces(self.data);w.catalog.import_support(self.save(),reviewed_sha256=object_hash(self.p),confirmed=True)
  j=w.new_plan('other-game');previous=j.plan.copy();old=w.catalog.get('other-game')['revision']
  p=copy.deepcopy(self.p);p['definition']['mods_relative']='NewMods'
  w.catalog.import_support(self.save(p),reviewed_sha256=object_hash(p),expected_revision=object_hash(self.p),expected_recipe_revision=old,confirmed=True)
  self.assertEqual(Job(j.path).plan,previous);self.assertEqual(w.new_plan('other-game').plan['game_definition']['mods_relative'],'NewMods')
 def test_second_game_cannot_borrow_first_job(self):
  w=GameWorkspaces(self.data);j=w.new_plan('stardew-valley')
  with self.assertRaises(ModError):w.export_for_manager('pathfinder-kingmaker',j.path.name,w.revision(j),self.root/'export',True)
 def test_smapi_manifest_and_contentpack(self):
  p=make_pack(adapter='smapi');q=plan(compose_recipe(p),mode='default');item=q['items'][0]
  for info in [{'UniqueID':'Test.Mod','Version':'1.0','EntryDll':'stub.dll'},
               {'UniqueID':'Test.Mod','Version':'1.0','ContentPackFor':{'UniqueID':'Pathoschild.ContentPatcher'}}]:
   z=self.z({'Test/manifest.json':info,'Test/stub.dll':'TEXT ONLY','Readme.txt':'doc'})
   a=inspect_archive(z,item,q);self.assertEqual(a['mod_id'],'Test.Mod');self.assertEqual(a['kind'],'smapi_mod')
   self.assertIn('manifest.json',a['files']);self.assertEqual(a['prefix'],'Test/')
 def test_smapi_wrong_id_and_missing_assembly(self):
  q=plan(compose_recipe(make_pack(adapter='smapi')),mode='default')
  for info in [{'UniqueID':'Wrong.Mod','Version':'1.0','EntryDll':'stub.dll'},
               {'UniqueID':'Test.Mod','Version':'1.0','EntryDll':'missing.dll'}]:
   with self.subTest(info=info),self.assertRaises(ModError):inspect_archive(self.z({'manifest.json':info,'stub.dll':'text'}),q['items'][0],q)
 def test_smapi_multiple_manifests_refused(self):
  q=plan(compose_recipe(make_pack(adapter='smapi')),mode='default');info={'UniqueID':'Test.Mod','Version':'1.0','EntryDll':'s.dll'}
  with self.assertRaises(ModError):inspect_archive(self.z({'a/manifest.json':info,'a/s.dll':'x','b/manifest.json':info,'b/s.dll':'x'}),q['items'][0],q)
 def test_generic_root_selection_explicit_and_recorded(self):
  p=make_pack();item=p['recipe']['items'][0];item.update(archive_root='Payload',required_files=['safe.txt'])
  q=plan(compose_recipe(p),mode='default');a=inspect_archive(self.z({'Payload/safe.txt':'ok','OTHER.dll':'not copied'}),q['items'][0],q)
  self.assertEqual(list(a['files']),['safe.txt']);self.assertEqual(a['excluded_by_explicit_root'],['OTHER.dll'])
 def test_required_files_and_unsafe_zip_still_checked(self):
  p=make_pack();p['recipe']['items'][0]['required_files']=['needed.txt'];q=plan(compose_recipe(p),mode='default')
  for files in [{'other.txt':'x'},{'needed.txt':'x','../evil.txt':'x'}]:
   with self.subTest(files=files),self.assertRaises(ModError):inspect_archive(self.z(files),q['items'][0],q)
 def test_inventory_metadata_not_runtime_or_execution(self):
  root,d=self.installed(files={'Mods/T/manifest.json':{'UniqueID':'Test.Mod','Version':'1.2','EntryDll':'stub.dll'},'Mods/T/stub.dll':'raise AssertionError("never load")'})
  a=inspect_game(root,d);self.assertTrue(a['complete']);self.assertEqual(a['mods'][0]['id'],'Test.Mod')
  self.assertEqual(a['runtime'],'NOT_VERIFIED');self.assertEqual(a['enabled_state'],'UNKNOWN');self.assertNotIn(str(root),json.dumps(a))
 def test_inventory_wrong_game_rejected(self):
  root,d=self.installed();(root/'bin/My Game.exe').unlink()
  with self.assertRaises(ModError):inspect_game(root,d)
 def test_unknown_content_makes_absence_inconclusive(self):
  root,d=self.installed(files={'Mods/Unknown/a.txt':'unknown'});a=inspect_game(root,d)
  self.assertFalse(a['complete']);self.assertEqual(a['unrecognized_file_count'],1)
  q=plan(compose_recipe(make_pack(adapter='smapi')),mode='default');c=compare_installed(q,a)
  self.assertEqual(c['items'][0]['state'],'INCONCLUSIVE')
 def test_depth_limit_is_partial_not_empty_success(self):
  root,d=self.installed(files={'Mods/a/b/c/manifest.json':{'UniqueID':'X.Mod','Version':'1','EntryDll':'a.dll'}});d['scan_depth']=1
  a=inspect_game(root,d);self.assertFalse(a['complete']);self.assertEqual(a['inventory_status'],'PARTIAL_INVENTORY')
 def test_duplicate_identity_not_version_match(self):
  info={'UniqueID':'Test.Mod','Version':'1','EntryDll':'x.dll'}
  root,d=self.installed(files={'Mods/a/manifest.json':info,'Mods/a/x.dll':'x','Mods/b/manifest.json':info,'Mods/b/x.dll':'x'})
  a=inspect_game(root,d);q=plan(compose_recipe(make_pack(adapter='smapi')),mode='default')
  self.assertEqual(compare_installed(q,a)['items'][0]['state'],'AMBIGUOUS_DUPLICATE')
 def test_comparison_versions_and_ignored_folder(self):
  info={'UniqueID':'Test.Mod','Version':'1.2','EntryDll':'x.dll'}
  root,d=self.installed(files={'Mods/.disabled/manifest.json':info,'Mods/.disabled/x.dll':'x'})
  p=make_pack(adapter='smapi');p['recipe']['items'][0]['expected_version']='1.2';q=plan(compose_recipe(p),mode='default')
  a=inspect_game(root,d);self.assertEqual(compare_installed(q,a)['items'][0]['state'],'IGNORED_FOLDER_PRESENT')
  (root/'Mods/.disabled').rename(root/'Mods/enabled');a=inspect_game(root,d)
  self.assertEqual(compare_installed(q,a)['items'][0]['state'],'VERSION_MATCH');self.assertEqual(a['enabled_state'],'UNKNOWN')
 def test_bepinex_inventory_cannot_infer_binary_identity(self):
  root,d=self.installed('bepinex',{'BepInEx/plugins/a.dll':'TEXT ONLY'})
  a=inspect_game(root,d);self.assertIsNone(a['mods'][0]['id']);self.assertIsNone(a['mods'][0]['version']);self.assertEqual(a['runtime'],'NOT_VERIFIED')
 def test_external_manager_keeps_ownership(self):
  root,d=self.installed('external');a=inspect_game(root,d)
  self.assertEqual(a['inventory_status'],'MANAGER_HANDOFF_REQUIRED');self.assertFalse(a['complete'])
 def test_inventory_symlink_refused(self):
  root,d=self.installed(files={'Mods/a.txt':'x'});(root/'Mods/link').symlink_to(self.root,target_is_directory=True)
  with self.assertRaises(ModError):inspect_game(root,d)
 def test_manager_handoff_original_bytes_with_no_install(self):
  q=plan(compose_recipe(self.p),mode='default');j=Job.create(self.data,q);z=self.z({'hello.txt':'original'})
  import_archive(j,'test-mod',z,confirmed_source=True);before=j.events();dest=self.root/'for-manager'
  r=export_handoff(j,dest,reviewed_revision=GameWorkspaces.revision(j),confirmed=True)
  self.assertEqual(r['status'],'HANDOFF_EXPORTED_NOT_INSTALLED');self.assertEqual(digest(z),digest(dest/'01_test-mod.zip'))
  self.assertFalse(read_json(dest/'MANAGER-HANDOFF.json')['installed']);self.assertTrue((dest/'OPEN Manager Handoff.html').is_file());self.assertEqual(before,j.events())
 def test_handoff_confirmation_revision_and_destination(self):
  j=Job.create(self.data,plan(compose_recipe(self.p),mode='default'));dest=self.root/'export'
  for kwargs in [{},{'confirmed':True,'reviewed_revision':'0'*64}]:
   with self.assertRaises((ModError,TypeError)):export_handoff(j,dest,**kwargs)
  self.assertFalse(dest.exists())
 def test_ai_support_tools_are_read_only_no_hidden_registration(self):
  e=Endpoint(WorkspaceAI(self.data),True)
  for name,args in [('games_support_schema',{}),('games_support_template',{'game_id':'new-game','name':'New game'}),
                    ('games_support_validate',{'pack':self.p}),('games_support_details',{'game_id':'stardew-valley'})]:
   v=e.call(name,args);self.assertIsInstance(v,dict);self.assertNotIn(str(self.data),json.dumps(v))
  self.assertFalse(self.data.exists());self.assertEqual(len(tools(True,True)),10)
  names=[x['name'] for x in tools(True,True)];self.assertFalse(any('install' in x or 'approve' in x or 'import' in x for x in names))
 def test_ai_default_nongame_combat_plan(self):
  a=WorkspaceAI(self.data).preview_plan('stardew-valley');self.assertEqual(a['mode'],'default');self.assertFalse(self.data.exists())
 def test_recipe_change_invalidates_pending_request(self):
  w=GameWorkspaces(self.data);w.catalog.import_support(self.save(),reviewed_sha256=object_hash(self.p),confirmed=True)
  service=w.service('other-game');r=service.propose('mods.create_plan',{'selected':['test-mod'],'mode':'default'},request_id='before-change')
  p=copy.deepcopy(self.p);p['notes']=['new reviewed definition'];old=w.catalog.get('other-game')['revision']
  w.catalog.import_support(self.save(p),reviewed_sha256=object_hash(p),expected_revision=object_hash(self.p),expected_recipe_revision=old,confirmed=True)
  new=w.service('other-game');self.assertNotEqual(new.recipe_hash,service.recipe_hash)
  with self.assertRaises(ModError):new.approve_local('before-change',r['request_sha256'])

 def test_source_review_date_must_be_real(self):
  self.p['sources'][0]['checked_on']='2026-99-99'
  with self.assertRaises(ModError):validate_pack(self.p)
 def test_secret_download_link_refused_in_recipe(self):
  self.p['recipe']['items'][0]['download_page']='https://example.invalid/mod?token=private'
  with self.assertRaises(ModError):validate_pack(self.p)
 def test_manager_adapter_disagreement_refused(self):
  self.p['definition']['manager_id']='smapi';self.p['recipe']['manager_id']='smapi'
  with self.assertRaises(ModError):validate_pack(self.p)
 def test_custom_manager_can_reuse_supported_data_adapter(self):
  self.p['definition']['manager_id']='custom-local-manager';self.p['recipe']['manager_id']='custom-local-manager'
  self.add();self.assertEqual(read_json(self.r.recipe_path('other-game'))['manager_id'],'custom-local-manager')
 def test_inventory_missing_payload_is_not_version_match(self):
  root,d=self.installed(files={'Mods/T/manifest.json':{'UniqueID':'Test.Mod','Version':'1.2','EntryDll':'missing.dll'}})
  p=make_pack(adapter='smapi');p['recipe']['items'][0]['expected_version']='1.2'
  c=compare_installed(plan(compose_recipe(p),mode='default'),inspect_game(root,d))
  self.assertEqual(c['items'][0]['state'],'PAYLOAD_MARKER_MISSING')
 def test_incomplete_import_revision_not_activated(self):
  self.add();root=self.r.root/'other-game';rev=root/('1'*64);rev.mkdir();(rev/'partial.txt').write_text('partial')
  self.assertEqual(self.r.get('other-game')['revision'],object_hash(self.p))
 def test_external_selection_change_during_import_refused(self):
  first=self.add();p=copy.deepcopy(self.p);p['notes']=['changed']
  pointer=self.r.root/'other-game/current.json';previous=pointer.read_bytes()
  import game_mod_ops.support as module
  actual=module.json_new
  def competing_writer(path,data):
   actual(path,data)
   if path.name=='recipe.json':pointer.write_text('unexpected concurrent selection')
  with patch.object(module,'json_new',side_effect=competing_writer),self.assertRaises(ModError):self.add(p,first['revision'])
  self.assertEqual(pointer.read_text(),'unexpected concurrent selection')
 def test_handoff_preserves_existing_output(self):
  j=Job.create(self.data,plan(compose_recipe(self.p),mode='default'));dest=self.root/'output';dest.mkdir();(dest/'user.txt').write_text('KEEP')
  with self.assertRaises(ModError):export_handoff(j,dest,reviewed_revision=GameWorkspaces.revision(j),confirmed=True)
  self.assertEqual((dest/'user.txt').read_text(),'KEEP')
 def test_handoff_incomplete_download_refused(self):
  j=Job.create(self.data,plan(compose_recipe(self.p),mode='default'));j.event('test-mod','DOWNLOADING');dest=self.root/'output'
  with self.assertRaises(ModError):export_handoff(j,dest,reviewed_revision=GameWorkspaces.revision(j),confirmed=True)
  self.assertFalse(dest.exists())
 def test_removed_item_keeps_old_proposal_reviewable_not_approvable(self):
  w=GameWorkspaces(self.data);w.catalog.import_support(self.save(),reviewed_sha256=object_hash(self.p),confirmed=True)
  r=w.service('other-game').propose('mods.create_plan',{'selected':['test-mod'],'mode':'default'},request_id='old-item')
  p=copy.deepcopy(self.p);p['recipe']['items'][0]['id']='new-item';p['recipe']['presets']['default']=['new-item'];old=w.catalog.get('other-game')['revision']
  w.catalog.import_support(self.save(p),reviewed_sha256=object_hash(p),expected_revision=object_hash(self.p),expected_recipe_revision=old,confirmed=True)
  view=w.request_review('other-game','old-item');self.assertFalse(view['current']);self.assertEqual(view['items'],['test-mod'])

 def test_damaged_support_zip_is_a_readable_refusal(self):
  p=self.root/'broken.zip';p.write_bytes(b'not a ZIP')
  with self.assertRaises(ModError) as e:read_pack(p)
  self.assertEqual(e.exception.code,'INVALID_SUPPORT_ZIP');self.assertFalse(self.data.exists())

if __name__=='__main__':unittest.main(verbosity=2)
