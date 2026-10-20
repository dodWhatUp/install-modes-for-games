"""Local session, role/scope, enrollment lifecycle and emergency stop."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(SCRIPTS))
from game_system_control.contracts import ContextError
from game_system_control.access import AccessStore,ROLES
from game_system_control.workspace_state import principal


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="managed-access-");self.root=Path(self.tmp.name)
        self.access=AccessStore.create(self.root/"access","admin","admin-device","project",now=100)
        self.actor={"account_id":"admin","device_id":"admin-device","project_id":"project","workspace_id":"workspace","capability":"enrollment.manage","generation":1}
    def tearDown(self):self.tmp.cleanup()
    def change(self,action,values):
        p=self.access.propose_change(self.actor,action,values,now=100)
        return self.access.accept(self.actor,p,p["preview_sha256"],now=100)
    def account(self,name,role):
        self.change("account",{"account_id":name})
        self.change("membership",{"account_id":name,"project_id":"project","roles":[role]})
        self.change("enroll",{"device_id":name+"-device","account_id":name})
        return {**self.actor,"account_id":name,"device_id":name+"-device","capability":"metadata.read","generation":1}

    def test_fresh_local_os_principal_is_observed_not_a_cloud_login(self):
        self.assertEqual(self.access.snapshot()["body"]["accounts"][0]["subject_hash"],principal())
        result=self.access.authorize({**self.actor,"capability":"metadata.read"},now=100)
        self.assertTrue(result["allowed"]);self.assertEqual(result["remote_authentication"],"not_connected")

    def test_role_matrix_does_not_conflate_operator_admin_and_contributor(self):
        for name,role in (("view","viewer"),("write","contributor"),("operate","operator"),("policy","policy_administrator")):
            request=self.account(name,role)
            for capability in ("metadata.read","policy.propose","enrollment.manage"):
                with self.subTest(role=role,capability=capability):
                    self.assertEqual(self.access.authorize({**request,"capability":capability},now=100)["allowed"],capability in ROLES[role])

    def test_membership_and_storage_permission_are_independent(self):
        request=self.account("writer","contributor");revision="a"*64
        self.change("pin_policy",{"policy_revision":revision});self.change("acknowledge",{"device_id":"writer-device","policy_revision":revision})
        request.update(capability="managed.write",policy_revision=revision,storage_id="disk",content_class="selected_results")
        self.assertEqual(self.access.authorize(request,now=100)["reason"],"storage_scope_denied")
        self.change("storage",{"account_id":"writer","project_id":"project","storage_id":"disk","read":["project_source"],"write":["selected_results"]})
        self.assertTrue(self.access.authorize(request,now=100)["allowed"])
        self.assertFalse(self.access.authorize({**request,"content_class":"project_source"},now=100)["allowed"])
        self.assertFalse(self.access.authorize({**request,"storage_id":"other"},now=100)["allowed"])

    def test_missing_account_workspace_project_and_device_do_not_inherit(self):
        for key in ("account_id","workspace_id","project_id","device_id"):
            request={**self.actor,key:"unknown","capability":"metadata.read"}
            self.assertFalse(self.access.authorize(request,now=100)["allowed"])

    def test_provider_login_cannot_be_claimed_by_an_imported_declaration(self):
        for action,values in (("account",{"account_id":"provider","provider":"openai"}),("enroll",{"device_id":"peer","provider":"imported_token"})):
            with self.subTest(action=action),self.assertRaises(ContextError):self.access.propose_change(self.actor,action,values,now=100)
        self.assertEqual(len(self.access.snapshot()["body"]["accounts"]),1)

    def test_central_proposal_still_needs_destination_scope_and_explicit_acceptance(self):
        request=self.account("policy","policy_administrator")
        self.assertTrue(self.access.authorize({**request,"capability":"policy.propose"},now=100)["allowed"])
        with self.assertRaises(ContextError):self.access.propose_change(self.actor,"membership",{"account_id":"admin","project_id":"another","roles":["operator"]},now=100)
        p=self.access.propose_change(self.actor,"enroll",{"device_id":"new"},now=100)
        self.assertNotIn("new",[d["id"] for d in self.access.snapshot()["body"]["devices"]])
        with self.assertRaises(ContextError):self.access.accept(self.actor,p,"0"*64,now=100)

    def test_revocation_blocks_old_writer_and_retirement_cannot_be_reused(self):
        request=self.account("reader","viewer");self.change("revoke",{"device_id":"reader-device"})
        self.assertFalse(self.access.authorize(request,now=100)["allowed"])
        self.change("retire",{"device_id":"reader-device"})
        with self.assertRaises(ContextError):self.change("enroll",{"device_id":"reader-device","account_id":"reader"})

    def test_expiry_and_backwards_clock_are_denied(self):
        request={**self.actor,"capability":"metadata.read"}
        self.assertEqual(self.access.authorize(request,now=3700)["reason"],"expired_or_clock_drift")
        self.assertEqual(self.access.authorize(request,now=99)["reason"],"expired_or_clock_drift")

    def test_renewal_fences_previous_generation_and_clears_ack(self):
        request=self.account("reader","viewer");self.change("renew",{"device_id":"reader-device","seconds":600})
        self.assertEqual(self.access.authorize(request,now=100)["reason"],"stale_writer_generation")
        self.assertTrue(self.access.authorize({**request,"generation":2},now=100)["allowed"])
        self.assertIsNone(next(d for d in self.access.snapshot()["body"]["devices"] if d["id"]=="reader-device")["policy_ack"])

    def test_offline_and_stale_devices_block_actions_but_keep_metadata_distinct(self):
        request=self.account("operator","operator")
        self.change("heartbeat",{"device_id":"operator-device","online":False})
        self.assertTrue(self.access.authorize(request,now=100)["allowed"])
        self.assertEqual(self.access.authorize({**request,"capability":"operation.propose"},now=100)["reason"],"offline_or_stale_device")
        self.assertEqual(self.access.authorize({**request,"capability":"operation.propose"},now=500)["reason"],"offline_or_stale_device")

    def test_new_policy_revision_invalidates_previous_acknowledgement(self):
        request=self.account("operator","operator");self.change("pin_policy",{"policy_revision":"a"*64})
        self.change("acknowledge",{"device_id":"operator-device","policy_revision":"a"*64})
        request.update(capability="operation.propose",policy_revision="a"*64)
        self.assertTrue(self.access.authorize(request,now=100)["allowed"])
        self.change("pin_policy",{"policy_revision":"b"*64})
        self.assertEqual(self.access.authorize(request,now=100)["reason"],"policy_ack_required")
        with self.assertRaises(ContextError):self.change("acknowledge",{"device_id":"operator-device","policy_revision":"a"*64})

    def test_stop_is_immediate_and_resume_requires_current_local_admin(self):
        request=self.account("reader","viewer");receipt=self.access.stop_local()
        self.assertEqual(self.access.authorize(request,now=100)["reason"],"local_stop")
        self.assertEqual(self.access.stop_local()["stop_sha256"],receipt["stop_sha256"])
        with self.assertRaises(ContextError):self.access.resume_local({**request,"capability":"enrollment.manage"},receipt["stop_sha256"],now=100)
        self.access.resume_local(self.actor,receipt["stop_sha256"],now=100)
        self.assertTrue(self.access.authorize(request,now=100)["allowed"])

    def test_stop_still_works_when_registry_is_corrupt(self):
        (self.access.state.root/"00000000.json").write_bytes(b"broken")
        self.access.stop_local()
        self.assertEqual(self.access.authorize(self.actor,now=100)["reason"],"local_stop")

    def test_registry_copied_to_another_os_principal_is_refused(self):
        with patch("game_system_control.workspace_state.principal",return_value="b"*64):
            with self.assertRaises(ContextError):self.access.snapshot()

    def test_revoked_or_stale_admin_cannot_apply_prepared_change(self):
        request=self.account("administrator","policy_administrator");request["capability"]="enrollment.manage"
        p=self.access.propose_change(request,"enroll",{"device_id":"prepared"},now=100)
        self.change("revoke",{"device_id":"administrator-device"})
        with self.assertRaises(ContextError):self.access.accept(request,p,p["preview_sha256"],now=100)

    def test_arbitrary_commands_and_unknown_roles_are_refused(self):
        with self.assertRaises(ContextError):self.access.propose_change(self.actor,"shell",{"command":"never runs"},now=100)
        with self.assertRaises(ContextError):self.access.propose_change(self.actor,"membership",{"account_id":"admin","project_id":"project","roles":["root"]},now=100)

    def test_existing_control_center_can_render_foundations_without_a_new_ui_engine(self):
        from game_system_control.vault import VaultRegistry
        from game_system_control.policy import PolicyStore
        from game_system_control.workspace_view import workspace_context
        from game_system_control.report import accessible_report
        VaultRegistry.create(self.root/"bindings")
        PolicyStore.create(self.root/"policy")
        context=workspace_context(self.root)
        report=accessible_report(context,self.root)
        self.assertEqual(len(context["nodes"]),3)
        self.assertIn("provider sign-in not connected",report)
        self.assertNotIn(principal(),report)
        self.access.stop_local()
        self.assertIn("Local stop active",accessible_report(workspace_context(self.root),self.root))

    def test_boolean_float_or_string_cannot_impersonate_integer_writer_generation(self):
        for value in (True,False,1.0,"1",None):
            request={**self.actor,"capability":"metadata.read","generation":value}
            with self.subTest(value=value):self.assertEqual(self.access.authorize(request,now=100)["reason"],"stale_writer_generation")


if __name__=="__main__":unittest.main(verbosity=2)
