"""Bounded saved-summary adapters. No live providers, launch, capture or settings.

Supported signatures: Cyberpunk 2077 worldBenchmarkSummary JSON (observed 2.31)
and the PresentMon GUI nine-column *-stats.csv layout reviewed at v2.6.0.
Source schema recognition is not proof of the provider binary, delivered FG,
loaded mods, complete settings, frame coverage or independent repeated runs.
"""
from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
import types


VERSION = "0.1.0"
MAX_REPORT_BYTES = 2 * 1024 * 1024
MAX_REPORTS = 32
MAX_FIELDS = 512
_SHA = re.compile(r"[a-fA-F0-9]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
_NUM = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")
_ADAPTERS = {"auto", "cyberpunk_benchmark_summary", "presentmon_gui_stats"}
_PM_HEADER = ["Duration", "Total Frames", "Average FPS", "Minimum FPS",
              "1st Percentile FPS", "5th Percentile FPS", "Maximum FPS",
              "AnimationErrorPerSecond", "AnimationErrorPerFrame"]
_CP_SETTINGS = {
    "renderWidth", "renderHeight", "windowMode", "verticalSync", "fpsClamp",
    "presetName", "textureQualityPresetLocalizedName", "upscalingType",
    "frameGenerationType", "DLAAEnabled", "DLSSEnabled", "DLSSPreset",
    "DLSSDEnabled", "DLSSQuality", "DLSSFrameGenEnabled",
    "DLSSMultiFrameGenEnabled", "DLSSMultiFrameGenFrameToGenerate",
    "FSR2Enabled", "FSR2Quality", "FSR3Enabled", "FSR3Quality",
    "FSR4Enabled", "FSR4Quality", "XeSSEnabled", "XeSSQuality",
    "FSR3FrameGenEnabled", "XeSSFrameGenEnabled", "DRSEnabled",
    "DRSTargetFPS", "DRSMinimalResolutionPercentage", "DRSMaximalResolutionPercentage",
    "rayTracingEnabled", "rayTracedReflections", "rayTracedSunShadows",
    "rayTracedLocalShadows", "rayTracedLightingQuality", "rayTracedPathTracingEnabled"}
_CP_CAPACITY = {"gpuMemory", "systemMemory"}
_CORE = None


class ReportImportError(ValueError):
    """Path-free validation/import errors suitable for a desktop status field."""


def _error(message):
    raise ReportImportError(message)


def _text(value, maximum=4096):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(
            ord(char) < 32 and char not in "\r\n\t" for char in value):
        _error("Invalid or overlong report text.")
    return value


def _bounded(value, depth=0, budget=None):
    if budget is None:
        budget = [0]
    budget[0] += 1
    if depth > 8 or budget[0] > 12000:
        _error("Saved report exceeds its nesting/work limit.")
    if isinstance(value, dict):
        if len(value) > MAX_FIELDS:
            _error("Saved report has too many fields.")
        for key, item in value.items():
            _text(key, 100)
            _bounded(item, depth + 1, budget)
    elif isinstance(value, list):
        if len(value) > MAX_FIELDS:
            _error("Saved report contains a raw trace or oversized list, not a supported summary.")
        for item in value:
            _bounded(item, depth + 1, budget)
    elif isinstance(value, str):
        if len(value) > 4096 or any(ord(char) < 32 and char not in "\r\n\t" for char in value):
            _error("Saved report contains invalid or overlong text.")
    elif value is None or type(value) is bool:
        return
    elif type(value) in (int, float):
        if abs(value) > 1e100 or not math.isfinite(value):
            _error("Saved report contains a nonfinite or oversized number.")
    else:
        _error("Unsupported saved report value.")


def _number(value, name, *, integer=False):
    if value is None:
        return None
    if type(value) not in (int, float) or abs(value) > 1e100 or not math.isfinite(value) or value < 0:
        _error("Invalid " + name + ": expected a finite nonnegative number, not boolean/text.")
    if integer and type(value) is not int:
        _error("Invalid " + name + ": expected an integer count.")
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _error("Duplicate JSON field; ambiguous saved report refused.")
        result[key] = value
    return result


def _no_links(path):
    """Reject linked files/directories before resolving either sources or outputs."""
    locator = os.fspath(path)
    if not isinstance(locator, str) or not locator or len(locator) > 4096 or any(ord(char) < 32 for char in locator):
        _error("Invalid local source or destination path.")
    path = Path(locator).absolute()
    for part in (path, *path.parents):
        try:
            metadata = part.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            _error("Source or destination path could not be checked safely.")
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            _error("Linked source or destination paths are not supported.")
    return path


def _identity(metadata):
    return metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns


def _read_source(path):
    try:
        path = _no_links(path)
        with path.open("rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_REPORT_BYTES:
                _error("Saved report must be a nonempty regular file within the two-MiB limit.")
            data = source.read(MAX_REPORT_BYTES + 1)
            after = os.fstat(source.fileno())
        current = path.stat()
        if len(data) > MAX_REPORT_BYTES or _identity(before) != _identity(after) or _identity(after) != _identity(current):
            _error("Saved report changed during its bounded read; reload before import.")
        _no_links(path)
        return data, {"path": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    except (OSError, RuntimeError, TypeError):
        _error("Saved report could not be read safely.")


def _metric(identifier, label, provider, version, definition, frame_class, value):
    return {"id": identifier, "label": label, "provider": provider,
            "provider_version": version, "definition": definition, "unit": "FPS",
            "scope": "provider_selected_game_capture", "frame_class": frame_class,
            "latency_endpoints": None, "additive": False, "value": value}


def _cyberpunk(parsed):
    if not isinstance(parsed, dict) or set(parsed) != {"RootType", "Data"} or parsed["RootType"] != "worldBenchmarkSummary" or not isinstance(parsed["Data"], dict):
        _error("JSON is not the supported Cyberpunk worldBenchmarkSummary report.")
    data = parsed["Data"]
    if not any(key in data for key in ("averageFps", "minFps", "maxFps")):
        _error("Cyberpunk summary has no recognized FPS summary fields.")
    version = data.get("gameVersion", "unknown")
    if version is None:
        version = "unknown"
    _text(version, 100)
    duration = _number(data.get("time"), "Cyberpunk elapsed duration")
    count = _number(data.get("frameNumber"), "Cyberpunk frameNumber", integer=True)
    issues = ["No UTC start/end timestamps are supplied by this report; file times are not substituted.",
              "Native FG/DRS fields are requested configuration, not effective FG or loaded-mod evidence.",
              "FPS frame class and calculation definition are not specified by this report.",
              "Complete constant-settings state, cache state and memory-warning status are unverified."]
    if version != "2.31":
        issues.append("This shape was observed for Cyberpunk 2.31; other/missing game versions have not been locally validated.")
    metrics = []
    for field, identifier, label in (("averageFps", "cp_average_fps", "Cyberpunk average FPS"),
                                     ("minFps", "cp_minimum_fps", "Cyberpunk minimum FPS"),
                                     ("maxFps", "cp_maximum_fps", "Cyberpunk maximum FPS")):
        value = _number(data.get(field), field)
        if value is None:
            issues.append(field + " is missing; retained as unavailable, not zero.")
        metrics.append(_metric(identifier, label, "Cyberpunk 2077 built-in benchmark", version,
            "Provider-reported " + field + "; calculation semantics unspecified by the saved report.", "unknown", value))
    if count == 0 or duration == 0:
        for metric in metrics:
            metric["value"] = None
        issues.append("Zero duration/frame count cannot certify measured FPS; provider values retained only in raw metadata.")
    metadata = {"gameVersion": data.get("gameVersion"),
                "requested_settings": {}, "capacity_metadata_not_usage": {},
                "reported_fps": {field: data.get(field) for field in ("averageFps", "minFps", "maxFps")}}
    if "benchmarkName" in data:
        _text(data["benchmarkName"], 1024)
        metadata["benchmarkName"] = data["benchmarkName"]
    for field in sorted(_CP_SETTINGS | _CP_CAPACITY):
        if field in data:
            if not (data[field] is None or type(data[field]) in (str, bool, int, float)):
                _error("Recognized Cyberpunk setting/capacity metadata must be scalar.")
            destination = "capacity_metadata_not_usage" if field in _CP_CAPACITY else "requested_settings"
            metadata[destination][field] = data[field]
    return {"adapter": "cyberpunk_benchmark_summary", "provider": "Cyberpunk 2077 built-in benchmark",
            "provider_version": version, "source_schema": "worldBenchmarkSummary (observed Cyberpunk 2.31)",
            "metrics": metrics, "coverage": {"started_utc": None, "ended_utc": None,
            "duration_seconds": duration, "sample_count": count}, "raw_metadata": metadata,
            "provider_outcome": "zero_frames" if count == 0 or duration == 0 else "not_reported", "issues": issues}


def _csv_number(value, name, integer=False):
    if not isinstance(value, str) or not _NUM.fullmatch(value):
        _error("Invalid PresentMon " + name + ": decimal summary numbers are required.")
    if integer:
        if not re.fullmatch(r"\d+", value):
            _error("PresentMon Total Frames must be an integer count.")
        return _number(int(value), name, integer=True)
    return _number(float(value), name)


def _presentmon(text):
    try:
        rows = []
        for row in csv.reader(io.StringIO(text, newline=""), delimiter=",", strict=True):
            rows.append(row)
            if len(rows) > 2:
                break  # Summary-only: never allocate or process a raw trace.
    except csv.Error:
        _error("Malformed CSV quoting or overlong fields; supported delimiter is comma.")
    if not rows or rows[0] != _PM_HEADER:
        header = rows[0] if rows else []
        if any(field in header for field in ("Application", "ProcessID", "SwapChainAddress", "CPUStartTime", "MsBetweenPresents", "FrameTime", "CPUStartTimeInSeconds")):
            _error("Raw PresentMon frame CSV is not a summary; export the GUI *-stats.csv report instead. No frame metrics are recalculated.")
        _error("CSV is not the supported PresentMon GUI nine-column stats summary (comma delimiter).")
    if len(rows) != 2:
        _error("PresentMon stats summary must contain exactly one header and one summary row.")
    if any(len(field) > 4096 for row in rows for field in row):
        _error("PresentMon summary field exceeds its text limit.")
    row = rows[1]
    issues = ["Provider version, application identity, UTC timestamps and constant settings are absent from this CSV.",
              "Recognized writer schema does not verify the installed provider version or effective FG.",
              "Presented-interval FPS is not independently verified base-rendered or displayed-frame FPS.",
              "Animation-error fields are preserved as raw metadata only; animation sample coverage is absent.",
              "Memory-warning and cache state are unverified."]
    empty = len(row) == 8 and all(value == "0" for value in row)
    defect = len(row) == 8 and row[-1] == "00" and not empty
    if len(row) != 9 and not (empty or defect):
        _error("PresentMon stats row width is invalid; only the documented zero-count/00 writer defects are recognized.")
    if empty:
        issues.append("Recognized zero-frame writer row; zero FPS placeholders are unavailable metrics, not measured performance.")
    elif defect:
        issues.append("Recognized PresentMon missing-comma '00' animation tail; first seven columns preserved and animation values unavailable.")
    duration = _csv_number(row[0], "Duration")
    count = _csv_number(row[1], "Total Frames", integer=True)
    summaries = [_csv_number(row[index], _PM_HEADER[index]) for index in range(2, 7)]
    animation = None
    if len(row) == 9:
        animation = [_csv_number(row[7], _PM_HEADER[7]), _csv_number(row[8], _PM_HEADER[8])]
    if empty or count == 0 or duration == 0:
        values = [None] * 5
        if not empty:
            issues.append("Zero duration/frame count cannot certify measured FPS; reported numbers remain raw only.")
    else:
        values = summaries
    # The provider calculates these summaries; this adapter never recomputes them.
    definitions = [
        ("pm_average_fps", "PresentMon average FPS", "Reciprocal of provider mean between-presents interval, converted to FPS."),
        ("pm_minimum_fps", "PresentMon minimum FPS", "Reciprocal of provider maximum between-presents interval, converted to FPS."),
        ("pm_percentile_1_fps", "PresentMon 1st percentile FPS", "Reciprocal of provider interpolated 99th-percentile between-presents interval; not mean of slowest 1% frames."),
        ("pm_percentile_5_fps", "PresentMon 5th percentile FPS", "Reciprocal of provider interpolated 95th-percentile between-presents interval; not mean of slowest 5% frames."),
        ("pm_maximum_fps", "PresentMon maximum FPS", "Reciprocal of provider minimum between-presents interval, converted to FPS.")]
    metrics = [_metric(identifier, label, "PresentMon GUI", "unknown",
        "Recognized writer schema reviewed at 2.6.0: " + definition, "presented_intervals", value)
        for (identifier, label, definition), value in zip(definitions, values)]
    return {"adapter": "presentmon_gui_stats", "provider": "PresentMon GUI", "provider_version": "unknown",
            "source_schema": "PresentMon GUI nine-column stats (writer schema reviewed 2.6.0)",
            "metrics": metrics, "coverage": {"started_utc": None, "ended_utc": None,
            "duration_seconds": duration, "sample_count": count},
            "raw_metadata": {"headers": list(_PM_HEADER), "reported_summary_values": summaries,
                             "animation_fields": animation, "writer_row": list(row), "writer_defect": defect,
                             "zero_frame_writer_row": empty},
            "provider_outcome": "zero_frames" if empty or count == 0 or duration == 0 else "not_reported", "issues": issues}


def _inspect_bytes(data, source, adapter):
    if not isinstance(adapter, str) or adapter not in _ADAPTERS:
        _error("Unknown saved-report adapter; choose auto, cyberpunk_benchmark_summary or presentmon_gui_stats.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError:
        _error("Saved reports must use UTF-8 (an optional UTF-8 BOM is supported).")
    if any(ord(char) < 32 and char not in "\r\n\t" for char in text):
        _error("Saved report contains unsupported control characters.")
    if text.lstrip().startswith(("{", "[")):
        if adapter == "presentmon_gui_stats":
            _error("Selected PresentMon adapter cannot read JSON.")
        try:
            parsed = json.loads(text, object_pairs_hook=_pairs,
                parse_constant=lambda value: _error("Nonfinite JSON numbers are refused."))
        except ReportImportError:
            raise
        except (json.JSONDecodeError, RecursionError, ValueError):
            _error("Malformed or excessively nested saved JSON report.")
        _bounded(parsed)
        result = _cyberpunk(parsed)
    else:
        if adapter == "cyberpunk_benchmark_summary":
            _error("Selected Cyberpunk adapter requires worldBenchmarkSummary JSON.")
        result = _presentmon(text)
    result.update({"schema_version": 1, "adapter_revision": VERSION, "private_source": dict(source)})
    _bounded({key: value for key, value in result.items() if key != "private_source"})
    return result


def inspect_report(path, adapter="auto"):
    """Read-only signature-based inspection; never write or infer filename metadata."""
    data, source = _read_source(path)
    return deepcopy(_inspect_bytes(data, source, adapter))


def _core():
    global _CORE
    if _CORE is None:
        path = Path(__file__).with_name("GameToolComparison.py")
        try:
            _no_links(path)
            with path.open("rb") as source:
                before = os.fstat(source.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_size > 1024 * 1024:
                    _error("Authored comparison module is outside its bounded source limit.")
                data = source.read(1024 * 1024 + 1)
                after = os.fstat(source.fileno())
            if len(data) > 1024 * 1024 or _identity(before) != _identity(after) or _identity(after) != _identity(path.stat()):
                _error("Authored comparison module changed during its bounded source read.")
        except OSError:
            _error("Authored comparison module could not be read safely.")
        module = types.ModuleType("game_report_import_comparison_core")
        module.__file__ = str(path)
        exec(compile(data, str(path), "exec"), module.__dict__)
        _CORE = module
    return _CORE


def _prepare(assignments, title, question, factor, design, factor_b):
    if not isinstance(assignments, list) or not 1 <= len(assignments) <= MAX_REPORTS:
        _error("Choose between one and 32 saved reports per import bundle.")
    _text(title)
    _text(question)
    if design not in ("one_factor", "two_by_two"):
        _error("Import supports only one_factor or two_by_two designs.")
    factors = [factor] if design == "one_factor" else [factor, factor_b]
    if any(not isinstance(item, str) or not _ID.fullmatch(item) for item in factors) or len(set(factors)) != len(factors):
        _error("Import factor names must be distinct stable identifiers.")
    cases = {"baseline", "a"} if design == "one_factor" else {"baseline", "a", "b", "ab"}
    dataset = {"schema_version": 1, "origin": "imported_report", "title": title,
        "question": question, "measurement_scope": "rendering",
        "experiment": {"design": design, "factors": factors, "baseline_components": [], "dependencies": {}},
        "metrics": [], "runs": []}
    known_metrics = {}
    repeats = {case: 0 for case in cases}
    records = []
    seen_hashes = set()
    for index, assignment in enumerate(assignments, 1):
        if not isinstance(assignment, dict) or set(assignment) - {"path", "case", "adapter", "expected_sha256", "context"} or not {"path", "case"} <= set(assignment):
            _error("Import assignments require a source path and explicit case; unknown execution fields are refused.")
        case = assignment["case"]
        if not isinstance(case, str) or case not in cases:
            _error("Assign every saved report to a supported case; filenames do not establish experiment roles.")
        expected = assignment.get("expected_sha256")
        if expected is not None and (not isinstance(expected, str) or not _SHA.fullmatch(expected)):
            _error("Invalid expected saved-report SHA-256.")
        data, source = _read_source(assignment["path"])
        if expected is not None and source["sha256"] != expected.lower():
            _error("Saved report changed after preview; explicitly preview again before import.")
        if source["sha256"] in seen_hashes:
            _error("Duplicate report bytes are not independent runs; choose each distinct saved report once.")
        seen_hashes.add(source["sha256"])
        preview = _inspect_bytes(data, source, assignment.get("adapter", "auto"))
        context = assignment.get("context", {})
        if not isinstance(context, dict) or set(context) - {"scenario", "cache_state", "configuration_description"}:
            _error("Only descriptive scenario, cache_state and configuration_description import context is supported; context is not runtime verification.")
        for value in context.values():
            _text(value)
        metric_values = {}
        for entry in preview["metrics"]:
            descriptor = {key: deepcopy(value) for key, value in entry.items() if key != "value"}
            identifier = descriptor["id"]
            if identifier not in known_metrics:
                known_metrics[identifier] = descriptor
                dataset["metrics"].append(descriptor)
            metric_values[identifier] = {"value": entry["value"], "descriptor": descriptor}
        repeats[case] += 1
        coverage = deepcopy(preview["coverage"])
        components = []
        if case in {"a", "ab"}:
            components.append(factors[0])
        if case in {"b", "ab"}:
            components.append(factors[1])
        run = {"id": "import-" + str(index).zfill(3), "case": case, "repeat": repeats[case],
            "status": "incomplete", "failure_reason": "Import metadata incomplete; not evidence of a provider-run crash. UTC window, complete configuration and runtime state are unavailable.",
            "source_sha256": source["sha256"], **coverage,
            "workload": {"scenario": context.get("scenario", preview["raw_metadata"].get("benchmarkName", "unknown")),
                "revision": preview["raw_metadata"].get("gameVersion") or "unknown", "phase": "benchmark",
                "cache_state": context.get("cache_state", "unknown"), "process_scope": "unknown"},
            "configuration": {"fingerprint": None, "description": context.get("configuration_description", "Saved requested settings are partial and unverified; no complete constant-settings fingerprint.")},
            "fg": {"dynamic_mfg": "unverified", "effective_mode": "unknown", "multiplier": None, "evidence": "declared"},
            "memory_warning": "unverified", "components": components, "metrics": metric_values,
            "import_provenance": {key: deepcopy(preview[key]) for key in (
                "adapter", "adapter_revision", "source_schema", "raw_metadata", "issues", "coverage", "provider_outcome")}}
        run["import_provenance"].update({"source_sha256": source["sha256"], "case_assignment": "declared_not_observed", "runtime_verification": False})
        dataset["runs"].append(run)
        records.append({"data": data, "preview": preview})
    try:
        dataset = _core().validate_dataset(dataset)
    except ValueError:
        _error("Imported dataset exceeds the supported normalized schema or its bounded size/work limit.")
    return dataset, records


def build_dataset(assignments, title="Saved reports", question="Compare saved provider summaries.",
                  factor="changed_configuration", design="one_factor", factor_b="changed_configuration_b"):
    """Build detached schema-1 data without writing; never fabricate missing metadata."""
    dataset, _ = _prepare(assignments, title, question, factor, design, factor_b)
    return dataset


def _assert_records_current(records):
    for record in records:
        _, current = _read_source(record["preview"]["private_source"]["path"])
        if current["sha256"] != record["preview"]["private_source"]["sha256"]:
            _error("A saved report changed during import; no mixed-source bundle will be published.")


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8")


def import_bundle(assignments, output_directory, title="Saved reports",
                  question="Compare saved provider summaries.", factor="changed_configuration",
                  design="one_factor", factor_b="changed_configuration_b"):
    """Explicit exclusive private bundle export; preserve original report bytes.

    Validate/capture every input before output, stage and verify complete bytes,
    then publish into a newly created destination using exclusive hard links.
    On failure remove only this operation's own linked inodes, never replacements.
    """
    dataset, records = _prepare(assignments, title, question, factor, design, factor_b)
    try:
        target = _no_links(output_directory)
        if target.exists() or target.is_symlink() or not target.parent.is_dir():
            _error("Choose a fresh bundle directory inside an existing local parent; existing paths are never replaced.")
        parent_identity = target.parent.stat().st_dev, target.parent.stat().st_ino
        _assert_records_current(records)
        normalized = _json_bytes(dataset)
        if len(normalized) > MAX_REPORT_BYTES:
            _error("Normalized imported dataset exceeds its two-MiB limit.")
        payloads = {"comparison.json": normalized}
        receipt = {"schema_version": 1, "adapter_revision": VERSION, "execution": "none", "runtime_verification": False,
                   "coverage": "original report bytes captured and hash-verified; metadata incomplete; restore not tested", "sources": []}
        for index, record in enumerate(records, 1):
            preview = record["preview"]
            extension = ".json" if preview["adapter"] == "cyberpunk_benchmark_summary" else ".csv"
            name = "source-" + str(index).zfill(3) + extension
            payloads[name] = record["data"]
            receipt["sources"].append({"archive_name": name, "private_source": deepcopy(preview["private_source"]),
                "adapter": preview["adapter"], "adapter_revision": VERSION,
                "case": dataset["runs"][index - 1]["case"], "normalized_run_id": dataset["runs"][index - 1]["id"]})
        receipt["dataset_sha256"] = hashlib.sha256(normalized).hexdigest()
        payloads["private-receipt.json"] = _json_bytes(receipt)
        manifest = {"schema_version": 1, "execution": "none", "files": [
            {"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in payloads.items()]}
        payloads["manifest.json"] = _json_bytes(manifest)
        with tempfile.TemporaryDirectory(prefix=".game-report-import-", dir=target.parent) as staging_name:
            staging = Path(staging_name)
            for name, payload in payloads.items():
                with (staging / name).open("xb") as output:
                    output.write(payload)
                    output.flush()
                    os.fsync(output.fileno())
                if (staging / name).read_bytes() != payload:
                    _error("Staged report bundle bytes failed verification.")
            _assert_records_current(records)
            _no_links(target)
            if (target.parent.stat().st_dev, target.parent.stat().st_ino) != parent_identity:
                _error("Bundle parent changed during preparation; publication refused.")
            published = []
            created = False
            succeeded = False
            owned_directory = None
            try:
                target.mkdir()  # Exclusive, never exist_ok or recursive parent creation.
                created = True
                owned_directory = target.stat().st_dev, target.stat().st_ino
                for name, payload in payloads.items():
                    _no_links(target)
                    if (target.stat().st_dev, target.stat().st_ino) != owned_directory:
                        _error("Bundle directory changed during publication; operation stopped.")
                    os.link(staging / name, target / name)
                    published.append(name)
                    if (target / name).read_bytes() != payload:
                        _error("Published report bundle bytes failed verification.")
                _assert_records_current(records)
                succeeded = True
                return {"schema_version": 1, "status": "BLOCKED", "execution": "none",
                    "bundle_path": str(target.resolve()), "dataset_path": str((target / "comparison.json").resolve()),
                    "dataset_sha256": receipt["dataset_sha256"], "source_count": len(records),
                    "manifest_path": str((target / "manifest.json").resolve()), "runtime_verification": False}
            finally:
                # Success owns a full verified bundle; failures remove only our
                # exact hard-linked bytes, preserving concurrent replacements.
                if created and not succeeded:
                    for name in published:
                        try:
                            if os.path.samefile(target / name, staging / name):
                                (target / name).unlink()
                        except OSError:
                            pass
                    try:
                        if (target.stat().st_dev, target.stat().st_ino) == owned_directory:
                            target.rmdir()
                    except OSError:
                        pass
    except (OSError, RuntimeError, TypeError):
        _error("Private import bundle could not be published safely; no existing destination was replaced.")
