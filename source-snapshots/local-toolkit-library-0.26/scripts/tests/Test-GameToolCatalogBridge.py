"""Pure bridge contracts; temporary data fixtures, no app/game/capture acceptance."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("catalog_bridge", SCRIPTS / "GameToolCatalogBridge.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
EXAMPLE = SCRIPTS.parent / "examples/game-tool-hub/catalog.example.json"


def fixture_fg(scope, game, *args, **kwargs):
    """Synthetic policy receipt; never substitutes for a live inspector probe."""
    return {"schema_version": 1, "status": "NOT_APPLICABLE" if scope == "process-idle" else "PASS",
            "can_compare": True, "scope": scope, "game_id": game, "execution": "none",
            "reasons": ["Synthetic trusted policy output, not game evidence"], "source_revisions": {}}


class BridgeContracts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.path = self.directory / "catalog.example.json"
        self.raw = EXAMPLE.read_bytes()
        self.path.write_bytes(self.raw)
        self.service = bridge.CatalogService(self.path)
        patcher = mock.patch.object(bridge, "_run_fg_preflight", side_effect=fixture_fg)
        self.fg_spy = patcher.start()
        self.addCleanup(patcher.stop)

    def write_catalog(self, data):
        self.path.write_text(json.dumps(data, allow_nan=False), encoding="utf-8")

    def assert_all_refuse(self):
        requests = (lambda: self.service.options(), lambda: self.service.list_nodes(),
                    lambda: self.service.details("rhi"),
                    lambda: self.service.prepare_plan("process-idle", factors=["rhi"]))
        for request in requests:
            with self.assertRaises(bridge.CatalogBridgeError):
                request()

    def test_default_exact_source_and_version(self):
        default = bridge.CatalogService()
        self.assertEqual(default.path, EXAMPLE)
        self.assertEqual(default.catalog_version, "0.1.1")
        self.assertEqual(default.revision, hashlib.sha256(EXAMPLE.read_bytes()).hexdigest())

    def test_reload_summary(self):
        summary = self.service.reload()
        data = json.loads(self.raw)
        self.assertEqual(set(summary), {"version", "revision", "counts", "execution"})
        self.assertEqual(summary["counts"], {key: len(data[key]) for key in bridge._COLLECTIONS})
        self.assertEqual(summary["revision"], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(summary["execution"], "none")

    def test_options_plain_lists_and_named_games(self):
        options = self.service.options()
        self.assertEqual(set(options), {"kinds", "categories", "games", "statuses", "installations", "relationships", "sorts"})
        self.assertTrue(all(isinstance(value, list) for value in options.values()))
        self.assertTrue(all(set(game) == {"id", "name"} for game in options["games"]))
        self.assertIn({"id": "cyberpunk-2077", "name": "Cyberpunk 2077"}, options["games"])
        self.assertIn("feature", options["kinds"])
        self.assertEqual(options["sorts"], ["id", "name", "kind", "status"])

    def test_list_plain_backend_shape_and_default_order(self):
        actual = self.service.list_nodes()
        self.assertIsInstance(actual, list)
        self.assertEqual(actual, self.service._backend.filtered_nodes(self.service._snapshot))
        self.assertEqual([node["id"] for node in actual], sorted(node["id"] for node in actual))
        self.assertTrue(all("catalog_source" not in node for node in actual))

    def test_backend_filters_and_sorts_preserved(self):
        for filters in ({"kind": "feature", "game": "cyberpunk-2077"},
                        {"category": "graphics", "relationship": "manages"},
                        {"search": "SWITCHER", "status": "unknown"},
                        {"installation": "unknown", "sort": "name"},
                        {"sort": "kind"}, {"sort": "status"}):
            self.assertEqual(self.service.list_nodes(**filters),
                             self.service._backend.filtered_nodes(self.service._snapshot, **filters))

    def test_bad_filter_or_identifier_does_not_invalidate_good_source(self):
        for request in (lambda: self.service.list_nodes(launch=True),
                        lambda: self.service.list_nodes(sort="run"),
                        lambda: self.service.list_nodes(game="missing"),
                        lambda: self.service.details("missing")):
            with self.assertRaises(bridge.CatalogBridgeError):
                request()
            self.assertTrue(self.service.list_nodes())

    def test_details_backend_shape_and_portable_provenance(self):
        details = self.service.details("rhi")
        source = details.pop("catalog_source")
        self.assertEqual(details, self.service._backend.show_node(self.service._snapshot, "rhi"))
        self.assertEqual(source, {"revision": self.service.revision, "version": "0.1.1",
                                  "planning_only": True, "locator": self.path.name})
        self.assertNotIn(str(self.directory), json.dumps(source))

    def test_detached_return_values_cannot_mutate_snapshot(self):
        nodes = self.service.list_nodes()
        nodes[0]["provenance"][0]["reference"] = "changed-by-caller"
        detail = self.service.details("rhi")
        detail["name"] = "changed-by-caller"
        detail["declared_actions"].clear()
        options = self.service.options()
        options["games"][0]["name"] = "changed-by-caller"
        self.assertNotIn("changed-by-caller", json.dumps(self.service.list_nodes()))
        self.assertNotEqual(self.service.details("rhi")["name"], "changed-by-caller")
        self.assertNotIn("changed-by-caller", json.dumps(self.service.options()))

    def test_prepared_plan_backend_parity_and_nonexecution(self):
        factors = ["cp-renodx-hdr", "cp-ultra-pt21"]
        plan = self.service.prepare_plan("in-game", "cyberpunk-2077", factors)
        source = plan.pop("catalog_source")
        self.assertTrue(plan.pop("comparison_ready"))
        self.assertEqual(plan.pop("fg_preflight")["status"], "PASS")
        self.assertEqual(plan, self.service._backend.plan_overhead(self.service._snapshot, "in-game", "cyberpunk-2077", factors))
        self.assertEqual(len(plan["cases"]), 4)
        self.assertTrue({"reshade", "cet", "ultraplus"} <= set(plan["always_on"]))
        self.assertTrue(all(case["always_on"] == plan["always_on"] for case in plan["cases"]))
        self.assertEqual(plan["execution"], "none")
        self.assertFalse(plan["metrics_calculated"])
        self.assertTrue(all(value is None for value in plan["measured_metrics"].values()))
        self.assertTrue(all(value is None for case in plan["cases"] for value in case["measured_metrics"].values()))
        self.assertTrue(source["planning_only"])

    def test_factors_and_plan_returns_detached(self):
        factors = ["rhi"]
        plan = self.service.prepare_plan("process-idle", factors=factors)
        factors.append("reshade")
        plan["measured_metrics"]["cpu_time_s"] = 900
        fresh = self.service.prepare_plan("process-idle", factors=["rhi"])
        self.assertEqual(fresh["factors"], ["rhi"])
        self.assertIsNone(fresh["measured_metrics"]["cpu_time_s"])

    def test_unsupported_plan_stays_blocked(self):
        for scope, game, factors in (("in-game", "cyberpunk-2077", ["cp-ultra-highest"]),
                                     ("in-game", "skyrim-se", ["skyrim-pd-mfg"]),
                                     ("process-idle", None, ["dlss-switcher-unresolved"])):
            plan = self.service.prepare_plan(scope, game, factors)
            self.assertEqual(plan["status"], "blocked")
            self.assertEqual(plan["cases"], [])
            self.assertEqual(plan["execution"], "none")

    def test_actions_remain_declaration_only(self):
        for node in self.service.list_nodes():
            for action in self.service.details(node["id"])["declared_actions"]:
                self.assertEqual(action["execution"], "declaration-only")
                self.assertNotIn("command", action)

    def test_changed_catalog_refused_until_explicit_reload(self):
        old_revision = self.service.revision
        data = json.loads(self.raw)
        data["components"][0]["name"] += " (updated source)"
        self.write_catalog(data)
        self.assert_all_refuse()
        self.assertEqual(self.service.revision, old_revision)
        summary = self.service.reload()
        self.assertNotEqual(summary["revision"], old_revision)
        self.assertTrue(self.service.list_nodes())

    def test_restoring_old_bytes_does_not_silently_restore_current_state(self):
        self.path.write_bytes(self.raw + b" ")
        self.assert_all_refuse()
        self.path.write_bytes(self.raw)
        self.assert_all_refuse()
        self.service.reload()
        self.assertTrue(self.service.list_nodes())

    def test_missing_catalog_and_failed_reload_invalidate_snapshot(self):
        self.path.unlink()
        self.assert_all_refuse()
        with self.assertRaises(bridge.CatalogBridgeError):
            self.service.reload()
        self.path.write_bytes(self.raw)
        self.assert_all_refuse()
        self.service.reload()
        self.assertTrue(self.service.list_nodes())

    def test_invalid_reload_has_no_last_good_current_fallback(self):
        self.path.write_text("{}", encoding="utf-8")
        with self.assertRaises(bridge.CatalogBridgeError):
            self.service.reload()
        self.assert_all_refuse()
        self.path.write_bytes(self.raw)
        self.assert_all_refuse()

    def test_duplicate_keys_and_nonfinite_json_refused(self):
        for raw in (b'{"schema_version":1,"schema_version":1}', b'{"x":NaN}'):
            self.path.write_bytes(raw)
            with self.assertRaises(bridge.CatalogBridgeError):
                self.service.reload()
            self.assert_all_refuse()

    def test_oversized_source_rejected(self):
        self.path.write_bytes(b" " * (bridge.MAX_SOURCE_BYTES + 1))
        with self.assertRaises(bridge.CatalogBridgeError):
            self.service.reload()
        self.assert_all_refuse()

    def test_overbudget_list_shapes_refused_before_backend_validation(self):
        data = {"schema_version": 1, "status": "planning-foundation", "components": [{}] * 100,
                "games": [{}] * 100, "features": [], "relationships": [{}] * 300, "actions": []}
        self.write_catalog(data)
        self.assertLess(self.path.stat().st_size, bridge.MAX_SOURCE_BYTES)
        backend = self.service._backend
        with mock.patch.object(bridge, "_load_backend", return_value=backend), \
                mock.patch.object(backend, "validate", side_effect=AssertionError("Expensive validator must not run")) as validate:
            with self.assertRaisesRegex(bridge.CatalogBridgeError, "Catalog exceeds integration validation work budget"):
                self.service.reload()
            validate.assert_not_called()
        self.assert_all_refuse()

    def test_default_catalog_passes_work_budget_and_backend_validation(self):
        backend = self.service._backend
        with mock.patch.object(bridge, "_load_backend", return_value=backend), \
                mock.patch.object(backend, "validate", wraps=backend.validate) as validate:
            summary = self.service.reload()
            validate.assert_called_once()
        self.assertEqual(summary["revision"], hashlib.sha256(self.raw).hexdigest())
        self.assertTrue(self.service.list_nodes())

    def test_backend_change_refused_and_import_does_not_write_cache(self):
        backend_path = self.directory / "Game-Tool-Catalog.py"
        original = (SCRIPTS / "Game-Tool-Catalog.py").read_bytes()
        backend_path.write_bytes(original)
        with mock.patch.object(bridge, "_BACKEND_PATH", backend_path):
            service = bridge.CatalogService(self.path)
            self.assertFalse((self.directory / "__pycache__").exists())
            backend_path.write_bytes(original + b"\n# updated source\n")
            with self.assertRaises(bridge.CatalogBridgeError):
                service.details("rhi")
            service.reload()
            self.assertTrue(service.list_nodes())
            self.assertFalse((self.directory / "__pycache__").exists())

    def test_backend_version_mismatch_rejected(self):
        backend_path = self.directory / "Game-Tool-Catalog.py"
        raw = (SCRIPTS / "Game-Tool-Catalog.py").read_bytes()
        backend_path.write_bytes(raw.replace(b'VERSION = "0.1.1"', b'VERSION = "9.9.9"', 1))
        with mock.patch.object(bridge, "_BACKEND_PATH", backend_path):
            with self.assertRaises(bridge.CatalogBridgeError):
                self.service.reload()
        self.assert_all_refuse()

    def test_change_during_backend_call_refused(self):
        original = self.service._backend.show_node

        def changed(catalog, identifier):
            self.path.write_bytes(self.raw + b" ")
            return original(catalog, identifier)

        with mock.patch.object(self.service._backend, "show_node", side_effect=changed):
            with self.assertRaises(bridge.CatalogBridgeError):
                self.service.details("rhi")
        self.assert_all_refuse()

    def test_service_reads_do_not_modify_sources(self):
        before = self.path.read_bytes()
        before_stat = self.path.stat().st_mtime_ns
        self.service.options()
        self.service.list_nodes()
        self.service.details("renodx-devkit")
        self.service.prepare_plan("process-idle", factors=["rhi"])
        self.service.reload()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.path.stat().st_mtime_ns, before_stat)

    def test_dynamic_or_unknown_gate_blocks_and_suppresses_cases(self):
        for mode in ("dynamic", "unknown", "configured-only"):
            self.fg_spy.side_effect = lambda scope, game, *a, **kw: {
                "schema_version": 1, "status": "BLOCKED", "can_compare": False,
                "scope": scope, "game_id": game, "reasons": [mode], "execution": "none"}
            plan = self.service.prepare_plan("in-game", "cyberpunk-2077", ["cp-renodx-hdr"])
            self.assertEqual(plan["status"], "blocked")
            self.assertFalse(plan["comparison_ready"])
            self.assertEqual(plan["cases"], [])
            self.assertEqual(plan["suppressed_case_count"], 2)
            self.assertIn(mode, plan["blockers"][-1])
            self.assertTrue(all(v is None for v in plan["measured_metrics"].values()))

    def test_browse_reload_and_import_have_no_fg_reads(self):
        self.service.reload()
        self.service.options()
        self.service.list_nodes()
        self.service.details("rhi")
        self.fg_spy.assert_not_called()

    def test_each_preflight_and_plan_uses_new_observation(self):
        self.service.fg_preflight("in-game", "cyberpunk-2077")
        self.service.prepare_plan("in-game", "cyberpunk-2077", ["cp-renodx-hdr"])
        self.service.prepare_plan("in-game", "cyberpunk-2077", ["cp-renodx-hdr"])
        self.assertEqual(self.fg_spy.call_count, 3)

    def test_unknown_game_refuses_before_inspection(self):
        result = self.service.fg_preflight("in-game", "not-a-game")
        self.assertFalse(result["can_compare"])
        self.fg_spy.assert_not_called()

    def test_invalid_idle_game_selection_retains_structural_blocked_plan(self):
        result = self.service.prepare_plan("process-idle", "cyberpunk-2077", ["rhi"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["cases"], [])
        self.fg_spy.assert_not_called()

    def test_inspection_target_paths_forwarded_not_stored_in_plan(self):
        plan = self.service.prepare_plan("in-game", "cyberpunk-2077", ["cp-renodx-hdr"],
            executable="private-renderer-path", native_settings_path="private-settings-path")
        self.fg_spy.assert_called_once_with("in-game", "cyberpunk-2077",
            "private-renderer-path", "private-settings-path")
        self.assertNotIn("private-", json.dumps(plan))


class FgLoaderContracts(unittest.TestCase):
    def mocked_load(self, receipt):
        def populate(loader, module):
            module.VERSION = "0.1.0"
            if module.__name__ == "GameFgInspector":
                module.inspect_fg = lambda *a, **kw: {"fixture": True}
            else:
                module.assess_fg = lambda *a, **kw: deepcopy(receipt)
        return mock.patch.object(bridge._SnapshotLoader, "exec_module", populate)

    def test_minimal_mismatched_or_untrusted_pass_cannot_release_gate(self):
        base = {"schema_version": 1, "status": "PASS", "can_compare": True,
                "scope": "in-game", "game_id": "cyberpunk-2077", "execution": "none",
                "reasons": [], "reason_codes": [], "policy": {"version": "0.1.0"},
                "provenance": {"trusted": True}}
        for receipt in ({"schema_version": 1, "status": "PASS", "can_compare": True},
                        {**base, "game_id": "skyrim-se"}, {**base, "scope": "process-idle"},
                        {**base, "execution": "run"}, {**base, "reasons": "bad"},
                        {**base, "provenance": {"trusted": False}}):
            with mock.patch.object(bridge, "_read_source", return_value=(b"fixture", "a" * 64)), self.mocked_load(receipt):
                result = bridge._run_fg_preflight("in-game", "cyberpunk-2077")
            self.assertEqual(result["reason_codes"], ["FG_POLICY_INVALID"])
            self.assertFalse(result["can_compare"])

    def test_loader_restores_existing_module_entries_after_failure(self):
        sentinels = {name: object() for name in bridge._FG_PATHS}
        with mock.patch.dict(sys.modules, sentinels), \
                mock.patch.object(bridge, "_read_source", return_value=(b"broken", "a" * 64)), \
                mock.patch.object(bridge._SnapshotLoader, "exec_module", side_effect=SyntaxError("fixture")):
            result = bridge._run_fg_preflight("in-game", "cyberpunk-2077")
            self.assertTrue(all(sys.modules[name] is value for name, value in sentinels.items()))
        self.assertFalse(result["can_compare"])

    def test_drift_during_check_blocks_receipt(self):
        receipt = {"schema_version": 1, "status": "BLOCKED", "can_compare": False}
        with mock.patch.object(bridge, "_read_source", side_effect=[(b"fixture", "a" * 64),
                (b"fixture", "b" * 64), (b"new", "c" * 64)]), self.mocked_load(receipt):
            result = bridge._run_fg_preflight("in-game", "cyberpunk-2077")
        self.assertEqual(result["reason_codes"], ["FG_SOURCE_CHANGED"])

    def test_idle_does_not_read_or_load_adapter_sources(self):
        with mock.patch.object(bridge, "_read_source", side_effect=AssertionError("No reads")):
            result = bridge._run_fg_preflight("process-idle", None)
        self.assertEqual(result["status"], "NOT_APPLICABLE")

    def test_missing_optional_fg_module_blocks_without_exception_or_private_path(self):
        with mock.patch.object(bridge, "_FG_PATHS", {"GameFgInspector": Path("missing-private-adapter")}):
            result = bridge._run_fg_preflight("in-game", "cyberpunk-2077")
        self.assertFalse(result["can_compare"])
        self.assertEqual(result["reason_codes"], ["FG_ADAPTER_UNAVAILABLE"])
        self.assertNotIn("missing-private", json.dumps(result))

    def test_source_loader_does_not_accept_catalog_selected_code(self):
        self.assertEqual(set(bridge._FG_PATHS), {"GameFgInspector", "GameFgPreflight"})
        self.assertTrue(all(p.parent == SCRIPTS for p in bridge._FG_PATHS.values()))


if __name__ == "__main__":
    unittest.main()
