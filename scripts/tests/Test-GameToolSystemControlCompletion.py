"""Remaining P0 acceptance: selected guidance, deferred bodies, accessible reports."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from game_system_control.contracts import ContextError
from game_system_control.inventory import load_context, check_sources, environment_context
from game_system_control.explorer import build_view
from game_system_control.overview import fetch_detail
from game_system_control.preflight import check_request
from game_system_control.report import accessible_report


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="control-completion-")
        self.root = Path(self.tmp.name)
        for name in ("context.example.json", "instructions.example.md", "detail.example.txt"):
            (self.root/name).write_bytes((SCRIPTS.parent/"examples/system-control"/name).read_bytes())
        self.doc = load_context(self.root/"context.example.json")

    def tearDown(self):
        self.tmp.cleanup()

    def resource(self, raw, kind="attachment", name="attachment.bin"):
        (self.root/name).write_bytes(raw)
        source = {"id":"payload", "owner":"selected source export", "locator":name, "binding":"selected_project",
                  "sha256":hashlib.sha256(raw).hexdigest(), "availability":"available"}
        self.doc["sources"].append(source)
        self.doc["resources"].append({"id":"payload-ref", "source_id":"payload", "relative":name, "access":"local_selected", "content_type":kind})
        return source

    def projection(self, messages=None):
        return json.dumps({"schema_version":1,"kind":"GameToolsConversationProjection","coverage":"visible_messages",
                           "messages":messages if messages is not None else [{"role":"user","text":"Original request שלום"},{"role":"assistant","text":"Result"}]}).encode()

    def test_refresh_excludes_full_content_even_when_aliased_by_a_node(self):
        self.resource(b"private body")
        self.doc["nodes"].append({"id":"alias","source_id":"payload","kind":"component","label":"Metadata only",
                                 "scopes":["*"],"layer":"project","observation":"declared","depends_on":[]})
        from game_system_control.inventory import selected_text
        reads = []
        def tracked(root, relative, expected=None):
            reads.append(relative); return selected_text(root, relative, expected)
        with patch("game_system_control.explorer.selected_text", side_effect=tracked), patch("game_system_control.inventory.selected_text", side_effect=tracked):
            view=build_view(self.doc,self.root);check_sources(self.doc,self.root);accessible_report(self.doc,self.root)
        self.assertNotIn("attachment.bin",reads)
        self.assertNotIn("detail.example.txt",reads)
        self.assertFalse(next(n for n in view["all_nodes"] if n["id"]=="alias")["fresh"])

    def test_metadata_only_refresh_does_not_claim_payload_verification(self):
        s=self.resource(b"original");(self.root/"attachment.bin").unlink()
        view=build_view(self.doc,self.root)
        row=next(s for s in view["sources"] if s["id"]=="payload")
        self.assertEqual(row["verification"],"deferred_until_authorized_request")
        with self.assertRaises(ContextError): fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)

    def test_binary_read_requires_both_request_and_permission(self):
        self.resource(b"\x00\xff\x80exact bytes")
        with patch("game_system_control.overview.selected_bytes") as reader:
            for request,permission in ((False,False),(True,False),(False,True)):
                with self.assertRaises(ContextError): fetch_detail(self.doc,"payload-ref",self.root,requested=request,authorized=permission)
            reader.assert_not_called()
        value=fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)
        self.assertEqual(value["data"],b"\x00\xff\x80exact bytes")
        self.assertEqual(value["effect"],"read_only")

    def test_full_conversation_preserves_text_and_states_coverage(self):
        self.resource(self.projection(),"conversation","chat.json")
        value=fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)
        self.assertIn("Original request שלום",value["content"])
        self.assertEqual(value["coverage"],"visible_messages")
        self.assertEqual(value["native_chat_identity"],"not_imported")
        self.assertEqual(len(value["conversation"]["messages"]),2)

    def test_large_conversation_uses_its_own_bound(self):
        raw=self.projection([{"role":"user","text":"x"*100000},{"role":"assistant","text":"y"*100000}])
        self.resource(raw,"conversation","chat.json")
        value=fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)
        self.assertEqual(value["bytes"],len(raw))
        self.assertEqual(len(value["conversation"]["messages"][1]["text"]),100000)

    def test_malformed_native_and_duplicate_key_chat_refused(self):
        self.resource(b"{}","conversation","chat.json")
        for raw in (b'{"kind":"native_session"}',b'{"kind":"x","kind":"y"}',self.projection([{"role":"unknown","text":42}])):
            (self.root/"chat.json").write_bytes(raw);self.doc["sources"][-1]["sha256"]=hashlib.sha256(raw).hexdigest()
            with self.assertRaises(ContextError): fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)

    def test_full_content_changed_oversized_and_route_mismatch_refused(self):
        s=self.resource(b"original")
        (self.root/"attachment.bin").write_bytes(b"changed")
        with self.assertRaises(ContextError): fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)
        (self.root/"attachment.bin").write_bytes(b"x"*(16*1024*1024+1))
        s["sha256"]=hashlib.sha256((self.root/"attachment.bin").read_bytes()).hexdigest()
        with self.assertRaises(ContextError): fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)
        self.doc["resources"][-1]["relative"]="other.bin"
        with self.assertRaises(ContextError): fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)

    def test_context_cannot_bind_its_own_absolute_root(self):
        s=self.resource(b"private");s["binding"]="unselected";s["root"]=str(self.root)
        with self.assertRaises(ContextError): fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)
        self.assertEqual(fetch_detail(self.doc,"payload-ref",{"unselected":self.root},requested=True,authorized=True)["data"],b"private")

    def test_native_credential_sources_stay_excluded_for_binary_reads(self):
        self.resource(b"token","attachment","auth.json")
        with self.assertRaises(ContextError): fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)

    def test_inventory_global_project_child_skill_tools_automations(self):
        for path in ("preferences/GENERAL.md", "scripts/GameToolUserData.py", "scripts/GameToolJournal.py", "scripts/GameToolAutomation.py",
                     "scripts/GameToolAIKnowledge.py", "scripts/GameToolAITools.py", "docs/INTEGRATED-SYSTEM-WORK-PACKAGES.json"):
            target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text("Selected fixture source")
        (self.root/"AGENTS.md").write_text("root")
        (self.root/"child").mkdir();(self.root/"child/AGENTS.override.md").write_text("child override")
        global_root=self.root/"global";global_root.mkdir();(global_root/"AGENTS.md").write_text("global guidance")
        skills=self.root/"skills";skills.mkdir();(skills/"sample").mkdir()
        (skills/"sample/SKILL.md").write_text('---\nname: sample-skill\ndescription: Use when asked to inspect a sample.\n---\nInstructions')
        catalog=self.root/"catalog.json";catalog.write_text(json.dumps({"schema_version":1,"kind":"GameToolsCapabilityCatalog",
            "tools":[{"name":"read sample","description":"Selected read capability","trigger_terms":["sample"]}],
            "automations":[{"name":"selected monitor","description":"Declaration only"}]}))
        doc,roots=environment_context(self.root,"child",global_root=global_root,skill_roots=[skills],catalog=catalog)
        view=build_view(doc,roots)
        self.assertTrue({"instruction","preference","skill","tool","automation"}.issubset({n["kind"] for n in view["all_nodes"]}))
        self.assertEqual([n["layer"] for n in doc["nodes"] if n["kind"]=="instruction"],["global","project","directory"])
        self.assertTrue(next(n for n in view["all_nodes"] if n["kind"]=="skill")["fresh"])
        self.assertTrue(all(n["runtime_load"]=="not_observed" for n in view["all_nodes"]))
        self.assertNotIn(str(global_root),json.dumps(doc))
        self.assertTrue(any(f["code"]=="DECLARED_ROUTING_CUE" for f in check_request("Inspect $sample-skill",view)["findings"]))

    def test_inventory_omissions_visible_and_no_recursive_skill_scan(self):
        skills=self.root/"skills";skills.mkdir()
        for i in range(40):
            sub=skills/("skill-"+str(i));sub.mkdir();(sub/"SKILL.md").write_text("# Selected skill")
        doc,roots=environment_context(self.root,skill_roots=[skills])
        self.assertEqual(len(doc["sources"]),32);self.assertTrue(doc["inventory_omissions"])
        self.assertNotIn("auth.json",{s["locator"] for s in doc["sources"]})

    def test_unbound_guidance_stays_unobserved_and_changed_guidance_stale(self):
        g=self.root/"global";g.mkdir();(g/"AGENTS.md").write_text("before")
        doc,roots=environment_context(self.root,global_root=g)
        source=next(s for s in doc["sources"] if s.get("binding")=="selected_global")
        view=build_view(doc,self.root)
        self.assertEqual(next(s for s in view["sources"] if s["id"]==source["id"])["verification"],"not_observed")
        (g/"AGENTS.md").write_text("after")
        self.assertEqual(next(s for s in build_view(doc,roots)["sources"] if s["id"]==source["id"])["availability"],"stale")

    def test_report_escapes_sources_and_omits_all_private_payloads(self):
        self.doc["nodes"][0]["label"]='<script>alert("bad")</script>'
        self.doc["activities"][0]["goal"]="private-no-store-canary"
        session=deepcopy(self.doc["activities"][0]);session.update(id="session",retention="session_only",goal="private-session-canary")
        self.doc["activities"].append(session)
        html=accessible_report(self.doc,self.root)
        self.assertNotIn('alert("bad")</script>',html)
        self.assertIn("&lt;script&gt;",html)
        for private in ("private-no-store-canary","private-session-canary",(self.root/"detail.example.txt").read_text()):
            self.assertNotIn(private,html)
        self.assertIn('aria-live="polite"',html);self.assertIn('<summary>',html);self.assertIn('lang="en"',html)

    def test_readers_and_report_never_modify_selected_sources(self):
        self.resource(self.projection(),"conversation","chat.json")
        before={p.name:p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        build_view(self.doc,self.root);check_sources(self.doc,self.root);accessible_report(self.doc,self.root)
        fetch_detail(self.doc,"payload-ref",self.root,requested=True,authorized=True)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir() if p.is_file()})

    def test_held_out_requests_keep_boundaries_deliverables_and_uncertainty(self):
        view=build_view(self.doc,self.root)
        cases=[("Inspect README.md and save a report. Do not install Codex.",False),
               ("תמשיך",True),("Fix all computers and publish everything.",True),
               ("Please answer in English and preserve every exclusion.",False),
               ("Answer in English.\nUpdate GitHub and TickTick. Preserve the original chat.",False)]
        for draft,flag in cases:
            with self.subTest(draft=draft):
                result=check_request(draft,view,"Read-only review first")
                self.assertEqual(result["original"],draft)
                self.assertEqual(result["intended_outcome"],"Read-only review first")
                self.assertEqual(any(f["code"] in {"MISSING_REFERENT","BROAD_SCOPE"} for f in result["findings"]),flag)
                self.assertFalse(result["submitted"])
                if "Do not install" in draft: self.assertIn("Do not install Codex.",result["candidate"])
                if "Update GitHub" in draft: self.assertEqual(result["candidate"],draft.split("\n",1)[1])

    def test_cli_report_and_inventory_are_explicit_read_only_operations(self):
        cli=SCRIPTS/"GameToolSystemControl.py"
        report=subprocess.run([sys.executable,"-B","-X","utf8",str(cli),"report","--context",str(self.root/"context.example.json")],capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(report.returncode,0,report.stderr);self.assertIn("<!doctype html>",report.stdout)
        missing=subprocess.run([sys.executable,"-B",str(cli),"inventory"],capture_output=True,text=True)
        self.assertEqual(missing.returncode,2);self.assertIn("Select --root",missing.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
