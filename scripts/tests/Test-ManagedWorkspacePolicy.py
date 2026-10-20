"""Directional configuration, local restrictions and boundary staging."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
import json
try:
    import jsonschema
except ImportError:
    jsonschema=None

SCRIPTS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(SCRIPTS))
from GameToolAIContracts import stable_revision
from game_system_control.contracts import ContextError
from game_system_control.policy import PolicyStore,evaluate,trigger_due,DEPTHS


def rule(ident="rule",source="a",destination="b",origin="destination",depth="summary"):
    return {"id":ident,"scope":{"account_id":"account","workspace_id":"workspace","project_id":"project","source_device":source,
            "destination_device":destination,"capability":"managed.write","content_class":"selected_results"},"origin":origin,"enabled":True,
            "controls":{"transfer":True,"adoption":False,"index":True,"context":True},"context_depth":depth,"trigger":{"kind":"manual"}}


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="managed-policy-");self.root=Path(self.tmp.name)
        self.store=PolicyStore.create(self.root/"policy");self.rule=rule();self.put(self.rule);self.request=deepcopy(self.rule["scope"])
    def tearDown(self):self.tmp.cleanup()
    def put(self,row):
        p=self.store.propose_rule(row);return self.store.accept(p,p["preview_sha256"])
    def check(self,request=None,**kwargs):return evaluate(self.store.snapshot()["body"],request or self.request,**kwargs)

    def test_each_scope_dimension_is_independently_required(self):
        for key in self.request:
            request={**self.request,key:"other"}
            with self.subTest(key=key):self.assertFalse(any(self.check(request)["controls"].values()))

    def test_reverse_direction_does_not_inherit_forward_policy(self):
        reverse={**self.request,"source_device":"b","destination_device":"a"}
        self.assertFalse(self.check(reverse)["controls"]["transfer"])
        self.put(rule("reverse","b","a",depth="none"));self.assertTrue(self.check(reverse)["controls"]["transfer"])
        self.assertEqual(self.check(reverse)["context_depth"],"none");self.assertEqual(self.check()["context_depth"],"summary")

    def test_transfer_adoption_index_context_are_separate(self):
        decision=self.check();self.assertTrue(decision["controls"]["transfer"]);self.assertFalse(decision["controls"]["adoption"])
        self.assertTrue(decision["controls"]["index"]);self.assertTrue(decision["controls"]["context"]);self.assertEqual(decision["effect"],"none")

    def test_central_proposal_needs_exact_destination_acknowledgement(self):
        central=rule("central",origin="central");central["controls"]["transfer"]=False;self.put(central)
        self.assertTrue(self.check()["controls"]["transfer"])
        p=self.store.acknowledge_central("central");self.store.accept(p,p["preview_sha256"])
        self.assertFalse(self.check()["controls"]["transfer"])
        central["context_depth"]="notice";self.put(central)
        self.assertTrue(self.check()["controls"]["transfer"]);self.assertIn("central",self.check()["ignored_unacknowledged_or_peer"])

    def test_peer_content_cannot_authorize_or_override_local_policy(self):
        peer=rule("peer",origin="peer");peer["controls"]={k:False for k in peer["controls"]};self.put(peer)
        self.assertTrue(self.check()["controls"]["transfer"]);self.assertIn("peer",self.check()["ignored_unacknowledged_or_peer"])

    def test_local_exclusions_and_unknown_classes_override_allows(self):
        body=self.store.snapshot()["body"];wide=rule("wide");wide["scope"]["content_class"]="*";body["rules"]=[wide]
        for cls in ("credentials","os_credential_store","live_runtime_databases","unknown"):
            with self.subTest(cls=cls):self.assertFalse(any(evaluate(body,{**self.request,"content_class":cls})["controls"].values()))
        body["hard_exclusions"].append("selected_results")
        self.assertEqual(evaluate(body,self.request)["reason"],"local_hard_exclusion")

    def test_restrictive_intersection_and_disabled_specific_rule(self):
        narrow=rule("restriction");narrow["enabled"]=False;self.put(narrow)
        self.assertFalse(any(self.check()["controls"].values()))

    def test_all_context_depths_keep_active_turn_staged(self):
        for depth in DEPTHS:
            self.rule["context_depth"]=depth;self.put(self.rule)
            result=self.check(active_turn=True,boundary="new_turn")
            self.assertEqual(result["context_depth"],depth);self.assertEqual(result["context_staged"],depth!="none")
            self.assertFalse(result["context_ready_at_reported_boundary"])

    def test_context_boundary_is_reported_not_injected(self):
        result=self.check(active_turn=False,boundary="new_turn")
        self.assertTrue(result["context_ready_at_reported_boundary"]);self.assertEqual(result["model_context_delivery"],"not_connected")

    def test_staged_references_need_boundary_and_unchanged_policy(self):
        base=stable_revision(self.store.snapshot()["body"])
        p=self.store.stage_context("packet","a"*64,"task_packet");self.store.accept(p,p["preview_sha256"])
        with self.assertRaises(ContextError):self.store.context_notice("packet",base,active_turn=True,boundary="new_turn")
        result=self.store.context_notice("packet",base,active_turn=False,boundary="on_request")
        self.assertEqual(result["state"],"NOTICE_READY_NO_DELIVERY")
        changed=rule();changed["context_depth"]="notice";self.put(changed)
        with self.assertRaises(ContextError):self.store.context_notice("packet",base,active_turn=False,boundary="new_turn")

    def test_manual_checkpoint_reconnect_and_timers_do_not_execute(self):
        for kind in ("manual","checkpoint","reconnect"):
            self.assertTrue(trigger_due({"kind":kind},kind,now=100));self.assertFalse(trigger_due({"kind":kind},"other",now=100))
        self.assertFalse(trigger_due({"kind":"interval","seconds":10},"interval",now=100,last_fire=95))
        self.assertTrue(trigger_due({"kind":"interval","seconds":10},"interval",now=100,last_fire=90))
        self.assertTrue(trigger_due({"kind":"debounced","seconds":5},"debounced",now=100,last_change=90,last_fire=80))
        self.assertFalse(trigger_due({"kind":"debounced","seconds":5},"debounced",now=100,last_change=90,last_fire=95))
        self.assertEqual(self.check()["effect"],"none")

    def test_clock_drift_refuses_timer_eligibility(self):
        for value in (float("nan"),float("inf"),101,True):
            with self.subTest(value=value),self.assertRaises(ContextError):trigger_due({"kind":"interval","seconds":10},"interval",now=100,last_fire=value)

    def test_cancelled_edit_and_wrong_preview_never_persist(self):
        before=self.store.snapshot();changed=rule();changed["enabled"]=False;p=self.store.propose_rule(changed)
        self.assertEqual(self.store.snapshot(),before)
        with self.assertRaises(ContextError):self.store.accept(p,"0"*64)
        self.assertEqual(self.store.snapshot(),before)

    def test_hidden_controls_do_not_change_enablement(self):
        before=self.check();body=self.store.snapshot()["body"];body["view"]={"hidden_controls":["transfer","context"]}
        p=self.store.state.propose(body);self.store.accept(p,p["preview_sha256"])
        self.assertEqual(self.check()["controls"],before["controls"])

    def test_granular_rollback_preserves_other_direction_and_generation(self):
        old=self.store.snapshot()["revision"];changed=rule();changed["enabled"]=False;self.put(changed)
        self.put(rule("reverse","b","a"));before=self.store.snapshot()
        p=self.store.rollback_rule("rule",old);after=self.store.accept(p,p["preview_sha256"])
        self.assertGreater(after["generation"],before["generation"])
        self.assertEqual(len(after["body"]["rules"]),2);self.assertTrue(self.check()["controls"]["transfer"])

    def test_policy_drift_prevents_accepting_old_preview(self):
        p=self.store.propose_rule(rule("new"));self.put(rule("other"))
        with self.assertRaises(ContextError):self.store.accept(p,p["preview_sha256"])

    @unittest.skipUnless(jsonschema,"Full schema acceptance runs in the isolated guest.")
    def test_published_contract_accepts_runtime_revision_and_inert_example(self):
        schema=json.loads((SCRIPTS.parent/"schemas/managed-workspace.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(self.store.snapshot(),schema)
        example=json.loads((SCRIPTS.parent/"examples/managed-workspace/policy-rule.example.json").read_text())
        jsonschema.validate(example,schema)
        self.assertFalse(example["enabled"])
        bad=deepcopy(self.store.snapshot());bad["schema_version"]=2
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(bad,schema)


if __name__=="__main__":unittest.main(verbosity=2)
