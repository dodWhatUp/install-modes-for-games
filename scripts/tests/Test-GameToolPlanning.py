"""Read-only goal planning, opaque instance identity and UMM adapter contracts."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
import sys
import tempfile
import unittest

import jsonschema

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

from GameToolAIFoundation import FoundationService
from GameToolGameWorkspaces import WorkspaceAI
from GameToolPlanning import PlanningService
from GameToolAITestPackage import build_ai_test_package
from game_mod_ops.safety import ModError, object_hash


class ReadOnlyPlanningContracts(unittest.TestCase):
    def setUp(self):
        temp_parent = "/private/tmp" if sys.platform == "darwin" else None
        self.tmp = tempfile.TemporaryDirectory(dir=temp_parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / "private"
        self.game = self.root / "Kingmaker"
        (self.game / "Kingmaker_Data/Managed/UnityModManager").mkdir(parents=True)
        (self.game / "Kingmaker.exe").write_bytes(b"synthetic executable marker\n")
        (self.game / "Kingmaker_Data/Managed/UnityModManager/UnityModManager.dll").write_bytes(
            b"synthetic loader marker\n"
        )
        self._umm_mod(
            "KingmakerTactics", "1.0.1", "KingmakerTactics.dll",
            requirements=[], folder="KingmakerTactics",
        )
        self.service = WorkspaceAI(self.data)
        self.planning = PlanningService(self.service.workspaces)
        self.package = build_ai_test_package(SCRIPTS.parent, self.root / "package")
        self.foundation = FoundationService(self.service, source_root=self.package)
        self.before_game = self._tree_hash(self.game)

    def _umm_mod(self, ident, version, assembly, *, requirements, folder):
        root = self.game / "Mods" / folder
        root.mkdir(parents=True, exist_ok=True)
        (root / "Info.json").write_text(json.dumps({
            "Id": ident,
            "Version": version,
            "AssemblyName": assembly,
            "Requirements": requirements,
        }), encoding="utf-8")
        (root / assembly).write_bytes(b"synthetic assembly marker\n")

    @staticmethod
    def _tree_hash(root):
        rows = []
        for path in sorted(root.rglob("*")):
            if path.is_file():
                rows.append((
                    path.relative_to(root).as_posix(), path.stat().st_size,
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                ))
        return rows

    def register(self, instance_id="kingmaker-main"):
        return self.service.workspaces.instances.register_local(
            instance_id=instance_id,
            game_id="pathfinder-kingmaker",
            game_dir=self.game,
            store="steam",
            build="2.1.7",
            profile="default",
            confirmed=True,
        )

    def assert_game_unchanged(self):
        self.assertEqual(self.before_game, self._tree_hash(self.game))

    def test_construction_is_inert_and_registration_requires_local_confirmation(self):
        self.assertFalse((self.data / "game-instances").exists())
        with self.assertRaises(ModError) as raised:
            self.service.workspaces.instances.register_local(
                instance_id="kingmaker-main", game_id="pathfinder-kingmaker",
                game_dir=self.game, confirmed=False,
            )
        self.assertEqual(raised.exception.code, "LOCAL_APPROVAL_REQUIRED")
        self.assertFalse((self.data / "game-instances").exists())
        self.assert_game_unchanged()

    def test_registration_writes_only_private_metadata_and_public_result_has_no_path(self):
        result = self.register()
        self.assertTrue(result["metadata_written"])
        self.assertFalse(result["game_files_written"])
        self.assertEqual(result["instance"]["adapter"], "umm")
        self.assertFalse(result["instance"]["path_included"])
        self.assertNotIn(str(self.game), json.dumps(result))
        records = list((self.data / "game-instances").glob("*.json"))
        self.assertEqual(len(records), 1)
        stored = json.loads(records[0].read_text(encoding="utf-8"))
        self.assertEqual(stored["body"]["game_dir"], str(self.game))
        self.assert_game_unchanged()

    def test_public_build_and_profile_labels_refuse_paths_or_credentials(self):
        for field, value in (("build", "C:\\Users\\private"),
                             ("profile", "person@example.invalid"),
                             ("profile", "Bearer " + "x" * 30)):
            kwargs = {"build": "unknown", "profile": None}
            kwargs[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ModError) as raised:
                self.service.workspaces.instances.register_local(
                    instance_id="kingmaker-private-label", game_id="pathfinder-kingmaker",
                    game_dir=self.game, confirmed=True, **kwargs,
                )
            self.assertEqual(raised.exception.code, "INSTANCE_PRIVATE_LABEL")
        self.assertFalse((self.data / "game-instances").exists())
        self.assert_game_unchanged()

    def test_corrupt_registry_filename_is_never_exposed(self):
        registry = self.data / "game-instances"
        registry.mkdir(parents=True)
        private_name = "ghp_" + "a" * 24
        (registry / (private_name + ".json")).write_text("{}", encoding="utf-8")
        listing = self.planning.list_instances()
        self.assertEqual(listing["count"], 1)
        self.assertEqual(listing["instances"][0]["status"], "INCOMPLETE_OR_CORRUPT")
        self.assertEqual(listing["instances"][0]["instance_id"], "corrupt-record-001")
        self.assertNotIn(private_name, json.dumps(listing))
        self.assert_game_unchanged()

    def test_renamed_valid_record_is_reported_only_as_opaque_corruption(self):
        self.register()
        registry = self.data / "game-instances"
        original = registry / "kingmaker-main.json"
        renamed = registry / "renamed-private-record.json"
        original.rename(renamed)
        listing = self.planning.list_instances()
        self.assertEqual(listing["count"], 1)
        self.assertEqual(listing["instances"][0]["status"], "INCOMPLETE_OR_CORRUPT")
        self.assertEqual(listing["instances"][0]["instance_id"], "corrupt-record-001")
        self.assertNotIn("renamed-private-record", json.dumps(listing))
        self.assert_game_unchanged()

    def test_nonhex_record_revision_is_rejected_even_when_record_hash_matches(self):
        self.register()
        path = self.data / "game-instances/kingmaker-main.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["body"]["definition_revision"] = "Z" * 64
        record["revision"] = object_hash(record["body"])
        path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaises(ModError) as raised:
            self.service.workspaces.instances.public("kingmaker-main")
        self.assertEqual(raised.exception.code, "INSTANCE_CORRUPT")
        self.assert_game_unchanged()

    def _assert_private_manifest_value_refused(self, private_value):
        path = self.game / "Mods/KingmakerTactics/Info.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["Version"] = private_value
        path.write_text(json.dumps(value), encoding="utf-8")
        self.before_game = self._tree_hash(self.game)
        self.register()
        with self.assertRaises(ModError) as raised:
            self.planning.inspect_instance("kingmaker-main", "pathfinder-kingmaker")
        self.assertEqual(raised.exception.code, "INSTANCE_PRIVATE_METADATA")
        self.assertNotIn(private_value, str(raised.exception))
        blocker = self.foundation.blocker("INSTANCE_PRIVATE_METADATA")
        self.assertFalse(blocker["effects"]["unknown"])
        self.assertFalse(blocker["retry"]["allowed"])
        self.assert_game_unchanged()

    def test_public_inspection_refuses_credential_manifest_metadata(self):
        self._assert_private_manifest_value_refused("ghp_" + "b" * 24)

    def test_public_inspection_refuses_windows_path_manifest_metadata(self):
        private_path = "build C:" + "\\" + "Users" + "\\private\\file.dll"
        self._assert_private_manifest_value_refused(private_path)

    def test_public_inspection_refuses_posix_path_manifest_metadata(self):
        self._assert_private_manifest_value_refused("build /Users/private/file.dll")

    def test_public_inspection_refuses_generic_absolute_posix_path_metadata(self):
        self._assert_private_manifest_value_refused("build /games/private/file.dll")

    def test_public_inspection_refuses_unc_path_manifest_metadata(self):
        self._assert_private_manifest_value_refused(r"\\server\private\file.dll")

    def test_public_inspection_refuses_file_uri_manifest_metadata(self):
        private_uri = "build file:" + "///" + "Users/private/file.dll"
        self._assert_private_manifest_value_refused(private_uri)

    def test_public_inspection_refuses_punctuated_and_short_absolute_paths(self):
        slash = "/"
        backslash = "\\"
        values = [
            "build " + slash + "games",
            "build [" + slash + "games]",
            "path=" + slash + "games",
            "path:" + slash + "games",
            "build " + slash + "g",
            "build (" + slash + "g)",
            "build [C:" + backslash + "Users" + backslash + "private" + backslash + "file.dll]",
            "build,C:" + backslash + "Users" + backslash + "private" + backslash + "file.dll",
            "build [" + backslash * 2 + "server" + backslash + "share" + backslash + "file.dll]",
            "build," + backslash * 2 + "server" + backslash + "share" + backslash + "file.dll",
            "build " + backslash * 2 + "server",
            "build " + slash * 2 + "server",
            "build " + backslash + "Users" + backslash + "private" + backslash + "file.dll",
            "build ~" + slash + "private" + slash + "file.dll",
            "build ~other" + slash + "private" + slash + "file.dll",
            "build $HOME" + slash + "private" + slash + "file.dll",
            "build %USERPROFILE%" + backslash + "private" + backslash + "file.dll",
            "https:" + slash * 2 + "user:password@example.invalid/release",
        ]
        for value in values:
            with self.subTest(value=value):
                self._assert_private_manifest_value_refused(value)

    def test_public_metadata_keeps_relative_identifiers_versions_and_https(self):
        from GameToolInstances import _assert_public_metadata
        slash = "/"
        for value in (
            "1.0.1", "KingmakerTactics", "Mods" + slash + "Foo",
            "version 1.0" + slash + "2.0",
            "https:" + slash * 2 + "example.invalid/releases/v1",
        ):
            with self.subTest(value=value):
                _assert_public_metadata(value)

    def test_same_instance_case_alias_is_idempotent(self):
        self.register()
        alternate = Path(str(self.game).replace("Kingmaker", "KINGMAKER"))
        if not alternate.exists() or not os.path.samefile(self.game, alternate):
            self.skipTest("Filesystem is case-sensitive; exact-path idempotence is covered separately.")
        result = self.service.workspaces.instances.register_local(
            instance_id="kingmaker-main",
            game_id="pathfinder-kingmaker",
            game_dir=alternate,
            store="steam",
            build="2.1.7",
            profile="default",
            confirmed=True,
        )
        self.assertFalse(result["metadata_written"])
        self.assertEqual(result["instance"]["status"], "ALREADY_REGISTERED_READ_ONLY")
        self.assertEqual(len(list((self.data / "game-instances").glob("*.json"))), 1)
        self.assert_game_unchanged()

    def test_case_alias_cannot_register_the_same_existing_directory_twice(self):
        self.register()
        alternate = Path(str(self.game).replace("Kingmaker", "KINGMAKER"))
        if not alternate.exists() or not os.path.samefile(self.game, alternate):
            self.skipTest("Filesystem is case-sensitive; exact-path duplicate ownership is covered separately.")
        with self.assertRaises(ModError) as raised:
            self.service.workspaces.instances.register_local(
                instance_id="kingmaker-case-alias",
                game_id="pathfinder-kingmaker",
                game_dir=alternate,
                store="steam",
                build="2.1.7",
                profile="default",
                confirmed=True,
            )
        self.assertEqual(raised.exception.code, "INSTANCE_PATH_OWNED")
        self.assertEqual(len(list((self.data / "game-instances").glob("*.json"))), 1)
        self.assert_game_unchanged()

    def test_support_only_umm_game_can_plan_installed_inspection_without_recipe(self):
        wrath = self.root / "Wrath"
        wrath.mkdir()
        (wrath / "Wrath.exe").write_bytes(b"synthetic wrath executable marker\n")
        before = self._tree_hash(wrath)
        result = self.service.workspaces.instances.register_local(
            instance_id="wrath-main",
            game_id="pathfinder-wrath-of-the-righteous",
            game_dir=wrath,
            store="steam",
            build="synthetic",
            profile="default",
            confirmed=True,
        )
        self.assertEqual(result["inventory_summary"]["inventory_status"], "MOD_DIRECTORY_ABSENT")
        plan = self.planning.goal_plan(
            "pathfinder-wrath-of-the-righteous",
            "inspect-installed",
            instance_id="wrath-main",
        )
        self.assertEqual(plan["status"], "READY_FOR_READS")
        self.assertEqual(plan["blockers"], [])
        nodes = {row["id"]: row for row in plan["nodes"]}
        self.assertEqual(nodes["recipe"]["status"], "NOT_APPLICABLE")
        self.assertEqual(nodes["mod-plan"]["status"], "NOT_APPLICABLE")
        self.assertEqual(nodes["inventory"]["status"], "READY")
        self.assertEqual(before, self._tree_hash(wrath))

    def test_direct_planning_rejects_invalid_mode_before_selection(self):
        with self.assertRaises(ModError) as raised:
            self.planning.goal_plan(
                "pathfinder-kingmaker",
                "review-mods",
                mode="Bad Mode",
                selected=["kingmaker-tactics"],
            )
        self.assertEqual(raised.exception.code, "MODE")

    def test_same_registration_is_idempotent_and_path_cannot_get_two_owners(self):
        self.register()
        second = self.register()
        self.assertFalse(second["metadata_written"])
        with self.assertRaises(ModError) as raised:
            self.register("kingmaker-other")
        self.assertEqual(raised.exception.code, "INSTANCE_PATH_OWNED")
        self.assertEqual(len(list((self.data / "game-instances").glob("*.json"))), 1)
        self.assert_game_unchanged()

    def test_filtered_instance_list_reports_truncation_only_for_matching_rows(self):
        self.register()
        wrath = self.root / "Wrath-listing"
        wrath.mkdir()
        (wrath / "Wrath.exe").write_bytes(b"synthetic wrath executable marker\n")
        self.service.workspaces.instances.register_local(
            instance_id="wrath-listing", game_id="pathfinder-wrath-of-the-righteous",
            game_dir=wrath, confirmed=True,
        )
        one_game = self.planning.list_instances("pathfinder-kingmaker", limit=1)
        self.assertEqual(one_game["count"], 1)
        self.assertFalse(one_game["truncated"])

        second = self.root / "Kingmaker-second"
        shutil.copytree(self.game, second)
        self.service.workspaces.instances.register_local(
            instance_id="kingmaker-second", game_id="pathfinder-kingmaker",
            game_dir=second, confirmed=True,
        )
        two_matching = self.planning.list_instances("pathfinder-kingmaker", limit=1)
        self.assertEqual(two_matching["count"], 1)
        self.assertTrue(two_matching["truncated"])
        self.assert_game_unchanged()

    def test_public_list_and_batch_status_never_return_private_path(self):
        self.register()
        listing = self.planning.list_instances("pathfinder-kingmaker")
        self.assertEqual(listing["count"], 1)
        self.assertNotIn(str(self.game), json.dumps(listing))
        batch = self.foundation.status_batch([
            {"kind": "instance", "id": "kingmaker-main", "game_id": "pathfinder-kingmaker"}
        ])
        self.assertEqual(batch["data"]["results"][0]["status"], "REGISTERED_READ_ONLY")
        self.assertNotIn(str(self.game), json.dumps(batch))
        self.assert_game_unchanged()

    def test_umm_inspection_reads_manifest_identity_without_loading_or_writing(self):
        self.register()
        result = self.planning.inspect_instance("kingmaker-main", "pathfinder-kingmaker")
        inventory = result["inventory"]
        self.assertEqual(inventory["adapter"], "umm")
        self.assertEqual(inventory["runtime"], "NOT_VERIFIED")
        self.assertEqual(inventory["mods"][0]["id"], "KingmakerTactics")
        self.assertTrue(inventory["mods"][0]["payload_marker_present"])
        self.assertEqual(result["adapter_contract"]["writes"], [])
        self.assertFalse(result["adapter_contract"]["manager_profile_read"])
        self.assertNotIn(str(self.game), json.dumps(result))
        self.assert_game_unchanged()

    def test_goal_plan_is_deterministic_acyclic_and_creates_no_job_or_request(self):
        first = self.planning.goal_plan("pathfinder-kingmaker", "review-mods", mode="real-time")
        second = self.planning.goal_plan("pathfinder-kingmaker", "review-mods", mode="real-time")
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "READY_FOR_READS")
        self.assertEqual(first["effects"]["write"], [])
        self.assertFalse(first["automatic_execution"])
        nodes = {row["id"]: row for row in first["nodes"]}
        self.assertEqual(nodes["instance"]["status"], "NOT_APPLICABLE")
        self.assertEqual(nodes["mod-plan"]["status"], "READY")
        self.assertFalse((self.data / "mod-workflows/jobs").exists())
        self.assertFalse((self.data / "automation/requests").exists())
        schema = json.loads((SCRIPTS.parent / "schemas/game-tools-goal-plan.schema.json").read_text())
        jsonschema.validate(first, schema)
        self.assert_game_unchanged()

    def test_compare_goal_requires_registered_instance_without_accepting_path(self):
        plan = self.planning.goal_plan(
            "pathfinder-kingmaker", "compare-intended-installed", mode="real-time"
        )
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertIn("INSTANCE_REQUIRED", plan["blockers"])
        self.assertNotIn("game_dir", json.dumps(plan))
        self.assertFalse((self.data / "game-instances").exists())

    def test_declared_active_conflict_blocks_plan_and_graph_keeps_both_owners(self):
        selected = ["buff-bot", "autobuff"]
        plan = self.planning.goal_plan(
            "pathfinder-kingmaker", "review-mods", mode="real-time", selected=selected
        )
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertIn("CHOICE_CONFLICT", plan["blockers"])
        graph = self.planning.conflict_graph(
            "pathfinder-kingmaker", mode="real-time", selected=selected
        )
        self.assertEqual(graph["status"], "BLOCKING_CONFLICTS")
        conflicts = [row for row in graph["edges"] if row["kind"] == "conflicts"]
        self.assertTrue(any(row["active"] for row in conflicts))
        node_ids = {row["id"] for row in graph["nodes"]}
        self.assertTrue(all(row["from"] in node_ids and row["to"] in node_ids for row in graph["edges"]))
        self.assertFalse(graph["automatic_resolution"])

    def test_advisory_alternative_conflict_has_a_real_unselected_node(self):
        graph = self.planning.conflict_graph(
            "pathfinder-kingmaker", mode="real-time", selected=["buff-bot"]
        )
        nodes = {row["id"]: row for row in graph["nodes"]}
        self.assertIn("item:autobuff", nodes)
        self.assertFalse(nodes["item:autobuff"]["selected"])
        edge = next(row for row in graph["edges"] if row["kind"] == "conflicts")
        self.assertFalse(edge["active"])
        self.assertEqual(graph["status"], "REVIEW_REQUIRED")

    def test_instance_graph_uses_umm_id_fallback_for_planned_observed_comparison(self):
        self.register()
        graph = self.planning.conflict_graph(
            "pathfinder-kingmaker", instance_id="kingmaker-main",
            mode="real-time", selected=["kingmaker-tactics"],
        )
        comparison = {row["item_id"]: row for row in graph["comparison"]["items"]}
        self.assertEqual(comparison["kingmaker-tactics"]["state"], "IDENTITY_PRESENT")
        self.assertEqual(graph["comparison"]["compares"], "plan_vs_observed_manifest_not_runtime")
        self.assertFalse(graph["runtime_verified"])
        self.assertNotIn(str(self.game), json.dumps(graph))
        self.assert_game_unchanged()

    def test_modern_foundation_tools_are_read_only_and_schema_valid(self):
        self.register()
        listed = self.foundation.instances("pathfinder-kingmaker")
        inspected = self.foundation.instance_inspect("kingmaker-main", "pathfinder-kingmaker")
        planned = self.foundation.plan_goal(
            "pathfinder-kingmaker", "compare-intended-installed",
            instance_id="kingmaker-main", mode="real-time",
        )
        graph = self.foundation.conflicts(
            "pathfinder-kingmaker", instance_id="kingmaker-main", mode="real-time",
        )
        envelope_schema = json.loads(
            (SCRIPTS.parent / "schemas/ai-result-envelope.schema.json").read_text()
        )
        plan_schema = json.loads(
            (SCRIPTS.parent / "schemas/game-tools-goal-plan.schema.json").read_text()
        )
        for value in (listed, inspected, planned, graph):
            jsonschema.validate(value, envelope_schema)
            self.assertEqual(value["effects"]["write"], [])
            self.assertFalse(value["effects"]["network"])
            self.assertNotIn(str(self.game), json.dumps(value))
        jsonschema.validate(planned["data"], plan_schema)
        self.assertEqual(inspected["completion"]["runtime"], "not_started")
        self.assertEqual(inspected["completion"]["publication"], "not_started")
        self.assert_game_unchanged()

    def test_non_umm_definition_is_visible_as_pending_not_silently_generalized(self):
        with self.assertRaises(ModError) as raised:
            self.service.workspaces.instances.register_local(
                instance_id="cyberpunk-main",
                game_id="cyberpunk-2077",
                game_dir=self.game,
                confirmed=True,
            )
        self.assertEqual(raised.exception.code, "ADAPTER_ACCEPTANCE_PENDING")
        self.assert_game_unchanged()

    def test_exact_host_pins_include_planning_and_match_current_source(self):
        import check_host
        result = check_host.check(SCRIPTS.parent)
        self.assertEqual(result["status"], "EXACT_DEPENDENCIES_MATCH")
        self.assertEqual(result["host_reference_version"], "0.27.0-preview.1")
        pinned = {row["path"] for row in result["files"]}
        self.assertTrue({"scripts/GameToolInstances.py", "scripts/GameToolPlanning.py"} <= pinned)
        self.assertTrue(all(row["matches"] for row in result["files"]))
        self.assertFalse(result["installed"])
        self.assertFalse(result["repinned"])

    def test_ai_surface_has_no_registration_or_arbitrary_path_argument(self):
        from GameToolAITools import foundation_tools
        definitions = foundation_tools(True)
        names = {row["name"] for row in definitions}
        self.assertTrue({
            "game_tools_instances", "game_tools_instance_inspect",
            "game_tools_plan_goal", "game_tools_conflicts",
        } <= names)
        self.assertFalse(any("register" in name for name in names))
        for definition in definitions:
            properties = definition["inputSchema"]["properties"]
            self.assertFalse({"path", "game_dir", "root", "directory"} & set(properties))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ReadOnlyPlanningContracts)
    )
    raise SystemExit(not result.wasSuccessful())
