# Future task: compare game mods with reproducible telemetry

Requested 2026-10-10. Status: **backlog / design prepared**. No scheduled execution or reminder. The current Cyberpunk validation is the first evidence set, not completion of this cross-game product.

Goal: a small local tool that captures and compares how an individual mod or compatible stack changes frame pacing, resource pressure, latency and failure behavior, while keeping raw measurements usable for future analysis.

## Build sequence and acceptance

1. **Capture contract and private archive.** Versioned run/phase/event schemas, UTC + QPC clock mapping, immutable files, hardware/settings/mod hashes, provenance and failure states. Store private paths/saves/raw logs outside Git. Acceptance: an interrupted capture remains readable and cannot overwrite the baseline.
2. **Minimal runner and resources.** Reuse the initial PowerShell collector, reduce sampling overhead, sample resident/private/system commit and adapter VRAM separately, expose supported CPU/GPU clocks/power/thermal/paging/I/O values. Optional existing-tool adapters, not mandatory services. Acceptance: explicit nulls for unavailable data, bounded overhead measured against matched control runs, no clock/limiter changes or game injection.
3. **Frame events and offline analysis.** Reuse documented PresentMon/ETW and verify event-loss diagnostics; do not rewrite ETW decoding first. Isolate swapchains and instrumented frame classes, phase boundaries, slow tails, stutter timestamps and coverage. Validate the analyzer with known traces, bad/missing/zero values, dropped frames and FG examples. Acceptance: formulas and sample sizes are exported; rendered/displayed/unknown rates never collapse into one unlabeled FPS.
4. **Comparison and stability report.** Three-or-more comparable runs, ordered/randomized A/B/A comparisons when practical, settings equality checks, distributions and spread, crash/exit/device events, before/after memory growth and headroom. Acceptance: a different PT/SR/cache workload is explicitly flagged rather than sold as a mod speedup.
5. **Scenario runner.** Repeatable routes plus non-periodic/new-area runs, cold-start/first-visit/warm-revisit labels, load/alt-tab/resolution changes, and manual event markers. Guard all file/profile switches against a running game/store/launcher/compiler. Acceptance: no quest advancement or overwritten recovery saves, resumable checkpoints, validated rollback.
6. **Latency/visual extension.** Optional Reflex/PC/display/input metrics with endpoint and coverage definitions; separate rotation, translation, HUD and animation scenarios. Later optical hardware/high-speed-video adapter if requested. Acceptance: no claim of physical camera/animation latency from FPS or a software counter alone; recording overhead calibrated.
7. **Cross-game profiles and sharing.** Portable metadata/config profiles, schema-migration tests and a local HTML report. Private raw evidence bundle to the user's Drive; sanitized docs/source/results to the canonical GitHub repository. Acceptance: no proprietary binaries, private paths, credentials, saves or full raw game logs in Git.

## Architecture choices

Build the coordinator, markers, schemas, statistical analysis, comparison/reporting, profile guards and optional adapters ourselves. Reuse Windows/NVIDIA sensor APIs and a validated frame-event collector; these supply information that a polling script cannot invent. Start with standard-library Python/PowerShell and no resident overlay, database or web server. Streaming CSV/JSON is enough initially. Add a UI only after the capture/data contract works.

Capture process CPU/memory and collection duration. Prefer persistent readers/batched calls over launching one program per sensor or repeated expensive WMI queries. Sample resources at an appropriate low frequency and events at native frame frequency. Keep optional heavyweight video/WPR traces for a reproducible anomaly. MSI Afterburner, RTSS and NVIDIA tools should remain optional data adapters when already configured, preserving their preconfigured baseline.

## Cyberpunk follow-up queue

- Complete combined ReShade/RenoDX/Ultra+ benchmark and loaded-save controls with resource capture.
- Validate the first user-authorized ETW CSV; capture raw frame times and supported latency fields. The NVIDIA bundled capture exited silently; standalone Intel 2.6.0 reported access denied without privileges. Automated elevation was initially rejected; renewed explicit user authorization allowed the approval prompt and the elevated capture process launched. Data delivery still needs verification.
- Repeat matching PT-off and PT21 configurations separately; distinguish FG-enabled presentation from base rendering. Initial stock/HDR/Ultra runs are one-run short comparisons.
- Test new-area streaming/camera motion and first encounter with new shader/effects if ordinary play disagrees with the built-in scene. Record cache state first; no global cache deletion.
- Test longer allocation/thermal/latency trends and enough samples for meaningful 0.1% / 0.01% tails; do not extend a session solely to report a fragile extreme statistic.

Current reference: [measurement procedure](GAME-PERFORMANCE-MEASUREMENT.md), [Cyberpunk evidence](../games/cyberpunk-2077/RUNTIME-VALIDATION.md). Future work is tracked in [GitHub issue #3](https://github.com/dodWhatUp/install-modes-for-games/issues/3). Private Drive archive links are added after verified publishing.
