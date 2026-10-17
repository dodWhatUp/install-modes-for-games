"""Format transactions, real subprocess interruption, CLI and strict recovery tests."""
from __future__ import annotations
import json,os,sys,subprocess,tempfile,unittest,shutil
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).absolute().parents[1]))
from test_keybinds import Fixtures,BASE,KEYS,field,spec
from game_keybind_ops.core import Service,sha
from game_keybind_ops.documents import Document
from game_keybind_ops.deps import Error,Journal
from game_keybind_ops.recovery import inspect_lock,retire_lock_local,pid_state

class Review(Fixtures):
    def test_xml_utf16_declaration(self):
        text='<?xml version="1.0" encoding="UTF-16"?><settings><!--אב--><bind key="E" /></settings>'
        raw=b'\xff\xfe'+text.encode('utf-16-le');d=Document(raw,'xml');result=d.render([({'element':'settings[0]/bind[0]','attribute':'key'},'F')])
        self.assertEqual(result,b'\xff\xfe'+text.replace('key="E"','key="F"').encode('utf-16-le'))
    def test_xml_cp1252_declaration(self):
        text='<?xml version="1.0" encoding="windows-1252"?><s caption="caf\xe9" key="E" />'
        raw=text.encode('cp1252');self.assertEqual(Document(raw,'xml','cp1252').render([({'element':'s[0]','attribute':'key'},'F')]),text.replace('key="E"','key="F"').encode('cp1252'))
    def test_journal_transplant_blocked(self):
        p=self.stage();d=self.s.plans/'plan';
        with Journal.create(d/'apply.jsonl',{'owner':'GameToolsKeybinds','plan_id':'different','plan_sha256':p['plan_sha256']}) as j:
            j.append('keybind_result',{'status':'APPLIED_FILES_RUNTIME_UNVERIFIED','verified_files':1});j.append('session_closed',{})
        self.fails('JOURNAL_CORRUPT',lambda:self.s.status('plan'))
    def test_false_success_missing_file_receipt(self):
        p=self.stage()
        with Journal.create(self.s.plans/'plan/apply.jsonl',{'owner':'GameToolsKeybinds','plan_id':'plan','plan_sha256':p['plan_sha256']}) as j:
            j.append('keybind_result',{'status':'APPLIED_FILES_RUNTIME_UNVERIFIED','verified_files':1});j.append('session_closed',{})
        self.fails('JOURNAL_CORRUPT',lambda:self.s.status('plan'))
    def test_preserves_escaped_original_on_exact_rollback(self):
        self.path.write_bytes(BASE.replace(b'"use":"E"',b'"use":"\\u0045"'));old=self.path.read_bytes();p=self.stage();self.apply(p)
        u=self.s.exact_rollback_preview('plan');self.apply(self.s.prepare_rollback('plan',u['preview_sha256']));self.assertEqual(self.path.read_bytes(),old)
    def test_unlisted_ini_target_key_collision(self):
        p=self.game/'a.ini';p.write_bytes(b'[Input]\nE=Use\nF=UnknownAction\n')
        sp=spec(self.game,'a.ini','ini','ini',fields=[field('use',{'section':'Input','command':'Use','occurrence':0,'part':'key'})]);r=self.s.register_local(sp)
        self.fails('KEY_COLLISION',lambda:self.s.preview([{'target_id':'ini','target_revision':r['target_revision'],'changes':{'use':'F'}}]))
    def test_controlled_format_roundtrips(self):
        cases=[('ini',b';keep\r\n[ACTION_KEYS]\r\nuse = E\r\nreload=R\r\n[DISPLAY]\r\nhdr=true\r\n',{'section':'ACTION_KEYS','key':'use','occurrence':0,'part':'value'}),
            ('ini',b'[Engine.Input]\nE=Use\nR=Reload\nMouse1=Fire\n',{'section':'Engine.Input','command':'Use','occurrence':0,'part':'key'}),
            ('ue-ini',b'[/Script/Engine.InputSettings]\n+ActionMappings=(ActionName="Use",Key=E,bShift=False,bCtrl=True,bAlt=False)\n[Else]\nGamma=2\n',{'section':'/Script/Engine.InputSettings','action':'Use','occurrence':0}),
            ('xml',b'<?xml version="1.0"?><settings><bind action="Use" key="E"/><graphics hdr="1"/></settings>',{'element':'settings[0]/bind[0]','attribute':'key'}),
            ('cfg-bind',b'//keep\nbind "E" "_use"\nbind "Mouse1" "_attack"\nset r_mode "4k"\n',{'command':'_use','occurrence':0})]
        for n,(adapter,raw,selector) in enumerate(cases):
            with self.subTest(adapter=adapter,n=n):
                suffix={'ini':'ini','ue-ini':'ini','xml':'xml','cfg-bind':'cfg'}[adapter];filename=f'test{n}.{suffix}';path=self.game/filename;path.write_bytes(raw)
                sp=spec(self.game,filename,adapter,'format'+str(n),fields=[field('use',selector)]);r=self.s.register_local(sp)
                items=[{'target_id':r['target_id'],'target_revision':r['target_revision'],'changes':{'use':'F'}}]
                pv=self.s.preview(items);pl=self.s.prepare(items,pv['preview_sha256']);res=self.apply(pl);self.assertEqual(res['status'],'APPLIED_FILES_RUNTIME_UNVERIFIED')
                self.assertNotEqual(path.read_bytes(),raw);undo=self.s.exact_rollback_preview(pl['plan_id']);self.apply(self.s.prepare_rollback(pl['plan_id'],undo['preview_sha256']));self.assertEqual(path.read_bytes(),raw)
    def test_ini_selective_undo_after_rekey(self):
        raw=b'[Input]\nE=Use\nR=Reload\n[Graphics]\nquality=ultra\n';path=self.game/'bindings.ini';path.write_bytes(raw)
        sp=spec(self.game,'bindings.ini','ini','inikey',fields=[field('use',{'section':'Input','command':'Use','occurrence':0,'part':'key'})]);r=self.s.register_local(sp)
        items=[{'target_id':r['target_id'],'target_revision':r['target_revision'],'changes':{'use':'F'}}];pv=self.s.preview(items);pl=self.s.prepare(items,pv['preview_sha256']);self.apply(pl)
        path.write_bytes(path.read_bytes().replace(b'ultra',b'high'));u=self.s.rollback_preview(pl['plan_id'],selective=True);self.apply(self.s.prepare_rollback(pl['plan_id'],u['preview_sha256'],selective=True));self.assertEqual(path.read_bytes(),raw.replace(b'ultra',b'high'))
    def test_cli_catalog(self):
        p=subprocess.run([sys.executable,str(Path(__file__).absolute().parents[1]/'Game-Keybinds.py'),'--data-dir',str(self.root/'data'),'catalog'],capture_output=True,timeout=10)
        self.assertEqual(p.returncode,0);self.assertEqual(len(json.loads(p.stdout)['games']),17)
    def test_cli_apply_cannot_be_piped(self):
        pl=self.stage();p=subprocess.run([sys.executable,str(Path(__file__).absolute().parents[1]/'Game-Keybinds.py'),'--data-dir',str(self.root/'data'),'apply','--plan',pl['plan_id'],'--plan-sha',pl['plan_sha256']],input=(pl['plan_sha256']+'\n').encode(),capture_output=True,timeout=10)
        self.assertEqual(p.returncode,2);self.assertEqual(json.loads(p.stdout)['status'],'INTERACTIVE_APPROVAL_REQUIRED');self.assertEqual(self.path.read_bytes(),BASE)
    def test_cli_status_valid_json(self):
        self.stage();p=subprocess.run([sys.executable,str(Path(__file__).absolute().parents[1]/'Game-Keybinds.py'),'--data-dir',str(self.root/'data'),'status','--plan','plan'],capture_output=True,timeout=10)
        self.assertEqual(json.loads(p.stdout)['status'],'STAGED_NOT_INSTALLED')
    def test_current_pid_alive(self):self.assertEqual(pid_state(os.getpid()),'ALIVE')
    def test_unknown_pid(self):self.assertEqual(pid_state(-1),'UNKNOWN')
    def test_no_lock(self):self.assertEqual(inspect_lock(self.s)['status'],'NO_LOCK')
    def make_lock(self,pid=456789):
        path=self.s.root/'.keybind-ops.lock';path.write_text(json.dumps({'pid':pid,'created_unix':1,'kind':'cooperative-only'}));return path
    def test_alive_lock_not_retired(self):
        self.make_lock();view=inspect_lock(self.s,lambda _: 'ALIVE');self.fails('OWNER_UNKNOWN',lambda:retire_lock_local(self.s,view['inspection_sha256'],authorize=lambda _:True,pid_reader=lambda _:'ALIVE'))
    def test_unknown_lock_not_retired(self):
        self.make_lock();view=inspect_lock(self.s,lambda _: 'UNKNOWN');self.assertFalse(view['retirement_available'])
    def test_dead_lock_requires_local_approval(self):
        self.make_lock();view=inspect_lock(self.s,lambda _:'DEAD');self.fails('LOCAL_APPROVAL_REQUIRED',lambda:retire_lock_local(self.s,view['inspection_sha256'],authorize=lambda _:False,pid_reader=lambda _:'DEAD'))
    def test_dead_lock_original_archived(self):
        path=self.make_lock();raw=path.read_bytes();view=inspect_lock(self.s,lambda _:'DEAD');result=retire_lock_local(self.s,view['inspection_sha256'],authorize=lambda _:True,pid_reader=lambda _:'DEAD')
        self.assertEqual(result['status'],'DEAD_LOCK_ARCHIVED');self.assertFalse(path.exists());self.assertEqual(next((self.s.root/'retired-locks').glob('*/original-lock.json')).read_bytes(),raw)
    def test_dead_lock_stale_inspection_refused(self):
        path=self.make_lock();v=inspect_lock(self.s,lambda _:'DEAD');path.write_text(path.read_text().replace('456789','456780'))
        self.fails('LOCK_CHANGED',lambda:retire_lock_local(self.s,v['inspection_sha256'],authorize=lambda _:True,pid_reader=lambda _:'DEAD'))
    def test_real_process_interruption_no_replay(self):
        pl=self.stage();scripts=str(Path(__file__).absolute().parents[1])
        code='''import sys,os\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nfrom game_keybind_ops.core import Service,replace_existing\ndef die(p,b):\n replace_existing(p,b);os._exit(23)\ns=Service(Path(sys.argv[2]),process_reader=lambda:set(),replacer=die)\ns.apply_local("plan",sys.argv[3],authorize=lambda _:True)\n'''
        p=subprocess.run([sys.executable,'-c',code,scripts,str(self.root/'data'),pl['plan_sha256']],capture_output=True,timeout=10)
        self.assertEqual(p.returncode,23);self.assertEqual(self.s.status('plan')['status'],'INTERRUPTED_RECONCILE');self.assertEqual(self.s.reconcile('plan')['files'][0]['state'],'AFTER')
        v=inspect_lock(self.s);self.assertEqual(v['owner_state'],'DEAD');retire_lock_local(self.s,v['inspection_sha256'],authorize=lambda _:True)
        self.fails('RECONCILIATION_REQUIRED',lambda:self.apply(pl))
        u=self.s.exact_rollback_preview('plan');self.apply(self.s.prepare_rollback('plan',u['preview_sha256']));self.assertEqual(self.path.read_bytes(),BASE)
    def test_corrupt_journal_cannot_retire(self):
        self.apply();p=self.s.plans/'plan/apply.jsonl';p.write_bytes(p.read_bytes().replace(b'keybind_file_verified',b'keybind_file_corrupted'));self.make_lock()
        self.fails('JOURNAL_CORRUPT',lambda:inspect_lock(self.s,lambda _:'DEAD'))
    def test_diverged_file_keeps_recovery_block(self):
        self.apply();self.path.write_bytes(BASE.replace(b'ultra',b'new'));self.make_lock();self.assertFalse(inspect_lock(self.s,lambda _:'DEAD')['retirement_available'])

if __name__=='__main__':unittest.main(verbosity=2)
