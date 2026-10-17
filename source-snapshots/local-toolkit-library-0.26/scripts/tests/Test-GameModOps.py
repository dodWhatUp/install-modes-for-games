#!/usr/bin/env python3
"""Synthetic contracts only. Never contacts a provider, opens a game or changes user data."""
from __future__ import annotations
import copy
import hashlib
import io
import json
import os
import stat
import sys
import tempfile
import time
import unittest
import urllib.request
import warnings
import zipfile
from pathlib import Path
from threading import Event
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game_mod_ops.safety import *
from game_mod_ops.recipes import load_recipe, plan, validate_plan, validate_recipe
from game_mod_ops.archive import inspect_zip, stage_zip, tree_audit
from game_mod_ops.network import Budget, Http, SafeRedirect, https_url, nxm_parameters, resolve
from game_mod_ops.workflow import Job, acquire, import_archive, stage
from game_mod_ops.umm import inventory, install_new, audit_installed, rollback_new, require_closed, LOADER_RELATIVE

ROOT = Path(__file__).resolve().parents[2]
RECIPE = ROOT/'examples/game-tool-hub/mod-recipes/pathfinder-kingmaker.json'

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def fail_code(self,code,fn):
        with self.assertRaises(ModError) as ctx:fn()
        self.assertEqual(ctx.exception.code,code)
    def archive(self,name='Demo',extra=None,info_extra=None):
        p=self.root/(name+'.zip')
        info={'Id':name,'Version':'1.0.0','ManagerVersion':'0.23.0',**(info_extra or {})}
        with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr(name+'/Info.json',json.dumps(info));z.writestr(name+'/'+name+'.dll',b'fixture-not-executable')
            for n,b in extra or []:z.writestr(n,b)
        return p
    def recipe(self,provider='manual',ident='demo',ummid='Demo'):
        item={'id':ident,'name':'Synthetic mod','kind':'mod','display_version':'1.0.0','max_download_bytes':1048576,
              'umm_id':ummid,'sha256':None,'download_page':'https://github.com/example/example/releases',
              'requires':[],'source':{'kind':provider}}
        if provider=='github_release':item['source'].update(repository='example/example',tag='v1',asset='Demo.zip')
        if provider=='nexus':item['source'].update(game='pathfinderkingmaker',mod_id=119,file_id=123)
        return {'schema_version':1,'kind':'game_mod_recipe','game_id':'pathfinder-kingmaker','game_exe':'Kingmaker.exe',
                'manager_id':'unity-mod-manager','name':'Fixture','presets':{'real-time':[ident]},'items':[item]}
    def job(self,recipe=None):return Job.create(self.root/'private',plan(recipe or self.recipe()))
    def prepared(self):
        j=self.job();p=self.archive();import_archive(j,'demo',p,confirmed_source=True);stage(j,'demo');return j
    def game(self):
        p=self.root/'game';p.mkdir();(p/'Kingmaker.exe').write_bytes(b'fixture-exe')
        dll=p/LOADER_RELATIVE;dll.parent.mkdir(parents=True);dll.write_bytes(b'fixture-loader')
        data=self.root/'user-data';(data/'Saves').mkdir(parents=True);(data/'Saves/test.zks').write_bytes(b'fixture-save')
        return p,data
    def install(self,j,game,data,**kw):
        with patch('game_mod_ops.umm.require_closed'):
            return install_new(j,'demo',game,data,approved_plan_sha256=j.plan['plan_sha256'],game_version='2.1.7',umm_version='0.33.2',**kw)

class PathTests(Base):
    def test_unsafe_windows_and_traversal(self):
        for path in ['../x','/root/x','a/../../b','a\\b','C:/x','x:stream','a//b','a./x','NUL.txt','con','COM1/x','LPT¹','a/./b','x\x00y','a /b']:
            with self.subTest(path=path):self.fail_code('UNSAFE_PATH',lambda:safe_relative(path))
    def test_safe_nested(self):self.assertEqual(str(safe_relative('a/b-1.json')),'a/b-1.json')
    def test_symlink_parent(self):
        target=self.root/'real';target.mkdir();link=self.root/'link';link.symlink_to(target,target_is_directory=True)
        self.fail_code('LINK_BLOCKED',lambda:no_links(link/'new'))
    def test_immutable_write(self):
        p=self.root/'x';write_new(p,b'a')
        with self.assertRaises(FileExistsError):write_new(p,b'b')
        self.assertEqual(p.read_bytes(),b'a')
    def test_duplicate_json(self):
        p=self.root/'x.json';p.write_text('{"id":1,"id":2}')
        self.fail_code('INVALID_JSON',lambda:read_json(p))
    def test_nonfinite_json(self):self.fail_code('INVALID_JSON',lambda:strict_json('{"x":NaN}'))
    def test_cooperative_lock(self):
        with local_lock(self.root):self.fail_code('OWNER_UNKNOWN',lambda:local_lock(self.root).__enter__())
        self.assertFalse((self.root/'.mod-ops.lock').exists())

class RecipeTests(Base):
    def test_real_profile_presets(self):
        r=load_recipe(RECIPE)
        self.assertEqual(len(plan(r)['items']),3)
        self.assertNotIn('kingmaker-tactics',[i['id'] for i in plan(r,mode='turn-based')['items']])
        validate_plan(plan(r))
    def test_conflicting_buffs(self):self.fail_code('CHOICE_CONFLICT',lambda:plan(load_recipe(RECIPE),['buff-bot','autobuff']))
    def test_real_time_only(self):self.fail_code('MODE_UNSUPPORTED',lambda:plan(load_recipe(RECIPE),['kingmaker-tactics'],mode='turn-based'))
    def test_pin_nexus_exact(self):self.assertEqual(plan(load_recipe(RECIPE),file_pins={'buff-bot':123})['items'][-1]['source']['file_id'],123)
    def test_unknown_pin_rejected(self):self.fail_code('UNKNOWN_ITEM',lambda:plan(load_recipe(RECIPE),file_pins={'unknown':123}))
    def test_unknown_selection(self):self.fail_code('UNKNOWN_ITEM',lambda:plan(load_recipe(RECIPE),['unknown']))
    def test_plan_hash(self):
        p=plan(self.recipe());p['items'][0]['name']='edited'
        self.fail_code('PLAN_CHANGED',lambda:validate_plan(p))
    def test_cycle(self):
        r=self.recipe();r['items'].append(copy.deepcopy(r['items'][0]));r['items'][1]['id']='other';r['items'][0]['requires']=['other'];r['items'][1]['requires']=['demo']
        self.fail_code('DEPENDENCY_CYCLE',lambda:validate_recipe(r))
    def test_nested_secret_or_command(self):
        r=self.recipe();r['items'][0]['source']['command']='execute downloaded text'
        self.fail_code('EXECUTABLE_RECIPE',lambda:validate_recipe(r))
    def test_dependency_order(self):
        p=plan(load_recipe(RECIPE));p['items'].reverse();p.pop('plan_sha256');p['plan_sha256']=object_hash(p)
        self.fail_code('DEPENDENCY_ORDER',lambda:validate_plan(p))

class ArchiveTests(Base):
    def test_valid_umm(self):
        r=inspect_zip(self.archive(),'Demo');self.assertEqual(r['mod_id'],'Demo');self.assertEqual(len(r['files']),2)
    def test_manager_archive(self):
        p=self.root/'manager.zip'
        with zipfile.ZipFile(p,'w') as z:
            z.writestr('UMM/UnityModManager.exe',b'fixture');z.writestr('UMM/UnityModManagerConfig.xml','<Config/>')
        self.assertEqual(inspect_zip(p,manager=True)['kind'],'umm_manager')
    def test_wrong_id(self):self.fail_code('MOD_ID_MISMATCH',lambda:inspect_zip(self.archive(),'Different'))
    def test_generic_archive(self):
        p=self.root/'generic.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('Data/file.txt','fixture')
        self.assertEqual(inspect_zip(p,layout='generic')['kind'],'generic_zip')
    def test_no_info_umm(self):
        p=self.root/'noinfo.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('file.dll','fixture')
        self.fail_code('ARCHIVE_LAYOUT',lambda:inspect_zip(p))
    def test_archive_traversal(self):self.fail_code('UNSAFE_PATH',lambda:inspect_zip(self.archive(extra=[('../bad','bad')])) )
    def test_case_collision(self):self.fail_code('ZIP_COLLISION',lambda:inspect_zip(self.archive(extra=[('Demo/info.json','{}')])) )
    def test_file_as_directory(self):self.fail_code('ZIP_COLLISION',lambda:inspect_zip(self.archive(extra=[('Demo/x','a'),('Demo/x/y','b')])) )
    def test_symlink_zip(self):
        p=self.archive();zinfo=zipfile.ZipInfo('Demo/link');zinfo.create_system=3;zinfo.external_attr=(stat.S_IFLNK|0o777)<<16
        with zipfile.ZipFile(p,'a') as z:z.writestr(zinfo,'/etc/passwd')
        self.fail_code('ZIP_SPECIAL_FILE',lambda:inspect_zip(p))
    def test_bomb_ratio(self):self.fail_code('ZIP_RATIO',lambda:inspect_zip(self.archive(extra=[('Demo/big',b'0'*(2*1024*1024))])) )
    def test_unexpected_extra_payload(self):self.fail_code('ARCHIVE_LAYOUT',lambda:inspect_zip(self.archive(extra=[('outside.dll','fixture')])) )
    def test_stage_unchanged(self):
        p=self.archive();ins=inspect_zip(p);dest=self.root/'stage';stage_zip(p,dest,ins)
        self.assertEqual(tree_audit(dest,ins['files'])['status'],'MATCH')
    def test_stage_archive_changed(self):
        p=self.archive();ins=inspect_zip(p)
        with p.open('ab') as f:f.write(b'changed')
        self.fail_code('SOURCE_CHANGED',lambda:stage_zip(p,self.root/'stage',ins))
    def test_drift_generated_settings_not_deleted(self):
        p=self.archive();ins=inspect_zip(p);d=self.root/'stage';stage_zip(p,d,ins);(d/'Settings.xml').write_text('new')
        self.assertEqual(tree_audit(d,ins['files'])['extra'],['Settings.xml']);self.assertTrue((d/'Settings.xml').exists())

class NetworkTests(Base):
    def test_host_allowlist(self):
        self.assertEqual(https_url('https://github.com/o/r/releases','github'),'github.com')
        for url in ['http://github.com/x','https://github.com.evil.test/x','https://127.0.0.1/x','https://user:pw@github.com/x','https://github.com:8080/x']:
            with self.subTest(url=url):
                with self.assertRaises(ModError):https_url(url,'github')
    def test_credentials_cannot_redirect(self):
        h=SafeRedirect('nexus-api',Budget(),None);req=urllib.request.Request('https://api.nexusmods.com/v1/test',headers={'apikey':'SECRET'})
        self.fail_code('AUTH_REDIRECT_BLOCKED',lambda:h.redirect_request(req,None,302,'',{},'https://api.nexusmods.com/other'))
    def test_redirect_drops_headers(self):
        h=SafeRedirect('github',Budget(),None);req=urllib.request.Request('https://github.com/x',headers={'Authorization':'SECRET'})
        new=h.redirect_request(req,None,302,'',{},'https://release-assets.githubusercontent.com/asset')
        self.assertNotIn('Authorization',new.headers)
    def test_nxm_identity_and_expiry(self):
        link='nxm://pathfinderkingmaker/mods/119/files/123?key=SECRET&expires='+str(int(time.time())+1000)
        self.assertEqual(nxm_parameters(link,'pathfinderkingmaker',119,123)['key'],'SECRET')
        self.fail_code('NXM_MISMATCH',lambda:nxm_parameters(link,'other',119,123))
        self.fail_code('EXPIRED_NXM',lambda:nxm_parameters('nxm://g/mods/1/files/2?key=secret&expires=1','g',1,2))
    def test_budget_and_cancel(self):
        b=Budget(2,1,100);b.request();self.fail_code('REQUEST_LIMIT',lambda:b.request())
        self.fail_code('BUDGET_EXCEEDED',lambda:b.consume(3))
        e=Event();e.set();self.fail_code('CANCELLED',lambda:Budget().check(e))
    def test_github_exact_tag(self):
        item=self.recipe('github_release')['items'][0]
        class Fake:
            def json(self,*a):return {'tag_name':'wrong','assets':[]}
        self.fail_code('UPSTREAM_CHANGED',lambda:resolve(item,Fake()))
    def test_nexus_free_does_not_download_without_click(self):
        item=self.recipe('nexus')['items'][0]
        class Fake:
            def json(self,*a):return {'is_premium':False}
        self.fail_code('WAITING_USER_DOWNLOAD',lambda:resolve(item,Fake(),'SECRET'))
    def test_download_digest_failure_retains_partial(self):
        class Resp(io.BytesIO):
            headers={'Content-Length':'3'}
            def geturl(self):return 'https://github.com/file'
        h=Http()
        with patch.object(h,'_open',return_value=Resp(b'abc')):
            self.fail_code('HASH_MISMATCH',lambda:h.download('https://github.com/file','github',self.root/'x.zip',30,'0'*64))
        self.assertTrue((self.root/'x.zip.part').exists());self.assertFalse((self.root/'x.zip').exists())

class WorkflowTests(Base):
    def test_no_network_without_action(self):self.fail_code('NETWORK_NOT_AUTHORIZED',lambda:acquire(self.job()))
    def test_download_success_then_reuse(self):
        j=self.job(self.recipe('github_release'));payload=self.archive().read_bytes();sha=hashlib.sha256(payload).hexdigest()
        metadata={'tag_name':'v1','assets':[{'name':'Demo.zip','id':1,'digest':'sha256:'+sha,'browser_download_url':'https://github.com/example/example/releases/download/v1/Demo.zip'}]}
        class Resp(io.BytesIO):
            def __init__(self,data,url):super().__init__(data);self.headers={'Content-Length':str(len(data))};self.url=url
            def geturl(self):return self.url
        def response(url,*a):return Resp(json.dumps(metadata).encode() if 'api.github.com' in url else payload,url)
        h=Http()
        with patch.object(h,'_open',side_effect=response) as opened:
            self.assertEqual(acquire(j,allow_network=True,http=h)['items'][0]['status'],'ACQUIRED')
            self.assertEqual(acquire(j,allow_network=True,http=h)['items'][0]['status'],'ACQUIRED');self.assertEqual(opened.call_count,2)
        self.assertEqual(j.checkpoint('demo','ACQUIRED')['integrity'],'upstream_digest_matched')
        self.assertEqual(stage(j,'demo')['status'],'STAGED_NOT_INSTALLED')
    def test_no_key_is_wait_not_failure(self):
        j=self.job(self.recipe('nexus'));r=acquire(j,allow_network=True);self.assertEqual(r['items'][0]['status'],'WAITING_NEXUS_AUTH')
        self.assertNotIn('SECRET',json.dumps(j.events()))
    def test_import_requires_confirmation(self):self.fail_code('SOURCE_CONFIRMATION_REQUIRED',lambda:import_archive(self.job(),'demo',self.archive()))
    def test_import_stage_idempotent(self):
        j=self.prepared();p=self.root/'Demo.zip';import_archive(j,'demo',p,confirmed_source=True)
        self.assertTrue(stage(j,'demo')['reused']);self.assertEqual(len(list((j.path/'downloads').iterdir())),1)
    def test_corrupt_stored_archive(self):
        j=self.prepared();(j.path/'downloads/demo.zip').write_bytes(b'corrupt')
        self.fail_code('HASH_MISMATCH',lambda:j.acquired('demo'))
    def test_unfinished_intent_not_retried(self):
        j=self.job(self.recipe('github_release'));j.event('demo','DOWNLOADING')
        class Fail:
            def json(self,*a):raise AssertionError('must not retry')
        self.assertEqual(acquire(j,allow_network=True,http=Fail())['items'][0]['status'],'DOWNLOADING')
    def test_access_denied_provider_persists(self):
        r=self.recipe('nexus');other=copy.deepcopy(r['items'][0]);other['id']='other';r['items'].append(other);r['presets']['real-time'].append('other')
        j=self.job(r)
        class Denied:
            calls=0
            def json(self,*a):self.calls+=1;raise ModError('ACCESS_DENIED','Provider denied access.')
        fake=Denied();acquire(j,allow_network=True,nexus_key='SECRET',http=fake);acquire(j,allow_network=True,nexus_key='SECRET',http=fake)
        self.assertEqual(fake.calls,1);self.assertNotIn('SECRET',json.dumps(j.events()))
    def test_rate_limit_not_retried(self):
        j=self.job(self.recipe('github_release'))
        class Rate:
            calls=0
            def json(self,*a):self.calls+=1;raise ModError('RATE_LIMITED','Rate limited.')
        h=Rate();acquire(j,allow_network=True,http=h);acquire(j,allow_network=True,http=h);self.assertEqual(h.calls,1)
    def test_journal_gap(self):
        j=self.job();j.event('demo','PLANNED');(j.path/'events/000001.json').rename(j.path/'events/000003.json')
        # Sequence must also agree with the filename, not just payload.
        self.fail_code('JOURNAL_CORRUPT',lambda:j.events())
    def test_generic_download_import_stage(self):
        r=self.recipe();r['game_id']='another-game';r['manager_id']='vortex';j=self.job(r);p=self.root/'generic.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('Data/mod.txt','fixture')
        import_archive(j,'demo',p,confirmed_source=True);self.assertEqual(stage(j,'demo')['status'],'STAGED_NOT_INSTALLED')

class DeploymentTests(Base):
    def test_native_guard_non_windows(self):
        if os.name=='nt':self.skipTest('Linux-specific gate')
        self.fail_code('WINDOWS_REQUIRED',require_closed)
    def test_explicit_plan_approval(self):
        j=self.prepared();g,d=self.game()
        self.fail_code('APPROVAL_MISMATCH',lambda:install_new(j,'demo',g,d,approved_plan_sha256='wrong',game_version='2.1.7',umm_version='0.33.2'))
    def test_new_install_and_rollback_preserve_sources(self):
        j=self.prepared();g,d=self.game();before=digest(g/'Kingmaker.exe');save=digest(d/'Saves/test.zks')
        result=self.install(j,g,d);self.assertEqual(result['status'],'FILES_INSTALLED_RUNTIME_UNVERIFIED')
        self.assertEqual(audit_installed(j,'demo')['status'],'MATCH');self.assertEqual(digest(g/'Kingmaker.exe'),before)
        self.assertEqual(digest(d/'Saves/test.zks'),save)
        with patch('game_mod_ops.umm.require_closed'):self.assertEqual(rollback_new(j,'demo',j.plan['plan_sha256'])['status'],'ROLLED_BACK_RETAINED')
        self.assertFalse((g/'Mods/Demo').exists());self.assertTrue(list((g/'.mod-workflow-recovery').iterdir()))
    def test_install_idempotent(self):
        j=self.prepared();g,d=self.game();self.install(j,g,d);self.assertTrue(self.install(j,g,d)['reused'])
        self.assertEqual(len(list((j.path/'recovery').glob('*.zip'))),1)
    def test_existing_mod_not_overwritten(self):
        j=self.prepared();g,d=self.game();target=g/'Mods/Demo';target.mkdir(parents=True);(target/'Info.json').write_text('{"Id":"Demo","Version":"9.0"}')
        self.fail_code('EXISTING_MOD',lambda:self.install(j,g,d));self.assertIn('9.0',(target/'Info.json').read_text())
    def test_rollback_refuses_new_save_state(self):
        j=self.prepared();g,d=self.game();self.install(j,g,d);(d/'Saves/test.zks').write_bytes(b'later save')
        with patch('game_mod_ops.umm.require_closed'):self.fail_code('SAVE_STATE_CHANGED',lambda:rollback_new(j,'demo',j.plan['plan_sha256']))
        self.assertTrue((g/'Mods/Demo').exists());self.assertEqual((d/'Saves/test.zks').read_bytes(),b'later save')
    def test_rollback_refuses_generated_settings(self):
        j=self.prepared();g,d=self.game();self.install(j,g,d);(g/'Mods/Demo/Settings.xml').write_text('later settings')
        with patch('game_mod_ops.umm.require_closed'):self.fail_code('CONCURRENT_CHANGE',lambda:rollback_new(j,'demo',j.plan['plan_sha256']))
        self.assertTrue((g/'Mods/Demo/Settings.xml').exists())
    def test_missing_loader(self):
        j=self.prepared();g,d=self.game();(g/LOADER_RELATIVE).unlink()
        self.fail_code('LOADER_MISSING',lambda:self.install(j,g,d));self.assertFalse((g/'Mods/Demo').exists())
    def test_missing_recovery(self):
        j=self.prepared();g,d=self.game();(d/'Saves/test.zks').unlink()
        self.fail_code('RECOVERY_REQUIRED',lambda:self.install(j,g,d));self.assertFalse((g/'Mods/Demo').exists())
    def test_unknown_mod_identity_needs_review(self):
        r=self.recipe();r['items'][0]['umm_id']=None;j=self.job(r);import_archive(j,'demo',self.archive(),confirmed_source=True);stage(j,'demo');g,d=self.game()
        self.fail_code('MOD_ID_REVIEW_REQUIRED',lambda:self.install(j,g,d))
    def test_interrupted_install_not_repeated(self):
        j=self.prepared();g,d=self.game()
        calls=[0]
        def guard():
            calls[0]+=1
            if calls[0]>=3:raise ModError('RUNNING_OWNER','A process appeared.')
        with patch('game_mod_ops.umm.require_closed',side_effect=guard):
            self.fail_code('RUNNING_OWNER',lambda:install_new(j,'demo',g,d,approved_plan_sha256=j.plan['plan_sha256'],game_version='2.1.7',umm_version='0.33.2'))
        self.assertEqual(j.latest('demo')['status'],'INSTALLING')
        self.fail_code('RECONCILIATION_REQUIRED',lambda:self.install(j,g,d))
    def test_missing_dependency_does_not_deploy(self):
        j=self.job();p=self.archive(info_extra={'Requirements':['RequiredMod-1.0']});import_archive(j,'demo',p,confirmed_source=True);stage(j,'demo');g,d=self.game()
        self.fail_code('DEPENDENCY_MISSING',lambda:self.install(j,g,d));self.assertFalse((g/'Mods/Demo').exists())
    def test_old_versions_stop_before_files(self):
        j=self.prepared();g,d=self.game()
        self.fail_code('VERSION_TOO_OLD',lambda:install_new(j,'demo',g,d,approved_plan_sha256=j.plan['plan_sha256'],game_version='2.0.7',umm_version='0.33.2'))

if __name__=='__main__':unittest.main(verbosity=2)
