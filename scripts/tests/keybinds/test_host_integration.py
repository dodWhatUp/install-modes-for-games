"""Run against an explicitly supplied, verified Hub source; synthetic game files only."""
from __future__ import annotations
import io,json,os,sys,time,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
HOST=os.environ.get('GAME_TOOLS_HOST_SOURCE')
if not HOST:raise SystemExit('Set GAME_TOOLS_HOST_SOURCE to the verified 0.21.0-preview.1 source root.')
SCRIPTS=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(Path(HOST)/'scripts'));sys.path.insert(0,str(SCRIPTS))
from test_keybinds import Fixtures,BASE
from GameToolKeybindIntegration import KeybindAutomationService,OPERATIONS,capabilities
from GameToolKeybindAI import Endpoint,stdio,extra_tools
from GameToolAI import tools as original_tools
from game_keybind_ops.deps import Error,object_hash

class Integration(Fixtures):
    def setUp(self):
        super().setUp();self.host=KeybindAutomationService(self.root/'data',keybind_service=self.s)
    def args(self):
        e=self.edits();return {'items':e,'preview_sha256':self.s.preview(e)['preview_sha256']}
    def proposal(self,ident='prepare'):
        return self.host.propose('keybinds.prepare',self.args(),request_id=ident)
    def approved_stage(self):
        p=self.proposal();r=self.host.approve_local(p['request_id'],p['request_sha256']);self.assertEqual(r['status'],'COMPLETED')
        return r['result']
    def approved_apply(self):
        p=self.approved_stage();req=self.host.propose('keybinds.apply',{'plan_id':p['plan_id'],'plan_sha256':p['plan_sha256']},request_id='apply')
        return self.host.approve_local('apply',req['request_sha256'])
    def test_constructor_reuses_same_mailbox(self):self.assertEqual(self.host.requests,self.root/'data/automation/requests')
    def test_proposal_does_not_apply_or_stage(self):
        r=self.proposal();self.assertEqual(r['status'],'AWAITING_LOCAL_APPROVAL');self.assertEqual(self.path.read_bytes(),BASE);self.assertFalse(self.s.plans.exists())
    def test_local_approve_stages_only(self):self.approved_stage();self.assertEqual(self.path.read_bytes(),BASE)
    def test_local_approve_apply(self):
        self.approved_apply();self.assertEqual(json.loads(self.path.read_bytes())['bindings']['use'],'F')
    def test_history_readable_after_changed_config(self):
        self.approved_apply();self.assertEqual(self.host.request_status('prepare')['status'],'COMPLETED');self.assertEqual(self.host.request_status('apply')['status'],'COMPLETED')
    def test_changed_content_invalidates_unapproved(self):
        p=self.proposal();self.path.write_bytes(BASE.replace(b'ultra',b'high'))
        self.fails('PREVIEW_STALE',lambda:self.host.approve_local('prepare',p['request_sha256']))
    def test_apply_proposal_is_not_execution(self):
        p=self.approved_stage();self.host.propose('keybinds.apply',{'plan_id':p['plan_id'],'plan_sha256':p['plan_sha256']},request_id='only-propose');self.assertEqual(self.path.read_bytes(),BASE)
    def test_same_request_id_no_duplicate_effect(self):
        p=self.proposal();q=self.proposal();self.assertEqual(p['request_sha256'],q['request_sha256']);self.assertEqual(len(self.host.list_requests()),1)
    def test_changed_request_id_content_blocked(self):
        self.proposal();a=self.args();a['items'][0]['changes']={'use':'V'}
        self.fails('REQUEST_ID_CONFLICT',lambda:self.host.propose('keybinds.prepare',a,request_id='prepare'))
    def test_attempted_request_not_replayed(self):
        p=self.proposal();self.host.approve_local('prepare',p['request_sha256'])
        self.fails('RECONCILIATION_REQUIRED',lambda:self.host.approve_local('prepare',p['request_sha256']))
    def test_expiry(self):
        p=self.proposal()
        with patch('GameToolAutomation.time.time',return_value=time.time()+1000):self.fails('EXPIRED',lambda:self.host.approve_local('prepare',p['request_sha256']))
    def test_host_busy_guard(self):
        p=self.proposal();self.fails('ACTION_BUSY',lambda:self.host.approve_local('prepare',p['request_sha256'],busy_guard=lambda:True))
    def test_ai_cannot_self_approve_argument(self):
        a=self.args();a['approved']=True;self.fails('INVALID_ARGUMENTS',lambda:self.host.propose('keybinds.prepare',a))
    def test_ai_cannot_supply_path(self):
        a=self.args();a['root']='/';self.fails('INVALID_ARGUMENTS',lambda:self.host.propose('keybinds.prepare',a))
    def test_execute_outside_approval_blocked(self):
        p=self.proposal();self.fails('LOCAL_APPROVAL_REQUIRED',lambda:self.host._execute(self.host._read_request('prepare')))
    def test_long_id_still_works(self):
        p=self.proposal('a'*100);r=self.host.approve_local(p['request_id'],p['request_sha256']);self.assertEqual(r['status'],'COMPLETED')
    def test_undo_requires_separate_apply(self):
        self.approved_apply();p=self.host.request_status('prepare')['result']['result'];u=self.s.exact_rollback_preview(p['plan_id'])
        req=self.host.propose('keybinds.prepare_rollback',{'plan_id':p['plan_id'],'preview_sha256':u['preview_sha256'],'selective':False},request_id='undo')
        result=self.host.approve_local('undo',req['request_sha256']);self.assertEqual(result['status'],'COMPLETED');self.assertNotEqual(self.path.read_bytes(),BASE)
        inverse=result['result'];a=self.host.propose('keybinds.apply',{'plan_id':inverse['plan_id'],'plan_sha256':inverse['plan_sha256']},request_id='undo-apply')
        self.host.approve_local('undo-apply',a['request_sha256']);self.assertEqual(self.path.read_bytes(),BASE)
    def test_cancel_goes_through_host(self):
        p=self.proposal();self.host.cancel.set();r=self.host.approve_local('prepare',p['request_sha256']);self.assertEqual(r['status'],'STOPPED_RECONCILE');self.assertEqual(self.path.read_bytes(),BASE)
    def test_original_mod_planning_preserved(self):
        self.assertTrue(self.host.preview_plan());self.assertIn('mods.create_plan',capabilities()['requestable'])

class Protocol(Integration):
    # Do not inherit Integration test cases twice in the reported suite.
    def ready(self,requests=True):
        e=Endpoint(self.host,requests);e.handle({'jsonrpc':'2.0','id':1,'method':'initialize','params':{}})
        self.assertIsNone(e.handle({'jsonrpc':'2.0','method':'notifications/initialized'}));return e
    def call(self,e,name,args=None,ident=2):return e.handle({'jsonrpc':'2.0','id':ident,'method':'tools/call','params':{'name':name,'arguments':args or {}}})
    def test_preinit_refused(self):self.assertIn('error',self.call(Endpoint(self.host),'keybinds_context'))
    def test_tools_retain_originals(self):
        e=self.ready();t=e.handle({'jsonrpc':'2.0','id':2,'method':'tools/list'})['result']['tools'];names={x['name'] for x in t}
        self.assertTrue({x['name'] for x in original_tools(True)}<=names);self.assertIn('keybinds_context',names);self.assertEqual(len(names),len(t))
    def test_readonly_no_proposals(self):self.assertTrue(self.call(self.ready(False),'keybinds_propose',{})['result']['isError'])
    def test_no_approve_tool(self):self.assertTrue(self.call(self.ready(),'keybinds_approve',{})['result']['isError'])
    def test_no_register_tool(self):self.assertTrue(self.call(self.ready(),'keybinds_register',{})['result']['isError'])
    def test_context_path_free(self):
        v=self.call(self.ready(),'keybinds_context')['result']['structuredContent'];self.assertNotIn(str(self.root),json.dumps(v))
    def test_incremental_context(self):
        e=self.ready();v=self.call(e,'keybinds_context')['result']['structuredContent'];v2=self.call(e,'keybinds_context',{'known_revision':v['revision']})['result']['structuredContent'];self.assertTrue(v2['unchanged'])
    def test_preview_no_writes(self):
        v=self.call(self.ready(),'keybinds_preview',{'items':self.edits()})['result'];self.assertFalse(v['isError']);self.assertFalse(self.s.plans.exists())
    def test_mcp_proposal_not_apply(self):
        v=self.call(self.ready(),'keybinds_propose',{'operation':'keybinds.prepare','arguments':self.args(),'request_id':'ai'})['result'];self.assertFalse(v['isError']);self.assertEqual(self.path.read_bytes(),BASE)
    def test_notification_does_not_execute(self):
        e=self.ready();self.assertIsNone(e.handle({'jsonrpc':'2.0','method':'tools/call','params':{'name':'keybinds_propose','arguments':{'operation':'keybinds.prepare','arguments':self.args(),'request_id':'no-id'}}}));self.assertFalse(self.host.requests.exists())
    def test_injection_operation_refused(self):self.assertTrue(self.call(self.ready(),'keybinds_propose',{'operation':'shell.exec','arguments':{},'request_id':'no'})['result']['isError'])
    def test_path_field_refused(self):self.assertTrue(self.call(self.ready(),'keybinds_context',{'file':'/etc/passwd'})['result']['isError'])
    def test_stdio_real_framing(self):
        inp=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'keybinds_context','arguments':{}}}]
        out=io.BytesIO();stdio(self.host,False,io.BytesIO(b'\n'.join(json.dumps(x).encode() for x in inp)+b'\n'),out)
        rows=[json.loads(x) for x in out.getvalue().splitlines()];self.assertEqual([r['id'] for r in rows],[1,2]);self.assertIn('targets',rows[1]['result']['structuredContent'])
    def test_stdio_separate_process(self):
        lines=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{}},
          {'jsonrpc':'2.0','method':'notifications/initialized'},
          {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'keybinds_context','arguments':{}}},
          {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'keybinds_propose','arguments':{'operation':'keybinds.prepare','arguments':self.args(),'request_id':'from-client'}}}]
        env=dict(os.environ);env['PYTHONPATH']=str(Path(HOST)/'scripts')
        proc=subprocess.run([sys.executable,str(SCRIPTS/'GameToolKeybindAI.py'),'--data-dir',str(self.root/'data'),'--allow-requests','stdio'],input=b'\n'.join(json.dumps(x).encode() for x in lines)+b'\n',capture_output=True,env=env,timeout=10)
        self.assertEqual(proc.returncode,0,proc.stderr.decode());answers=[json.loads(x) for x in proc.stdout.splitlines()]
        self.assertEqual([a['id'] for a in answers],[1,2,3]);self.assertFalse(answers[-1]['result']['isError'])
        self.assertEqual(self.host.request_status('from-client')['status'],'AWAITING_LOCAL_APPROVAL');self.assertEqual(self.path.read_bytes(),BASE)
    def test_stdio_invalid_json(self):
        out=io.BytesIO();stdio(self.host,False,io.BytesIO(b'not json\n'),out);self.assertEqual(json.loads(out.getvalue())['error']['code'],-32700)
    def test_stdio_oversize_stops(self):
        out=io.BytesIO();stdio(self.host,False,io.BytesIO(b'x'*70000+b'\n'),out);self.assertEqual(out.getvalue(),b'')

if __name__=='__main__':
    suite=unittest.TestSuite()
    for cls in (Integration,Protocol):
        for name in cls.__dict__:
            if name.startswith('test_'):suite.addTest(cls(name))
    r=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not r.wasSuccessful())
