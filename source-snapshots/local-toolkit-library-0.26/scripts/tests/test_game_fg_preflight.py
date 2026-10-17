"""Pure policy/issuance fixtures; no live FG, hardware, game or benchmark claims.

Prepared PASS cases mock the trusted issuer in-process. They are not an external
JSON import route or evidence that the current inspector has a runtime adapter.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
from types import MappingProxyType, ModuleType, SimpleNamespace
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
POLICY_RAW = (SCRIPTS / "GameFgPreflight.py").read_bytes()
policy = ModuleType("GameFgPreflight_policy_fixture")
policy.__file__ = str(SCRIPTS / "GameFgPreflight.py")
exec(compile(POLICY_RAW, policy.__file__, "exec"), policy.__dict__)
NOW = datetime(2026, 10, 11, 12, 0, 0, tzinfo=timezone.utc)
NOW_TEXT = "2026-10-11T12:00:00Z"
PATH_HASH = "a" * 64
MODE_NAMES = MappingProxyType({0: "override-disabled", 1: "off", 2: "on", 3: "auto", 4: "dynamic"})


def layer(mode="override-disabled", location="current_profile", match="exact-path"):
    raw_mode = next(raw for raw, name in MODE_NAMES.items() if name == mode)
    settings = {}
    for name, raw in (("mode", raw_mode), ("frame_count", 0),
                      ("dynamic_max_count", 0), ("dynamic_target", 0)):
        settings[name] = {"status": "observed", "raw_value": raw,
                          "enum_name": mode if name == "mode" else None,
                          "location": location, "predefined": False}
    return {"status": "observed", "configured_mode": mode, "fixed_multiplier": None,
            "frame_count_raw": 0, "dynamic_target_raw": 0, "dynamic_max_count_raw": 0,
            "profile_match": match, "source_id": "nvapi-system-drs", "settings": settings,
            "reasons": []}


def prepared_payload(mode="fixed", multiplier=2):
    """Hypothetical reviewed runtime-proof shape, not actual inspector output."""
    multiplier = multiplier if mode == "fixed" else None
    return {
        "schema_version": 1,
        "provider": {"name": "GameFgInspector", "version": "0.1.0", "read_only": True},
        "observed_at_utc": NOW_TEXT,
        "target": {"game_id": "cyberpunk-2077", "executable": "Cyberpunk2077.exe",
                   "executable_match": "exact-path", "executable_path_sha256": PATH_HASH},
        "native": {"status": "observed", "configured_mode": mode, "multiplier": multiplier,
                   "source_id": "native-settings-json", "source_scope": "current-known-path",
                   "source_sha256": "b" * 64, "reasons": []},
        "driver": {"status": "observed", "version": "617.42",
                   "global": layer(location="global_profile", match="unknown"),
                   "per_application": layer(), "effective_configuration": layer(), "reasons": []},
        "effective": {"mode": mode, "fixed_multiplier": multiplier,
                      "dynamic_mfg": "inactive", "verification": "runtime-verified"},
        "runtime": {"status": "observed", "mode": mode, "fixed_multiplier": multiplier,
                    "dynamic_mfg": "inactive", "game_id": "cyberpunk-2077",
                    "executable": "Cyberpunk2077.exe", "executable_path_sha256": PATH_HASH,
                    "source_id": "reviewed-runtime-proof",
                    "coverage": ["effective-fg-mode", "dynamic-mfg", "fg-owners", "target-identity"]},
        "sources": [
            {"id": "native-settings-json", "kind": "configured-observation",
             "version": "cyberpunk-usersettings-v1", "observed_at_utc": NOW_TEXT},
            {"id": "nvapi-system-drs", "kind": "configured-observation",
             "version": "617.42", "observed_at_utc": NOW_TEXT},
            {"id": "reviewed-runtime-proof", "kind": "runtime-observation",
             "version": "pure-fixture-not-installed", "observed_at_utc": NOW_TEXT},
        ], "reasons": [],
    }


class IssuedFixture(dict):
    """Only the mock issuer below accepts registered, unchanged instances."""


class PolicyContracts(unittest.TestCase):
    def setUp(self):
        self.issued = {}
        self.inspector = SimpleNamespace(
            VERSION="0.1.0", SUPPORTED_GAMES=MappingProxyType({
                "cyberpunk-2077": "Cyberpunk2077.exe", "skyrim-special-edition": "SkyrimSE.exe"}),
            MODE_NAMES=MODE_NAMES, is_inspector_observation=self.is_issued)
        patcher = mock.patch.dict(sys.modules, {"GameFgInspector": self.inspector})
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).digest()

    def issue(self, payload=None):
        result = IssuedFixture(deepcopy(payload if payload is not None else prepared_payload()))
        self.issued[id(result)] = (result, self.digest(result))
        return result

    def is_issued(self, value):
        try:
            registered, digest = self.issued.get(id(value), (None, None))
            return type(value) is IssuedFixture and registered is value and digest == self.digest(value)
        except (TypeError, ValueError):
            return False

    def assess(self, payload=None, now=NOW, game="cyberpunk-2077", scope="in-game"):
        return policy.assess_fg(scope, game, self.issue(payload), now)

    def assert_blocked(self, result, code=None):
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIs(result["can_compare"], False)
        self.assertTrue(result["reasons"])
        if code:
            self.assertIn(code, result["reason_codes"])
        json.dumps(result, allow_nan=False)

    def altered(self, path, value, code=None):
        data = prepared_payload()
        node = data
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
        result = self.assess(data)
        self.assert_blocked(result, code)
        return result

    def test_prepared_fixed_pass_is_fg_only_and_nonexecuting(self):
        result = self.assess()
        self.assertEqual(result["status"], "PASS")
        self.assertIs(result["can_compare"], True)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["policy"]["version"], "0.1.0")
        self.assertIs(result["policy"]["fg_gate_only"], True)
        self.assertEqual(result["execution"], "none")
        self.assertEqual(result["memory_status"], "not_assessed")
        self.assertIs(result["provenance"]["trusted"], True)
        self.assertEqual(result["scope"], "in-game")
        self.assertEqual(result["game_id"], "cyberpunk-2077")
        self.assertEqual(result["reason_codes"], ["verified-fixed"])

    def test_prepared_off_pass(self):
        result = self.assess(prepared_payload("off"))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["reason_codes"], ["verified-off"])

    def test_idle_has_no_issuer_or_observation_requirement(self):
        with mock.patch.dict(sys.modules, {"GameFgInspector": None}):
            result = policy.assess_fg("process-idle", None, now=NOW)
        self.assertEqual(result["status"], "NOT_APPLICABLE")
        self.assertIs(result["can_compare"], True)
        self.assertFalse(result["provenance"]["trusted"])

    def test_adaptive_experience_not_a_silent_bypass(self):
        self.assert_blocked(self.assess(scope="adaptive-fg-experience"), "unsupported-scope")

    def test_unknown_scope_blocked(self):
        for scope in (None, "", "benchmark", {}, [], 1):
            with self.subTest(scope=scope):
                self.assert_blocked(self.assess(scope=scope), "unsupported-scope")

    def test_unknown_or_malformed_game_blocked(self):
        for game in (None, {}, "unsupported", "Cyberpunk", "../cyberpunk-2077"):
            with self.subTest(game=game):
                self.assert_blocked(self.assess(game=game), "unsupported-game")

    def test_missing_observation_blocked(self):
        self.assert_blocked(policy.assess_fg("in-game", "cyberpunk-2077", now=NOW), "untrusted-observation")

    def test_plain_dict_and_json_roundtrip_are_not_trusted(self):
        issued = self.issue()
        for value in (prepared_payload(), dict(issued), json.loads(json.dumps(issued))):
            self.assert_blocked(policy.assess_fg("in-game", "cyberpunk-2077", value, NOW), "untrusted-observation")

    def test_unregistered_same_class_is_not_trusted(self):
        self.assert_blocked(policy.assess_fg("in-game", "cyberpunk-2077", IssuedFixture(prepared_payload()), NOW), "untrusted-observation")

    def test_mutated_issued_observation_rejected(self):
        issued = self.issue()
        issued["effective"]["dynamic_mfg"] = "active"
        self.assert_blocked(policy.assess_fg("in-game", "cyberpunk-2077", issued, NOW), "untrusted-observation")

    def test_checker_exception_or_nonboolean_cannot_pass(self):
        for checker in (mock.Mock(side_effect=RuntimeError("fixture failure")), lambda _: 1, lambda _: "yes", lambda _: None):
            with mock.patch.object(self.inspector, "is_inspector_observation", checker):
                self.assert_blocked(policy.assess_fg("in-game", "cyberpunk-2077", self.issue(), NOW), "untrusted-observation")

    def test_missing_or_unsupported_issuer_blocked(self):
        for issuer in (None, SimpleNamespace(VERSION="0.2.0"), SimpleNamespace(VERSION="0.1.0")):
            with mock.patch.dict(sys.modules, {"GameFgInspector": issuer}):
                self.assert_blocked(policy.assess_fg("in-game", "cyberpunk-2077", self.issue(), NOW), "inspector-unavailable")

    def test_mappingproxy_supported_games_and_modes_work(self):
        self.assertIsInstance(self.inspector.SUPPORTED_GAMES, MappingProxyType)
        self.assertEqual(self.assess()["status"], "PASS")

    def test_invalid_issuer_game_identity_fails_closed(self):
        for executable in (None, "", "folder/Cyberpunk2077.exe", "folder\\Cyberpunk2077.exe"):
            with mock.patch.object(self.inspector, "SUPPORTED_GAMES", {"cyberpunk-2077": executable}):
                self.assert_blocked(self.assess(), "invalid-game-adapter")

    def test_schema_version_exact_integer(self):
        for version in (None, 0, 2, True, "1", 1.0):
            self.altered(["schema_version"], version, "unsupported-schema")

    def test_provider_name_version_and_read_only_required(self):
        for field, value in (("name", "fixture-provider"), ("version", "0.2.0"), ("read_only", False), ("read_only", 1)):
            self.altered(["provider", field], value, "invalid-provider")

    def test_provider_missing_or_bad_shape(self):
        for value in (None, [], "GameFgInspector"):
            self.altered(["provider"], value, "invalid-provider")

    def test_manual_flags_never_override(self):
        for name in ("manual_override", "force_pass", "skip_checks", "test_fixture"):
            data = prepared_payload()
            data[name] = True
            self.assert_blocked(self.assess(data), "unsupported-approval")

    def test_stale_observation_blocked(self):
        self.assert_blocked(self.assess(now=NOW + timedelta(seconds=121)), "stale-observation")

    def test_freshness_boundary_and_expiry(self):
        result = self.assess(now=NOW + timedelta(seconds=120))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["provenance"]["age_seconds"], 120)
        self.assertEqual(result["provenance"]["valid_until_utc"], "2026-10-11T12:02:00.000000Z")

    def test_any_future_observation_blocked(self):
        self.assert_blocked(self.assess(now=NOW - timedelta(microseconds=1)), "future-observation")

    def test_invalid_observation_timestamp(self):
        for value in (None, "yesterday", "2026-10-11T12:00:00", "2026-10-11T15:00:00+03:00", "x" * 65):
            self.altered(["observed_at_utc"], value, "invalid-observation-time")

    def test_invalid_assessment_time(self):
        for value in (True, 123, "now", datetime(2026, 10, 11, 12)):
            self.assert_blocked(self.assess(now=value), "invalid-assessment-time")

    def test_aware_assessment_timezone_is_normalized(self):
        result = self.assess(now=NOW.astimezone(timezone(timedelta(hours=3))))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["provenance"]["age_seconds"], 0)

    def test_exact_target_game_executable_match_required(self):
        for field, value in (("game_id", "skyrim-special-edition"), ("executable", "SkyrimSE.exe"), ("executable_match", "basename-only"), ("executable_path_sha256", "a")):
            self.altered(["target", field], value, "target-identity-unverified")

    def test_windows_executable_case_insensitive(self):
        data = prepared_payload()
        data["target"]["executable"] = "CYBERPUNK2077.EXE"
        data["runtime"]["executable"] = "cyberpunk2077.exe"
        self.assertEqual(self.assess(data)["status"], "PASS")

    def test_missing_target_and_sections_fail_closed(self):
        for section in ("target", "native", "driver", "effective", "runtime"):
            for value in (None, [], "unknown"):
                self.altered([section], value)

    def test_configuration_only_never_passes(self):
        data = prepared_payload()
        data["effective"] = {"mode": "unknown", "fixed_multiplier": None,
                             "dynamic_mfg": "unknown", "verification": "configured-only"}
        data["runtime"] = {"status": "not_observed", "mode": None, "coverage": None}
        result = self.assess(data)
        self.assert_blocked(result, "effective-fg-unverified")
        self.assertIn("runtime-fg-unverified", result["reason_codes"])
        self.assertNotIn("conflicting-runtime-fg", result["reason_codes"])
        self.assertNotIn("runtime-identity-unverified", result["reason_codes"])
        self.assertNotIn("conflicting-configured-fg", result["reason_codes"])

    def test_unknown_effective_mode_is_not_a_runtime_conflict(self):
        data = prepared_payload()
        data["driver"]["per_application"] = layer("off")
        data["driver"]["effective_configuration"] = layer("off")
        data["effective"] = {"mode": "unknown", "fixed_multiplier": None,
                             "dynamic_mfg": "unknown", "verification": "configured-only"}
        data["runtime"] = {"status": "not_observed", "mode": None, "coverage": None}
        result = self.assess(data)
        self.assert_blocked(result, "effective-fg-unverified")
        self.assertNotIn("conflicting-configured-fg", result["reason_codes"])

    def test_native_menu_only_with_override_disabled_not_fg_off(self):
        data = prepared_payload("off")
        data["effective"]["verification"] = "configured-only"
        data["runtime"]["status"] = "not_observed"
        self.assert_blocked(self.assess(data), "effective-fg-unverified")

    def test_native_current_source_and_hash_required(self):
        for field, value in (("status", "unknown"), ("source_scope", "caller-selected-file"), ("source_scope", "unknown"), ("source_sha256", None), ("source_id", "imported-json")):
            self.altered(["native", field], value, "native-state-unverified")

    def test_native_and_effective_multipliers_strict(self):
        for value in (None, True, 0, 1, 17, 2.0, "2"):
            self.altered(["native", "multiplier"], value, "invalid-native-multiplier")
            self.altered(["effective", "fixed_multiplier"], value, "invalid-effective-multiplier")

    def test_off_cannot_carry_a_multiplier(self):
        data = prepared_payload("off")
        data["native"]["multiplier"] = 2
        data["effective"]["fixed_multiplier"] = 2
        self.assert_blocked(self.assess(data), "invalid-effective-multiplier")

    def test_driver_partial_and_version_unknown_blocked(self):
        self.altered(["driver", "status"], "partial", "driver-state-unverified")
        self.altered(["driver", "version"], None, "driver-state-unverified")

    def test_unknown_driver_layers_blocked(self):
        for name in ("global", "per_application", "effective_configuration"):
            self.altered(["driver", name, "status"], "unknown", "driver-" + name + "-unverified")

    def test_basename_driver_profile_is_not_exact(self):
        self.altered(["driver", "per_application", "profile_match"], "basename-only", "driver-profile-unverified")
        self.altered(["driver", "effective_configuration", "profile_match"], "unknown", "driver-profile-unverified")

    def test_effective_dynamic_and_auto_modes_blocked(self):
        for mode in ("dynamic", "auto"):
            data = prepared_payload()
            data["driver"]["per_application"] = layer(mode)
            data["driver"]["effective_configuration"] = layer(mode)
            self.assert_blocked(self.assess(data), "adaptive-fg-configured")

    def test_overridden_global_dynamic_does_not_claim_active(self):
        data = prepared_payload("off")
        data["driver"]["global"] = layer("dynamic", location="global_profile", match="unknown")
        data["driver"]["per_application"] = layer("off")
        data["driver"]["effective_configuration"] = layer("off")
        self.assertEqual(self.assess(data)["status"], "PASS")

    def test_inherited_global_dynamic_blocks(self):
        data = prepared_payload()
        data["driver"]["global"] = layer("dynamic", location="global_profile", match="unknown")
        data["driver"]["per_application"] = layer("dynamic", location="global_profile")
        data["driver"]["effective_configuration"] = layer("dynamic", location="global_profile")
        self.assert_blocked(self.assess(data), "adaptive-fg-configured")

    def test_driver_raw_enum_and_mode_must_agree(self):
        self.altered(["driver", "effective_configuration", "settings", "mode", "raw_value"], 4, "conflicting-driver-mode")
        self.altered(["driver", "global", "settings", "mode", "enum_name"], "off", "conflicting-driver-mode")

    def test_unmapped_driver_mode_blocked(self):
        self.altered(["driver", "global", "settings", "mode", "raw_value"], 99, "conflicting-driver-mode")

    def test_driver_provenance_missing_or_bad_shape_blocked(self):
        for value in (None, {}, "observed"):
            self.altered(["driver", "effective_configuration", "settings"], value, "driver-setting-provenance-unverified")
        self.altered(["driver", "global", "settings", "mode", "predefined"], 1, "driver-setting-provenance-unverified")

    def test_raw_frame_count_never_relabels_multiplier(self):
        data = prepared_payload()
        for name in ("global", "per_application", "effective_configuration"):
            data["driver"][name]["frame_count_raw"] = 5
            data["driver"][name]["settings"]["frame_count"]["raw_value"] = 5
        result = self.assess(data)
        self.assertEqual(result["status"], "PASS")
        self.assertIsNone(result["driver"]["effective_configuration"]["fixed_multiplier"])
        self.assertEqual(result["effective"]["fixed_multiplier"], 2)
        self.altered(["driver", "effective_configuration", "fixed_multiplier"], 6, "unsupported-driver-multiplier")

    def test_driver_raw_fields_and_settings_conflict(self):
        self.altered(["driver", "global", "frame_count_raw"], 3, "conflicting-driver-setting")

    def test_driver_resolved_and_app_readbacks_conflict(self):
        data = prepared_payload()
        data["driver"]["per_application"] = layer("off")
        self.assert_blocked(self.assess(data), "conflicting-driver-inheritance")

    def test_inherited_global_readback_must_match(self):
        data = prepared_payload("off")
        data["driver"]["per_application"] = layer("off", location="global_profile")
        data["driver"]["effective_configuration"] = layer("off", location="global_profile")
        self.assert_blocked(self.assess(data), "conflicting-driver-inheritance")

    def test_effective_dynamic_status_must_be_inactive(self):
        for value in (None, "unknown", "active", "configured", False):
            self.altered(["effective", "dynamic_mfg"], value, "dynamic-mfg-unverified")

    def test_runtime_mode_multiplier_dynamic_conflicts(self):
        for field, value in (("mode", "off"), ("fixed_multiplier", 4), ("dynamic_mfg", "active")):
            self.altered(["runtime", field], value, "conflicting-runtime-fg")

    def test_runtime_identity_and_path_must_match(self):
        for field, value in (("game_id", "skyrim-special-edition"), ("executable", "SkyrimSE.exe"), ("executable_path_sha256", "c" * 64)):
            self.altered(["runtime", field], value, "runtime-identity-unverified")

    def test_runtime_coverage_and_proof_source_required(self):
        for value in (None, [], ["effective-fg-mode"], [None], "all"):
            self.altered(["runtime", "coverage"], value, "runtime-fg-unverified")
        self.altered(["runtime", "source_id"], ["not-a-source-id"], "runtime-fg-unverified")

    def test_source_shapes_and_test_fixture_kinds_rejected(self):
        for value in (None, [], {}, [None]):
            self.altered(["sources"], value, "invalid-sources")
        self.altered(["sources", 2, "kind"], "test-fixture", "invalid-sources")

    def test_unhashable_source_fields_fail_closed(self):
        for field in ("id", "kind", "version"):
            for value in ([], {}):
                self.altered(["sources", 2, field], value, "invalid-sources")

    def test_unhashable_layer_status_and_mode_fields_fail_closed(self):
        paths = (["provider", "name"], ["provider", "version"], ["provider", "read_only"],
                 ["native", "status"], ["native", "configured_mode"], ["native", "source_id"],
                 ["driver", "status"], ["driver", "effective_configuration", "configured_mode"],
                 ["effective", "mode"], ["effective", "dynamic_mfg"],
                 ["runtime", "status"], ["runtime", "source_id"], ["runtime", "coverage"])
        for path in paths:
            for value in ([], {}):
                with self.subTest(path=path, value=value):
                    self.altered(path, value)

    def test_all_driver_settings_need_observed_provenance(self):
        for name in ("global", "per_application", "effective_configuration"):
            for key in ("mode", "frame_count", "dynamic_max_count", "dynamic_target"):
                for field, value in (("status", "unknown"), ("raw_value", []),
                                     ("location", "unknown"), ("predefined", None)):
                    with self.subTest(layer=name, key=key, field=field):
                        self.altered(["driver", name, "settings", key, field], value,
                                     "driver-setting-provenance-unverified")

    def test_driver_boolean_raw_field_is_not_integer_zero(self):
        self.altered(["driver", "global", "frame_count_raw"], False, "conflicting-driver-setting")

    def test_source_versions_and_duplicate_ids_rejected(self):
        self.altered(["sources", 2, "version"], None, "invalid-sources")
        data = prepared_payload()
        data["sources"].append(deepcopy(data["sources"][0]))
        self.assert_blocked(self.assess(data), "invalid-sources")

    def test_each_observation_source_freshness_is_required(self):
        for value in ("2026-10-11T11:57:59Z", "2026-10-11T12:00:01Z", None):
            self.altered(["sources", 2, "observed_at_utc"], value, "noncurrent-source")

    def test_primary_documentation_may_be_historical_not_runtime(self):
        data = prepared_payload()
        data["sources"].append({"id": "official-docs", "kind": "primary-documentation",
                                "version": "pinned-source-revision", "observed_at_utc": None})
        self.assertEqual(self.assess(data)["status"], "PASS")
        data["sources"][2]["kind"] = "primary-documentation"
        self.assert_blocked(self.assess(data), "runtime-fg-unverified")

    def test_effective_off_driver_cannot_conflict_with_fixed_runtime(self):
        data = prepared_payload()
        data["driver"]["per_application"] = layer("off")
        data["driver"]["effective_configuration"] = layer("off")
        self.assert_blocked(self.assess(data), "conflicting-configured-fg")

    def test_without_override_native_and_runtime_must_match(self):
        data = prepared_payload()
        data["effective"]["fixed_multiplier"] = 4
        data["runtime"]["fixed_multiplier"] = 4
        self.assert_blocked(self.assess(data), "conflicting-configured-fg")

    def test_verified_override_keeps_native_and_effective_distinct(self):
        data = prepared_payload()
        data["driver"]["per_application"] = layer("on")
        data["driver"]["effective_configuration"] = layer("on")
        data["effective"]["fixed_multiplier"] = 4
        data["runtime"]["fixed_multiplier"] = 4
        result = self.assess(data)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["native"]["multiplier"], 2)
        self.assertEqual(result["effective"]["fixed_multiplier"], 4)

    def test_receipt_is_detached_and_preserves_evidence(self):
        issued = self.issue()
        result = policy.assess_fg("in-game", "cyberpunk-2077", issued, NOW)
        result["driver"]["global"]["configured_mode"] = "changed"
        result["provenance"]["sources"].clear()
        self.assertTrue(self.is_issued(issued))
        self.assertEqual(issued["driver"]["global"]["configured_mode"], "override-disabled")

    def test_malformed_nonjson_and_oversized_observations_block(self):
        for value in (float("nan"), object(), "x" * (policy.MAX_OBSERVATION_BYTES + 1)):
            data = prepared_payload()
            data["extra"] = value
            with mock.patch.object(self.inspector, "is_inspector_observation", return_value=True):
                self.assert_blocked(policy.assess_fg("in-game", "cyberpunk-2077", data, NOW), "invalid-observation")

    def test_policy_import_does_not_inspect_or_load_an_adapter(self):
        namespace = {"__name__": "isolated_policy_import"}
        with mock.patch.dict(sys.modules, {"GameFgInspector": None}), \
                mock.patch("builtins.open", side_effect=AssertionError("No policy file IO")):
            exec(compile(POLICY_RAW, "GameFgPreflight.py", "exec"), namespace)
        self.assertEqual(namespace["VERSION"], "0.1.0")


class ActualInspectorIntegration(unittest.TestCase):
    """Exact sibling source + mocked reads: verifies contract, not live hardware."""

    def setUp(self):
        source = SCRIPTS / "GameFgInspector.py"
        self.inspector = ModuleType("GameFgInspector")
        self.inspector.__file__ = str(source)
        exec(compile(source.read_bytes(), str(source), "exec"), self.inspector.__dict__)
        patcher = mock.patch.dict(sys.modules, {"GameFgInspector": self.inspector})
        patcher.start()
        self.addCleanup(patcher.stop)

    def observed(self):
        data = prepared_payload()
        reader = SimpleNamespace(observe=lambda *args: deepcopy(data["driver"]))
        with mock.patch.object(self.inspector, "_utc_now", return_value=NOW_TEXT), \
                mock.patch.object(self.inspector, "_target", return_value=(data["target"], "fixture-executable", [])), \
                mock.patch.object(self.inspector, "_read_native", return_value=data["native"]), \
                mock.patch.object(self.inspector, "_NvapiReader", return_value=reader):
            return self.inspector.inspect_fg("cyberpunk-2077")

    def test_real_inspector_observation_trusted_but_not_runtime_verified(self):
        observation = self.observed()
        result = policy.assess_fg("in-game", "cyberpunk-2077", observation, NOW)
        self.assertTrue(result["provenance"]["trusted"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertNotIn("inspector-unavailable", result["reason_codes"])
        self.assertIn("effective-fg-unverified", result["reason_codes"])
        self.assertEqual(result["runtime"]["status"], "not_observed")

    def test_real_inspector_json_and_mutation_rejected(self):
        observation = self.observed()
        imported = json.loads(json.dumps(observation))
        result = policy.assess_fg("in-game", "cyberpunk-2077", imported, NOW)
        self.assertIn("untrusted-observation", result["reason_codes"])
        observation["effective"]["mode"] = "off"
        result = policy.assess_fg("in-game", "cyberpunk-2077", observation, NOW)
        self.assertIn("untrusted-observation", result["reason_codes"])

    def test_constructor_does_not_issue_a_real_observation(self):
        unregistered = self.inspector._IssuedObservation(prepared_payload())
        result = policy.assess_fg("in-game", "cyberpunk-2077", unregistered, NOW)
        self.assertIn("untrusted-observation", result["reason_codes"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
