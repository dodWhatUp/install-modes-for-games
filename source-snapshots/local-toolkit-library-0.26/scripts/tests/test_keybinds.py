"""Synthetic configs only. No games or user configuration files are used."""
from __future__ import annotations
import copy
import io
import json
import os
from pathlib import Path
import random
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS=Path(__file__).absolute().parents[1]
sys.path.insert(0,str(SCRIPTS))
from game_keybind_ops.core import Service,compile_changes,validate_spec,snapshot,sha
from game_keybind_ops.documents import Document
from game_keybind_ops.discovery import walk_pattern,discover_local,catalog
from game_keybind_ops.deps import Error,object_hash,Journal,inspect_journal
from game_keybind_ops.planner import extract,cached_extract

KEYS={k:k for k in ['E','F','Q','R','V','Space','LShift','RShift','LCtrl','RCtrl',
                    'MouseLeft','MouseRight','WheelUp','WheelDown','MouseMiddle']}
BASE=b'{\n  "bindings": {"use":"E", "reload":"R", "fire":"MouseLeft", "aim":"MouseRight", "scroll":"WheelUp"},\n  "graphics": {"quality":"ultra", "hdr":true}, "unrelated": "keep this text"\n}\n'

def field(i,selector,keys=None,group='gameplay',**kwargs):
    return {'id':i,'selector':selector,'keys':keys or KEYS,'collision_group':group,**kwargs}

def spec(root:Path,relative='settings.json',adapter='json',ident='fixture',fields=None,**kwargs):
    return {'schema_version':1,'target_id':ident,'game_id':'synthetic-game','root':str(root.absolute()),
       'relative':relative,'adapter':adapter,'fields':fields or [field(n,{'pointer':'/bindings/'+n}) for n in ['use','reload','fire','aim','scroll']],
       'inventory_complete':True,'stopped_processes':['synthetic-game.exe','steam.exe'],
       'evidence':'SYNTHETIC FIXTURE: tests parser/transaction behavior, not a shipped game schema.',**kwargs}

class Fixtures(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.game=self.root/'game';self.game.mkdir()
        self.path=self.game/'settings.json';self.path.write_bytes(BASE)
        self.s=Service(self.root/'data',process_reader=lambda:set())
        self.record=self.s.register_local(spec(self.game));self.revision=self.record['target_revision']
    def tearDown(self):self.tmp.cleanup()
    def edits(self,changes=None):return [{'target_id':'fixture','target_revision':self.revision,'changes':changes or {'use':'F'}}]
    def stage(self,changes=None,ident='plan'):
        items=self.edits(changes);p=self.s.preview(items)
        return self.s.prepare(items,p['preview_sha256'],plan_id=ident)
    def apply(self,p=None):
        p=p or self.stage()
        return self.s.apply_local(p['plan_id'],p['plan_sha256'],authorize=lambda _:True)
    def fails(self,code,fn):
        with self.assertRaises(Error) as ctx:fn()
        self.assertEqual(ctx.exception.code,code)

class CoreTests(Fixtures):
    def test_constructor_inert(self):
        p=self.root/'absent';Service(p);self.assertFalse(p.exists())
    def test_register_no_game_change(self):self.assertEqual(self.path.read_bytes(),BASE)
    def test_preview_no_effect(self):
        before=list(self.s.root.rglob('*'));p=self.s.preview(self.edits());self.assertEqual(p['status'],'PREVIEW_NOT_INSTALLED');self.assertEqual(before,list(self.s.root.rglob('*')))
    def test_stage_only_copies(self):
        p=self.stage();self.assertEqual(p['status'],'STAGED_NOT_INSTALLED');self.assertEqual(self.path.read_bytes(),BASE)
    def test_apply_roundtrip_and_byte_exact_backup(self):
        p=self.apply();self.assertEqual(p['status'],'APPLIED_FILES_RUNTIME_UNVERIFIED')
        self.assertEqual(self.path.read_bytes(),BASE.replace(b'"use":"E"',b'"use":"F"'))
        self.assertEqual((self.s.plans/'plan/00-before.bin').read_bytes(),BASE)
    def test_complete_journal(self):
        self.apply();r=inspect_journal(self.s.plans/'plan/apply.jsonl');self.assertTrue(r['valid']);self.assertTrue(r['clean_end'])
    def test_no_approval(self):
        p=self.stage();self.fails('LOCAL_APPROVAL_REQUIRED',lambda:self.s.apply_local('plan',p['plan_sha256'],authorize=lambda _:False));self.assertEqual(self.path.read_bytes(),BASE)
    def test_wrong_plan_hash(self):
        self.stage();self.fails('PLAN_CHANGED',lambda:self.s.apply_local('plan','0'*64,authorize=lambda _:True))
    def test_source_changed_after_preview(self):
        p=self.s.preview(self.edits());self.path.write_bytes(BASE+b' ')
        self.fails('PREVIEW_STALE',lambda:self.s.prepare(self.edits(),p['preview_sha256']))
    def test_source_changed_after_stage(self):
        p=self.stage();later=BASE.replace(b'ultra',b'high');self.path.write_bytes(later)
        self.fails('SOURCE_CHANGED',lambda:self.apply(p));self.assertEqual(self.path.read_bytes(),later)
    def test_source_deleted(self):
        p=self.stage();self.path.unlink()
        with self.assertRaises(FileNotFoundError):self.apply(p)
        self.assertFalse(self.path.exists())
    def test_game_running(self):
        p=self.stage();self.s.process_reader=lambda:{'synthetic-game.exe'}
        self.fails('PROCESS_RUNNING',lambda:self.apply(p));self.assertEqual(self.path.read_bytes(),BASE)
    def test_cloud_writer_running(self):
        p=self.stage();self.s.process_reader=lambda:{'STEAM.EXE'};self.fails('PROCESS_RUNNING',lambda:self.apply(p))
    def test_process_unknown(self):
        p=self.stage();self.s.process_reader=lambda:None;self.fails('PROCESS_STATE_UNKNOWN',lambda:self.apply(p))
    def test_read_only(self):
        p=self.stage();self.path.chmod(0o444)
        try:self.fails('READ_ONLY',lambda:self.apply(p))
        finally:self.path.chmod(0o644)
    def test_backup_tamper(self):
        p=self.stage();(self.s.plans/'plan/00-before.bin').write_bytes(b'tampered');self.fails('BACKUP_CORRUPT',lambda:self.apply(p))
    def test_staged_tamper(self):
        p=self.stage();(self.s.plans/'plan/00-after.bin').write_bytes(b'tampered');self.fails('BACKUP_CORRUPT',lambda:self.apply(p))
    def test_plan_tamper(self):
        self.stage();path=self.s.plans/'plan/plan.json';p=json.loads(path.read_text());p['items'][0]['after_sha256']='0'*64;path.write_text(json.dumps(p))
        self.fails('PLAN_CORRUPT',lambda:self.s.status('plan'))
    def test_stale_lock_not_deleted(self):
        p=self.stage();lock=self.s.root/'.keybind-ops.lock';lock.write_text('{"pid":12345}')
        self.fails('OWNER_UNKNOWN',lambda:self.apply(p));self.assertTrue(lock.exists())
    def test_repeated_stage_same_id_idempotent(self):
        p=self.stage();self.assertEqual(p,self.stage())
    def test_repeated_stage_conflicting_id(self):
        self.stage();self.fails('PLAN_ID_CONFLICT',lambda:self.stage({'use':'Q'}))
    def test_repeated_apply_is_noop(self):
        p=self.stage();self.apply(p);before=list(self.s.root.rglob('*'));stamp=self.path.stat().st_mtime_ns;self.apply(p)
        self.assertEqual(before,list(self.s.root.rglob('*')));self.assertEqual(stamp,self.path.stat().st_mtime_ns)
    def test_repeated_apply_after_drift_refused(self):
        p=self.stage();self.apply(p);self.path.write_bytes(BASE);self.fails('SOURCE_CHANGED',lambda:self.apply(p))
    def test_cancel_before_first_write(self):
        from threading import Event
        e=Event();e.set();p=self.stage();r=self.s.apply_local('plan',p['plan_sha256'],authorize=lambda _:True,cancel=e)
        self.assertEqual(r['status'],'STOPPED_RECONCILE');self.assertEqual(self.path.read_bytes(),BASE)
    def test_io_failure_no_retry(self):
        p=self.stage();self.s.replacer=lambda *_:(_ for _ in ()).throw(PermissionError())
        self.assertEqual(self.apply(p)['status'],'STOPPED_RECONCILE');self.fails('RECONCILIATION_REQUIRED',lambda:self.apply(p))
    def test_failure_after_effect_classified(self):
        def uncertain(path,data):path.write_bytes(data);raise OSError('simulated interruption')
        p=self.stage();self.s.replacer=uncertain;self.apply(p)
        self.assertEqual(self.s.reconcile('plan')['files'][0]['state'],'AFTER')
    def test_wrong_postwrite_bytes(self):
        p=self.stage();self.s.replacer=lambda path,data:path.write_bytes(b'not reviewed')
        self.assertEqual(self.apply(p)['status'],'STOPPED_RECONCILE');self.assertEqual(self.s.reconcile('plan')['files'][0]['state'],'DIVERGED')
    def test_keyboard_swap_whole_transaction(self):
        self.apply(self.stage({'use':'R','reload':'E'}));r=json.loads(self.path.read_bytes());self.assertEqual(r['bindings']['use'],'R');self.assertEqual(r['bindings']['reload'],'E')
    def test_keyboard_collision(self):self.fails('KEY_COLLISION',lambda:self.s.preview(self.edits({'use':'R'})))
    def test_unreviewed_setting(self):self.fails('UNREVIEWED_FIELD',lambda:self.s.preview(self.edits({'quality':'F'})))
    def test_unknown_key(self):self.fails('KEY_UNSUPPORTED',lambda:self.s.preview(self.edits({'use':'unknown'})))
    def test_left_mouse_protected(self):self.fails('MOUSE_PROTECTED',lambda:self.s.preview(self.edits({'fire':'F'})))
    def test_right_mouse_protected(self):self.fails('MOUSE_PROTECTED',lambda:self.s.preview(self.edits({'aim':'F'})))
    def test_scroll_protected(self):self.fails('MOUSE_PROTECTED',lambda:self.s.preview(self.edits({'scroll':'F'})))
    def test_assigning_mouse_protected(self):self.fails('MOUSE_PROTECTED',lambda:self.s.preview(self.edits({'use':'MouseLeft'})))
    def test_middle_without_explicit_recipe(self):self.fails('MIDDLE_REVIEW_REQUIRED',lambda:self.s.preview(self.edits({'use':'MouseMiddle'})))
    def test_target_revision_drift(self):
        e=self.edits();e[0]['target_revision']='0'*64;self.fails('TARGET_CHANGED',lambda:self.s.preview(e))
    def test_duplicate_target(self):self.fails('DUPLICATE_TARGET',lambda:self.s.preview(self.edits()*2))
    def test_same_file_different_target_ids(self):
        r=self.s.register_local(spec(self.game,ident='alias'));e=self.edits()+[{'target_id':'alias','target_revision':r['target_revision'],'changes':{'use':'F'}}]
        self.fails('DUPLICATE_TARGET',lambda:self.s.preview(e))
    def test_exact_undo(self):
        self.apply();p=self.s.exact_rollback_preview('plan');undo=self.s.prepare_rollback('plan',p['preview_sha256'],plan_id='undo')
        self.apply(undo);self.assertEqual(self.path.read_bytes(),BASE)
    def test_exact_undo_refuses_later_graphics(self):
        self.apply();self.path.write_bytes(self.path.read_bytes().replace(b'ultra',b'high'));self.fails('ROLLBACK_CONFLICT',lambda:self.s.exact_rollback_preview('plan'))
    def test_selective_undo_preserves_later_graphics(self):
        self.apply();later=self.path.read_bytes().replace(b'ultra',b'high');self.path.write_bytes(later)
        p=self.s.rollback_preview('plan',selective=True);u=self.s.prepare_rollback('plan',p['preview_sha256'],selective=True);self.apply(u)
        self.assertEqual(self.path.read_bytes(),BASE.replace(b'ultra',b'high'))
    def test_selective_undo_refuses_later_binding(self):
        self.apply();self.path.write_bytes(self.path.read_bytes().replace(b'"use":"F"',b'"use":"V"'))
        self.fails('ROLLBACK_CONFLICT',lambda:self.s.rollback_preview('plan',selective=True))
    def test_undo_not_applied(self):self.stage();self.fails('NOT_APPLIED',lambda:self.s.exact_rollback_preview('plan'))
    def test_context_incremental(self):
        a=self.s.context();b=self.s.context(a['revision']);self.assertTrue(b['unchanged']);self.assertNotIn('targets',b)
    def test_context_no_paths(self):self.assertNotIn(str(self.root),json.dumps(self.s.context()))
    def test_replacement_accepts_binding_only(self):
        r=self.root/'new.json';r.write_bytes(BASE.replace(b'"use":"E"',b'"use":"F"'))
        v=self.s.replacement_preview_local('fixture',r);self.assertEqual(v['items_request'][0]['changes'],{'use':'F'})
    def test_replacement_rejects_graphics(self):
        r=self.root/'new.json';r.write_bytes(BASE.replace(b'"use":"E"',b'"use":"F"').replace(b'ultra',b'low'))
        self.fails('UNRELATED_CHANGE',lambda:self.s.replacement_preview_local('fixture',r))
    def test_replacement_rejects_format_only_rewrite(self):
        r=self.root/'new.json';v=json.loads(BASE);v['bindings']['use']='F';r.write_text(json.dumps(v))
        self.fails('UNRELATED_CHANGE',lambda:self.s.replacement_preview_local('fixture',r))
    def test_register_existing_conflicting_spec(self):
        s=spec(self.game,notes='a new interpretation');self.fails('TARGET_CONFLICT',lambda:self.s.register_local(s))
    def test_incomplete_inventory(self):
        ss=spec(self.game,ident='incomplete');ss['inventory_complete']=False;r=self.s.register_local(ss)
        self.fails('INVENTORY_INCOMPLETE',lambda:self.s.preview([{'target_id':'incomplete','target_revision':r['target_revision'],'changes':{'use':'F'}}]))
    def test_locked_field(self):
        ss=spec(self.game,ident='locked');ss['fields'][0]['locked']=True;r=self.s.register_local(ss)
        self.fails('FIELD_PROTECTED',lambda:self.s.preview([{'target_id':'locked','target_revision':r['target_revision'],'changes':{'use':'F'}}]))
    def test_linked_group(self):
        ss=spec(self.game,ident='linked');ss['fields'][0]['linked_group']='one';ss['fields'][1]['linked_group']='one';r=self.s.register_local(ss)
        self.fails('LINKED_ACTIONS',lambda:self.s.preview([{'target_id':'linked','target_revision':r['target_revision'],'changes':{'use':'F'}}]))
    def test_middle_with_reviewed_recipe(self):
        ss=spec(self.game,ident='middle',allow_middle=True);r=self.s.register_local(ss)
        v=self.s.preview([{'target_id':'middle','target_revision':r['target_revision'],'changes':{'use':'MouseMiddle'}}]);self.assertEqual(v['status'],'PREVIEW_NOT_INSTALLED')
    def test_hardlink(self):
        other=self.root/'hard';os.link(self.path,other)
        self.fails('HARDLINK_BLOCKED',lambda:self.s.inspect_target('fixture'))
    def test_symlink(self):
        link=self.game/'link.json';link.symlink_to(self.path);self.fails('LINK_BLOCKED',lambda:self.s.register_local(spec(self.game,relative='link.json',ident='link')))
    def test_traversal(self):self.fails('UNSAFE_PATH',lambda:validate_spec(spec(self.game,relative='../outside.json')))
    def test_no_registry_or_binary(self):self.fails('ADAPTER_UNSUPPORTED',lambda:validate_spec(spec(self.game,adapter='binary')))
    def test_no_save_file(self):self.fails('FILE_ROLE_UNSUPPORTED',lambda:validate_spec(spec(self.game,relative='SlotData_0.dat')))
    def test_storage_budget_preserves_original(self):
        with patch('game_keybind_ops.core.MAX_STORAGE',1):self.fails('STORAGE_BUDGET',self.stage)
        self.assertEqual(self.path.read_bytes(),BASE)
    def test_low_disk_preserves_original(self):
        with patch('game_keybind_ops.core.shutil.disk_usage',return_value=type('Usage',(),{'free':0})()):self.fails('DISK_SPACE',self.stage)
        self.assertEqual(self.path.read_bytes(),BASE)
    def test_explicit_current_recipe_tamper(self):
        path=self.s.targets/'fixture.json';r=json.loads(path.read_text());r['spec']['fields'][0]['locked']=True;path.write_text(json.dumps(r))
        self.fails('TARGET_CORRUPT',lambda:self.s.inspect_target('fixture'))
    def test_noop_change(self):self.fails('NO_CHANGES',lambda:self.s.preview(self.edits({'use':'E'})))
    def test_empty_config(self):self.path.write_bytes(b'');self.fails('SIZE_LIMIT',lambda:self.s.inspect_target('fixture'))
    def test_oversized_config(self):
        with patch('game_keybind_ops.core.MAX_BYTES',8):self.fails('SIZE_LIMIT',lambda:self.s.inspect_target('fixture'))
    def test_hash_tampered_journal(self):
        self.apply();p=self.s.plans/'plan/apply.jsonl';p.write_bytes(p.read_bytes().replace(b'keybind_file_verified',b'keybind_file_modified'))
        self.fails('JOURNAL_CORRUPT',lambda:self.s.status('plan'))
    def test_two_file_success(self):
        second=self.game/'other.json';second.write_bytes(BASE);r=self.s.register_local(spec(self.game,'other.json',ident='other'))
        e=self.edits()+[{'target_id':'other','target_revision':r['target_revision'],'changes':{'use':'V'}}]
        p=self.s.preview(e);st=self.s.prepare(e,p['preview_sha256']);self.apply(st)
        self.assertEqual(json.loads(second.read_bytes())['bindings']['use'],'V')
    def test_partial_transaction_explicit_recovery(self):
        second=self.game/'other.json';second.write_bytes(BASE);r=self.s.register_local(spec(self.game,'other.json',ident='other'))
        e=self.edits()+[{'target_id':'other','target_revision':r['target_revision'],'changes':{'use':'V'}}]
        p=self.s.preview(e);st=self.s.prepare(e,p['preview_sha256']);n=[0]
        from game_keybind_ops.core import replace_existing
        def failure(path,data):
            n[0]+=1
            if n[0]==2:raise OSError('simulated denied file')
            replace_existing(path,data)
        self.s.replacer=failure;result=self.apply(st);self.assertEqual(result['status'],'STOPPED_RECONCILE')
        states=self.s.reconcile(st['plan_id']);self.assertEqual([f['state'] for f in states['files']],['AFTER','BEFORE'])
        self.s.replacer=replace_existing;undo=self.s.exact_rollback_preview(st['plan_id']);u=self.s.prepare_rollback(st['plan_id'],undo['preview_sha256']);self.apply(u)
        self.assertEqual(self.path.read_bytes(),BASE);self.assertEqual(second.read_bytes(),BASE)

class DocumentTests(unittest.TestCase):
    def fail(self,code,fn):
        with self.assertRaises(Error) as c:fn()
        self.assertEqual(c.exception.code,code)
    def test_json_unchanged_bytes(self):
        d=Document(BASE,'json');out=d.render([({'pointer':'/bindings/use'},'F')]);self.assertEqual(out,BASE.replace(b'"use":"E"',b'"use":"F"'))
    def test_json_duplicate_fields(self):self.fail('INVALID_JSON',lambda:Document(b'{"x":1,"x":2}','json'))
    def test_json_nan(self):self.fail('INVALID_JSON',lambda:Document(b'{"x":NaN}','json'))
    def test_json_array_and_escaped_pointer(self):
        d=Document(b'{"a/b":[{"~c":"E"}]}','json');self.assertEqual(d.select({'pointer':'/a~1b/0/~0c'}).value,'E')
    def test_json_escaped_string_preserved(self):
        raw=b'{"key":"E","keep":"\\u05d0"}';self.assertEqual(Document(raw,'json').render([({'pointer':'/key'},'F')]),raw.replace(b'"E"',b'"F"'))
    def test_utf8_bom(self):
        raw=b'\xef\xbb\xbf'+BASE;out=Document(raw,'json').render([({'pointer':'/bindings/use'},'F')]);self.assertTrue(out.startswith(b'\xef\xbb\xbf'))
    def test_utf16le_bom(self):
        raw=b'\xff\xfe'+BASE.decode().encode('utf-16-le');out=Document(raw,'json').render([({'pointer':'/bindings/use'},'F')]);self.assertEqual(out,b'\xff\xfe'+BASE.replace(b'"use":"E"',b'"use":"F"').decode().encode('utf-16-le'))
    def test_utf16be_bom(self):
        raw=b'\xfe\xff'+BASE.decode().encode('utf-16-be');out=Document(raw,'json').render([({'pointer':'/bindings/use'},'F')]);self.assertTrue(out.startswith(b'\xfe\xff'))
    def test_ini_crlf_comments(self):
        raw=b'; keep\r\n[ACTION_KEYS]\r\nuse = 69  ; note\r\n[Graphics]\r\nquality=ultra\r\n'
        out=Document(raw,'ini').render([({'section':'ACTION_KEYS','key':'use','occurrence':0,'part':'value'},'70')]);self.assertEqual(out,raw.replace(b'69',b'70'))
    def test_ini_cp1252(self):
        raw=b'; caf\xe9\n[Keys]\na=E\n';d=Document(raw,'ini','cp1252');self.assertIn(b'caf\xe9',d.render([({'section':'Keys','key':'a','occurrence':0,'part':'value'},'F')]))
    def test_ini_rekey_stable_command(self):
        raw=b'[Engine.Input]\nE=Use\nR=Reload\nLeftMouse=Fire\n';d=Document(raw,'ini');sel={'section':'Engine.Input','command':'Use','occurrence':0,'part':'key'}
        out=d.render([(sel,'F')]);self.assertEqual(Document(out,'ini').select(sel).value,'F')
    def test_ini_duplicate_key_requires_occurrence(self):
        d=Document(b'[K]\na=E\na=F\n','ini');self.assertEqual(d.select({'section':'K','key':'a','occurrence':1,'part':'value'}).value,'F')
    def test_ini_no_bare_defaults_invented(self):self.fail('FORMAT_UNSUPPORTED',lambda:Document(b'[K]\nmissing delimiter\n','ini'))
    def test_unreal_repeated_action(self):
        raw=b'[/Script/Engine.InputSettings]\n+ActionMappings=(ActionName="Use",Key=E,bShift=False,bCtrl=False)\n+ActionMappings=(ActionName="Use",Key=Q,bShift=True,bCtrl=False)\n'
        d=Document(raw,'ue-ini');s={'section':'/Script/Engine.InputSettings','action':'Use','occurrence':1}
        self.assertEqual(d.render([(s,'F')]),raw.replace(b'Key=Q',b'Key=F'))
    def test_xml_attributes_only(self):
        raw=b'<?xml version="1.0"?><settings><!-- keep --><bind action="Use" key = \'E\'/><graphics hdr="yes"/></settings>'
        d=Document(raw,'xml');sel={'element':'settings[0]/bind[0]','attribute':'key'};self.assertEqual(d.render([(sel,'F')]),raw.replace(b"'E'",b"'F'"))
    def test_xml_gt_inside_attribute(self):
        raw=b'<r><x a="a>b" key="E"/></r>';d=Document(raw,'xml');self.assertEqual(d.select({'element':'r[0]/x[0]','attribute':'key'}).value,'E')
    def test_xml_dtd_blocked(self):self.fail('XML_ENTITY_BLOCKED',lambda:Document(b'<!DOCTYPE r [<!ENTITY x "E">]><r k="&x;"/>','xml'))
    def test_xml_malformed(self):self.fail('FORMAT_INVALID',lambda:Document(b'<r><x></r>','xml'))
    def test_cfg_native_command_preserved(self):
        raw=b'// settings\nbind "e" "_use"\nr_quality "ultra"\n';sel={'command':'_use','occurrence':0}
        self.assertEqual(Document(raw,'cfg-bind').render([(sel,'f')]),raw.replace(b'"e"',b'"f"'))
    def test_cfg_unknown_bind_shape(self):self.fail('FORMAT_UNSUPPORTED',lambda:Document(b'bind e _use\n','cfg-bind'))
    def test_no_command_injection(self):
        d=Document(b'[K]\na=E\n','ini');self.fail('INVALID_VALUE',lambda:d.render([({'section':'K','key':'a','occurrence':0,'part':'value'},'F\nnew=bad')]))
    def test_no_ambiguous_selector(self):
        self.fail('SELECTOR_AMBIGUOUS',lambda:Document(BASE,'json').select({'pointer':'/absent'}))
    def test_no_double_edit(self):
        d=Document(BASE,'json');s={'pointer':'/bindings/use'};self.fail('OVERLAPPING_PATCH',lambda:d.render([(s,'F'),(s,'Q')]))
    def test_no_binary_guessing(self):self.fail('BINARY_UNSUPPORTED',lambda:Document(b'opaque\x00blob','ini'))
    def test_100_randomized_key_swaps(self):
        rng=random.Random(672);keys=list('EFQRV')
        ss=spec(Path('/fixture'),fields=[field(k,{'pointer':'/'+k}) for k in keys])
        for _ in range(100):
            rng.shuffle(keys);raw=json.dumps(dict(zip('EFQRV',keys))).encode();a,b=rng.sample(list('EFQRV'),2)
            values=json.loads(raw);out,_=compile_changes(raw,ss,{a:values[b],b:values[a]})
            desired=dict(values);desired[a],desired[b]=values[b],values[a];self.assertEqual(json.loads(out),desired)

class DiscoveryTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_known_17_games(self):self.assertEqual(len(catalog()['games']),17)
    def test_none_marked_write_ready(self):self.assertTrue(all(g['discovery_only'] and not g['native_recipe_bundled'] for g in catalog()['games']))
    def test_bound_casefold_match(self):
        (self.root/'Settings').mkdir();(self.root/'Settings/INPUT.INI').write_text('a=b');self.assertEqual(len(walk_pattern(self.root,'settings/input.ini')),1)
    def test_no_recursive_glob(self):
        with self.assertRaises(Error):walk_pattern(self.root,'**/Input.ini')
    def test_no_traversal_glob(self):
        with self.assertRaises(Error):walk_pattern(self.root,'../Input.ini')
    def test_discovery_candidate_not_active(self):
        p=self.root/'CD Projekt Red/Cyberpunk 2077/UserSettings.json';p.parent.mkdir(parents=True);p.write_bytes(BASE)
        r=discover_local('cyberpunk-2077',{'local':self.root});self.assertEqual(len(r['candidates']),1);self.assertFalse(r['active_file_verified']);self.assertFalse(r['candidates'][0]['write_ready'])
    def test_multi_profile_no_guessing(self):
        for n in ('account-A','account-B'):
            p=self.root/f'Rockstar Games/GTAV Enhanced/Profiles/{n}/control/user.xml';p.parent.mkdir(parents=True);p.write_text('<r/>')
        r=discover_local('gta-v-enhanced',{'documents':self.root});self.assertEqual(len(r['candidates']),2);self.assertEqual(r['selection'],'operator_review_required')
    def test_version_folders_no_newest_guess(self):
        for n in ('v3','v4'):
            p=self.root/f'Stunlock Studios/VRising/Settings/{n}/InputSettings.json';p.parent.mkdir(parents=True);p.write_text('{}')
        r=discover_local('v-rising',{'locallow':self.root});self.assertEqual(len(r['candidates']),2);self.assertFalse(r['active_file_verified'])
    def test_no_save_slot_collection(self):
        g=next(g for g in catalog()['games'] if g['id']=='nier-automata');self.assertFalse(any('SlotData' in l['pattern'] for l in g['locations']))
    def test_registry_and_shadow_of_war_report_unresolved(self):
        for game in ['pathfinder-kingmaker','middle-earth-shadow-of-war']:
            r=discover_local(game,{});self.assertFalse(r['candidates'])
    def test_directory_limit(self):
        for n in range(8):(self.root/f'{n}.ini').write_text('a=b')
        with patch('game_keybind_ops.discovery.MAX_ENTRIES',4),self.assertRaises(Error):walk_pattern(self.root,'*.ini')
    def test_symlink_boundary(self):
        (self.root/'link').symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(Error):walk_pattern(self.root,'link/*')

class PlannerTests(unittest.TestCase):
    def minimal(self):
        d={'maps':[{'name':'Game','id':'g','family':'SPARSE6','strategic':{'variants':[
            {'mode':'WASD','context':'gameplay','assignments':{'F':{'en':'Use','target_output':'F','original_output':'E'}},'catalog':[]}]}}],
            'planner_revision':'fixture','audit_corrections':['kept']}
        return b'<script id="map-data" type="application/json">'+json.dumps(d).encode()+b'</script><script>throw new Error("MUST NOT EXECUTE")</script>'
    def test_inert_extraction(self):r=extract(self.minimal());self.assertEqual(r['games'],1);self.assertFalse(r['native_files_generated'])
    def test_keep_context_and_corrections(self):
        r=extract(self.minimal());self.assertEqual(r['variants'][0]['input_preset'],'WASD');self.assertEqual(r['pending_or_source_corrections'],['kept'])
    def test_hash_cache(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'p.html';p.write_bytes(self.minimal());a=cached_extract(p,Path(t)/'data');b=cached_extract(p,Path(t)/'data')
            self.assertFalse(a['cache_hit']);self.assertTrue(b['cache_hit']);self.assertEqual(a['source_sha256'],b['source_sha256'])
    def test_multiple_json_blocks_rejected(self):
        with self.assertRaises(Error):extract(self.minimal()+self.minimal())

if __name__=='__main__':unittest.main(verbosity=2)
