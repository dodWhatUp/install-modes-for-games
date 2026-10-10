# Tool and feature resource overhead comparisons

Requested 2026-10-11. The main goal is to measure CPU, GPU, RAM and VRAM costs of individual tools, game-specific features and compatible combinations. A tool catalog and prepared experiment plans support this goal; they do not supply measurements or prove compatibility by themselves. Game benchmarks and recording remain deferred behind the [architecture gates](GAME-TOOLS-ARCHITECTURE.md).

## Three different costs

1. **External process cost:** a manager, overlay app, recorder or sensor provider while closed, idle, active or doing a named operation. Measure the correct process tree and service/helper scope. Installation duration and idle overhead are different workloads.
2. **In-game feature cost:** an injected host/add-on, shader, engine setting, DLSS runtime/model or mod feature running inside the rendering process. It may have no separate process at all; use controlled feature comparisons rather than assigning an arbitrary share of game memory to a DLL.
3. **Combination effect:** compatible components can share resources, duplicate work, add synchronization or change the workload. Their combined cost need not equal the sum of isolated deltas. Unsupported combinations are excluded, not automatically installed for comparison.

For example, record a ReShade host, a Cyberpunk-specific RenoDX add-on and a selected RenoDX feature separately. RHI's own process usage, files/settings it deploys and the running graphics components are distinct records. RHI advertises management of ReShade/RenoDX, OptiScaler and DLSS versions; those are upstream capabilities, not automatic local compatibility or permission to run Update All. [RHI upstream](https://github.com/RankFTW/RHI).

The user-named “DLSS SWITCHER” has unresolved exact identity. [DLSS Swapper](https://github.com/beeradmoore/dlss-swapper) is a verified candidate, not an assumed match. Its documented role is version management for supported games, not adding missing engine DLSS inputs. The catalog must keep aliases and confirmation state explicit.

## Catalog records and relationships

Store stable IDs, kind (tool, component, feature, store, mod manager or SDK/mod kit), role, original links, game/build/API constraints, version/review date, local installation versus runtime status, source confidence, settings/file owner, adapter capabilities and measurement coverage.

Relationships are typed and scoped: `manages`, `hosts`, `enables`, `depends_on`, `alternative_to` and `conflict_candidate`. A conflict candidate requires investigation; it is not a proven incompatibility. Capture conditions, versions and evidence on each edge. A feature's host dependency must survive experiment planning.

Support views by game, role, feature, relationship, installed/running/tested status, source freshness and automation support. Keep executable paths and native identifiers private. Official download/store links can be public; opening an app uses an observed registered interface, not an arbitrary URL/command. Direct installation is a later explicit action with provenance, snapshot and ownership checks.

Seed the catalog with ReShade, RenoDX, OptiScaler, RHI, Ultra+, measurement providers, native input tools, stores and mod managers. Add official game/engine mod kits through per-product researched adapters rather than guessing a universal SDK. The [read-only catalog source](../scripts/Game-Tool-Catalog.py) is a foundation; a dynamic integrated GUI and operation adapters require separate acceptance.

## Metrics and interpretation

| Resource or result | Preserve | Main limitation |
|---|---|---|
| CPU | Process/tree CPU time or utilization, normalization, cores, wall time, sampled phase | Different percentage conventions and bottlenecks are not interchangeable |
| GPU | Engine/load scope, frame/GPU time when provider reports it, clocks/power/thermal conditions | Utilization alone is not a causal GPU cost or proof of better/worse performance |
| RAM | Working set/resident versus private bytes and system commit, provider definitions | Summing process working sets can double-count shared memory |
| VRAM | Adapter dedicated/shared use versus process allocation/residency/budget when available | Whole-GPU usage is not game-only usage; cached allocation is not necessarily a leak |
| Performance | Provider-defined rendered/displayed FPS, frame time, lows, latency endpoints and coverage | FG presentation cannot substitute for base-render performance; missing reports remain unavailable |
| Quality and stability | Effective feature settings, HDR/SDR, artifacts, resets, crashes and workload differences | A faster run with less rendering work is not a like-for-like mod improvement |

Existing programs collect and calculate specialized metrics. Import original reports, definitions and source versions; do not build a duplicate lows/latency/trace engine. A comparison layer can calculate simple differences from validated provider summaries without relabeling unlike definitions.

## Experiment protocol

For every in-game one-factor or 2×2 cost plan, pass the [mandatory FG/memory preflight](GAME-PERFORMANCE-MEASUREMENT.md#mandatory-benchmark-preflight--fg-and-memory) before collector activation/runs: Dynamic MFG inactive, effective FG Off or one matched fixed multiplier, matched PT/SR/quality and validated frame/memory scopes. Active/suspected/unverified adaptive FG or unknown mode blocks execution. Pure external closed/idle manager tests without a rendering workload may mark the FG gate not applicable. Stop and retain an interrupted/confounded run on memory warnings; do not change textures/budgets or disable the warning and reuse it as a matched run. Explicit adaptive-FG experience studies remain separate. This is an agent procedure/planner requirement, not implemented automatic Hub detection or permission to resume deferred work.

1. Define the exact question, game/build, scene/phase, feature IDs and allowed mutations. Check dependencies, anti-cheat, hooks/file owners and current deferred scope. Save baseline plus current-state snapshots before any later change.
2. For external apps, define process/service tree and closed/idle/active workloads. For injected features, hold the shared host and unrelated layers constant. Record requested and observed states separately.
3. Validate provider coverage, timestamps/clock mapping, metric definitions and sampling phase. Measure the coordinator/provider overhead; optional video needs its own matched overhead comparison.
4. Use repeated matched runs and A/B/A or counterbalanced order where practical. Separate first launch/shader compilation, warm revisits and steady state. Preserve cache state; no blanket cache deletion. Match resolution, SR/RR/FG, HDR, PT, camera/scene, settings, limiters, background apps and thermal/power conditions.
5. For two compatible independent features A and B on shared host H, use H, H+A, H+B and H+A+B. Do not create an impossible B-without-host condition. If disabling A also removes a mandatory B dependency, use a different valid experiment and state that independent attribution is unavailable.
6. For a consistently defined additive cost metric Y, show A delta, B delta, combined delta and the interaction contrast `Y(H+A+B) - Y(H+A) - Y(H+B) + Y(H)`. This is a descriptive contrast, not proof of a root cause or statistical significance. FPS is nonlinear; prefer provider-reported frame-time costs where available. Keep noise/spread and unequal workloads visible.
7. Stop on instability or excessive pressure, preserve first failure evidence and restore only owned changes. Do not force a game crash or load a save merely to fill a comparison table. Mark incomplete runs and unresolved confounders.

An optimization study may separately change quality/model/engine settings, but must label that workload change. A feature's cost can be justified by better image quality; present both rather than automatically ranking the lowest memory number as best.

## Prepared operations for Codex

Each catalog capability names the supported route, parameters, prerequisites, expected observations, timeout/cancel behavior, side effects and rollback. Start with read-only discovery, configuration inspection, report imports and experiment preparation. Later actions can open a verified interface, adjust an explicitly selected owned setting, install a selected component or coordinate an approved capture. No general-purpose hidden input endpoint or unrestricted shell execution is implied.

Expose concise structured summaries and diffs so the chat can reuse known facts rather than rediscover every menu. Unknown automation stays unsupported; app source, availability and interfaces must be checked before claiming an adapter works. Prepared scripts/recipes do not grant authority beyond the user's current request.

RenoDX already documents a relevant optional route: a game-side DevKit add-on connects through a local bridge to MCP for frame/shader/resource inspection and selected live editing. This is an upstream-supported diagnostic candidate, not installed or tested here. Its snapshots, resource cloning and replacement operations can affect rendering/resource use, so keep diagnostic sessions distinct from passive performance comparisons. Installing/configuring it or exposing modifying operations needs a separate scoped action and validation. [RenoDX DevKit MCP documentation](https://github.com/clshortfuse/renodx/blob/main/docs/DEVKIT_MCP.md).

## Acceptance and future scope

Pure catalog checks validate IDs/edges, dependency-preserving plans, filters, unresolved aliases and null measurements. Runtime acceptance later verifies dynamic UI, real adapter interactions and provider readback. Resource results need actual comparable runs and uncertainty; synthetic fixtures are never costs.

The final Cyberpunk highest Ultra+ VRAM test remains a separate gated experiment. Exact highest compatible preset and effective PT/SR/RR/FG must be established; historical PT21 Fast runs do not answer it. Save-free built-in benchmarks can provide repeatable evidence, while difficult game routes and unsupported per-feature isolation remain future adapters.
