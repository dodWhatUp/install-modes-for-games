"""Pure catalog contracts; synthetic plans are not measurements or live acceptance."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("catalog", Path(__file__).parents[1] / "Game-Tool-Catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class Contracts(unittest.TestCase):
    def setUp(self):
        self.data = catalog.load_catalog(catalog.DEFAULT_CATALOG)

    def reject(self):
        with self.assertRaises(catalog.CatalogError):
            catalog.validate(self.data)

    def test_example_valid(self):
        index = catalog.validate(self.data)
        self.assertIn("cp-ultra-pt21", index)
        self.assertIn("renodx-devkit", index)

    def test_duplicate_id_refused(self):
        self.data["components"].append(copy.deepcopy(self.data["components"][0]))
        self.reject()

    def test_unknown_dependency_refused(self):
        self.data["relationships"][0]["to"] = "not-known"
        self.reject()

    def test_cycle_refused(self):
        item = copy.deepcopy(next(r for r in self.data["relationships"] if r["id"] == "xl-requires-red4ext"))
        item.update(id="cycle", **{"from": "red4ext", "to": "archivexl"})
        self.data["relationships"].append(item)
        self.reject()

    def test_recorded_installation_requires_evidence(self):
        self.data["components"][0]["installation"]["status"] = "recorded-present"
        self.reject()

    def test_no_executable_recipe(self):
        self.data["actions"][0]["execution"] = "execute"
        self.reject()

    def test_no_command_field(self):
        self.data["actions"][0]["command"] = "launch something"
        self.reject()

    def test_unknown_relationship_type(self):
        self.data["relationships"][0]["type"] = "same_as"
        self.reject()

    def test_unresolved_alias_not_silently_renamed(self):
        node = catalog.show_node(self.data, "dlss-switcher-unresolved")
        self.assertEqual(node["kind"], "unresolved-alias")
        self.assertEqual(node["installation"]["status"], "unknown")
        self.assertEqual(catalog.show_node(self.data, "dlss-swapper-candidate")["installation"]["status"], "unknown")

    def test_no_metric_estimates(self):
        node = catalog.show_node(self.data, "rhi")
        self.assertTrue(all(value is None for value in node["measured_metrics"].values()))

    def test_dynamic_game_filter(self):
        nodes = catalog.filtered_nodes(self.data, game="cyberpunk-2077", kind="feature")
        self.assertTrue(nodes)
        self.assertTrue(all(x["game"] == "cyberpunk-2077" for x in nodes))
        self.assertFalse(any(x["id"].startswith("skyrim") for x in nodes))

    def test_category_relationship_filters(self):
        nodes = catalog.filtered_nodes(self.data, category="graphics", relationship="manages")
        self.assertIn("rhi", {x["id"] for x in nodes})
        self.assertNotIn("rtss", {x["id"] for x in nodes})

    def test_search_and_status_filters(self):
        nodes = catalog.filtered_nodes(self.data, search="SWITCHER", status="unknown")
        self.assertEqual([x["id"] for x in nodes], ["dlss-switcher-unresolved"])

    def test_installation_filters_preserve_recorded_evidence(self):
        for state in ("unknown", "recorded-present", "recorded-absent"):
            nodes = catalog.filtered_nodes(self.data, installation=state)
            self.assertTrue(nodes)
            self.assertTrue(all(x["installation"]["status"] == state for x in nodes))
        unknown = {x["id"] for x in catalog.filtered_nodes(self.data, installation="unknown")}
        self.assertTrue({"steam", "mod-organizer-2", "vortex", "nexus-mods", "skyrim-creation-kit", "cyberpunk-redmod"} <= unknown)

    def test_sort_options_are_stable_with_id_tie_breaks(self):
        for field in ("id", "name", "kind", "status"):
            nodes = catalog.filtered_nodes(self.data, sort=field)
            expected = sorted(nodes, key=lambda node: (str(node.get(field, node["entity"] if field == "kind" else "unknown")).casefold(), node["id"]))
            self.assertEqual(nodes, expected)
        self.assertEqual(catalog.filtered_nodes(self.data), catalog.filtered_nodes(self.data, sort="id"))

    def test_invalid_sort_and_installation_filters_refused(self):
        for options in ({"sort": "run-now"}, {"installation": "installed-live"}):
            with self.assertRaises(catalog.CatalogError):
                catalog.filtered_nodes(self.data, **options)

    def test_mod_kit_not_required_by_normal_game_feature(self):
        plan = catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", ["cp-renodx-hdr", "cp-ultra-pt21"])
        self.assertNotIn("cyberpunk-redmod", plan["always_on"])
        self.assertNotIn("skyrim-creation-kit", plan["always_on"])
        self.assertEqual(catalog.show_node(self.data, "cyberpunk-redmod")["declared_actions"], [])

    def test_store_and_services_are_not_payload_features(self):
        for node in ("steam", "vortex", "mod-organizer-2", "skyrim-creation-kit"):
            self.assertEqual(catalog.plan_overhead(self.data, "process-idle", factors=[node])["execution"], "none")
            self.assertEqual(catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", [node])["status"], "blocked")
        self.assertEqual(catalog.plan_overhead(self.data, "process-idle", factors=["nexus-mods"])["status"], "blocked")

    def test_unknown_game_refused(self):
        with self.assertRaises(catalog.CatalogError):
            catalog.filtered_nodes(self.data, game="guessed-game")

    def test_idle_manager_not_payload(self):
        plan = catalog.plan_overhead(self.data, "process-idle", factors=["rhi"])
        self.assertEqual(plan["status"], "prepared-not-authorized")
        self.assertEqual(len(plan["cases"]), 2)
        self.assertIn("Closing a manager does not disable its payload", plan["interpretation"])
        self.assertEqual(plan["execution"], "none")

    def test_idle_alias_collector_or_game_feature_blocked(self):
        for node in ("dlss-switcher-unresolved", "presentmon-console", "cp-renodx-hdr"):
            plan = catalog.plan_overhead(self.data, "process-idle", factors=[node])
            self.assertEqual(plan["status"], "blocked")
            self.assertEqual(plan["cases"], [])

    def test_one_factor_keeps_host_on(self):
        plan = catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", ["cp-renodx-hdr"])
        self.assertEqual(plan["status"], "prepared-not-authorized")
        self.assertIn("reshade", plan["always_on"])
        self.assertIn("native-cyberpunk", plan["always_on"])
        self.assertFalse(plan["cases"][0]["factor_state"]["cp-renodx-hdr"])
        self.assertIn("reshade", plan["cases"][0]["always_on"])

    def test_2x2_preserves_all_shared_foundations_in_every_case(self):
        plan = catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", ["cp-renodx-hdr", "cp-ultra-pt21"])
        self.assertEqual(plan["status"], "prepared-not-authorized")
        self.assertEqual(len(plan["cases"]), 4)
        needed = {"native-cyberpunk", "reshade", "cet", "red4ext", "archivexl", "redscript", "audiopoolfix"}
        for case in plan["cases"]:
            self.assertTrue(needed <= set(case["always_on"]))
            self.assertTrue(all(x is None for x in case["measured_metrics"].values()))
            self.assertEqual(case["runs"], [])

    def test_highest_preset_remains_blocked(self):
        plan = catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", ["cp-ultra-highest"])
        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["cases"], [])

    def test_wrong_game_and_component_factor_blocked(self):
        for factors in (["skyrim-pd-mfg"], ["rhi"]):
            plan = catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", factors)
            self.assertEqual(plan["status"], "blocked")

    def test_unreviewed_combination_blocked(self):
        next(x for x in self.data["features"] if x["id"] == "cp-optiscaler-path")["planning"] = "prepared"
        plan = catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", ["cp-optiscaler-path", "cp-renodx-hdr"])
        self.assertEqual(plan["status"], "blocked")
        self.assertIn("cp-proxy-chain-review", " ".join(plan["blockers"]))

    def test_factor_as_dependency_blocks_off_off(self):
        relation = copy.deepcopy(self.data["relationships"][0])
        relation.update(id="dependent-factor", type="depends_on", game="cyberpunk-2077", **{"from": "cp-ultra-pt21", "to": "cp-renodx-hdr"})
        self.data["relationships"].append(relation)
        plan = catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", ["cp-renodx-hdr", "cp-ultra-pt21"])
        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["cases"], [])

    def test_unknown_mandatory_chain_blocked(self):
        next(x for x in self.data["relationships"] if x["id"] == "reshade-hosts-cp-renodx")["status"] = "unknown"
        plan = catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", ["cp-renodx-hdr"])
        self.assertEqual(plan["status"], "blocked")

    def test_duplicate_or_too_many_factors_refused(self):
        for factors in ([], ["rhi", "rhi"], ["rhi", "rtss", "afterburner"]):
            with self.assertRaises(catalog.CatalogError):
                catalog.plan_overhead(self.data, "process-idle", factors=factors)

    def test_planning_does_not_mutate_source(self):
        before = copy.deepcopy(self.data)
        catalog.plan_overhead(self.data, "in-game", "cyberpunk-2077", ["cp-renodx-hdr", "cp-ultra-pt21"])
        self.assertEqual(self.data, before)

    def test_json_duplicate_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.json"
            for payload in ('{"schema_version":1,"schema_version":1}', '{"bad":NaN}'):
                path.write_text(payload)
                with self.assertRaises(catalog.CatalogError):
                    catalog.load_catalog(path)

    def test_json_stdout_commands(self):
        for command in (["validate"], ["list", "--kind", "manager"], ["list", "--installation", "unknown", "--sort", "name"], ["show", "renodx-mcp-bridge"],
                        ["plan-overhead", "--scope", "in-game", "--game", "cyberpunk-2077", "--factor", "cp-renodx-hdr"]):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                result = catalog.main(command)
            self.assertEqual(result, 0)
            self.assertEqual(err.getvalue(), "")
            self.assertIsInstance(json.loads(out.getvalue()), dict)

    def test_error_is_json_stdout_not_traceback(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = catalog.main(["do-not-execute"])
        self.assertEqual(result, 2)
        self.assertEqual(err.getvalue(), "")
        self.assertEqual(json.loads(out.getvalue())["execution"], "none")

    def test_cli_never_rewrites_catalog(self):
        before = catalog.DEFAULT_CATALOG.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(catalog.main(["validate"]), 0)
        self.assertEqual(catalog.DEFAULT_CATALOG.read_bytes(), before)

    def test_devkit_is_diagnostic_and_not_connected(self):
        node = catalog.show_node(self.data, "renodx-mcp-bridge")
        self.assertEqual(node["installation"]["status"], "unknown")
        self.assertFalse(node["idle_process"])
        self.assertTrue(all(a["execution"] == "declaration-only" for a in node["declared_actions"]))
        self.assertIn("prepare-diagnostic-capture", {a["capability"] for a in node["declared_actions"]})


if __name__ == "__main__":
    unittest.main()
