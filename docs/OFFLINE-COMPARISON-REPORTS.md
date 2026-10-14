# Offline comparison and reporting contract

Hub 0.6.0 retains the optional Comparison tab and adds bounded saved-report import adapters alongside `compare-report`. This is a saved-data reporting stage, not a collector or benchmark executor. It does not launch or control a game, record video, start providers, modify graphics, migrate profiles or upload reports. The [master checklist](GAME-TOOLS-MASTER-CHECKLIST.md) tracks the wider unfinished toolkit.

## Use the existing Hub

Open Comparison with Ctrl+7. Choose **Import saved reports** for supported original summaries, or **Load summary JSON** for an existing normalized dataset. Select a provider-defined metric; inspect the case means/minimum/maximum, contrasts, raw runs, blockers and definitions. Copy summary copies only the selected metric's report. Export JSON/HTML creates a new local file; an existing destination is refused, not overwritten. Nothing is opened or uploaded afterward.

Ctrl+R explicitly reloads the selected source and Ctrl+C copies the current summary outside text fields. The original Ctrl+1–6 assignments stay unchanged. On Comparison, Ctrl+O/A/S/I/E cannot trigger remembered Tools/Reports actions. Modal dialogs and ordinary text selection/copy retain ownership. This optional module does not add a file watcher or sensor-refresh task.

```text
python -B scripts/Game-Tool-Hub.py compare-report --source examples/game-tool-hub/comparison-fixture.example.json
python -B scripts/Game-Tool-Hub.py compare-report --source <existing-normalized.json> --metric <metric-id> --output <new-local-report.html> --format html
```

Exit 0 means a descriptive report has eligible metrics, including a PARTIAL report whose other metrics are blocked. Exit 3 means BLOCKED: raw evidence and reasons remain available and can be explicitly exported, but numeric contrasts are suppressed. Exit 2 means an invalid request, unsafe source or refused export. Each result reports `execution: none`. A successful report is not authorization to execute a plan or proof of a measured game/tool cost.

The [example dataset](../examples/game-tool-hub/comparison-fixture.example.json) contains **synthetic demonstration values**, not measurements. Its banner, JSON origin and report warnings must remain intact. Do not copy its provider names, hashes, FG declarations or configuration fingerprint into a real report.

## Saved-report adapters — Hub 0.6.0

The [shared importer](../scripts/GameToolReportImport.py) handles two narrowly identified formats; it is not a universal CSV/JSON converter:

| Format | Retained provider summaries | Evidence and limitations |
|---|---|---|
| Cyberpunk benchmark `summary.json` | Average/minimum/maximum FPS, elapsed seconds, frame count; selected embedded game/settings/capacity fields | Exact `RootType: worldBenchmarkSummary`/`Data` schema observed in four existing 2.31 reports. FPS calculation/frame class are unknown. GPU/system memory fields are capacities, **not measured usage**. Other source metadata remains in the original archive. |
| PresentMon GUI statistics CSV | Duration, total frames, average/minimum/maximum and 1st/5th percentile FPS | Pinned GUI writer layout; FPS derives from between-present intervals, not verified rendered/base/displayed FPS. Percentiles are provider reciprocal frametime percentiles, **not average slowest-frame lows**. Version, UTC, workload and settings are absent. |

PresentMon's exact nine-column header and missing-animation eight-field `00` writer defect follow the pinned [v2.6.0 writer](https://github.com/GameTechDev/PresentMon/blob/e13fce6acdb55a808fd8318175a56863e532d95f/IntelPresentMon/Core/source/pmon/RawFrameDataWriter.cpp#L539) and [statistics implementation](https://github.com/GameTechDev/PresentMon/blob/e13fce6acdb55a808fd8318175a56863e532d95f/IntelPresentMon/Core/source/pmon/StatisticsTracker.cpp). The recognized defect preserves FPS/coverage while marking animation unavailable; animation is not a latency metric. Empty captures remain incomplete. No actual local PresentMon statistics export was found: this adapter's acceptance is source-layout fixtures only. Cyberpunk's exact schema is observed-local, not claimed to be officially documented by CDPR.

Choose files, inspect the extracted metrics/definitions/issues, and explicitly assign each file to `baseline` or `a`. Files begin **unassigned**. Set the title, question and tested factor, then **Create import and load** into a new private directory. The importer writes original bytes, a hash-bound private manifest and normalized `comparison.json`; it does not replace the originals. Removing/cancelling a draft writes no bundle and leaves the previous loaded comparison intact. No filename-based roles or timestamps are inferred.

```text
python -B scripts/Game-Tool-Hub.py inspect-saved-report --source <existing-summary.json>
python -B scripts/Game-Tool-Hub.py import-saved-reports --baseline <baseline-summary.json> --a <changed-summary.json> --output-directory <new-private-folder> --factor <tested-factor-id>
```

Repeat `--baseline`/`--a` for multiple saved reports. Inspection writes nothing and omits the original private locator from stdout. Import exit **3** means the bundle was created but its performance comparison is **BLOCKED**; exit **2** means refused/invalid import. Output paths in an import receipt are private local handoff locations, not portable cloud metadata. Up to 32 sources and 2 MiB per source are allowed; originals and aggregate output are bounded. Existing destinations, unsupported layouts, raw per-frame CSV/HML, linked sources, duplicate/conflicting assignments and changed bytes are refused rather than guessed or overwritten. Partial output from an interrupted/failed import may be retained as evidence, not labeled a successful bundle.

Native FG/MFG fields are recorded as saved declarations only. Every imported rendering dataset forces unknown effective FG, unverified Dynamic MFG and unverified memory-warning state; no checkbox, source field or title can grant runtime PASS. Neither format supplies a UTC run start or complete non-tested configuration identity. Those values remain null/unknown, with an explicit **import metadata incomplete, not a provider-run crash** reason. Values/coverage remain visible in raw runs, but are excluded from eligible comparison arithmetic. Missing sample counts are never reconstructed as FPS × duration. A later metadata/runtime adapter is separate work, not a request to run a game now.

## Normalized summary schema 1

The [pure core](../scripts/GameToolComparison.py) validates a bounded UTF-8 JSON object: at most 2 MiB, 256 runs, 64 metrics and bounded text/nesting/validation work. Resolved metric-definition expansion is limited to 8 MiB and final exported bytes to 16 MiB. Duplicate fields, unknown schema fields, ambiguous identities, nonfinite numbers and boolean substitutes for numbers are refused. The existing Reports tab's opaque original-byte archive stays available; Comparison conversion is limited to the two reviewed adapters above. There is no arbitrary CSV/HML conversion, filename-based grouping or claimed adapter for every provider.

Required top-level fields:

| Field | Meaning |
|---|---|
| `schema_version`, `origin`, `title`, `question` | Version 1; `synthetic_fixture` or `imported_report`; explicit descriptive purpose |
| `measurement_scope` | `external_process`, `rendering` or `injected_feature`; never infer injected payload cost from its idle manager |
| `experiment` | `design` (`one_factor` or `two_by_two`), ordered `factors`, constant `baseline_components`, and explicit `dependencies` |
| `metrics` | Descriptors with `id`, `label`, `provider`, `provider_version`, `definition`, `unit`, `scope`, `frame_class`, `latency_endpoints` (null or two defined endpoints), `additive` |
| `runs` | Explicit report/condition/repeat identities, outcome, timing, workload, configuration, components, FG, warning and provider-summary values |

Each run supplies `id`, `case` (`baseline`, `a`, `b`, `ab` as applicable), positive `repeat`, `status` (`complete`, `incomplete`, `failed`, `cancelled`), `failure_reason`, declared `source_sha256`, UTC `started_utc`/`ended_utc`, `duration_seconds`, `sample_count`, `workload`, `configuration`, `fg`, `memory_warning`, `components`, and `metrics`.

`workload` contains `scenario`, `revision`, `phase`, `cache_state`, `process_scope`. `configuration` contains a SHA-256 `fingerprint` of **non-tested settings** and their `description`. Include game/build, scene, PT/RT, SR model/resolution, RR/HDR, quality, limiters, capture mode and background state in that identity when applicable; it is a declared identity, not an observed settings audit. Tested factor changes belong in the condition/components, not in unrelated configuration drift. A future adapter must construct this identity consistently rather than substituting a random hash.

`fg` contains `dynamic_mfg`, `effective_mode`, `multiplier`, `evidence`. Its enums are defined by the core/example. These imported fields are **declarations only**, never trusted effective-FG runtime evidence. `memory_warning` is `none`, `active` or `unverified`. A metric entry is `{value: number-or-null}` with an optional full `descriptor` override when its actual provider semantics differ. Failed/incomplete runs retain their reasons and supplied raw values, but are excluded from summary arithmetic. Missing metrics remain null/unavailable, not zero.

Schema 1's backwards-compatible import extension permits null `started_utc` and `configuration.fingerprint` only for non-complete runs. Complete runs retain the original strict UTC/settings requirements. Optional bounded `import_provenance` retains adapter/schema evidence, source identity and raw metadata/issues; it is data, not an executable locator or trusted runtime seal. Unknown values must not be replaced by filesystem timestamps, random hashes or synthetic declarations.

## Gates and arithmetic

Inference requires at least three complete, non-null reports per condition and metric, distinct declared report identities, matched workload and non-tested settings, matching metric lineage, correct component membership and preserved required hosts. Memory warnings or unverified warning state suspend ordinary comparison. Unknown semantics do not become comparable merely because they are equal strings. A bad metric can be excluded while independently eligible metrics remain PARTIAL; inspect the blockers rather than interpreting PARTIAL as a universal pass.

For real imports, only matched **external manager-idle** summaries are eligible in this version, with FG explicitly not applicable. Real rendering/injected-feature imports remain BLOCKED even when JSON declares FG Off/fixed or Dynamic MFG inactive. The [existing FG preflight](../scripts/GameFgPreflight.py) is unchanged; this reporting API cannot create its trusted PASS. Synthetic rendering fixtures exercise the arithmetic with synthetic FG states, but establish no runtime coverage.

The core computes only simple means/minimum/maximum and deltas across already calculated provider run summaries. It does not recalculate raw-trace lows, percentiles, latency, CPU utilization or memory peaks. Retain provider definitions and supported sample coverage. Repeat spread is descriptive—not a confidence interval, significance test, causal diagnosis or quality/compatibility verdict. Zero baselines leave relative percentages unavailable rather than inventing infinity.

A dependency-preserving 2×2 uses H, H+A, H+B and H+A+B. Absolute contrasts are reported against H. `AB - A - B + baseline` is permitted only for metrics explicitly declared additive; total FPS is nonlinear and must not be labeled additive tool cost. The core refuses a design that removes a required host or a factor's mandatory dependency.

Memory descriptors must distinguish physical capacity, usage, budget/availability/headroom, allocated/resident memory, adapter/process/engine scope and GB/GiB. Ultra+'s changing `used + available` display is not the fixed capacity or proven free-memory formula. A queued warning can outlive its trigger; supplied event/source/timing evidence must be reconciled before any later performance test. See [measurement protocol](GAME-PERFORMANCE-MEASUREMENT.md) and [resource attribution](TOOL-RESOURCE-OVERHEAD.md).

## Source integrity, privacy and recovery

The loader hashes the exact normalized source bytes. Copy/export/metric-change checks refuse changed sources until explicit reload. The in-memory source locator is private and not emitted in portable results. Manually normalized original-report hashes remain `declared_only`. The saved-report importer verifies exact original/archive bytes at import time and records that boundary in its receipt; the comparison core does not continuously reopen those archives or establish trusted measurement provenance. An unchanged normalized file or byte-identical archive is not evidence that its contents or FG declarations are true.

JSON retains raw runs/definitions/blockers. HTML escapes supplied text and contains no scripts, external resources or executable links. Both are explicit local exports, not privacy-redacted cloud packages: review user-supplied free text before sharing. The source exporter separately scans curated authored files; personal reports/settings/raw logs do not belong in Git.

Exports stage and flush complete bytes, then exclusively publish a new destination on a supported filesystem. Existing files and source bytes are preserved; source changes refuse publication. Unsupported exclusive publication fails closed. Reports do not claim crash-proof capture or universal network-filesystem durability.

Rollback: close only the Hub being replaced, preserve private registry/imports/reports, and restore the immediately preceding Hub source and exporter from the local before-change snapshot. The optional comparison modules can be removed/ignored without restoring game/native/AHK profiles. Do not reset unrelated dirty files or restart the AHK host as part of this rollback.

Tests and acceptance receipts are maintained in [tool connections](GAME-TOOL-CONNECTIONS.md). Withdrawn Tk fixtures establish desktop widget/callback contracts, not observed live desktop focus, native-device behavior, benchmark results or recording recovery.
