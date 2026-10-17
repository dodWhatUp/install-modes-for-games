"""Offline integration contracts. No remote tools, provider I/O, games or screenshots."""
from __future__ import annotations
import copy, importlib.util, io, json, sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S));sys.dont_write_bytecode=True
import GameToolAutomation as a
import GameToolAI as transport
from game_mod_ops.safety import ModError,object_hash
from GameToolJournal import Journal

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
ovtest=load('automation_overlay_fixture',S/'tests/Test-GameToolOverlay.py')
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.data=self.root/'private'
        self.service=a.AutomationService(self.data)
    def proposal(self,ident='fixture'):
        return self.service.propose('mods.create_plan',{'selected':['unity-mod-manager'],'mode':'real-time'},request_id=ident)
    def approve(self,row):return self.service.approve_local(row['request_id'],row['request_sha256'])
    def code(self,code,func):
        with self.assertRaises(ModError) as c:func()
        self.assertEqual(c.exception.code,code)
    def test_constructor_no_write(self):self.assertFalse(self.data.exists())
    def test_context_no_write(self):self.service.context();self.assertFalse(self.data.exists())
    def test_preview_no_write(self):self.service.preview_plan();self.assertFalse(self.data.exists())
    def test_turnbased_preset_excludes_tactics(self):self.assertNotIn('kingmaker-tactics',[i['id'] for i in self.service.preview_plan(mode='turn-based')['items']])
    def test_no_install_capability(self):self.assertFalse(any('install' in n for n in a.capabilities()['requestable']))
    def test_proposal_not_execution(self):
        row=self.proposal();self.assertEqual(row['status'],'AWAITING_LOCAL_APPROVAL');self.assertFalse(self.service.mods_root.exists())
    def test_unknown_operation_refused(self):self.code('CAPABILITY_UNAVAILABLE',lambda:self.service.propose('shell',{'command':'calc'}))
    def test_authorization_argument_rejected(self):self.code('INVALID_ARGUMENTS',lambda:self.service.propose('mods.create_plan',{'selected':[],'mode':'real-time','approved':True}))
    def test_idempotent_proposal(self):
        row=self.proposal();self.assertEqual(row,self.proposal());self.assertEqual(len(self.service.list_requests()),1)
    def test_request_id_conflict(self):
        self.proposal();self.code('REQUEST_ID_CONFLICT',lambda:self.service.propose('mods.create_plan',{'selected':['buff-bot'],'mode':'real-time'},request_id='fixture'))
    def test_approval_creates_one_job(self):
        row=self.proposal();receipt=self.approve(row);self.assertEqual(receipt['status'],'COMPLETED');self.assertEqual(len(list((self.service.mods_root/'jobs').iterdir())),1)
        self.assertEqual(self.service.request_status('fixture')['status'],'COMPLETED')
    def test_cannot_reapprove_completed(self):
        row=self.proposal();self.approve(row);self.code('RECONCILIATION_REQUIRED',lambda:self.approve(row))
    def test_rejected_not_replayable(self):
        row=self.proposal();self.assertEqual(self.service.reject_local('fixture',row['request_sha256'])['status'],'REJECTED')
        self.code('RECONCILIATION_REQUIRED',lambda:self.approve(row));self.assertFalse(self.service.mods_root.exists())
    def test_expiry(self):
        row=self.proposal()
        with patch.object(a.time,'time',return_value=row['expires_unix']+1):
            self.assertEqual(self.service.request_status('fixture')['status'],'EXPIRED');self.code('EXPIRED',lambda:self.approve(row))
    def test_wrong_approval_hash(self):self.code('REQUEST_CHANGED',lambda:self.service.approve_local('fixture','0'*64)) if self.proposal() else None
    def test_request_tamper(self):
        self.proposal();p=self.service.requests/'fixture/request.json';r=json.loads(p.read_text());r['arguments']['selected']=['buff-bot'];p.write_text(json.dumps(r))
        self.code('REQUEST_CORRUPT',lambda:self.service.request_status('fixture'))
    def test_receipt_tamper_detected(self):
        row=self.proposal();self.approve(row);p=self.service.requests/'fixture/result.json';r=json.loads(p.read_text());r['status']='FAKE_PASS';p.write_text(json.dumps(r))
        self.code('RECEIPT_CORRUPT',lambda:self.service.request_status('fixture'))
    def test_journal_tamper_detected(self):
        row=self.proposal();self.approve(row);p=self.service.requests/'fixture/audit.jsonl';p.write_bytes(p.read_bytes()+b'broken')
        self.code('RECEIPT_CORRUPT',lambda:self.service.request_status('fixture'))
    def test_uncertain_interruption_never_replayed(self):
        row=self.proposal()
        with Journal.create(self.service.requests/'fixture/audit.jsonl',{'fixture':'interrupted'}) as j:j.append('operation_intent',{})
        self.assertEqual(self.service.request_status('fixture')['status'],'IN_FLIGHT_OR_INTERRUPTED_RECONCILE')
        self.code('RECONCILIATION_REQUIRED',lambda:self.approve(row))
    def test_failure_saved_not_automatic_retry(self):
        row=self.proposal()
        with patch.object(self.service,'_execute',side_effect=ModError('DENIED','fixture')) as fn:
            self.assertEqual(self.approve(row)['status'],'STOPPED_RECONCILE');self.code('RECONCILIATION_REQUIRED',lambda:self.approve(row));self.assertEqual(fn.call_count,1)
    def test_unknown_effects_saved_not_replayed(self):
        row=self.proposal()
        with patch.object(self.service,'_execute',side_effect=RuntimeError('private secret path')):
            r=self.approve(row);self.assertEqual(r['status'],'UNKNOWN_EFFECTS_RECONCILE');self.assertNotIn('secret',json.dumps(r))
    def test_stop_before_dispatch_is_not_cleared(self):
        row=self.proposal();self.service.stop();r=self.approve(row)
        self.assertEqual(r['status'],'STOPPED_RECONCILE');self.assertEqual(r['result']['reason'],'CANCELLED')
        self.assertFalse(self.service.mods_root.exists())
    def test_peer_busy_stops_before_journal(self):
        row=self.proposal();self.code('ACTION_BUSY',lambda:self.service.approve_local('fixture',row['request_sha256'],busy_guard=lambda:True))
        self.assertFalse((self.service.requests/'fixture/audit.jsonl').exists())
    def test_second_controller_cannot_replay(self):
        row=self.proposal();self.approve(row);other=a.AutomationService(self.data)
        self.code('RECONCILIATION_REQUIRED',lambda:other.approve_local('fixture',row['request_sha256']))
    def test_job_drift_refuses_request(self):
        receipt=self.approve(self.proposal());v=receipt['result'];job=self.service._job(v['job_id'])
        row=self.service.propose('mods.download',{'job_id':v['job_id'],'job_revision':v['job_revision']},request_id='download')
        job.event('unity-mod-manager','WAITING_MANUAL_DOWNLOAD',reason='fixture change')
        self.code('CONCURRENT_CHANGE',lambda:self.approve(row))
    def test_waiting_download_is_not_success(self):
        v=self.approve(self.proposal())['result'];row=self.service.propose('mods.download',{'job_id':v['job_id'],'job_revision':v['job_revision']})
        with patch.object(a,'acquire',return_value={'fixture':'no transfer'}):
            receipt=self.approve(row);self.assertEqual(receipt['status'],'RETURNED_WITH_PENDING_ITEMS')
    def test_context_delta(self):
        first=self.service.context();second=self.service.context(first['revisions']);self.assertEqual(second['sections'],{});self.assertEqual(len(second['unchanged']),5)
        self.approve(self.proposal());third=self.service.context(first['revisions']);self.assertEqual(set(third['sections']),{'jobs'})
    def test_bad_delta_arguments(self):
        for value in ([],False,{'jobs':'not a hash'}):self.code('INVALID_ARGUMENTS',lambda:self.service.context(value))
    def test_paths_and_tokens_absent(self):
        self.approve(self.proposal());raw=json.dumps(self.service.context());self.assertNotIn(str(self.root),raw);self.assertNotIn('download_url',raw)
    def test_recipe_change_rejected(self):
        path=self.root/'recipe.json';path.write_bytes(a.RECIPE.read_bytes());self.service=a.AutomationService(self.data,path);row=self.proposal();r=json.loads(path.read_text());r['name']='New recipe';path.write_text(json.dumps(r))
        self.code('SOURCE_CHANGED',lambda:self.approve(row))
    def test_record_limit_prevents_extra(self):
        self.proposal()
        with patch.object(a,'MAX_REQUESTS',1):self.code('RECORD_LIMIT',lambda:self.proposal('second'));self.assertEqual(self.proposal()['request_id'],'fixture')
    def test_id_traversal_refused(self):self.code('INVALID_ID',lambda:self.proposal('../outside'))
    def test_symlink_data_root_rejected(self):
        target=self.root/'target';target.mkdir();link=self.root/'link';link.symlink_to(target,target_is_directory=True)
        self.code('LINK_BLOCKED',lambda:a.AutomationService(link))
    def overlay(self):
        _m,src=ovtest.fixture(self.root);store=a.Store(self.data);store.import_manifest(src,'absent');return store
    def test_overlay_select_preserves_inputs_assets_display(self):
        store=self.overlay();before,rev=store.load();row=self.service.propose('overlays.select',{'game_id':'game','group_id':'group-b','store_revision':rev})
        receipt=self.approve(row);after,_=store.load();self.assertEqual(receipt['status'],'COMPLETED');self.assertEqual(after['manifest'],before['manifest']);self.assertEqual(after['preferences']['display'],before['preferences']['display']);self.assertEqual(after['preferences']['overrides']['game'],'group-b')
    def test_stale_overlay_refused(self):
        store=self.overlay();_,rev=store.load();row=self.service.propose('overlays.select',{'game_id':'game','group_id':'group-b','store_revision':rev})
        store.update('select',{'game_id':'game','group_id':'group-a'},rev);self.code('CONCURRENT_CHANGE',lambda:self.approve(row))
    def test_return_auto(self):
        store=self.overlay();_,rev=store.load();store.update('select',{'game_id':'game','group_id':'group-b'},rev);_,rev=store.load()
        row=self.service.propose('overlays.auto',{'game_id':'game','group_id':'group-b','store_revision':rev});self.approve(row);self.assertNotIn('game',store.load()[0]['preferences']['overrides'])
    def test_report_sharing_no_raw_or_paths(self):
        p=self.root/'private-report.json';p.write_text(json.dumps({'RootType':'worldBenchmarkSummary','Data':{'gameVersion':'2.31','benchmarkName':'SECRET_FIXTURE','averageFps':60,'minFps':40,'maxFps':90,'time':60,'frameNumber':3600}}))
        self.service.share_report_local(p);raw=json.dumps(self.service.context());self.assertNotIn('SECRET_FIXTURE',raw);self.assertNotIn(str(p),raw);self.assertIn('60',raw)
    def test_shared_tool_status_projection(self):
        snapshot={'observed_utc':'2026-10-13T00:00:00Z','tools':[
            {'id':'afterburner','path':'C:\\Users\\private','name':'SECRET_NAME','installed':True,'running':False,'version':'4.6.6'},
            {'id':'custom-secret-id','name':'PRIVATE_CUSTOM','installed':True,'running':True}]}
        self.service.share_tool_status_local(snapshot);raw=json.dumps(self.service.context())
        self.assertNotIn('SECRET_NAME',raw);self.assertNotIn('PRIVATE_CUSTOM',raw);self.assertNotIn('Users',raw)
        self.assertIn('afterburner',raw);self.assertIn('2026-10-13T00:00:00Z',raw)
    def test_share_tool_status_requires_existing_read(self):
        self.code('STATUS_UNAVAILABLE',lambda:self.service.share_tool_status_local({}))
    def test_no_automatic_tool_status_sharing(self):
        self.assertEqual(self.service.context()['sections']['tool_status'],[])
    def test_report_not_shared_on_construct(self):self.assertEqual(self.service.context()['sections']['reports'],[])
    def test_report_share_is_idempotent(self):
        # Adapter stub is limited to data-shaping checks; separate test exercises actual parser.
        r={'adapter':'fixture','provider':'Fixture','provider_version':'SECRET /private','private_source':{'sha256':'a'*64},'coverage':{},'metrics':[{'id':'fps','provider_version':'SECRET','value':60,'unit':'FPS'}]}
        with patch.object(a,'inspect_report',return_value=r):
            self.service.share_report_local(self.root/'notread');self.service.share_report_local(self.root/'notread')
        rows=self.service.context()['sections']['reports'];self.assertEqual(len(rows),1);self.assertNotIn('SECRET',json.dumps(rows))

class ProtocolTests(Tests):
    # Inherits fixture helpers; protocol-only tests collected separately below.
    def endpoint(self,allow=False):
        e=transport.Endpoint(self.service,allow);return e
    def ready(self,e):
        e.handle({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':transport.PROTOCOL,'capabilities':{},'clientInfo':{'name':'fixture','version':'1'}}})
        e.handle({'jsonrpc':'2.0','method':'notifications/initialized'})
    def test_protocol_lifecycle(self):
        e=self.endpoint();self.assertIn('error',e.handle({'jsonrpc':'2.0','id':1,'method':'tools/list'}));self.ready(e);r=e.handle({'jsonrpc':'2.0','id':2,'method':'tools/list'});self.assertEqual(len(r['result']['tools']),4)
    def test_no_approval_tool_even_in_proposal_mode(self):self.assertFalse(any('approv' in t['name'] for t in transport.tools(True)));self.assertEqual(len(transport.tools(True)),5)
    def test_proposals_disabled_in_readonly(self):
        e=self.endpoint();self.ready(e);r=e.handle({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'hub_propose','arguments':{}}});self.assertIn('error',r);self.assertFalse(self.data.exists())
    def test_proposal_protocol_not_execution(self):
        e=self.endpoint(True);self.ready(e);r=e.handle({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'hub_propose','arguments':{'operation':'mods.create_plan','arguments':{'mode':'real-time','selected':['unity-mod-manager']},'request_id':'mcp-fixture'}}})
        self.assertFalse(r['result']['isError']);self.assertEqual(r['result']['structuredContent']['status'],'AWAITING_LOCAL_APPROVAL');self.assertFalse(self.service.mods_root.exists())
    def test_structured_and_text_match(self):
        e=self.endpoint();self.ready(e);r=e.handle({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'hub_context','arguments':{}}})['result'];self.assertEqual(json.loads(r['content'][0]['text']),r['structuredContent'])
    def test_unknown_args_error_no_write(self):
        e=self.endpoint(True);self.ready(e);r=e.handle({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'mods_preview_plan','arguments':{'command':'run'}}});self.assertTrue(r['result']['isError']);self.assertFalse(self.data.exists())
    def test_stdio_line_output_and_no_preamble(self):
        messages=[{'jsonrpc':'2.0','id':1,'method':'initialize'},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list'}];out=io.BytesIO()
        transport.stdio(self.service,input_stream=io.BytesIO(b'\n'.join(json.dumps(m).encode() for m in messages)+b'\n'),output_stream=out)
        rows=out.getvalue().splitlines();self.assertEqual(len(rows),2);self.assertTrue(all(json.loads(r)['jsonrpc']=='2.0' for r in rows))
    def test_stdio_oversize_halts_without_side_effect(self):
        out=io.BytesIO();transport.stdio(self.service,input_stream=io.BytesIO(b'x'*65537),output_stream=out);self.assertEqual(out.getvalue(),b'');self.assertFalse(self.data.exists())
    def test_duplicate_json_keys_rejected(self):
        out=io.BytesIO();transport.stdio(self.service,input_stream=io.BytesIO(b'{"jsonrpc":"2.0","id":1,"method":"ping","id":2}\n'),output_stream=out);self.assertEqual(json.loads(out.getvalue())['error']['code'],-32700)
    def test_tool_has_no_network_or_install_arguments(self):
        names={t['name'] for t in transport.tools(True)};self.assertNotIn('execute',names);self.assertNotIn('download',names)

if __name__=='__main__':
    suite=unittest.TestLoader().loadTestsFromTestCase(Tests)
    # Avoid double-counting inherited fixtures as independent new tests.
    suite.addTests(ProtocolTests(n) for n in ProtocolTests.__dict__ if n.startswith('test_'))
    result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not result.wasSuccessful())
