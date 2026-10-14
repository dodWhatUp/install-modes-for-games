# Offline comparison dataset contract — 0.1.1

This is a normalization boundary for **existing provider report summaries**, not a collector or a frame/lows/latency calculation engine. The [example](comparison-fixture.example.json) is visibly synthetic and contains no measured costs. Hub 0.6.0 adds specific original-report adapters through [GameToolReportImport.py](../../scripts/GameToolReportImport.py); do not relabel an arbitrary CSV as this schema. The [offline guide](../../docs/OFFLINE-COMPARISON-REPORTS.md) owns supported layouts and evidence limits.

All operations are offline-only, with `execution: none` and `runtime_verification: false`. This code never opens games, discovers processes, activates providers or recording, changes settings, edits profiles or executes source text. Tests use temporary authored fixtures only.

## Public Python API

`scripts/GameToolComparison.py` supplies:

- `validate_dataset(dataset)`: validate and detach bounded JSON data.
- `load_dataset(path)`: validate a two-MiB UTF-8 JSON file and retain a private `_source` path/SHA-256 in memory.
- `assert_source_current(path, expected_sha256)`: refuse stale bytes; callers must explicitly reload.
- `compare_dataset(dataset, metric_id=None)`: preserve raw runs and return definition-aware descriptive summaries/gates. A loaded object's data must still equal its file snapshot, not merely claim its hash.
- `render_html(result)`: escaped standalone report, no JavaScript, external links, media or private source locator.
- `export_report(source_path, output_path, format='json', expected_sha256=None, metric_id=None)`: recompute from current source, refuse drift and existing destinations, publish a complete staged file through an exclusive atomic link. Filesystems without hard-link support fail closed. The source file is never replaced.

Errors raise `ComparisonError` with path-free messages. Outputs are `COMPARABLE`, `PARTIAL` or `BLOCKED`; a synthetic comparable fixture is **not** runtime acceptance. User-provided titles/definitions are escaped, not automatically a privacy review. Review report text before sharing it; exports are local, not uploaded.

`GameToolReportImport.py` adds `inspect_report(path, adapter='auto')`, `build_dataset(assignments, title=..., question=..., factor=...)` and `import_bundle(assignments, output_directory, title=..., question=..., factor=...)`. The first two do not write. Assignments explicitly supply `path` and `case`; wizard/Hub CLI support baseline/a, with automatic repeat numbering, not filename inference. Inspection's `private_source` locator is local-only and omitted by Hub inspect stdout. Explicit bundle creation archives exact bytes to a fresh exclusive directory, verifies hashes and returns private local manifest/dataset paths. No action imports a runtime-FG seal or changes profiles.

## Schema version 1

Unknown fields, duplicate JSON keys, nonfinite/oversized numbers, numeric booleans and unbounded structures are refused. Limits: two MiB source/canonical dataset bytes, 256 runs, 64 metrics, depth 12, 25,000 validation nodes, 4,096 characters/text and 80-character stable IDs. Resolved per-run definition expansion is bounded to an eight-MiB work budget and serialized exports to sixteen MiB; a small file cannot amplify shared definitions into an unbounded report.

| Record | Required fields |
|---|---|
| Dataset | integer `schema_version: 1`, `origin: synthetic_fixture` or `imported_report`, `title`, `question`, `measurement_scope: external_process`, `rendering` or `injected_feature`, `experiment`, `metrics`, `runs` |
| Experiment | `design: one_factor` or `two_by_two`, one/two stable `factors`, constant `baseline_components`, typed `dependencies` object mapping component IDs to required component IDs |
| Metric | `id`, `label`, `provider`, `provider_version`, exact `definition`, `unit`, `scope`, `frame_class`, `latency_endpoints` null or two named boundaries, explicit boolean `additive` |
| Run | `id`, `case`, positive integer `repeat`, `status`, `failure_reason`, `source_sha256`, `started_utc`, `ended_utc`, `duration_seconds`, `sample_count`, `workload`, `configuration`, `fg`, `memory_warning`, observed `components`, `metrics` |
| Workload | `scenario`, `revision`, `phase`, `cache_state`, exact `process_scope`; preserve unknowns rather than inferring them |
| Configuration | SHA-256 `fingerprint` of **constant non-tested conditions**, human `description`; tested components are separately represented, not hidden in a different fingerprint |
| FG | `dynamic_mfg: inactive`, `active`, `unverified` or `not_applicable`; `effective_mode: off`, `fixed`, `unknown` or `not_applicable`; `multiplier` fixed positive integer 2–16 or null; `evidence: synthetic`, `declared` or `not_applicable` |
| Run metric | `{value: number or null}`, optionally a full `descriptor` to preserve a run's differing provider version/definition/scope; absent metrics remain unavailable |

Cases are `baseline`, `a` for one-factor; `baseline`, `a`, `b`, `ab` for 2×2. Observed components must equal constant baseline plus the selected factor(s). Every case must retain every mandatory dependency: a factor that depends on the other tested factor cannot be independently attributed using 2×2. This validates declarations, not real compatibility or loaded components.

UTC end follows start; complete runs require positive duration/sample coverage and null failure reason. Declared duration must match the UTC window within one percent or one millisecond rounding tolerance, and compared complete-run durations must match within the same tolerance. Sample counts are declared coverage, not independent proof that a provider captured every event. Incomplete/failed/cancelled runs retain an explicit reason and nullable coverage/end. Hashes associate declared original reports; this core verifies normalized dataset bytes, **not** the reports' actual bytes. Repeat IDs and complete-run report hashes must be independent: duplicate hashes cannot count as new repetitions. Equal unknown/unverified workload fields never become a match; explicit `cache_state: not_applicable` is permitted only for external idle scope.

Backwards-compatible schema 1 extension: only non-complete runs may have null `started_utc` and `configuration.fingerprint`. Optional bounded `import_provenance` retains adapter/schema/raw metadata/issues without private locators or runtime verification. Complete-run requirements remain unchanged. A native summary can be successfully read while its comparison context is incomplete; adapters use an explicit metadata-incomplete reason, not an inferred failed/crashed provider run. Never synthesize UTC from filenames/mtime, settings identity from a random hash, or frame counts from FPS × duration. Original/archive hashes verified by an import receipt establish byte identity at import time only; the core's original-report associations remain declarations, not continuous archive verification or measurement truth.

## Comparison gates and interpretation

Actual imports are eligible only for explicitly non-rendering **manager-idle** provider summaries, with matched known process scope and FG `not_applicable`. Real rendering/injected imports stay raw-table-only and `BLOCKED` because a JSON declaration and the current configuration-only inspector cannot establish trusted effective FG. There is intentionally no importable runtime-PASS field or seal. A later runtime adapter requires separate acceptance and authorization.

Synthetic rendering exercises require explicitly synthetic inactive Dynamic MFG, Off or one matched fixed FG mode. Active/unverified Dynamic MFG, unknown/mismatched FG, active/unverified memory warning, observed component mismatch, workload/configuration mismatch or duplicated report blocks inference. No texture/budget change or warning dismissal occurs.

For each consistently defined metric, at least three complete non-null repeats per condition are required. Provider/version/definition/unit/scope/frame class/latency endpoints must match. Unknown semantic fields block that metric. Raw run values, coverage, failures and per-run definitions remain present even when blocked; unavailable is null, never zero. Failed and incomplete runs are excluded from means, but are not deleted or advertised as stability success.

Valid metrics show arithmetic mean, min/max **across provider run summaries**, A/B/combined deltas and percentages (null for a zero baseline or numeric overflow). Additive 2×2 metrics additionally show `AB - A - B + baseline`. It is descriptive, not statistical significance or root-cause proof. Non-additive metrics such as FPS do not get an interaction contrast. GPU utilization alone does not establish causal GPU time/cost; adapter VRAM is not game-only memory, residency, budget or capacity. No lows, percentile, latency or frame metrics are reconstructed from traces.

## Result shape and preservation

Results include `metrics` descriptor list; `raw_runs` with numeric/null `metrics` and exact `metric_definitions`; `case_summaries` rows (`metric_id`, `case`, `n`, `mean`, `min`, `max`, `unit`); `comparisons` rows (`metric_id`, `contrast`, `delta`, `percent`, `unit`); `gates` (`code`, `message`, nullable `run_id`, `metric_id`); warnings and normalized-source provenance. Private `_source.path` is excluded from JSON/HTML reports. The complete raw report remains the original unchanged file.

The optional Hub panel/CLI must recheck source identity before copy, metric change, chart or export; stale work needs explicit reload. Charts are available only for a comparable selected metric. No new registry/settings migration is required. Rollback this optional source module/panel only; do not restore native device or game profiles.
