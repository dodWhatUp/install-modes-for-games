"""Pure, fail-closed FG gate; never inspect hardware or execute a comparison.

Only a current, sealed observation issued by the already-loaded exact sibling
``GameFgInspector`` is eligible. Plain dictionaries, imported JSON and manual
approval flags are not observation routes. The host loads the reviewed inspector
under its canonical module name before an explicit read-only check.

The initial inspector reports configuration, not runtime verification. Its actual
observations therefore remain BLOCKED. The runtime-proof contract below is a
prepared requirement for a future reviewed adapter, not an implemented probe.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import json
import re
import sys


VERSION = "0.1.0"
SCHEMA_VERSION = 1
INSPECTOR_VERSION = "0.1.0"
MAX_AGE_SECONDS = 120
MAX_OBSERVATION_BYTES = 128 * 1024
_COVERAGE = {"effective-fg-mode", "dynamic-mfg", "fg-owners", "target-identity"}
_SOURCE_KINDS = {"primary-documentation", "configured-observation", "runtime-observation"}
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")


def _timestamp(value):
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("An explicit UTC timestamp is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("An explicit UTC timestamp is required")
    return parsed.astimezone(timezone.utc)


def _utc_now(value):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, str):
        return _timestamp(value)
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.astimezone(timezone.utc)
    raise ValueError("Assessment time must be timezone-aware")


def _stamp(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _text(value, maximum=160):
    return isinstance(value, str) and 0 < len(value) <= maximum and not any(
        ord(character) < 32 for character in value
    )


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _digest(value):
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _inspector():
    """No import or inspection on policy load/evaluation; missing issuer blocks."""
    module = sys.modules.get("GameFgInspector")
    if module is None or getattr(module, "VERSION", None) != INSPECTOR_VERSION:
        return None
    if not callable(getattr(module, "is_inspector_observation", None)):
        return None
    if not isinstance(getattr(module, "SUPPORTED_GAMES", None), Mapping):
        return None
    if not isinstance(getattr(module, "MODE_NAMES", None), Mapping):
        return None
    return module


def assess_fg(scope, game, observation=None, now=None):
    """Return a JSON-compatible gate receipt without any mutation or inspection.

    ``scope`` is ``process-idle`` (non-rendering only) or ``in-game``. ``game`` is
    an exact inspector-supported game ID. ``now`` accepts an aware datetime or
    explicit UTC ISO timestamp and exists for deterministic pure tests. There is
    no freshness, provenance or manual-approval override parameter.

    PASS is this FG gate only, not workload/memory/metric acceptance or permission
    to launch, change settings, activate a collector or execute a comparison.
    """
    safe_game = game if isinstance(game, str) and _SLUG.fullmatch(game) else None
    safe_scope = scope if scope in ("process-idle", "in-game") else None
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "policy": {"name": "GameFgPreflight", "version": VERSION,
                   "max_age_seconds": MAX_AGE_SECONDS, "fg_gate_only": True},
        "scope": safe_scope, "game_id": safe_game, "status": "BLOCKED",
        "can_compare": False, "reasons": [], "reason_codes": [],
        "native": None, "driver": None, "effective": None, "runtime": None,
        "provenance": {"trusted": False, "provider": None,
                       "observed_at_utc": None, "assessed_at_utc": None,
                       "age_seconds": None, "valid_until_utc": None, "sources": []},
        "execution": "none", "memory_status": "not_assessed",
        "limitations": ["FG gate only; workload, memory and metric gates remain separate.",
                        "No launch, settings change, capture or comparison is authorized.",
                        "This receipt describes one observation, not continuous monitoring."],
    }

    def block(code, message):
        if code not in receipt["reason_codes"]:
            receipt["reason_codes"].append(code)
            receipt["reasons"].append(message)

    try:
        assessed = _utc_now(now)
        receipt["provenance"]["assessed_at_utc"] = _stamp(assessed)
    except (ValueError, TypeError, OverflowError):
        block("invalid-assessment-time", "Assessment time is invalid; no current verdict is possible.")
        return receipt
    if safe_scope is None:
        block("unsupported-scope", "Only non-rendering process-idle and ordinary in-game scopes are supported.")
        return receipt
    if scope == "process-idle":
        receipt.update(status="NOT_APPLICABLE", can_compare=True)
        receipt["reasons"] = ["FG is not applicable to a process-idle test with no game-rendering workload."]
        receipt["reason_codes"] = ["non-rendering-scope"]
        return receipt
    issuer = _inspector()
    if issuer is None:
        block("inspector-unavailable", "The reviewed read-only observation issuer is unavailable.")
        return receipt
    if safe_game is None or game not in issuer.SUPPORTED_GAMES:
        block("unsupported-game", "The requested game has no reviewed FG identity adapter.")
        return receipt
    expected_executable = issuer.SUPPORTED_GAMES.get(game)
    if not _text(expected_executable) or "/" in expected_executable or "\\" in expected_executable:
        block("invalid-game-adapter", "The reviewed game identity adapter has an invalid executable identity.")
        return receipt
    try:
        trusted = issuer.is_inspector_observation(observation) is True
    except Exception:
        trusted = False
    if not trusted:
        block("untrusted-observation", "A fresh sealed inspector observation is required; imported JSON or manual approval is not evidence.")
        return receipt
    if not isinstance(observation, dict):
        block("invalid-observation", "The observation has an unsupported shape.")
        return receipt
    try:
        encoded = json.dumps(dict(observation), allow_nan=False, ensure_ascii=True)
        if len(encoded) > MAX_OBSERVATION_BYTES:
            raise ValueError("Observation too large")
        data = json.loads(encoded)
    except Exception:
        block("invalid-observation", "The observation cannot be detached safely.")
        return receipt
    receipt["provenance"]["trusted"] = True
    if any(key in data for key in ("manual_override", "force_pass", "skip_checks", "test_fixture")):
        block("unsupported-approval", "Manual approval or fixture flags cannot substitute for current evidence.")
        return receipt
    if type(data.get("schema_version")) is not int or data["schema_version"] != SCHEMA_VERSION:
        block("unsupported-schema", "The observation schema is unsupported.")
        return receipt
    provider = data.get("provider")
    if not isinstance(provider, dict) or provider.get("name") != "GameFgInspector" or \
            provider.get("version") != INSPECTOR_VERSION or provider.get("read_only") is not True:
        block("invalid-provider", "Provider identity/version or read-only provenance is invalid.")
        return receipt
    receipt["provenance"]["provider"] = provider
    try:
        observed = _timestamp(data.get("observed_at_utc"))
        age = (assessed - observed).total_seconds()
        receipt["provenance"].update(observed_at_utc=_stamp(observed), age_seconds=age,
                                     valid_until_utc=_stamp(observed + timedelta(seconds=MAX_AGE_SECONDS)))
        if age < 0:
            block("future-observation", "The observation timestamp is in the future.")
        elif age > MAX_AGE_SECONDS:
            block("stale-observation", "The observation expired; an explicit fresh inspection is required.")
    except (ValueError, TypeError, OverflowError):
        observed = None
        block("invalid-observation-time", "The observation needs a valid explicit UTC timestamp.")
    target = data.get("target")
    if not isinstance(target, dict) or target.get("game_id") != game or \
            not _text(target.get("executable")) or not _text(expected_executable) or \
            target["executable"].casefold() != expected_executable.casefold() or \
            target.get("executable_match") != "exact-path" or not _digest(target.get("executable_path_sha256")):
        block("target-identity-unverified", "Game and exact rendering-executable identity are missing or mismatched.")
    sections = ("native", "driver", "effective", "runtime")
    for section in sections:
        if not isinstance(data.get(section), dict):
            block("invalid-" + section, "The " + section + " evidence has an unsupported shape.")
        else:
            receipt[section] = data[section]
    sources = data.get("sources")
    source_map = {}
    if not isinstance(sources, list) or not 1 <= len(sources) <= 32:
        block("invalid-sources", "Bounded versioned observation sources are required.")
    else:
        for source in sources:
            if not isinstance(source, dict) or not _text(source.get("id")) or \
                    not _text(source.get("kind")) or source["kind"] not in _SOURCE_KINDS or \
                    not _text(source.get("version")) or \
                    source["id"] in source_map:
                block("invalid-sources", "Source identity, kind or version is invalid or duplicated.")
                continue
            source_map[source["id"]] = source
            if source["kind"] != "primary-documentation":
                try:
                    source_time = _timestamp(source.get("observed_at_utc"))
                    source_age = (assessed - source_time).total_seconds()
                    if source_age < 0 or source_age > MAX_AGE_SECONDS or observed is None or source_time > observed:
                        block("noncurrent-source", "A configuration/runtime source is stale, future-dated or inconsistent with the inspection.")
                except (ValueError, TypeError, OverflowError):
                    block("noncurrent-source", "A configuration/runtime source has no valid UTC provenance.")
        receipt["provenance"]["sources"] = sources
    if any(receipt[section] is None for section in sections):
        return receipt
    native, driver, effective, runtime = (data[section] for section in sections)
    if native.get("status") != "observed" or native.get("configured_mode") not in ("off", "fixed") or \
            native.get("source_scope") != "current-known-path" or not _digest(native.get("source_sha256")) or \
            native.get("source_id") != "native-settings-json" or \
            source_map.get("native-settings-json", {}).get("kind") != "configured-observation":
        block("native-state-unverified", "Current known-path native selection is unverified; a caller-selected file is not sufficient.")
    native_multiplier = native.get("multiplier")
    if (native.get("configured_mode") == "fixed" and not _integer(native_multiplier, 2, 16)) or \
            (native.get("configured_mode") == "off" and native_multiplier is not None):
        block("invalid-native-multiplier", "Native multiplier conflicts with the native FG mode.")
    if driver.get("status") != "observed" or not _text(driver.get("version")) or \
            source_map.get("nvapi-system-drs", {}).get("kind") != "configured-observation":
        block("driver-state-unverified", "Current global/per-application driver state and version are incomplete.")
    for name in ("global", "per_application", "effective_configuration"):
        layer = driver.get(name)
        if not isinstance(layer, dict) or layer.get("status") != "observed" or \
                layer.get("source_id") != "nvapi-system-drs":
            block("driver-" + name + "-unverified", "Driver " + name + " configuration is unverified.")
            continue
        mode = layer.get("configured_mode")
        if mode in ("auto", "dynamic") and name == "effective_configuration":
            block("adaptive-fg-configured", "Adaptive/Dynamic FG is configured for the effective profile; ordinary comparisons are blocked.")
        elif mode not in ("override-disabled", "off", "on", "auto", "dynamic"):
            block("driver-" + name + "-unverified", "Driver " + name + " FG mode is unknown or unsupported.")
        if name != "global" and layer.get("profile_match") != "exact-path":
            block("driver-profile-unverified", "The applicable driver profile is not matched to the exact executable.")
        settings = layer.get("settings")
        for key, raw_field in (("mode", None), ("frame_count", "frame_count_raw"),
                               ("dynamic_max_count", "dynamic_max_count_raw"),
                               ("dynamic_target", "dynamic_target_raw")):
            setting = settings.get(key) if isinstance(settings, dict) else None
            if not isinstance(setting, dict) or setting.get("status") != "observed" or \
                    not _integer(setting.get("raw_value"), 0, 0xFFFFFFFF) or \
                    setting.get("location") not in ("current_profile", "global_profile", "base_profile", "default_profile") or \
                    type(setting.get("predefined")) is not bool:
                block("driver-setting-provenance-unverified", "Driver setting raw value or inheritance provenance is incomplete.")
                continue
            if key == "mode":
                documented_mode = issuer.MODE_NAMES.get(setting["raw_value"])
                if documented_mode is None or setting.get("enum_name") != documented_mode or mode != documented_mode:
                    block("conflicting-driver-mode", "Driver raw mode, documented enum and configured mode conflict.")
            elif type(layer.get(raw_field)) is not int or layer[raw_field] != setting["raw_value"]:
                block("conflicting-driver-setting", "A driver raw field conflicts with its observed setting.")
        if layer.get("fixed_multiplier") is not None:
            block("unsupported-driver-multiplier", "A raw driver frame-count setting cannot be relabeled as a verified multiplier.")
    if effective.get("dynamic_mfg") != "inactive":
        block("dynamic-mfg-unverified", "Dynamic MFG is active, configured or not verified inactive.")
    mode = effective.get("mode")
    multiplier = effective.get("fixed_multiplier")
    if mode not in ("off", "fixed") or effective.get("verification") != "runtime-verified":
        block("effective-fg-unverified", "Configuration alone does not establish effective Off or fixed FG.")
    if (mode == "fixed" and not _integer(multiplier, 2, 16)) or (mode == "off" and multiplier is not None):
        block("invalid-effective-multiplier", "Effective FG requires a known fixed multiplier or Off without a multiplier.")
    coverage = runtime.get("coverage")
    runtime_source_id = runtime.get("source_id")
    if runtime.get("status") != "observed" or not isinstance(coverage, list) or len(coverage) > 16 or \
            any(not _text(item) for item in coverage) or not _COVERAGE.issubset(set(coverage)) or \
            not _text(runtime_source_id) or source_map.get(runtime_source_id, {}).get("kind") != "runtime-observation":
        block("runtime-fg-unverified", "No reviewed current runtime evidence covers FG mode, Dynamic MFG, owners and identity.")
    if runtime.get("status") == "observed":
        runtime_mode = runtime.get("mode")
        runtime_multiplier = runtime.get("fixed_multiplier")
        if runtime_mode not in ("off", "fixed") or runtime.get("dynamic_mfg") != "inactive" or \
                (runtime_mode == "fixed" and not _integer(runtime_multiplier, 2, 16)) or \
                (runtime_mode == "off" and runtime_multiplier is not None):
            block("runtime-mode-unverified", "Runtime evidence does not verify inactive Dynamic MFG and known Off/fixed mode.")
        if mode in ("off", "fixed") and (runtime_mode != mode or runtime_multiplier != multiplier or \
                runtime.get("dynamic_mfg") not in ("inactive", "unknown", None)):
            block("conflicting-runtime-fg", "Observed runtime and effective FG evidence conflict.")
        if not isinstance(target, dict) or runtime.get("game_id") != game or \
                not _text(runtime.get("executable")) or runtime["executable"].casefold() != expected_executable.casefold() or \
                runtime.get("executable_path_sha256") != target.get("executable_path_sha256"):
            block("runtime-identity-unverified", "Runtime FG evidence is not bound to the requested rendering executable.")
    configured = driver.get("effective_configuration")
    if isinstance(configured, dict):
        driver_mode = configured.get("configured_mode")
        resolved_setting = configured.get("settings", {}).get("mode") if isinstance(configured.get("settings"), dict) else None
        per_application = driver.get("per_application")
        app_setting = per_application.get("settings", {}).get("mode") if isinstance(per_application, dict) and isinstance(per_application.get("settings"), dict) else None
        global_layer = driver.get("global")
        global_setting = global_layer.get("settings", {}).get("mode") if isinstance(global_layer, dict) and isinstance(global_layer.get("settings"), dict) else None
        if isinstance(resolved_setting, dict) and isinstance(app_setting, dict):
            if any(resolved_setting.get(key) != app_setting.get(key) for key in ("raw_value", "enum_name", "location")):
                block("conflicting-driver-inheritance", "Applicable and effective driver mode readbacks disagree.")
            if resolved_setting.get("location") == "global_profile" and isinstance(global_setting, dict) and \
                    resolved_setting.get("raw_value") != global_setting.get("raw_value"):
                block("conflicting-driver-inheritance", "Inherited global driver mode conflicts with the observed global setting.")
        if driver_mode == "off" and mode in ("off", "fixed") and mode != "off":
            block("conflicting-configured-fg", "Driver Off conflicts with the effective runtime FG mode.")
        if driver_mode == "override-disabled" and mode in ("off", "fixed") and (native.get("configured_mode") != mode or native_multiplier != multiplier):
            block("conflicting-configured-fg", "Without a driver override, native and runtime FG evidence conflict.")
    if not receipt["reason_codes"]:
        receipt.update(status="PASS", can_compare=True)
        receipt["reason_codes"] = ["verified-off" if mode == "off" else "verified-fixed"]
        receipt["reasons"] = ["Current trusted runtime evidence verifies Dynamic MFG inactive and effective FG " + mode + "."]
    return receipt
