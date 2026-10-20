"""Managed vault and local state contracts; only new synthetic directories."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from GameToolUserData import UserDataError
from GameToolJournal import JournalError
from game_mod_ops.safety import ModError
from game_system_control.contracts import ContextError
from game_system_control.workspace_state import LocalState
from game_system_control.vault import VaultRegistry, volume_identity

REFUSED = (ContextError, UserDataError, ModError, JournalError, OSError)


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="managed-vault-");self.root=Path(self.tmp.name)
        self.observe=lambda p:{"volume_id":"fixture-volume", "system_volume":False, "adapter":"synthetic"}
        self.registry=VaultRegistry.create(self.root/"bindings",self.observe)
        self.registry.enroll(self.root/"vault","workspace",self.registry.state.snapshot()["revision"])
        self.ident=self.registry.state.snapshot()["body"]["vaults"][0]["marker"]["vault_id"]
        self.source=self.root/"selected.txt";self.source.write_bytes("Selected source שלום\n".encode())
        self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()

    def tearDown(self): self.tmp.cleanup()

    def test_all_managed_classes_place_and_reopen_exact_bytes(self):
        for cls in ("project_source","selected_assets","selected_results","continuation_packet"):
            result=self.registry.place(self.ident,"project",cls,"שלום/record.txt",self.source,self.sha)
            reopened=VaultRegistry(self.root/"bindings",self.observe)
            self.assertEqual(reopened.route(self.ident,"project",cls,"שלום/record.txt").read_bytes(),self.source.read_bytes())
            self.assertEqual(result["sha256"],self.sha);self.assertFalse(result["originals_changed"])

    def test_system_volume_enrollment_refused_without_fallback(self):
        registry=VaultRegistry.create(self.root/"other-bindings",lambda p:{"volume_id":"system", "system_volume":True, "adapter":"synthetic"})
        with self.assertRaises(ContextError):registry.enroll(self.root/"no-vault","w",registry.state.snapshot()["revision"])
        self.assertFalse((self.root/"no-vault").exists())

    def test_absent_vault_does_not_create_any_fallback_output(self):
        (self.root/"vault").rename(self.root/"disconnected")
        with self.assertRaises(ContextError):self.registry.place(self.ident,"p","selected_results","result.txt",self.source,self.sha)
        self.assertFalse((self.root/"vault").exists())

    def test_renamed_mount_or_username_root_rebinds_same_directory(self):
        old=self.root/"vault";new=self.root/"new-user-mount";old.rename(new)
        self.registry.rebind(self.ident,new,self.registry.state.snapshot()["revision"])
        self.assertTrue(self.registry.inspect(self.ident)["available"])
        self.assertIn(new,self.registry.route(self.ident,"p","selected_results","result.txt").parents)

    def test_other_volume_and_clone_directory_refused(self):
        clone=self.root/"clone";shutil.copytree(self.root/"vault",clone)
        with self.assertRaises(ContextError):self.registry.rebind(self.ident,clone,self.registry.state.snapshot()["revision"])
        changed=VaultRegistry(self.root/"bindings",lambda p:{"volume_id":"replacement", "system_volume":False, "adapter":"synthetic"})
        with self.assertRaises(ContextError):changed.inspect(self.ident)

    def test_attached_clone_collision_is_visible_and_duplicate_selection_is_not(self):
        clone=self.root/"clone";shutil.copytree(self.root/"vault",clone)
        self.assertEqual(self.registry.selected_collisions([self.root/"vault",clone])["state"],"blocked")
        self.assertEqual(self.registry.selected_collisions([self.root/"vault",self.root/"vault"])["state"],"declarations_consistent")

    def test_native_and_credential_classes_never_route(self):
        for cls in ("credentials","browser_profiles","os_credential_store","local_permissions","live_runtime_databases","schedules","action_approvals","unknown"):
            with self.subTest(cls=cls),self.assertRaises(ContextError):self.registry.route(self.ident,"p",cls,"x")

    def test_unsafe_portable_paths_and_unicode_aliases_refused(self):
        for relative in ("../out","a/../x","/abs","C:/data","a\\b","CON.txt","trailing. ","a//b","e\u0301.txt",".env.local","sessions/chat.jsonl","data.db"):
            with self.subTest(path=relative),self.assertRaises(REFUSED):self.registry.route(self.ident,"p","project_source",relative)

    def test_case_collision_and_existing_output_preserve_original(self):
        self.registry.place(self.ident,"Project","selected_results","Result.txt",self.source,self.sha)
        for project,name in (("Project","Result.txt"),("Project","result.txt"),("project","Other.txt")):
            with self.subTest(project=project,name=name),self.assertRaises(REFUSED):self.registry.place(self.ident,project,"selected_results",name,self.source,self.sha)
        self.assertEqual(self.registry.route(self.ident,"Project","selected_results","Result.txt").read_bytes(),self.source.read_bytes())

    def test_symlink_escape_is_refused(self):
        target=self.root/"outside";target.mkdir()
        link=self.root/"vault/projects/escape"
        try:link.symlink_to(target,target_is_directory=True)
        except OSError:self.skipTest("Windows symlink privilege unavailable; covered in isolated Linux fixtures.")
        with self.assertRaises(REFUSED):self.registry.route(self.ident,"escape","selected_results","x")
        self.assertFalse(list(target.iterdir()))

    def test_changed_source_or_marker_cannot_be_placed(self):
        self.source.write_bytes(b"changed")
        with self.assertRaises(ContextError):self.registry.place(self.ident,"p","selected_results","x",self.source,self.sha)
        marker=self.root/"vault/vault.json";marker.write_text("{}")
        with self.assertRaises(ContextError):self.registry.inspect(self.ident)

    def test_native_source_tree_is_excluded_before_read(self):
        p=self.root/".codex/sessions";p.mkdir(parents=True);source=p/"chat.jsonl";source.write_bytes(b"private")
        with self.assertRaises(ContextError):self.registry.place(self.ident,"p","continuation_packet","packet.txt",source,hashlib.sha256(b"private").hexdigest())

    def test_state_edit_is_preview_only_until_exact_acceptance(self):
        store=self.registry.state;before=store.snapshot();proposal=store.propose({**before["body"],"future":{"inert":True}})
        self.assertEqual(store.snapshot(),before)
        with self.assertRaises(ContextError):store.commit(proposal,"0"*64)
        result=store.commit(proposal,proposal["preview_sha256"])
        self.assertEqual(result["body"]["future"],{"inert":True});self.assertGreater(result["generation"],before["generation"])

    def test_revision_drift_prevents_stale_writer(self):
        store=self.registry.state;a=store.propose({**store.snapshot()["body"],"a":True});b=store.propose({**store.snapshot()["body"],"b":True})
        store.commit(a,a["preview_sha256"])
        with self.assertRaises(ContextError):store.commit(b,b["preview_sha256"])
        self.assertNotIn("b",store.snapshot()["body"])

    def test_interrupted_lock_is_not_automatically_removed(self):
        lock=self.registry.state.root/".workspace-state.lock";lock.write_text("uncertain")
        proposal=self.registry.state.propose(self.registry.state.snapshot()["body"])
        with self.assertRaises(ModError):self.registry.state.commit(proposal,proposal["preview_sha256"])
        self.assertEqual(lock.read_text(),"uncertain")

    def test_incomplete_audit_blocks_reopened_state(self):
        audit=self.registry.state.root/"audit/00000001.jsonl";audit.write_bytes(audit.read_bytes().splitlines(keepends=True)[0])
        with self.assertRaises(ContextError):self.registry.state.snapshot()

    def test_oversized_state_refused_before_creation(self):
        with self.assertRaises(ContextError):LocalState.create(self.root/"large","fixture",{"x":"x"*131072})
        self.assertFalse((self.root/"large").exists())

    def test_no_codex_or_onedrive_local_state(self):
        for name in (".codex","OneDrive"):
            parent=self.root/name;parent.mkdir()
            with self.assertRaises(ContextError):LocalState.create(parent/"state","fixture",{})

    def test_cli_requires_explicit_root_and_state(self):
        p=subprocess.run([sys.executable,"-B",str(SCRIPTS/"GameToolManagedWorkspace.py"),"vault-create"],capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertIn("Select --state",p.stderr)

    def test_publication_guard_can_stop_copy_after_source_review(self):
        def stop():raise ContextError("local stop")
        with self.assertRaises(ContextError):self.registry.place(self.ident,"p","selected_results","blocked.txt",self.source,self.sha,before_publish=stop)
        self.assertFalse(self.registry.route(self.ident,"p","selected_results","blocked.txt").exists())

    def test_separate_processes_cannot_publish_the_same_generation_twice(self):
        store=self.registry.state;proposal=store.propose({**store.snapshot()["body"],"race":"single winner"})
        path=self.root/"proposal.json";path.write_text(json.dumps(proposal))
        code="import sys,json;sys.path.insert(0,sys.argv[1]);from game_system_control.workspace_state import LocalState;s=LocalState(sys.argv[2],'workspace-vault-bindings');p=json.load(open(sys.argv[3]));s.commit(p,p['preview_sha256'])"
        command=[sys.executable,"-B","-c",code,str(SCRIPTS),str(store.root),str(path)]
        a=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE);b=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        a.communicate(timeout=30);b.communicate(timeout=30)
        self.assertEqual(sum(p.returncode==0 for p in (a,b)),1)
        self.assertEqual(store.snapshot()["body"]["race"],"single winner")

    def test_new_local_binding_store_can_attach_existing_vault_without_rewriting_it(self):
        before={str(p.relative_to(self.root/"vault")):p.read_bytes() for p in (self.root/"vault").rglob("*") if p.is_file()}
        other=VaultRegistry.create(self.root/"destination-bindings",self.observe)
        other.attach(self.root/"vault",other.state.snapshot()["revision"])
        self.assertTrue(other.inspect(self.ident)["available"])
        self.assertEqual(before,{str(p.relative_to(self.root/"vault")):p.read_bytes() for p in (self.root/"vault").rglob("*") if p.is_file()})
        with self.assertRaises(ContextError):other.attach(self.root/"vault",other.state.snapshot()["revision"])

    def test_edit_preparation_cannot_silently_rebase_an_old_body(self):
        state=self.registry.state;old=state.snapshot();p=state.propose({**old["body"],"concurrent":"preserve"})
        state.commit(p,p["preview_sha256"])
        with self.assertRaises(ContextError):state.propose(old["body"],old["revision"])
        self.assertEqual(state.snapshot()["body"]["concurrent"],"preserve")


if __name__=="__main__":unittest.main(verbosity=2)
