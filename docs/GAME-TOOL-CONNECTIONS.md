# Measurement-tool connections and user control

Current scope, confirmed **2026-10-11**: learn and connect existing tools, expose useful user controls and prepare a lightweight management helper. Benchmark execution, game launches and capture activation remain deferred. Complex lows, latency and specialized analysis must come from established programs.

## Current connection evidence

| Tool / interface | Observed state | What is established | Remaining boundary |
|---|---|---|---|
| MSI Afterburner 4.6.7.16935 | Installed, running | Read-only `MAHMSharedMemory` connection returned 20 fresh source entries. Saved profile has history logging Off and begin/end recording/logging hotkeys unset. | No game/run association or benchmark acceptance. Source definitions and scope need preservation. |
| RTSS 7.3.5.28314 | Installed, running | Existing companion identified and executable version read. Afterburner's author-supplied SDK defines source IDs for 1% and 0.1% lows. | This does not establish populated game lows, their method or base/generated-frame coverage. RTSS settings/benchmark mode have not been changed. |
| Intel PresentMon console 2.6.0 | Previously installed; older process still running | CLI collector is distinct from the GUI capture application. Historical process does not prove active recording or valid output. | No new frame CSV or latency validation. Inventory-only in learning mode; do not launch another collector. |
| Game Tool Hub 0.1.0 | Authored learning preview | Tool inventory, read-only Afterburner adapter, report archive, source definitions/hashes, user registration and structured agent commands. Nine contract tests passed. | GUI acceptance is recorded separately below. No hardware tuning, profile writeback, capture controller or custom metric engine. |

Desktop sensor snapshots are connection evidence. They are not new Cyberpunk performance measurements. The source polling timestamp is retained; stale/unavailable values are marked rather than replaced. The provider does not promise an atomic batch across all sensors.

GUI evidence: the Tools page was opened and visibly displayed installed/running status for all three registered tools. The CLI adapter returned fresh values; both low-FPS sources were correctly unavailable without a run. Nine contract tests cover original-value preservation, unavailable/zero values, bounded malformed layouts, unchanged report bytes/definitions, unique imports and overwrite refusal. Afterburner root/profile and RTSS configuration hashes matched the pre-helper baseline. A sensor-tab click encountered the supported tool's user-input guard; no forced retry or bypass was used. Other GUI button flows and the later footer-layout adjustment remain pending live acceptance. The panel is a learning preview, not a finished all-tool controller.

## Working methods

Prefer an existing API, SDK/shared memory or report export to reading repeated screenshots. Current Afterburner adapter uses the installed author's `SDK/Include/MAHMSharedMemory.h` v2 prefix. It opens only an existing `MAHMSharedMemory` mapping with `FILE_MAP_READ`, validates bounded sizes/counts and preserves names, units, source IDs, flags and original values. It does not use the hardware-control `MACM` interface or copy the SDK into Git. `FLT_MAX` and nonfinite values become unavailable; a reported zero remains zero. Live FPS counters are explicitly unscoped.

Read effective per-user settings from Afterburner's `Profiles/MSIAfterburner.cfg`, falling back to application defaults. The root default file alone is insufficient. Stored settings are configuration evidence, not proof of runtime recording state. The helper displays raw hotkey values instead of guessing their encoding. Proposed recording keys must be checked against native/mod bindings; Cyberpunk F9 already controls DLSS quality, so a guide's generic F9 recording suggestion must not be copied blindly.

Use supported Computer Use for observed ordinary-app controls. The previous `launch_app` route timed out while UAC was pending and did not leave Afterburner running after approval. A direct normal process launch subsequently opened it; UI/process readback confirmed success. Treat that as a launch-helper limitation observed in this session, not a proven Afterburner crash. Windows approval remains manual. No security setting was changed.

For future tools, register installed GUI executables and preserve their existing settings. Verify the exact program's exports before selecting it for a specific metric. The console collector and GUI analyzer may differ. OCR/accessibility are useful fallbacks for UI state; never use OCR labels alone as proof that a feature evaluated or a metric was captured. A future adapter can import documented summary fields without implementing the statistic again.

## User panel and agent integration

[Game Tool Hub source and launcher](../examples/game-tool-hub/README.md) provides Tools, Sensors, Reports and How to use tabs. Auto refresh starts Off; opening the panel does not start or save a time series. The user can register an installed interface, open tools, refresh connections, copy a status summary without local paths, save a new private snapshot and import existing reports. PresentMon console launch is unavailable in learning mode.

The agent can use `inspect`, `snapshot --output` and `import-report` with structured JSON receipts. There is no network listener or hidden input channel. The future larger AHK host can consume an explicitly requested snapshot or invoke the coordinator as a module/command; integration must preserve its input ownership, privacy, stop behavior and existing profiles. No automatic host wiring or global shortcuts were added here.

Imports preserve CSV/JSON/TXT/HML bytes plus source program, definition, UTC, size and SHA-256. No metrics are recalculated. Imports have no inferred run association. HML remains opaque until an established export/conversion path is validated. Local paths/receipts stay private; only authored code, methodology and sanitized evidence belong in Git. Existing raw test archives remain unchanged.

Rollback: close Game Tool Hub, preserve its private imports, and remove only the optional authored helper/launcher. No game or Afterburner/RTSS configuration restore is required for this connection work. Closing the panel does not terminate other applications or the historical idle collector.

## Next learning steps

1. Confirm the panel's GUI and read-only sensor refresh; keep capture controls absent.
2. Learn RTSS's exact available summary/export path and the installed version's low definitions before using its reports. Add a summary importer only for an observed documented format.
3. If a GUI analyzer is needed, research a compatible maintained existing program and its export/latency capabilities. Installation is a separate concrete action; no installer or new service was added in this stage.
4. Add explicit user-controlled settings adapters only for requested supported actions, with snapshots, visible state and rollback. Keep hardware tuning, game/profile changes and capture activation separately scoped.
5. Resume game scenarios and performance validation only after an explicit user request.

Primary references reviewed 2026-10-11: [MSI monitoring/OSD guide](https://www.msi.com/blog/msi-afterburner-on-screen-display/) and [Intel PresentMon capture application and metric definitions](https://github.com/GameTechDev/PresentMon/blob/main/README-CaptureApplication.md). Local SDK/profile evidence is stronger than a generic hotkey guide for this installed configuration.
