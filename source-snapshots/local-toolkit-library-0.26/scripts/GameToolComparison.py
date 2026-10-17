"""Bounded offline comparisons of normalized, provider-defined report summaries.

No collector, process discovery, input, recorder, game launch or metric engine is
present. Imported declarations cannot establish trusted runtime FG evidence.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile


VERSION = "0.1.1"
MAX_DATASET_BYTES = 2 * 1024 * 1024
MAX_RUNS = 256
MAX_METRICS = 64
MAX_DEPTH = 12
MAX_NODES = 25000
MAX_RESOLVED_BYTES = 8 * 1024 * 1024
MAX_REPORT_BYTES = 16 * 1024 * 1024
MIN_REPEATS = 3
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
_SHA = re.compile(r"[0-9a-fA-F]{64}\Z")
_CASES = {"one_factor": ("baseline", "a"),
          "two_by_two": ("baseline", "a", "b", "ab")}
_DESCRIPTOR_FIELDS = {"id", "label", "provider", "provider_version", "definition",
                      "unit", "scope", "frame_class", "latency_endpoints", "additive"}
_WORKLOAD_FIELDS = {"scenario", "revision", "phase", "cache_state", "process_scope"}


class ComparisonError(ValueError):
    """Safe, path-free validation or stale-source error."""


def _error(message):
    raise ComparisonError(message)


def _bounded(value, depth=0, budget=None):
    """Validate work before schema checks; booleans are data, never numbers."""
    if budget is None:
        budget = [0]
    budget[0] += 1
    if depth > MAX_DEPTH or budget[0] > MAX_NODES:
        _error("Dataset nesting or validation-work limit exceeded.")
    if isinstance(value, dict):
        if len(value) > 512:
            _error("Dataset object limit exceeded.")
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 100:
                _error("Invalid dataset field name.")
            _bounded(item, depth + 1, budget)
    elif isinstance(value, list):
        if len(value) > 512:
            _error("Dataset list limit exceeded.")
        for item in value:
            _bounded(item, depth + 1, budget)
    elif isinstance(value, str):
        if len(value) > 4096 or any(ord(char) < 32 and char not in "\n\r\t" for char in value):
            _error("Dataset text limit or character constraint exceeded.")
    elif value is None or type(value) is bool:
        return
    elif type(value) in (int, float):
        if abs(value) > 1e100 or not math.isfinite(value):
            _error("Dataset contains a nonfinite or oversized number.")
    else:
        _error("Dataset contains unsupported data.")


def _object(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - (set(required) | set(optional)) or set(required) - set(value):
        _error("Missing, unknown or invalid object fields.")
    return value


def _encoded_size(value, maximum):
    """Bound JSON expansion without constructing a single giant serialized copy."""
    total = 0
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    for piece in encoder.iterencode(value):
        total += len(piece.encode("utf-8"))
        if total > maximum:
            _error("Resolved dataset/report expansion exceeds its bounded work budget.")
    return total


def _text(value, *, identifier=False, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value.strip()) or len(value) > 4096:
        _error("Invalid required text.")
    if identifier and not _ID.fullmatch(value):
        _error("Invalid stable identifier.")
    return value


def _hash(value):
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        _error("Missing or invalid SHA-256 identity.")
    return value.lower()


def _number(value, *, minimum=None, integer=False, nullable=False):
    if value is None and nullable:
        return value
    if type(value) not in (int, float) or abs(value) > 1e100 or not math.isfinite(value):
        _error("Expected a finite number, not a boolean or substituted text.")
    if integer and type(value) is not int:
        _error("Expected an integer.")
    if minimum is not None and value < minimum:
        _error("Number is outside the permitted range.")
    return value


def _utc(value, nullable=False):
    if value is None and nullable:
        return None
    _text(value)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            _error("Run timestamps must use UTC.")
        return parsed
    except (ValueError, TypeError):
        _error("Invalid UTC run timestamp.")


def _ids(value, max_items=32):
    if not isinstance(value, list) or len(value) > max_items:
        _error("Invalid component list.")
    for item in value:
        _text(item, identifier=True)
    if len(set(value)) != len(value):
        _error("Duplicate component identifier.")
    return value


def _descriptor(value, expected_id=None):
    _object(value, _DESCRIPTOR_FIELDS)
    for field in _DESCRIPTOR_FIELDS - {"latency_endpoints", "additive"}:
        _text(value[field], identifier=(field == "id"))
    if expected_id is not None and value["id"] != expected_id:
        _error("Metric descriptor identity does not match its value.")
    if type(value["additive"]) is not bool:
        _error("Metric additive declaration must be explicit boolean data.")
    endpoints = value["latency_endpoints"]
    if endpoints is not None:
        if not isinstance(endpoints, list) or len(endpoints) != 2:
            _error("Latency endpoints must be null or exactly two defined boundaries.")
        for endpoint in endpoints:
            _text(endpoint)
    return value


def validate_dataset(dataset):
    """Return a detached normalized dataset; validation never runs providers."""
    _bounded(dataset)
    _object(dataset, {"schema_version", "origin", "title", "question", "measurement_scope",
                      "experiment", "metrics", "runs"}, {"_source"})
    if type(dataset["schema_version"]) is not int or dataset["schema_version"] != 1:
        _error("Unsupported normalized comparison schema.")
    if not isinstance(dataset["origin"], str) or dataset["origin"] not in {"synthetic_fixture", "imported_report"}:
        _error("Unknown dataset evidence origin.")
    if not isinstance(dataset["measurement_scope"], str) or dataset["measurement_scope"] not in {"external_process", "rendering", "injected_feature"}:
        _error("Unknown measurement scope.")
    _text(dataset["title"])
    _text(dataset["question"])
    exp = _object(dataset["experiment"], {"design", "factors", "baseline_components", "dependencies"})
    if not isinstance(exp["design"], str) or exp["design"] not in _CASES:
        _error("Only one-factor or dependency-preserving two-by-two designs are supported.")
    factors = _ids(exp["factors"], 2)
    if len(factors) != (1 if exp["design"] == "one_factor" else 2):
        _error("Design factor count does not match.")
    baseline = _ids(exp["baseline_components"])
    if set(baseline) & set(factors):
        _error("A tested factor cannot also be a constant baseline component.")
    if not isinstance(exp["dependencies"], dict) or len(exp["dependencies"]) > 32:
        _error("Invalid dependency declarations.")
    known = set(baseline) | set(factors)
    for component, dependencies in exp["dependencies"].items():
        _text(component, identifier=True)
        _ids(dependencies)
        if component not in known or set(dependencies) - known or component in dependencies:
            _error("Dependency has an unknown owner or self-reference.")
    # An independent 2x2 cannot drop a mandatory factor dependency.
    for case in _CASES[exp["design"]]:
        present = _case_components(exp, case)
        if any(set(exp["dependencies"].get(component, [])) - present for component in present):
            _error("Design removes a required dependency; independent attribution is unavailable.")
    metrics = dataset["metrics"]
    if not isinstance(metrics, list) or not 1 <= len(metrics) <= MAX_METRICS:
        _error("Dataset requires a bounded metric-definition list.")
    metric_ids = set()
    for metric in metrics:
        _descriptor(metric)
        if metric["id"] in metric_ids:
            _error("Duplicate metric identity.")
        metric_ids.add(metric["id"])
    runs = dataset["runs"]
    if not isinstance(runs, list) or not 1 <= len(runs) <= MAX_RUNS:
        _error("Dataset requires a bounded run list.")
    run_ids = set()
    repeat_ids = set()
    for run in runs:
        _object(run, {"id", "case", "repeat", "status", "failure_reason", "source_sha256",
                      "started_utc", "ended_utc", "duration_seconds", "sample_count", "workload",
                      "configuration", "fg", "memory_warning", "components", "metrics"},
                {"import_provenance"})
        _text(run["id"], identifier=True)
        if run["id"] in run_ids:
            _error("Duplicate run identity.")
        run_ids.add(run["id"])
        if not isinstance(run["case"], str) or run["case"] not in _CASES[exp["design"]]:
            _error("Run belongs to an unknown condition.")
        _number(run["repeat"], minimum=1, integer=True)
        repeat_key = (run["case"], run["repeat"])
        if repeat_key in repeat_ids:
            _error("Duplicate repeat identity within a condition.")
        repeat_ids.add(repeat_key)
        if not isinstance(run["status"], str) or run["status"] not in {"complete", "incomplete", "failed", "cancelled"}:
            _error("Unknown run outcome.")
        complete = run["status"] == "complete"
        if complete:
            if run["failure_reason"] is not None:
                _error("A completed run cannot hide a failure reason.")
        else:
            _text(run["failure_reason"])
        _hash(run["source_sha256"])
        started = _utc(run["started_utc"], nullable=not complete)
        ended = _utc(run["ended_utc"], nullable=not complete)
        if ended is not None and started is None:
            _error("An end timestamp cannot imply an unknown start timestamp.")
        if ended is not None and ended <= started:
            _error("Run end must follow its start.")
        _number(run["duration_seconds"], minimum=0.000001 if complete else 0, nullable=not complete)
        _number(run["sample_count"], minimum=1 if complete else 0, integer=True, nullable=not complete)
        workload = _object(run["workload"], _WORKLOAD_FIELDS)
        for value in workload.values():
            _text(value)
        configuration = _object(run["configuration"], {"fingerprint", "description"})
        if configuration["fingerprint"] is not None or complete:
            _hash(configuration["fingerprint"])
        _text(configuration["description"])
        if "import_provenance" in run:
            provenance = _object(run["import_provenance"], {
                "adapter", "adapter_revision", "source_schema", "source_sha256",
                "raw_metadata", "issues", "coverage", "provider_outcome",
                "case_assignment", "runtime_verification"})
            for field in ("adapter", "adapter_revision", "source_schema", "provider_outcome"):
                _text(provenance[field])
            if _hash(provenance["source_sha256"]) != _hash(run["source_sha256"]):
                _error("Import provenance and run report identities differ.")
            if provenance["runtime_verification"] is not False or provenance["case_assignment"] != "declared_not_observed":
                _error("Saved-report provenance cannot establish runtime or component verification.")
            if dataset["origin"] != "imported_report" or dataset["measurement_scope"] == "external_process":
                _error("Saved game-summary provenance cannot be relabeled as synthetic or manager-idle evidence.")
            if not isinstance(provenance["raw_metadata"], dict) or len(provenance["raw_metadata"]) > 128:
                _error("Import metadata must be a bounded object.")
            if not isinstance(provenance["issues"], list) or len(provenance["issues"]) > 32:
                _error("Import issues must be a bounded list.")
            for issue in provenance["issues"]:
                _text(issue)
            coverage = _object(provenance["coverage"], {"started_utc", "ended_utc", "duration_seconds", "sample_count"})
            if coverage != {field: run[field] for field in coverage}:
                _error("Import coverage must preserve the run's extracted coverage exactly.")
        fg = _object(run["fg"], {"dynamic_mfg", "effective_mode", "multiplier", "evidence"})
        if not isinstance(fg["dynamic_mfg"], str) or fg["dynamic_mfg"] not in {"inactive", "active", "unverified", "not_applicable"} or \
                not isinstance(fg["effective_mode"], str) or fg["effective_mode"] not in {"off", "fixed", "unknown", "not_applicable"} or \
                not isinstance(fg["evidence"], str) or fg["evidence"] not in {"synthetic", "declared", "not_applicable"}:
            _error("Unknown FG declaration; imported declarations are never runtime verification.")
        if fg["effective_mode"] == "fixed":
            _number(fg["multiplier"], minimum=2, integer=True)
            if fg["multiplier"] > 16:
                _error("Unsupported fixed multiplier declaration.")
        elif fg["multiplier"] is not None:
            _error("Only fixed FG may declare a multiplier.")
        if not isinstance(run["memory_warning"], str) or run["memory_warning"] not in {"none", "active", "unverified"}:
            _error("Memory-warning state must be explicit.")
        _ids(run["components"])
        if not isinstance(run["metrics"], dict) or set(run["metrics"]) - metric_ids:
            _error("Run contains an undefined metric.")
        for metric_id, item in run["metrics"].items():
            _object(item, {"value"}, {"descriptor"})
            _number(item["value"], nullable=True)
            if "descriptor" in item:
                _descriptor(item["descriptor"], metric_id)
    result = deepcopy(dataset)
    # _source is generated by load_dataset only, never accepted as imported proof.
    result.pop("_source", None)
    _encoded_size(result, MAX_DATASET_BYTES)
    return result


def _case_components(exp, case):
    selected = set(exp["baseline_components"])
    if case in {"a", "ab"}:
        selected.add(exp["factors"][0])
    if case in {"b", "ab"}:
        selected.add(exp["factors"][1])
    return selected


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _error("Duplicate JSON field; ambiguous data refused.")
        result[key] = value
    return result


def _source_bytes(path):
    path = Path(path)
    try:
        if path.is_symlink():
            _error("A linked source file is not supported.")
        with path.open("rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_DATASET_BYTES:
                _error("Dataset is not a regular file within the two-MiB limit.")
            data = source.read(MAX_DATASET_BYTES + 1)
            after = os.fstat(source.fileno())
        current = path.stat()
        identity = lambda entry: (entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns)
        if len(data) > MAX_DATASET_BYTES or identity(before) != identity(after) or identity(after) != identity(current):
            _error("Dataset changed during its bounded read; reload is required.")
        return data, hashlib.sha256(data).hexdigest()
    except (OSError, RuntimeError):
        _error("Dataset could not be read safely.")


def load_dataset(path):
    """Read/validate a bounded snapshot, retaining its private locator in memory."""
    data, digest = _source_bytes(path)
    try:
        parsed = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_unique_pairs,
                            parse_constant=lambda value: _error("Nonfinite JSON numbers are refused."))
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError):
        _error("Dataset is not a supported UTF-8 JSON object.")
    result = validate_dataset(parsed)
    result["_source"] = {"path": str(Path(path).resolve()), "sha256": digest}
    return result


def assert_source_current(path, expected_sha256):
    """Fail closed when bytes differ; no stale copy/chart/export verdict."""
    expected = _hash(expected_sha256)
    _, digest = _source_bytes(path)
    if digest != expected:
        _error("Dataset source changed; explicitly reload before comparison or export.")
    return digest


def _descriptor_identity(metric):
    # Display label is nonsemantic; every measurement-definition boundary remains.
    return json.dumps({key: metric[key] for key in _DESCRIPTOR_FIELDS - {"label"}},
                      sort_keys=True, ensure_ascii=False, allow_nan=False)


def compare_dataset(dataset, metric_id=None):
    """Descriptive matched-run means/spread/deltas, never raw-trace metrics."""
    data = validate_dataset(dataset)
    definitions = {item["id"]: item for item in data["metrics"]}
    if metric_id is not None and (not isinstance(metric_id, str) or metric_id not in definitions):
        _error("Selected metric is not defined by this dataset.")
    selected = list(definitions) if metric_id is None else [metric_id]
    # Shared definitions are expanded for exact per-run provenance. Refuse
    # pathological amplification before copying that matrix or rendering it.
    resolved_size = _encoded_size(data, MAX_DATASET_BYTES)
    descriptor_sizes = {key: _encoded_size(definitions[key], MAX_RESOLVED_BYTES) for key in selected}
    for run in data["runs"]:
        for key in selected:
            override = run["metrics"].get(key, {}).get("descriptor")
            resolved_size += descriptor_sizes[key] if override is None else _encoded_size(override, MAX_RESOLVED_BYTES)
            if resolved_size > MAX_RESOLVED_BYTES:
                _error("Resolved run-definition matrix exceeds its bounded work budget.")
    synthetic = data["origin"] == "synthetic_fixture"
    source = dataset.get("_source", {})
    # A source locator supplied by a caller is never trusted to establish bytes.
    source_digest = None
    if source:
        if not isinstance(source, dict) or set(source) != {"path", "sha256"}:
            _error("Invalid private source snapshot.")
        source_digest = assert_source_current(source["path"], source["sha256"])
        fresh = load_dataset(source["path"])
        fresh.pop("_source", None)
        if data != fresh:
            _error("Loaded dataset was altered in memory; explicitly reload its source snapshot.")
    result = {"schema_version": 1, "core_version": VERSION, "title": data["title"],
              "question": data["question"], "measurement_scope": data["measurement_scope"],
              "experiment": data["experiment"], "status": "BLOCKED", "execution": "none",
              "synthetic_fixture": synthetic, "runtime_verification": False,
              "metrics": [definitions[key] for key in selected], "raw_runs": [],
              "case_summaries": [], "comparisons": [], "gates": [], "warnings": [
                  "Descriptive summaries only: no significance, root-cause or compatibility claim.",
                  "Provider summaries retain their definitions; lows and latency are not recalculated."],
              "provenance": {"dataset_sha256": source_digest, "normalized_bytes_verified": source_digest is not None,
                             "report_hashes": "declared_only", "runtime_verification": False}}
    if synthetic:
        result["warnings"].insert(0, "SYNTHETIC FIXTURE — demonstration numbers, not measured tool or game costs.")
    def gate(code, message, run_id=None, metric=None):
        item = {"code": code, "message": message, "run_id": run_id, "metric_id": metric}
        if item not in result["gates"]:
            result["gates"].append(item)
    complete = [run for run in data["runs"] if run["status"] == "complete"]
    expected_cases = _CASES[data["experiment"]["design"]]
    for run in data["runs"]:
        row = {key: deepcopy(value) for key, value in run.items() if key != "metrics"}
        row["metrics"] = {key: run["metrics"].get(key, {}).get("value") for key in selected}
        row["metric_definitions"] = {key: deepcopy(run["metrics"].get(key, {}).get("descriptor", definitions[key]))
                                     for key in selected}
        result["raw_runs"].append(row)
        for field, value in run["workload"].items():
            marker = value.strip().lower()
            if marker in {"unknown", "unverified", "unspecified", "n/a", "na", "none", "null", "?", "not_applicable"} and \
                    not (field == "cache_state" and marker == "not_applicable" and data["measurement_scope"] == "external_process"):
                gate("WORKLOAD_UNKNOWN", "Required workload metadata is unknown or a placeholder; equal unknowns are not matched evidence.", run["id"])
        if run["started_utc"] is None or ("import_provenance" in run and any(
                run[field] is None for field in ("ended_utc", "duration_seconds", "sample_count"))):
            gate("COVERAGE_UNKNOWN", "UTC window or provider duration/count is missing; file times are not measurement coverage.", run["id"])
        if run["configuration"]["fingerprint"] is None:
            gate("CONFIGURATION_UNKNOWN", "A complete constant-settings fingerprint is missing; requested settings are not verified loaded state.", run["id"])
        if "import_provenance" in run:
            gate("IMPORTED_COMPONENTS_UNVERIFIED", "Imported case/component assignments are declared roles, not observed loaded component state.", run["id"])
        if run["started_utc"] is not None and run["ended_utc"] is not None and run["duration_seconds"] is not None:
            window = (_utc(run["ended_utc"]) - _utc(run["started_utc"])).total_seconds()
            if abs(run["duration_seconds"] - window) > max(0.001, window * 0.01):
                gate("COVERAGE_DURATION_CONTRADICTION", "Declared run duration contradicts its UTC window beyond rounding tolerance; sample count does not certify coverage.", run["id"])
        if run["memory_warning"] != "none":
            gate("MEMORY_WARNING", "Active or unverified memory warning suspends ordinary comparison.", run["id"])
        if set(run["components"]) != _case_components(data["experiment"], run["case"]):
            gate("COMPONENT_STATE_MISMATCH", "Observed components do not match the dependency-preserving condition.", run["id"])
        if run["status"] != "complete":
            result["warnings"].append(f"Run {run['id']} is {run['status']}; retained, excluded from summary math.")
    if not complete:
        gate("NO_COMPLETE_RUNS", "No completed runs are available.")
    if len({json.dumps(run["workload"], sort_keys=True) for run in complete}) > 1:
        gate("WORKLOAD_MISMATCH", "Scenario, revision, phase, cache or process scope differs between completed runs.")
    if len({run["configuration"]["fingerprint"].lower() for run in complete}) > 1:
        gate("CONFIGURATION_MISMATCH", "Non-tested settings/configuration fingerprints differ.")
    if complete:
        durations = [run["duration_seconds"] for run in complete]
        if max(durations) - min(durations) > max(0.001, max(durations) * 0.01):
            gate("COVERAGE_WINDOW_MISMATCH", "Completed run windows differ; preserve unequal coverage instead of silently pooling.")
    hashes = [run["source_sha256"].lower() for run in complete]
    if len(set(hashes)) != len(hashes):
        gate("DUPLICATED_REPORT", "A report hash is reused; copies are not independent repeats.")
    rendering = data["measurement_scope"] != "external_process"
    if rendering:
        for run in data["runs"]:
            fg = run["fg"]
            if fg["dynamic_mfg"] != "inactive":
                gate("DYNAMIC_MFG_ACTIVE_OR_UNVERIFIED", "Dynamic MFG must be inactive for ordinary rendering-cost attribution.", run["id"])
            if fg["effective_mode"] not in {"off", "fixed"}:
                gate("EFFECTIVE_FG_UNKNOWN", "Effective FG must be Off or a known matched fixed multiplier.", run["id"])
            if synthetic and fg["evidence"] != "synthetic":
                gate("FIXTURE_FG_DECLARATION", "A synthetic exercise requires explicitly synthetic FG declarations.", run["id"])
        if len({(run["fg"]["effective_mode"], run["fg"]["multiplier"]) for run in complete}) > 1:
            gate("FG_MODE_MISMATCH", "Compared runs declare different effective FG modes or multipliers.")
        if not synthetic:
            gate("RUNTIME_FG_UNVERIFIED", "Imported JSON and configuration-only checks cannot establish trusted effective-FG runtime PASS; raw reports only.")
    else:
        for run in data["runs"]:
            if run["workload"]["phase"] != "idle" or run["workload"]["process_scope"] == "unknown":
                gate("EXTERNAL_SCOPE_UNSUPPORTED", "This offline version permits actual external-process comparison only for matched manager-idle report summaries.", run["id"])
            if run["fg"] != {"dynamic_mfg": "not_applicable", "effective_mode": "not_applicable",
                            "multiplier": None, "evidence": "not_applicable"}:
                gate("EXTERNAL_FG_SCOPE", "Manager-idle reports must explicitly declare no rendering/FG workload.", run["id"])
    global_blocked = bool(result["gates"])
    comparable_metrics = 0
    for key in selected:
        metric = definitions[key]
        identity = _descriptor_identity(metric)
        for run in complete:
            descriptor = run["metrics"].get(key, {}).get("descriptor", metric)
            if _descriptor_identity(descriptor) != identity:
                gate("METRIC_DEFINITION_MISMATCH", "Provider/version/definition/unit/scope/frame class/endpoints differ; values are not comparable.", run["id"], key)
            if any(descriptor[field].strip().lower() in {"unknown", "unverified", "n/a", "na"}
                   for field in ("provider", "provider_version", "definition", "unit", "scope", "frame_class")):
                gate("METRIC_COVERAGE_UNKNOWN", "Unknown metric semantics cannot support a delta.", run["id"], key)
        case_values = {}
        for case in expected_cases:
            values = [run["metrics"].get(key, {}).get("value") for run in complete if run["case"] == case]
            case_values[case] = [value for value in values if value is not None]
            if len(case_values[case]) < MIN_REPEATS:
                gate("INSUFFICIENT_REPEATS", f"Metric {key}, condition {case} needs at least three complete non-null repeats.", metric=key)
        metric_blocked = any(item["metric_id"] == key for item in result["gates"])
        if global_blocked or metric_blocked:
            continue
        comparable_metrics += 1
        means = {}
        for case, values in case_values.items():
            means[case] = sum(values) / len(values)
            result["case_summaries"].append({"metric_id": key, "case": case, "n": len(values),
                "mean": means[case], "min": min(values), "max": max(values), "unit": metric["unit"]})
        baseline = means["baseline"]
        for case in expected_cases[1:]:
            delta = means[case] - baseline
            percent = None if baseline == 0 else delta / abs(baseline) * 100
            if percent is not None and not math.isfinite(percent):
                percent = None
                result["warnings"].append(f"Metric {key} percentage overflowed; percentage remains unavailable.")
            result["comparisons"].append({"metric_id": key, "contrast": case + " minus baseline",
                "delta": delta, "percent": percent,
                "unit": metric["unit"]})
        if data["experiment"]["design"] == "two_by_two":
            fps_unit = metric["unit"].strip().lower() in {"fps", "frames/s", "frames/sec", "frames per second"}
            if metric["additive"] and not fps_unit:
                result["comparisons"].append({"metric_id": key, "contrast": "ab - a - b + baseline",
                    "delta": means["ab"] - means["a"] - means["b"] + baseline,
                    "percent": None, "unit": metric["unit"]})
            else:
                reason = "FPS is nonlinear" if fps_unit else "not declared additive"
                result["warnings"].append(f"Metric {key}: {reason}; no interaction contrast is calculated.")
    if comparable_metrics:
        result["status"] = "COMPARABLE" if comparable_metrics == len(selected) else "PARTIAL"
    return result


def _display(value):
    return "unavailable" if value is None else str(value)


def render_html(result):
    """Escaped local report. No JavaScript, embedded media, links or source paths."""
    escape = lambda value: html.escape(_display(value), quote=True)
    def table(headers, rows):
        return "<table><thead><tr>" + "".join("<th>" + escape(item) + "</th>" for item in headers) + \
            "</tr></thead><tbody>" + "".join("<tr>" + "".join("<td>" + escape(item) + "</td>" for item in row) + "</tr>" for row in rows) + "</tbody></table>"
    banner = "SYNTHETIC FIXTURE — NOT MEASURED COSTS" if result["synthetic_fixture"] else "IMPORTED PROVIDER SUMMARIES — OFFLINE ONLY"
    body = ["<h1>" + escape(result["title"]) + "</h1>", "<p class='banner'>" + escape(banner) + "</p>",
            "<p>Status: " + escape(result["status"]) + "; execution: none; runtime verification: false.</p>",
            "<p>" + escape(result["question"]) + "</p>", "<h2>Gates and limitations</h2>",
            table(["Code", "Run", "Metric", "Reason"], [[item["code"], item["run_id"], item["metric_id"], item["message"]] for item in result["gates"]]),
            "<ul>" + "".join("<li>" + escape(item) + "</li>" for item in result["warnings"]) + "</ul>",
            "<h2>Provider definitions</h2>", table(["Metric", "Provider/version", "Definition", "Unit", "Scope", "Frame class", "Latency endpoints"],
                [[item["id"], item["provider"] + " / " + item["provider_version"], item["definition"], item["unit"], item["scope"], item["frame_class"], item["latency_endpoints"]] for item in result["metrics"]]),
            "<h2>All retained runs</h2>", table(["Run", "Case", "Repeat", "Outcome", "Failure", "Metric", "Provider summary", "Report SHA-256"],
                [[run["id"], run["case"], run["repeat"], run["status"], run["failure_reason"], key, value, run["source_sha256"]] for run in result["raw_runs"] for key, value in run["metrics"].items()]),
            "<h2>Exact per-run definitions, coverage and preflight declarations</h2>",
            "<p>Expand a run to inspect its own provider definitions, workload, constant configuration, FG and memory-warning declarations. Imported declarations are not runtime verification. Review user-supplied metadata for private content before sharing.</p>",
            "".join("<details><summary>" + escape(run["id"]) + " — " + escape(run["status"]) +
                    "</summary><pre>" + escape(json.dumps(run, ensure_ascii=False, indent=2, allow_nan=False)) +
                    "</pre></details>" for run in result["raw_runs"]),
            "<h2>Matched complete-repeat summaries</h2>", table(["Metric", "Case", "N", "Mean", "Min", "Max", "Unit"],
                [[item[field] for field in ("metric_id", "case", "n", "mean", "min", "max", "unit")] for item in result["case_summaries"]]),
            "<h2>Descriptive contrasts (not statistical significance)</h2>", table(["Metric", "Contrast", "Delta", "Percent", "Unit"],
                [[item[field] for field in ("metric_id", "contrast", "delta", "percent", "unit")] for item in result["comparisons"]]),
            "<h2>Normalized source provenance</h2><pre>" + escape(json.dumps(result["provenance"], indent=2)) + "</pre>"]
    return "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'\"><title>Offline comparison</title><style>body{font:15px system-ui,sans-serif;margin:24px;color:#202832;background:#fff}table{border-collapse:collapse;width:100%;margin-bottom:20px}th,td{border:1px solid #ccc;padding:7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}.banner{font-weight:bold;border:2px solid #b75;padding:12px}pre{white-space:pre-wrap}</style></head><body>" + "".join(body) + "</body></html>"


def export_report(source_path, output_path, format="json", expected_sha256=None, metric_id=None):
    """Export a new report exclusively; preserve source and every existing file.

    Complete bytes are staged/fsynced, then exclusively hard-linked into the
    target name. Unsupported filesystems fail closed rather than overwriting.
    """
    if not isinstance(format, str) or format not in {"json", "html"}:
        _error("Report export format must be json or html.")
    dataset = load_dataset(source_path)
    digest = dataset["_source"]["sha256"]
    if expected_sha256 is not None and digest != _hash(expected_sha256):
        _error("Dataset source changed; explicitly reload before export.")
    result = compare_dataset(dataset, metric_id=metric_id)
    content = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2) if format == "json" else render_html(result)
    payload = content.encode("utf-8")
    if len(payload) > MAX_REPORT_BYTES:
        _error("Serialized report exceeds its sixteen-MiB export limit.")
    target = Path(output_path)
    if target.resolve() == Path(source_path).resolve():
        _error("A report cannot replace its normalized source.")
    if target.exists() or target.is_symlink():
        _error("Report destination already exists; choose a new filename.")
    temporary = None
    installed = False
    try:
        with tempfile.NamedTemporaryFile(prefix=".game-comparison-", suffix=".tmp", dir=target.parent, delete=False) as staging:
            temporary = Path(staging.name)
            staging.write(payload)
            staging.flush()
            os.fsync(staging.fileno())
        assert_source_current(source_path, digest)
        os.link(temporary, target)  # Atomic exclusive publication, never replace.
        installed = True
        try:
            assert_source_current(source_path, digest)
        except ComparisonError:
            # Only remove our own just-published inode; a replacement stays intact.
            if target.exists() and os.path.samefile(target, temporary):
                target.unlink()
            installed = False
            raise
        return {"schema_version": 1, "status": result["status"], "execution": "none",
                "path": str(target.resolve()), "format": format, "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(), "dataset_sha256": digest}
    except OSError:
        if installed and temporary is not None and target.exists():
            try:
                if os.path.samefile(target, temporary):
                    target.unlink()
            except OSError:
                pass
        _error("Report could not be published exclusively; no existing destination was replaced.")
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass
