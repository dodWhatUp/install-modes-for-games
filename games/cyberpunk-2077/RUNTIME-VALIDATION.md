# Cyberpunk 2077 — Runtime validation, 2026-10-10

The user explicitly authorized launching and testing the clean ReShade/RenoDX/Ultra+ installation. This supersedes the installation-only handoff. Tests use patch 2.31 / Steam build 20383525, D3D12, RTX 5070 Ti 16 GB, driver 617.42, Ryzen 7 5800X3D and 64 GB RAM. A separate pre-runtime snapshot preserves 541 files, settings and all 221 save files. Private captures/logs retain the original evidence; this record contains sanitized observations.

## Layer tests and performance

All benchmarks use the built-in moving scene, 3840×2160 borderless, native DLSS Ultra Performance/CNN, RR off and native FG selected at x2. Values are **game-reported benchmark FPS**; base versus generated frames and frame pacing were not independently captured. PresentMon exited with code 1 and produced no CSV; its cause is unresolved. Do not divide these FPS values by two and call that measured base FPS.

| Profile | Average / minimum / maximum FPS | Scene duration / frames | Peak GPU allocation in capture | Result |
|---|---|---|---|---|
| Stock, original PT off | 148.53 / 129.33 / 171.04 | 64.23 s / 9540 | 10759 MiB | Completed |
| ReShade only | Not benchmarked | Startup/menu check | Not measured | D3D12/HDR host initialized and closed cleanly |
| ReShade + RenoDX, original PT off | 149.46 / 133.38 / 167.95 | 64.23 s / 9600 | 10669 MiB | Completed; control/presentation test passed |
| Ultra+ only, PT21/Fast/Vanilla streaming | 149.60 / 134.08 / 167.65 | 64.20 s / 9604 | 14533 MiB | Completed; PT setting true, RR false, NRD DLSS |
| ReShade + RenoDX + Ultra+, PT21/Fast/Vanilla streaming | 148.68 / 133.33 / 167.26 | 64.19 s / 9544 | 14228 MiB | Completed; PT true / RR false persisted |

GPU allocations are whole-device readings from roughly 90-second windows including loading/menu transitions, not isolated per-mod VRAM or long-term leak measurements. Stock and HDR differ by 0.63% in one run each, which does not establish a performance improvement. Ultra+ introduces a different PT workload; its similar FPS does not prove a speedup over native path tracing. Peak temperature was 50°C stock, 52°C HDR and 58°C Ultra+. No captured sample lost the game process.

### 2026-10-11 interpretation audit — effective FG mode remains unverified

Read-only audit of all four original result images and corresponding saved native-settings snapshots confirms FG Yes/MFG 2X, VSync and the native FPS limiter off, DLSS CNN Ultra Performance and 4K borderless. The pre-runtime checkpoint preserves NVIDIA DRS binary files, but no decoded per-run override or effective-multiplier readout was found. No frame CSV exists in the scoped runtime-run tree or either retained measurement archive; available CSVs contain resource samples, not frame classes. These checks strengthen selection provenance, not effective fixed-x2 or base-FPS evidence.

The user questioned whether Dynamic MFG masked a rendered-performance difference. This is a valid confounder: [NVIDIA documents](https://www.nvidia.com/en-us/geforce/news/dlss-4-5-dynamic-multi-frame-generation-6x-mode-released/) adaptive frame multipliers targeting a selected FPS or display refresh rate. Similar output rates can therefore coexist with different rendered-frame rates. The historical September 13 NVIDIA App observation showed Dynamic MFG targeting maximum refresh, up to 6x; it does **not** establish the effective mode during each October 10 run. The clean-rebuild record states driver overrides were not revalidated. Native menu selection of x2 is not proof that a driver override left fixed x2 effective.

Keep the raw results above, but do not interpret approximately 149 game-reported FPS as equal rendering performance, infer base FPS by dividing by two, or claim Dynamic MFG caused the similarity. The display was 150 Hz, but recorded maxima of 167–171 FPS also prevent calling these results a demonstrated hard 150-FPS cap. No independent frame-class capture succeeded. Stock PT off versus Ultra+ PT21, one run per configuration and differing capture windows are additional limitations.

A future controlled comparison must match the intended rendering workload, SR/resolution, scene and cache conditions, record native choices and effective per-game/global driver overrides per run, and distinguish rendered from displayed/generated frame rates using a validated provider. An FG-off control and a verified fixed-FG comparison can separate rendering cost from the intended Dynamic MFG experience; neither is authorized or executed by this read-only review. Preserve provider definitions for frame timing/lows and memory scope. [NVIDIA's integration guide](https://github.com/NVIDIA-RTX/Streamline/blob/main/docs/ProgrammingGuideDLSS_G.md#130-how-to-obtain-the-actual-frame-times-and-number-of-frames-presented) also distinguishes actual presentation counts and display-change timing; current upstream API documentation is not evidence that this older installed runtime or an existing collector supplied those fields. Game tests and benchmarks remain deferred.

Before any later ordinary cost comparison, pass the [mandatory FG/memory preflight](../../docs/GAME-PERFORMANCE-MEASUREMENT.md#mandatory-benchmark-preflight--fg-and-memory). Effective Dynamic MFG must be verified inactive; unknown state blocks the comparison. This documentation update does not perform that live check or resume deferred tests.

## HDR and controls already observed

- Windows reports HDR enabled at 3840×2160/150 Hz, PQ/BT.2020; the game uses HDR10 PQ. ReShade initialized a D3D12 `R10G10B10A2` swapchain with color space 12 (PQ/BT.2020).
- RenoDX registered 30 custom shaders / 27 injections. The user physically pressed Delete; ReShade opened and its direct **RenoDX** tab displayed the Cyberpunk controls. An exposure change from 1.00 to 0.61 visibly darkened the rendered menu; reset returned it to 1.00 and restored brightness. The user closed the panel with Delete. This proves shader-control delivery/presentation beyond DLL registration.
- Author defaults include detected display peak 644.2364 nits and game brightness 203 nits. Physical peak/black-level calibration was not measured. HDR screenshots are converted for display and cannot establish physical HDR appearance.
- Grave/tilde opened and closed CET/Ultra+ during the isolated Ultra+ run. Its panel showed PT21, V5, Fast, Game/Vanilla streaming and NRD DLSS. RED4ext/UltraTool logs show engine operations including V5, bright-light compression and particle/lighting processing; AudioPoolFix created the enlarged four-bank pool and serviced its first request.

## PT/RR startup correction

Starting Ultra+ PT21 with the original native PT flag false triggered a transition to PT true **and RR true**. Ultra+ then changed its denoiser to RR Clean. That is incompatible with this stack's native DLSS 310.1; Clean/Sharp require 310.6+. An immediate console read after setting RR false was misleading: the later native menu/disk state returned to RR true. That attempt is recorded as **failed persistence**, not a successful fix.

With the game/store/helpers closed and a fresh current-state checkpoint, changed only native `RayTracedPathTracing.value` from false to true and reseeded Ultra+ NRD DLSS. Reversing that one native value reproduces the exact pre-test settings text/hash. On restart, the engine read RR false / PT true, the native menu displayed RR off, and NRD DLSS persisted after `ConfirmChanges()` and through the completed benchmark. Ultra+'s author PT21 configuration deliberately sets the conventional `RayTracing` flag false and `RayTracedPathTracing` true; the benchmark's generic “Ray Tracing Enabled: No” field does not enumerate that separate PT flag.

The new native PT seed aligns the already-selected PT21 profile before startup. Preserve the original PT-off settings as recovery. If enabling RR later, select Vanilla denoiser with the current native runtime and verify after transitions. Do not silently replace the NVIDIA runtime set.

## Remaining combined checks

The combined benchmark passed. Loaded-save F9/F5/F6 behavior, camera/HUD, alt-tab and final save/configuration restoration are still in progress. Final conclusions belong here only after their observations are recorded. These are short-session startup/rendering observations, not long-session stability.

## Resource capture and future analysis

On explicit user request, added raw RAM/commit and GPU reservation/clock/limit measurements for the combined run. The 90-s resource window includes loading and most of the 64.19-s benchmark; it is not an exact scene-only interval. Ninety samples reported peak adapter use 14228 MiB, driver reservation 306 MiB, peak process working set 7563 MiB and private commit 18375 MiB. Peak system unavailable physical RAM was 35750 MiB, and system commit 49454 MiB. These are different quantities, not interchangeable game RAM usage. Adapter readings include other processes. Game-specific WDDM budget/reservation and eviction data are unavailable.

Whole-window GPU utilization averaged 79.93% (maximum 99%); peak temperature 56°C and power 213.86 W with a 300-W configured limit. No sampled software power-cap or hardware thermal-slowdown flag was active. No sample lost the process or reported it nonresponsive. These samples do not prove the absence of short hitches or establish a CPU/GPU bottleneck. Resource collection took about 149 ms per 1-s sample on average (222 ms maximum); collector CPU/observer effects have not been isolated with repeated A/B runs.

Installed MSI Afterburner/RTSS were idle and their profiles were not changed. NVIDIA's bundled PresentMon 1.9.12728.0 still exited with code 1 and no CSV or diagnostic. Downloaded standalone PresentMon 2.6.0 from the official Intel project, verified its Intel Authenticode signature and SHA-256 `B2A706BC6AD475749E3B7E3409263AA1E6906D45BDCF993F6DBC0F660188F1AF`. Its probe explicitly returned code 6 / ETW access denied. Automated administrator launch was rejected by approval review (`blocked by policy`). A private, inspectable command file is ready for manual user launch; it targets only the game PID with a temporary Ctrl+Alt+F8 capture hotkey. No ETW privileges or global security settings were changed.

After the user explicitly requested opening the approval prompt, a renewed administrator launch succeeded and the capture process is now waiting on its hotkey. This supersedes the earlier launch blocker; read back the first valid CSV before claiming ETW capture is working. There are **no measured 1%/0.1%/0.01% lows, per-frame pacing, rendered/generated-frame split or latency results yet**. An offline analyzer scaffold passes synthetic tests, but those tests are not game evidence. A roughly 9600-frame scene has only one 0.01%-tail observation and is too short to advertise that statistic as reliable. The current protocol saves CSV/JSON plus selected screenshots, not continuous benchmark video. Full raw captures remain private and are retained for later reanalysis.

The user requested a future tool, novel-route/shader-cache tests and more nuanced camera/animation latency coverage. See [measurement method](../../docs/GAME-PERFORMANCE-MEASUREMENT.md), [backlog plan](../../docs/GAME-TELEMETRY-TOOL-PLAN.md) and [issue #3](https://github.com/dodWhatUp/install-modes-for-games/issues/3). No reminder or scheduled experiment was created.

## Detailed-capture activation attempt — 18:30–18:33 local

The user renewed the FPS/1% low/latency request and provided a foreground test window. PresentMon remained alive with the approved game PID. An injected Ctrl+Alt+F8 produced no CSV even after subsequent readback. A physical Ctrl+Alt+F8 was requested, as physical Delete had already succeeded where automation did not. This is an input/capture activation boundary, not proof of a game crash or an ETW permission failure. Native menu navigation also encountered physical-input/focus interruptions and unreliable automation; these attempts are not eligible as clean benchmark repeats.

A separate resource window preserves the menu/capture probe. No benchmark 1% lows or latency may be inferred from a menu probe or advertised until valid scene frame rows and metric coverage are checked. Prior single-run FPS/VRAM comparisons remain the available game evidence. ReShade alone was not benchmarked; HDR is ReShade plus RenoDX. Ultra+ versus stock changes PT, so isolate native PT versus Ultra+ with matched settings and repeated runs in a subsequent controlled comparison.
