# Measurement-tool connections and user control

Current scope, confirmed **2026-10-11**: learn and connect existing tools, expose useful user controls and prepare a lightweight management helper. Benchmark execution, game launches and capture activation remain deferred. Complex lows, latency and specialized analysis must come from established programs.

## Current connection evidence

| Tool / interface | Observed state | What is established | Remaining boundary |
|---|---|---|---|
| MSI Afterburner 4.6.7.16935 | Installed, running | Read-only `MAHMSharedMemory` connection returned 20 fresh source entries. Saved profile has history logging Off and begin/end recording/logging hotkeys unset. | No game/run association or benchmark acceptance. Source definitions and scope need preservation. |
| RTSS 7.3.5.28314 | Installed, running, read-only mapping connected | v2.21 mapping returned six app entries, zero statistics samples and no capture flags. Author's consumer confirms FPS scaling; provider calculates summaries/lows. | No populated game lows, accepted interval, exact low method or base/generated-frame coverage. No OSD/profile/statistics writes. |
| Intel PresentMon console 2.6.0 | Previously installed; older process still running | CLI collector is distinct from the GUI capture application. Historical process does not prove active recording or valid output. | No new frame CSV or latency validation. Inventory-only in learning mode; do not launch another collector. |
| NVIDIA App | Existing interface; launch and running-state refresh passed | Installed program is discoverable/openable. File version is displayed separately from its product version. | Interface connection only; no overlay/recording/optimization setting changed or latency export validated. |
| NVIDIA FrameView SDK | Installed collector, inventory-only | Existing bundled console identified; no standalone FrameView GUI was located. Hub launch stays blocked. | SDK installation is not a populated latency source or proof of the GUI analyzer. |
| Game Tool Hub 0.2.0 | Authored learning preview | Afterburner/RTSS readers, documented PresentMon report preview, immutable archive, registration and local shortcuts. Twenty-two contracts and core GUI flows passed. | Optional Browse/free-text automation and actual game metric acceptance remain separate. No tuning, profile writeback, capture controller or custom metric engine. |

Desktop sensor snapshots are connection evidence. They are not new Cyberpunk performance measurements. The source polling timestamp is retained; stale/unavailable values are marked rather than replaced. The provider does not promise an atomic batch across all sensors.

Historical 0.1.0 GUI evidence: Tools was opened; the later footer adjustment and remaining flows were then pending. A sensor-tab click encountered the supported tool's user-input guard. The 0.2.0 acceptance below supersedes those pending core controls without implying that the larger cross-game product is complete.

## 2026-10-11 — 0.2.0 control acceptance

| Control | Observed result |
|---|---|
| Tools / Sensors / RTSS / Reports / How to use | All five tabs opened through local Ctrl+number shortcuts; final footer was visible. |
| Refresh; optional refresh On/Off | Live readings refreshed. Checkbox and Ctrl+T both tested; final refresh is Off. No time-series files appeared. |
| RTSS application selection | Provider interval/count, update age and absence of instrumentation endpoints displayed. No latency inferred. |
| Copy status | Completion visible; authored summary excludes local paths/app identities and lists only source/app counts. |
| Save snapshot | Ctrl+S created a new private JSON; file readback confirmed the connection state. Overwrite refusal separately covered by contracts. |
| Import / select receipt / open original | Synthetic PresentMon CSV archived through the visible form; original strings `1.250`, `NA` and blanks preserved; receipt showed no recalculation. Original-open dispatched to its associated app and completion was observed. |
| Add / Register / Cancel | Unconfirmed registration refused; explicit interface checkbox allowed an existing Notepad registration in an isolated test profile; prior registry backup verified. Cancel hid the form and original user registry stayed byte-identical. |
| Open selected; collector blocks | NVIDIA App opened and Refresh showed Running Yes. PresentMon and FrameView SDK console selections both refused launch; no new collector appeared. |
| Close/reopen | Only Hub closed/reopened. Test imports/registrations remained in a separate private acceptance folder; final Hub uses the original profile with no draft. |

Twenty-two contracts cover MAHM preservation, RTSS offsets/bounds/version gates, unavailable statistics/stale live counters/tick wrap, endpoint presence without calculated latency, original report cells/definitions/hashes, bounded previews, immutable files, registry backups/duplicate refusal, known collector blocking, keyboard-layout mapping and draft refusal of action/confirmation fields. Fixtures are synthetic, never performance results. Afterburner root/profile and RTSS configuration hashes matched the just-in-time baseline; no game launch or benchmark/recording activation occurred. The historical elevated PresentMon process stayed present and was not silently terminated or resumed. No previous per-frame CSV was located.

Observed automation limits: a native file dialog produced an unavailable cached element/screenshot error; it was cancelled. Automated Unicode text did not appear in Tk entries. Direct path forms and an optional bounded startup JSON draft provide a supported file-based route; draft fields remain visible and do not execute an action or populate confirmation. Optional Browse/free-text input remains user-operated or separately verified. User-input guards were respected; no forced input or security bypass was added.

## Working methods

Prefer an existing API, SDK/shared memory or report export to reading repeated screenshots. Current Afterburner adapter uses the installed author's `SDK/Include/MAHMSharedMemory.h` v2 prefix. It opens only an existing `MAHMSharedMemory` mapping with `FILE_MAP_READ`, validates bounded sizes/counts and preserves names, units, source IDs, flags and original values. It does not use the hardware-control `MACM` interface or copy the SDK into Git. `FLT_MAX` and nonfinite values become unavailable; a reported zero remains zero. Live FPS counters are explicitly unscoped.

RTSS uses existing `RTSSSharedMemoryV2` with `FILE_MAP_READ`. Header offsets/counts/stride govern the bounded application array; newer fields require both version and size gates. The installed author's `RTSSSharedMemory.h` and `OverlayDataProviderInternal.cpp` establish packing and tenths-of-FPS conversion. Zero statistics count leaves average/lows unavailable; raw provider values are retained. Live-counter freshness uses the provider's tick period with wrap handling. Historical summary values retain their interval and are never promoted to a fresh run. No OSD ownership, locks, statistics buffers, latency markers or capture flags are written. Instrumentation endpoints are availability evidence only; the helper computes no latency deltas. Reads are best effort, not an atomic provider snapshot.

Read effective per-user settings from Afterburner's `Profiles/MSIAfterburner.cfg`, falling back to application defaults. The root default file alone is insufficient. Stored settings are configuration evidence, not proof of runtime recording state. The helper displays raw hotkey values instead of guessing their encoding. Proposed recording keys must be checked against native/mod bindings; Cyberpunk F9 already controls DLSS quality, so a guide's generic F9 recording suggestion must not be copied blindly.

Use supported Computer Use for observed ordinary-app controls. The previous `launch_app` route timed out while UAC was pending and did not leave Afterburner running after approval. A direct normal process launch subsequently opened it; UI/process readback confirmed success. Treat that as a launch-helper limitation observed in this session, not a proven Afterburner crash. Windows approval remains manual. No security setting was changed.

For future tools, register installed GUI executables and preserve their existing settings. Verify the exact program's exports before selecting it for a specific metric. The console collector and GUI analyzer may differ. OCR/accessibility are useful fallbacks for UI state; never use OCR labels alone as proof that a feature evaluated or a metric was captured. A future adapter can import documented summary fields without implementing the statistic again.

## User panel and agent integration

[Game Tool Hub source and launcher](../examples/game-tool-hub/README.md) provides Tools, Sensors, RTSS, Reports and How to use tabs. Auto refresh starts Off; opening the panel does not start or save a time series. Visible path forms, optional non-executing startup drafts and local keyboard shortcuts improve user/agent control. Console collectors remain blocked in learning mode.

The agent can use `inspect`, `snapshot --output` and `import-report` with structured JSON receipts. There is no network listener or hidden input channel. The future larger AHK host can consume an explicitly requested snapshot or invoke the coordinator as a module/command; integration must preserve its input ownership, privacy, stop behavior and existing profiles. No automatic host wiring or global shortcuts were added here.

Imports preserve CSV/JSON/TXT/HML bytes plus source program, definition, UTC, size and SHA-256. No metrics are recalculated. Imports have no inferred run association. HML remains opaque until an established export/conversion path is validated. Local paths/receipts stay private; only authored code, methodology and sanitized evidence belong in Git. Existing raw test archives remain unchanged.

The PresentMon adapter recognizes documented v2-style headers only when that provider is declared. It previews at most five original rows and preserves application/PID/swapchain, timing convention and frame type when supplied. Documented GPU, display, input, instrumented and PC-latency fields retain units/endpoints; absent/blank/NA fields stay unavailable. Provider version is user-declared, not inferred from headers. Software input-to-display fields are not optical camera/animation latency measurements. NVIDIA App has no metric export adapter yet; FrameView SDK collector is not launched to obtain one.

Rollback: close Game Tool Hub, preserve its private imports, and remove only the optional authored helper/launcher. No game or Afterburner/RTSS configuration restore is required for this connection work. Closing the panel does not terminate other applications or the historical idle collector.

## Next learning steps

1. Core panel/read-only connections are accepted; optional native Browse/free-text automation remains separate. Keep capture controls absent.
2. Before using populated RTSS statistics, preserve exact provider low method, interval and frame coverage. Current SDK connection does not establish those game measurements.
3. Validate actual saved PresentMon/NVIDIA or analyzer output and choose any further adapter by documented export capability. No real latency CSV exists in this evidence set. Installation or recording requires a separate requested action; no installer/service was added here.
4. Add explicit user-controlled settings adapters only for requested supported actions, with snapshots, visible state and rollback. Keep hardware tuning, game/profile changes and capture activation separately scoped.
5. Resume game scenarios and performance validation only after an explicit user request.

Primary references reviewed 2026-10-11: [MSI monitoring/OSD guide](https://www.msi.com/blog/msi-afterburner-on-screen-display/), [Intel PresentMon 2.6.0 console field definitions](https://github.com/GameTechDev/PresentMon/blob/v2.6.0/README-ConsoleApplication.md) and [NVIDIA's standalone FrameView application](https://www.nvidia.com/en-us/geforce/technologies/frameview/). Installed RTSS SDK/profile evidence governs this exact configuration; a generic guide does not establish current tool state.
