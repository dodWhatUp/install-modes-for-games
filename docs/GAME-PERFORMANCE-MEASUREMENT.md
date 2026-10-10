# Game performance measurement

User-requested default, 2026-10-10: preserve machine-readable measurements and enough metadata for later analysis. Screenshots of results alone are insufficient. Use this procedure alongside the game-specific runtime record.

Implementation preference clarified 2026-10-10: existing programs supply complex metrics such as 1%/0.1% lows, latency and specialized sensor/trace analysis. The helper coordinates authorized tests and imports, compares and archives their outputs. Preserve tool versions, definitions, units, frame classes, coverage and sample sizes; mark undocumented definitions as unknown. Do not independently recalculate or relabel a program's lows, or build duplicate complex measurement engines, without an explicit user request. The definitions below are interpretation references, not a requirement to implement them ourselves.

## Capture and provenance

Each run needs an immutable ID, UTC timestamps plus local timezone, QPC/frequency markers, game/store/build, GPU/driver, display resolution/refresh/HDR/VRR, settings, native SR/RR/FG/Reflex state, mod versions/hashes, loaded owners, tool version/arguments, scene/save/route and cache state. Record requested versus observed settings separately. Store raw CSV/JSON and relevant logs privately; publish sanitized summaries and user-authored tools only. Include interrupted and failed runs with their failure boundaries. Never overwrite a prior capture.

Use one frame-event collector and one resource collector. Prefer an existing working PresentMon/FrameView path. MSI Afterburner/RTSS are useful existing alternatives when their logged fields and sampling are validated; do not enable an additional hook/limiter just to get an overlay. A monitoring overlay can change the workload. Record collector CPU/memory and sample duration, and check overhead with repeated matched runs before attributing a small difference to a mod.

`scripts/Measure-GameResources.ps1` is an initial read-only resource prototype whose existing evidence remains usable. `scripts/Analyze-FrameCapture.py` is a historical prototype for an explicitly selected timing column; under the clarified preference it is not the default provider of lows or latency. Prefer imports from validated existing programs for complex metrics. On this machine, ETW capture requires user-provided Windows privileges. An initial automated elevation was rejected; a renewed explicitly authorized approval prompt succeeded and the collector launched. Do not claim a frame CSV exists until readback proves it. Current Cyberpunk recording is on hold until the user explicitly resumes it.

## Memory, utilization and limits

| Quantity | Preserve | Interpret carefully |
|---|---|---|
| System RAM | physical total/available, system commit/limit, paging observations | Physical use, committed virtual memory and address-space reservation are different. Cache is not automatically a leak. |
| Game process | resident working set, private commit, CPU time deltas, process responsiveness | Working set includes shared pages; private commit is not necessarily resident RAM. Responding is not proof frames are flowing. |
| GPU adapter | total, driver-reserved, used/free VRAM; shared/committed counters when available | Adapter values include other processes. NVIDIA `memory.reserved` is driver reservation, not the game's requested reservation. |
| Game GPU budget | process-specific committed/resident values, WDDM budget/eviction counters if a validated source exposes them | Unknown until measured; do not substitute free adapter VRAM for the game's budget or create a second device and call its budget the game's. |
| GPU work | utilization, memory-controller activity, clocks/P-state, temperature, watts/power limit, clock-event reasons | Busy percent alone does not identify the limiting stage. Record power/thermal flags, their timestamps and durations. |
| CPU/storage | total and per-core use, per-process CPU, I/O and paging where supported | A single busy thread, streaming, presentation cap or foreground change may limit FPS even with modest total CPU usage. |

Limit diagnosis needs matching frame intervals, CPU/GPU durations, queue/presentation behavior, memory pressure and settings. Label direct flags as observations and a proposed CPU/GPU/VRAM/streaming bottleneck as an inference unless an intervention reproduces it. `N/A`, missing columns and unavailable sensors remain null, never zero.

## Mandatory benchmark preflight — FG and memory

User-confirmed default, 2026-10-11: before ordinary rendering-performance or injected-feature cost comparisons, verify that **Dynamic MFG is inactive** and effective FG is **Off or fixed at one known multiplier**, identical across compared conditions. Similar output FPS can conceal different rendered performance when an adaptive multiplier targets refresh/FPS. This is a mandatory agent procedure, not implemented automatic detection in the current Hub.

1. Identify the real rendering executable and classify the experiment: rendering/feature cost versus explicitly requested adaptive-FG experience. External manager-idle tests with no game-rendering workload may record this gate as not applicable.
2. Inspect the current native FG choice and effective global/per-game driver overrides, inheritance and mod/bridge FG owner. For NVIDIA, inspect the applicable `DLSS Override - Frame Generation Mode`, not just the game's x2/x4 selection. Preserve the observed mode, fixed multiplier or dynamic target/max multiplier, source/version, timestamp and available runtime/provider readback. A historical profile, saved native value, loaded DLL or output-FPS counter alone is insufficient.
3. Mark the preflight **PASS** only when Dynamic MFG is established inactive and effective FG Off/fixed is verified. Mark **BLOCKED** when adaptive FG is active, suspected or unverified, effective FG is unknown, or compared conditions differ. Do not start an ordinary comparison or silently substitute a different experiment. Any corrective settings change requires current authorization, a just-in-time snapshot, supported readback and restoration of the user's original settings afterward; the instruction itself grants no mutation or launch permission.
4. Match effective PT/RT, SR input/output resolution/model, RR, quality/texture/streaming, scene/cache, HDR, limiters and other non-tested conditions. Hold adaptive SR/automatic quality fixed for rendering-cost attribution, or label a separately requested optimization study. Verify the provider's frame classes and definitions before recording: rendered, app-present and displayed/generated FPS are distinct; never derive measured base FPS by dividing a total counter by a presumed multiplier. Preserve missing coverage as unavailable.
5. Record physical dedicated capacity, adapter-wide usage, game-process budget/residency/allocation, engine pools, process working set/private commit and system RAM/commit separately. Preserve a warning's reporter/version, exact text, time/phase and counter definitions. A mod's available-memory threshold is not proof of physical VRAM or system-RAM exhaustion. Suspend an ordinary comparison on a memory warning or severe sustained performance collapse, retain the interrupted/confounded run and diagnose safely. Do not dismiss/disable the warning, lower textures or raise a budget and then continue it as the same matched run.

An explicitly requested **adaptive-FG experience** experiment is separate: record its target FPS/refresh, maximum multiplier, effective state and rendered/displayed-frame coverage, and assess output smoothness/latency without claiming equal rendering cost from similar output FPS. Do not silently convert a blocked ordinary comparison into this class. Dynamic MFG is not Dynamic DLSS SR; disabling one does not establish the other is inactive.

The [Cyberpunk audit](../games/cyberpunk-2077/RUNTIME-VALIDATION.md#2026-10-11-interpretation-audit--effective-fg-mode-remains-unverified) illustrates the risk: historical approximately 149 game-reported FPS, native x2 selected but effective driver mode unverified, and PT-off versus PT21 workloads. The [warning history](../games/cyberpunk-2077/HISTORY.md) records Ultra+ rc7's `used / (used + reported available) (dedicated total)` HUD and proactive warning threshold; the native availability calculation remains unknown. [NVIDIA documents adaptive FG target behavior](https://www.nvidia.com/en-us/geforce/news/dlss-4-5-dynamic-multi-frame-generation-6x-mode-released/).

## Frame timing and stability

Capture individual events; resource samples at roughly 1 Hz cannot reconstruct frame pacing. Keep each swapchain and supported `FrameType` separate. Distinguish app-present rate, instrumented rendered-frame rate and displayed/generated-frame rate. Do not divide an FG counter by the multiplier and call that measured base FPS.

When an existing program exports them, preserve sample count and duration, mean/median, P90/P95/P99/P99.9/P99.99 milliseconds, average rate and worst intervals. Record unavailable fields as unavailable rather than creating a substitute calculation. Interpret reported lows using the source program's documented method; these reference definitions are different:

- Percentile reciprocal: `1000 / P99`, `1000 / P99.9`, `1000 / P99.99`; label these by their actual formula.
- Slowest-tail mean: `1000 / mean(slowest ceil(N * fraction) intervals)` for 1%, 0.1%, 0.01%. Keep it separate from percentile reciprocal and another application's differently defined “low”.
- Flag a tail as insufficient when it contains fewer than 20 observations; prefer at least 100 plus repeated runs. A 9600-frame scene contains only about one observation in the 0.01% tail. Do not advertise that as a reliable stability score.

Report dropped/not-displayed events, presentation mode changes and gaps. Preserve spikes above declared thresholds (for example 33.3/50/100 ms and twice that segment's median), their timestamps and duration; do not silently discard outliers. Missing ETW events or trace overflow invalidates associated statistics. Keep loading/transitions/capture interruptions as separately tagged segments, not hidden trims. Preserve the untrimmed trace.

Stability means scoped evidence: completed runs, crashes/device removal, frozen or nonresponsive samples, time to failure, allocation growth, loading/alt-tab/recreation and clean exit. One minute without a crash is short-session evidence, not a long-session guarantee. Three matched runs per configuration are the starting comparison; publish individual runs and spread, not just the best result. Change one layer/settings group at a time; identical scene alone is insufficient when PT, SR or FG differs.

## Latency and camera/animation tests

Preserve available render-present, GPU queue, display, PC/Reflex and input timing fields with their documented endpoints, coverage and `N/A` count. Software “input-to-photon” field names are not an optical measurement at the display. A benchmark with no meaningful input does not measure camera response. Do not infer latency from FPS alone.

Future tests need separate tagged actions: camera rotation, camera translation, HUD interaction and animation response. Input timestamps plus a repeatable visual change can estimate a software response boundary, provided clocks, motion blur, FG, animation interpolation and capture effects are recorded. Physical mouse-to-visible-pixel delay requires appropriate external measurement (high-speed camera/photodiode or supported latency hardware), calibration and repetitions. Game/simulation telemetry can help distinguish update rate from display rate; synthetic input or estimated optical flow is not engine motion data.

No continuous video by default. Save scene-start/end and result screenshots plus anomaly captures. If later diagnosing visual hitching/animation, authorize a bounded clip and measure recording overhead/HDR conversion. Saving a CSV has little token cost; feeding every video frame or screenshot to an agent does. Analyze numeric data first and inspect selected visual evidence.

## Cache and non-periodic coverage

Built-in repeated scenes can hide compilation and streaming hitches. Retain a future test boundary for a novel route, dense district, fast traversal, camera turns, new effects, save/load and area changes. Separate cold game start, first visit, warm revisit and documented shader/PSO-cache state. A cold process is not proof the shader cache is cold. Never clear global driver/game caches merely to manufacture a cold test; preserve cache metadata and recoverable game-specific state before an explicitly authorized targeted cache change.

Trigger the extended test when the benchmark and actual play disagree, the user reports uneven motion/input, allocation grows, or a game/driver/mod update changes shader/streaming behavior. Avoid quest advancement and risky saves. See the [future tool plan](GAME-TELEMETRY-TOOL-PLAN.md) and [Cyberpunk record](../games/cyberpunk-2077/RUNTIME-VALIDATION.md).

## Primary references

Reviewed 2026-10-10: [PresentMon console metrics and requirements](https://github.com/GameTechDev/PresentMon/blob/main/README-ConsoleApplication.md), [PresentMon ETW permissions](https://github.com/GameTechDev/PresentMon#user-access-denied), [NVIDIA SMI memory/utilization/clock reasons](https://docs.nvidia.com/deploy/nvidia-smi/index.html), [NVIDIA FrameView](https://www.nvidia.com/en-us/geforce/technologies/frameview/). Preserve the exact installed tool's help/schema; current upstream documentation does not establish that an older installed build exports the same fields.
