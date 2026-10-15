# Unified game tools architecture and build plan


## 2026-10-14 — Read-only planning and UMM instance slice

The canonical adopted source is `0.27.0-preview.1`. It adds an opaque private
installation registry, one accepted UMM folder/manifest reader, deterministic
goal-plan DAGs and declared ownership/conflict graphs. The four new modern tools
are available only on the multi-game endpoint; legacy MCP tool shapes remain
unchanged. AI cannot register a path, and public results omit local filesystem
paths. Plans create no job or proposal, and inspections write no game, manager,
profile, save, input or graphics state.

Read the [0.27 design and boundaries](AI-PLANNING-READONLY-SLICE.md) and the
[bounded Windows/source-package/external-stdio acceptance](AI-PLANNING-READONLY-WINDOWS-ACCEPTANCE-2026-10-14.md).
The runtime-tested product source is commit `e454433e81e067b1f11267a3cac18081b60512f8`;
PR #9 merged reviewed head `ab9c2cdf32dd9d361aa4273aca6e10a168e864d8` into
canonical `main` as `ef38d94be4fb4847cbbeda5f8fe41455b267aeaa`. Candidate R9
passed synthetic UMM, embedded-private-metadata, filtered-pagination and native
Windows process-level gates; the same acceptance record preserves R8, R5, R4 and
bounded R6/R7 evidence. A
separately authorized real-folder read remains unperformed. Install, upgrade,
disable and rollback transactions are still later work.

## 2026-10-14 — AI Efficiency Foundation implemented

The first read-first AI slice is implemented in `0.26.0-preview.1`: protocol framing is separated from deterministic business tools; modern and legacy stdio coexist; modern results expose explicit completion/evidence/effects/privacy; packaged knowledge supports bounded search/fetch/resources; continuation and batch tools inspect without replay; catalog/report reads reuse existing owners. Native Windows/Tk and independent external stdio acceptance passed. Local approval remains the only consequential boundary, and no daemon, arbitrary command/path, automatic execution or cloud credential was added. Read the [design](AI-EFFICIENCY-FOUNDATION.md), [Windows/client acceptance](AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.md) and [canonical reconciliation](AI-EFFICIENCY-FOUNDATION-RECONCILIATION-2026-10-14.md).

The next architecture gate remains read-only: separately accept another manager adapter or richer UMM installed-state evidence, then expose a planned-versus-observed diff through the existing owners. Write transactions remain later work.

## 2026-10-13 — Mods and shared AI source integration

**Hub 0.21.0-preview.1 source candidate**, based on the verified 0.20.2 export.
[Current integration, controls, provenance and remaining gates](MODS-AI-INTEGRATION.md)
adds the Mods and AI & automation workspaces, one Kingmaker recipe, local approvals,
MCP/CLI read-and-proposal interface and explicitly shared provider/tool summaries.
Source integration is not a Windows deployment, live provider acceptance or Git
publication. All original native Studio/AHK files remain byte-identical; original
features and GT-001–060 retain their existing owners and historical acceptance.

This advances **GT-006/008/009/034/040/041/055–059** within their existing scope.
Named mod operations share their previous ledger, overlay selection uses the original
Store, reports use their original parsers, and approvals reuse GameToolJournal.
No duplicate project queue, collector, remapping system, task master or cloud sync
was created. No game, capture, driver or benchmark action was started.


Continuation, 2026-10-12: [Hub 0.13.2 / Studio 2.2](UNIFIED-GAME-TOOLS.md)
adds a shared feature/goal registry and optional coherent workspace around the
existing panels, private data export/import and additive shared-record migration.
Schema/data versions are separate from program versions; native formats remain
opaque and byte-preserved. Compatible journal schema-1 evidence is readable
across module releases without rewriting immutable records. Source ownership,
bootstrap updates and restart cleanup strengthen the existing update path.
This is incremental reuse, not a replacement of every tool or implementation of
cloud sync/internal live automation. Desktop acceptance is recorded separately
after installation. Games, benchmarks, capture and deferred game-input work
remain stopped. Older dated acceptance paragraphs below remain historical.

Current continuation, 2026-10-11: [Hub 0.10.0](../examples/game-tool-hub/README.md#offline-provider-health-and-editable-scenarios--0100) implements the bounded offline provider-health and editable scenario portion of the benchmark-derived contracts below. Readiness 0.1.0 and Coordinator/Sessions 0.4.0 reuse fixed capture/journal/publishing guards; all earlier features remain. [Acceptance/preservation receipt](GAME-TOOL-CONNECTIONS.md#2026-10-11--0100-offline-provider-health-and-scenario-contracts): 870 toolkit passes/two skips, 11 separate AHK source checks and 52 export contracts. Mock health/declared preparation is never live capture, FG PASS, optical-latency proof or runner acceptance. Proposed observation/OCR/product adapters, recording/player and AHK migration remain unfinished; all game/capture deferrals remain. Earlier “current”/“proposed” paragraphs retain their dated boundary.

Current continuation, 2026-10-11: [Hub 0.9.0](../examples/game-tool-hub/README.md#installation-and-diagnostic-dry-runs--090) adds a generic data-only recipe engine/view and fixed workflow coordination, retaining all prior features. Coordinator/Sessions 0.3.0 reuse Journal 0.1.0 and source checks. Private change lists, owner/dependency/hash/recovery blockers, typed diagnostic evidence requests and conditional rollback plans are fixture-tested; no executable installer/rollback or current live preflight is supplied. GT-034/035/036/040 remain partial: researched per-game/product adapters and actual acceptance are separate. The 0.8.0 and older paragraphs below retain dated evidence, not latest-version claims. [Current receipt](GAME-TOOL-CONNECTIONS.md#2026-10-11--090-offline-workflow-dry-runs) owns scope; game/input/benchmark/recording deferrals remain.

Current continuation, 2026-10-11: Hub 0.8.0 adds [selected saved crash-evidence intake](../examples/game-tool-hub/README.md#saved-crash-evidence-intake--080) and Coordinator/Sessions 0.2.0, retaining Journal 0.1.0 and existing features. Bounded XML/journal/opaque-text inputs can form private hashed packets and a portable uncertain timeline. This completes an offline portion of gate 4/GT-028, not the full live crash companion. Tables describing 0.7.0 below remain historical foundation evidence. Live heartbeats/process/WER collection, recorder contracts/player and AHK/keymap integration are separate remaining stages; game/input/benchmark/recording deferrals remain unchanged.

Proposal, 2026-10-11. Combine the measurement Hub, optional AHK input module, overlays and keymap work through one shared coordination core. Preserve their working features and native device profiles. A single user interface can expose the modules without turning the entire project into one large AHK script.

The current boundary includes local Hub catalog integration, read-only FG planning gates, offline saved-summary comparison/reporting and the Hub 0.7.0 offline session/journal foundation. Broader operational adapters remain planned. Use the [master checklist](GAME-TOOLS-MASTER-CHECKLIST.md) for consolidated requirement status. Game input acceptance follows the tooling gates; MFG/FrameWarp remains deferred. The requested Cyberpunk highest-level Ultra+ VRAM benchmark comes last, after the earlier work and a user-facing continuation proposal. This plan does not activate recording, launch games, load saves, change graphics or schedule work.

The same-day extension makes individual tool/feature resource cost and combination interactions the primary analysis goal. Use the [typed catalog and overhead protocol](TOOL-RESOURCE-OVERHEAD.md), [knowledge and recovery index](GAME-TOOLS-KNOWLEDGE-INDEX.md) and [automation procedures](AUTOMATION-OPERATING-PROCEDURES.md). Extend the shared registry with managers, stores, official mod kits and scoped prepared capabilities; distinguish their external processes from the features they deploy or host inside a game.

## Architecture options

The preferred interface foundation is [compact UI and structured content design](UI-AND-CONTENT-DESIGN.md). Reuse a shared editable selection/search/entry component and contextual Show/Hide/disclosure controls across the existing host's pages where appropriate. Keep view preferences separate from operational settings and native profiles; maintain visible active state, overrides and errors. Use the same content hierarchy for help, learning materials and explanation exports. Integrate these decisions and fast behavioural checks into each requested creation slice, while preserving existing interfaces and source owners. Deeper usability research and shared component/content patterns are a future integration opportunity.

1. **Recommended: shared core with modular tools.** A small Python library supplies registry, sessions, capabilities, evidence and workflow state. Existing AHK handles hotkeys, pictures and guarded input; native Azeron/reWASD/Steam Input retain remapping; existing measurement/recording tools provide their specialized outputs. Benefit: reuse without discarding features. Main risks: interface migrations, key ownership and capture overhead. Difficulty 4/5; high design confidence, runtime confidence pending acceptance. Rollback: disable new modules and retain existing entry points, source and settings checkpoints.
2. **Keep separate tools with shared exports.** Standardize metadata and handoffs without a shared runtime or integrated panel. Benefit: quicker, smaller changes. Conflicts: manual coordination and duplicated state remain. Difficulty 2/5; high confidence for incremental adoption. Rollback: ignore the optional exports; original tools remain usable.
3. **Rewrite everything as one program.** Replace current implementations and potentially native integration surfaces. Benefit: one codebase. Conflicts: greater regression risk, duplicated specialized functions and harder rollback. Difficulty 5/5; low confidence relative to option 1. Rollback requires restoring every replaced component. Not recommended.

## Existing components and acceptance

| Component | Observed or recorded capability | Remaining boundary |
|---|---|---|
| Game Tool Hub 0.7.0 | Original readers/imports/registry/Catalog/Comparison retained; optional Sessions panel and structured offline CLI with compact ownership/lifecycle and append-only evidence | Tests are fixture/withdrawn-Tk contracts, not observed live desktop/game acceptance. Real rendering imports remain BLOCKED; broader adapters, runner, crash recording and synchronized video remain separate |
| Shared coordinator/journal 0.1.0 | Explicit fresh offline sessions, fixed saved-summary/comparison capabilities, cooperative expiry/cancellation, fsynced hash-chain records and new-copy verified-prefix recovery | No existing-session replay, desktop-wide reservation, game control, live heartbeat/WER collector, recorder or crash-cause diagnosis; durability guarantee is limited to verified-prefix process-interruption evidence |
| Game Tool Catalog 0.1.1 | Filterable typed catalog, dependency-preserving overhead plans and 35 pure tests | Read-only planning foundation; no external-tool execution or measured overhead acceptance |
| Overlay Studio 2 integration | Optional fifth tab and library wiring; 60 original methods retained; settings hash unchanged; saved picture preview observed after loader repair | Module Start/Stop/restart after the latest repair, HUD output and original-feature regression checks |
| GameInputModule v0.5-preview.3 | Native integrated-host validation, 36 module plus 8 host policy checks; installed and repository source match | Text, Unicode, Enter, Escape, hold/release and cancellation in each game |
| Historical Control Helper v0.3.1 | Partial agent-operated menus, one digit, caret and Backspace in both games | Does not validate the refactored host or extended actions |
| Azeron SHARED R5 | Four SOFTWARE profiles loaded; native events support three momentary selectors and release to BASIC outside games | Ordinary outputs, joystick/chords, gameplay prompts and native Import-dialog acceptance |
| Per-game keymap labels | Request and data-contract proposal in draft PR4 | Label generator implementation and acceptance |

Sources: [Hub evidence](GAME-TOOL-CONNECTIONS.md), [input integration record](../examples/game-input/OVERLAY-STUDIO-INTEGRATION.md), [draft keymap brief/PR4](https://github.com/dodWhatUp/install-modes-for-games/pull/4), and the requested benchmark/keymap chats. The follow-up owner report confirms all planned Pro material was already received in its separate workstream. Do not request it again; use that owner's handoff/revision for later scoped reconciliation. Its unseen code is not part of this acceptance claim. Follow [knowledge maintenance](KNOWLEDGE-MAINTENANCE.md) rather than replacing rich masters with summaries.

## Shared core and ownership

The component table is not the complete backlog. The [60-item requirement ledger](GAME-TOOLS-MASTER-CHECKLIST.md) preserves newer related-chat owner reports (including R8 and Pro transition-preservation work) and their independent-audit limits. [Offline reporting](OFFLINE-COMPARISON-REPORTS.md) accepts explicit normalized summaries or two reviewed original-summary adapters: provider metrics retain lineage, missing/failed runs remain visible, and eligible deltas do not certify compatibility, causal cost or runtime FG. Original-byte identity is not a measurement-validity seal. It adds no shared action server or AHK/profile migration.

The intended shared core serves input, measurement, mod workflows, crash evidence and label rendering through versioned contracts. Front ends remain replaceable; a new adapter should add a capability to the common registry rather than copy discovery and logging into every tool. The implemented 0.1.0 core deliberately serves only saved-data operations; it does not claim that every existing tool has migrated.

Implemented interfaces and usage are in [Hub Sessions](../examples/game-tool-hub/README.md#offline-coordination-and-crash-safe-journal-foundation--070). [Coordinator](../scripts/GameToolCoordinator.py) reuses the existing bounded saved-report/comparison backends and records compact action identity/outcome, not raw report or typed-input data. [Journal](../scripts/GameToolJournal.py) writes ordered UTC/monotonic clock-identified records, acknowledges only after flush/fsync and refuses continuation after durability failure. Inspection is read-only; recovery checks drift and publishes a new exclusive verified-prefix copy, never rewriting the original or conferring permission. An incomplete journal is not a game-crash verdict. The next operational adapter must independently establish scope, cancellation, target and result acceptance; adding a capability is not authorization to use it.

| Shared service | Responsibilities | Ownership boundary |
|---|---|---|
| Registry and capabilities | Games, real executables, devices, native profile revisions, installed tools, supported actions and freshness | A discovered or connected tool is not automatically permitted to capture, write settings or send input |
| Sessions and workflow | Scope, run/phase IDs, deadlines, cancellation, checkpoints and rollback recipes | No automatic game launch, save access or resumption of deferred work |
| Desktop and key reservations | One cooperating desktop-test owner, temporary triggers, output holds and expiry | Cooperative coordination, not an OS-wide lock or a bypass of control-tool guards |
| Evidence and clocks | Provenance, units, hashes, event order, source timestamps, uncertainty and archive state | Sent is not observed receipt; observed receipt is not graphics-feature correctness |
| Adapters and cache | SDK/export/UI adapters, bounded refresh, source revision and change notifications | Native software retains device remapping; established tools retain specialized measurements |
| Privacy and exports | Ephemeral payloads, retention limits, redaction and private versus publishable bundles | No automatic upload, microphone capture, secrets or raw private logs in Git |

Keep heavy discovery, file hashing, rendering and analysis away from AHK hotkey callbacks. Cache slow inventory separately from live readings. Use bounded queues, cancellation, stale-data markers and dropped-event counters. Batch related reads and send compact changes to the chat instead of repeated full inventories. Measure responsiveness and overhead before claiming a speed improvement.

## Session and action contracts

Before extracting code, define these shared records and test their migrations:

- **Session:** schema version, exact scope, owner, target identity, start/expiry, requested capabilities and stop conditions.
- **Run and phase:** scenario revision, observed settings/mod/tool versions, baseline hashes, warm/cold state, source file associations and reasons for excluded comparisons.
- **Action:** ID, allowed target/context, trigger and all possible output keys, total duration/character budget, cancellation and release policy. Typed payload stays ephemeral and is not written into the evidence journal.
- **Observation:** source, sample/receive time, units, freshness, coverage and evidence state. Use Requested → Armed → Dispatched → Observed → Verified; allow Failed, Cancelled and Unknown at each relevant boundary.
- **Event:** ordered sequence, UTC and monotonic/QPC anchors, phase marker, provider lifecycle, gaps and outcome. Preserve original provider timebases and clock precision.
- **Artifact:** immutable source bytes/hash, provider definition, frame class, run association, privacy class and incomplete/recovered status. Unknown associations and metrics remain null, not zero.

One helper instance owns injected holds. Release only its owned keys on cancellation, focus loss and normal Stop; forced termination cannot guarantee cleanup. The reservation audit must cover Studio shortcuts, management chords, game/mod hotkeys and known native mapper outputs. SHARED R5 TOOLS includes F2/F3/F8, which overlap current diagnostic triggers. Do not silently rewrite native mappings to resolve them.

Current `BindingPlan()` represents extended output as `prepared`; it does not enumerate Enter and every permitted held key. Expand that contract before relying on it as a complete reservation audit. The current 4,096-character limit can permit a long dispatch at per-character timings: add a total action budget and test timeout/cancellation, not merely a character limit.

Host diagnostics also need an inert entry point. The existing host retains `#SingleInstance Force`; invoking that same filename with a diagnostic argument while it is live can replace the host before the diagnostic branch. Until separated, run those checks only after verifying the host is stopped.

## External tools and Codex integration

Adapters declare discover, read, import, open interface, capture and write capabilities separately. Prefer documented SDKs, shared-memory contracts and stable exports. Use supported UI observation where needed; OCR is a bounded fallback with confidence, expiry and observed window identity, not unquestioned truth.

Start agent access with the existing structured CLI and curated evidence exports. A later scoped MCP/plugin can expose status, report retrieval, comparison and plan preparation. OpenAI documents focused MCP tools with schemas and per-request authorization; custom UI is optional. This is an integration path, not evidence of unrestricted game control. [Official MCP server guidance](https://developers.openai.com/plugins/build/mcp-server).

Keep actual game input on an authorized, supported control route. Do not introduce a hidden socket/file key-injection endpoint to bypass unavailable permissions, user-input guards or anti-cheat. Any future action connector must have its own supported capability, authenticated scope, target validation and cancellation acceptance. No model switch, API key, paid service, public server or background listener is required for the current proposal.

Useful UI additions are a compact capabilities/status page, visible active owner, one Stop control, a binding/conflict inspector, a last-failure panel and a preview of exactly what a recipe would change. A session can save an evidence request for another chat without sending it automatically.

## Benchmark-chat-derived contracts — 2026-10-11

The [Source B reconciliation](GAME-TOOLS-MASTER-CHECKLIST.md#benchmark-chat-reconciliation--2026-10-11) reviewed all 16 turns returned by the supported reader, with no older cursor. These are proposed expansions of existing GT IDs, not new implemented capabilities or renewed authority. Provider outputs/tool code/attachment bytes were not independently inspected in this chat review. Existing Hub 0.9.0 dry-runs and Journal 0.1.0 remain the accepted offline foundation; the following operational contracts are not implemented by that generic slice.

| Proposed contract | Required data and behavior | First offline acceptance |
|---|---|---|
| Provider lifecycle/health (GT-005/006/026/027/040) | Version/capabilities and separately recorded connection, permission, approval-pending, process-start, capture-armed and fresh-writing evidence; target/run/phase, actual sampling cadence, gaps/dropped data, last good record and stopped/failed boundary | Mock approved-but-not-started, started-without-output, stale/wrong-target files, partial writes, producer exit, missing fields and cancellation. Neither UAC approval nor an open process is a valid-capture claim. No capture action is enabled by discovery/import. |
| Scenario specification (GT-023/033/038) | Stable revision; built-in versus route/action mode; requested/observed workload identity; phases; cold-start/first-visit/warm-revisit/cache labels; rotation/translation/HUD/animation endpoint; input/calibration/repetition requirements and stop/checkpoint conditions | Parse/migrate authored data and preview actions without dispatch. Refuse unknown context, unsafe save/quest actions and phase ambiguity. A declared route is not proof of repeatability or save safety. |
| Supported observation fallback (GT-039) | API/export/accessibility first; bounded OCR text/coordinates/confidence only when needed; observed target/window and coordinate basis, display/layout/scale, timestamp/expiry, ambiguous alternatives and expected result | Mock source changes, stale coordinates, low confidence, moved windows, focus races and uncertain action outcomes. Require fresh inspection after any later authorized action; don't silently click a guessed match or introduce a hidden injection channel. |
| User-editable recipes and provider selection (GT-006/009/034/041) | Separate data schema/migrations, replaceable optional adapter IDs/version/capabilities, scope, dependencies, expected evidence and previewed diff; distinguish interface app from collector and supported versus unsupported actions | Preserve old entry points/settings/profiles; reject arbitrary command payloads, unsupported capabilities and stale sources. Direct path entry remains available when Browse is unreliable; test layout-independent shortcut identities separately from display text. |
| Deployment and effective-setting evidence (GT-001/012/034–036) | Exact shared/native file owners, manager deployment state, old script/shortcut redeployment hazards, current/known-good snapshots including external config, requested settings and post-apply dependent transitions | Data-only mocked manager inventories and PT/RR-style setting changes produce blockers/diffs, not installs. Later supported product adapters must read effective state; generic declared hashes/passes do not establish current process state or runtime correctness. |
| Efficient evidence policy (GT-010/030/032/039) | Original provider files, selected result/anomaly evidence and phase markers by default; optional video mode, privacy/retention/disk limits, provider/observer cadence and overhead recorded separately | Compare authored evidence policies without capturing. Later measure responsiveness, token/observation error cost and collector/recording overhead against matched controls before claiming savings. Preserve the separate synchronized-video backlog. |

Source B's decisive correction is retained: established tools calculate complex lows, latency and trace/sensor metrics. Our core coordinates, imports, checks comparability and reports; the historical custom analyzer remains a prototype, not the default engine. Camera response and physical input-to-pixel latency remain separate. Timed capture proposed during interrupted work is a future explicitly scoped option, not an automatic retry. Historical capture approval, save/route examples and obsolete key assignments do not survive later deferrals/current preferences as authority.

Proposed next development order while games/capture remain deferred: define these data contracts and migrations → test mocks and interrupted/stale evidence → integrate optional read-only status/previews into the existing Hub → separately authorized ordinary desktop acceptance. Only after a user-facing boundary report may supported provider/game actions be requested. The mandatory effective-FG/memory gate remains fail-closed; MFG/FrameWarp and highest-compatible Ultra+ VRAM work stay last. This review itself implements none of those stages.

## Keymaps and input devices

Retain native Azeron/reWASD features. Separate verified device geometry and physical positions, native outputs/layer gestures, effective game/mod bindings, and displayed actions/icons. One versioned mapping drives Keys, Actions and Combined views and the in-game picture overlay. Changing games must leave native output and geometry hashes unchanged.

Validate chat-returned JSON against known positions, outputs, baseline revision and cited binding evidence, then show a diff before rendering. Reject output changes or unknown IDs; retain Unknown/conflicting labels. Rebuild only affected views when a source revision changes. Include readable text, stable button numbers, selectors, hold behavior and return controls; icons must not be the only explanation.

Start with manual game/context/layer selection. Optional executable association changes labels only. Show an actual layer only from fresh reliable native evidence; otherwise show Selected or Unknown. AHK events cannot prove which physical device/button produced a shared key. Current SHARED R5 has dedicated SINGLE momentary selectors and returns to BASIC before another secondary bank; do not replace that with the historical V-tap/150 ms setup or assume nested transitions.

Acceptance includes all 120 visible digital cells agreeing with the source, unchanged native hashes when switching games, separate configuration versus gameplay/prompt status, and no synthetic events counted as physical activity. Analog/controller and unusual-device capabilities remain adapter-specific rather than promised universally.

## Mod installation and diagnosis workflows

Implemented offline slice: [schema/usage](../examples/game-tool-hub/README.md#installation-and-diagnostic-dry-runs--090), [planner](../scripts/GameToolWorkflow.py), optional Sessions child view and CLI. Recipes cannot choose code or commands. Fully declared proposals remain PREPARED_NOT_AUTHORIZED; copied/hash-inventory declarations, stopped-process declarations and declared verification passes cannot establish observed backups/current process state/runtime FG. Source-bound portable plans omit private targets; diagnosis ranks declared evidence counts rather than likelihood, and contains no mutations. Conditional rollback refuses incomplete/mismatched originals, unknown ownership and drift rather than acting on imported authority. General preparation is fixture-tested, not a researched game/product adapter or universal compatibility certificate.

Use one reusable recipe sequence: preflight → current-state snapshot → one scoped change → observed verification → evidence checkpoint → retain or rollback. A recipe declares supported game/build, exact input and hook owners, required stopped processes, save risk and expected component-specific evidence.

Provide dry-run, resumable boundaries, cancellation and a readable change list. Never swap loaded DLLs or treat an overlay as proof of FG/MFG/FrameWarp. Distinguish creation, evaluation, presentation, visual correctness and stability. On failure, preserve the first evidence, rank hypotheses by confidence, and change one layer at a time. Configuration advice and a running action are separate modes.

Product-specific plans must also inspect external manager deployment/redeployment and legacy switching entry points before proposing removal or replacement. Preserve shared dependencies and native files; no broad recursive cleanup. A later apply adapter must read back effective settings after dependent transitions rather than trust the intended recipe (the benchmark owner reported a PT confirmation changing RR). These are future adapter requirements, not capabilities of the current generic dry-run engine.

Gameplay assistance and automation are opt-in recipes with a named scope and duration, not an always-on controller. Unsupported protected games or inaccessible actions stay unsupported. A later mod-help workflow can inspect effective bindings, loaded components and logs before proposing a focused repair.

## Crash evidence and recording

An optional crash companion should live outside the game process and coordinate existing providers. Record provider heartbeats, source timestamps, process exits and supported WER/component evidence, with a bounded recent timeline and periodic durable checkpoints. Append complete journal records and recover the valid prefix after interruption. Declare flush/checkpoint policy and the possible unflushed tail; immutable imports alone are not live crash-durable capture.

For optional video, integrate an established recorder such as OBS through its supported interface, without replacing existing user profiles. OBS documents recoverable MKV and Hybrid MP4/MOV formats. Hybrid chapter metadata is finalized at close and may be lost on a crash, so keep important phase markers in the external journal as well. Format resilience does not guarantee every last frame or storage failure recovery. [OBS format guide](https://obsproject.com/kb/audio-video-formats-guide), [Hybrid format behavior](https://obsproject.com/kb/hybrid-mp4).

Recording is explicit, bounded and private by default. No audio or other-desktop capture unless requested. Prefer recoverable segments with disk/retention limits; preserve interrupted sessions and offer recovery without overwriting originals. Test abnormal producer/coordinator termination with fixtures or a harmless dummy process, not by deliberately crashing a game. Do not enable a replay buffer by default: it also consumes resources and captures private activity.

## Comparisons and synchronized video

The comparison table should show source-defined FPS/lows/latency, resource scope, VRAM peak and steady behavior, memory budget where supplied, configuration equality, sample coverage, run spread, failures and capture overhead. Existing providers calculate specialized metrics; the toolkit preserves definitions and displays them. Adapter-wide VRAM must not be labeled game-only allocation.

A comparison player can show two clips beside charts with a shared seek cursor, phase markers, frame stepping, gap warnings and manual offset adjustment. Map provider clocks to video PTS using measured anchors; show offset, drift and uncertainty. Matching timestamps alone do not establish matching camera position or game state. Repeatable scene markers take precedence; unsupported routes remain a future per-game adapter.

Separate telemetry-only and recording-enabled runs to measure CPU/GPU/VRAM/encoding/disk effects. Preserve HDR/color-space metadata and distinguish a tone-mapped preview from the original HDR recording. Do not use video-induced memory pressure as evidence of a mod's standalone VRAM cost.

## Build gates

**Local continuation completed, 2026-10-11:** the requested catalog-to-Hub slice of gate 3 is implemented without changing the installed AHK host or native profiles. The optional bridge/panel reuse Catalog 0.1.1, preserve original entry points/shortcuts and keep source freshness, dependency gates and unknown metrics visible. All 110 Python contracts and 41 export checks passed; 18 tracked preservation files are unchanged. This is not completion of session/action/owner contracts, host acceptance or the full shared core. Current user scope explicitly leaves games and benchmarks for later; gate 2's game checks are not implicitly resumed. See the [integration evidence](GAME-TOOL-CONNECTIONS.md#2026-10-11--030-catalog-integration) and [Hub usage](../examples/game-tool-hub/README.md).

1. **Consolidation and preservation.** Adopt architecture, reconcile source masters and revisions, keep private checkpoints and record current acceptance. No wholesale replacement of Studio 2 with Studio 3 or unpublished Pro artifacts.
2. **Input and host acceptance.** Complete mapper-aware reservations and inert diagnostic entry points; then observe actual host Start/Stop/restart, indicator, original picture/HUD availability and cleanup. Separately test safe text/raw/Unicode, harmless Credits Enter, Escape and caret hold/release/cancellation in each game. No saves or graphics changes. Unsupported fields/actions stay pending rather than choosing a dangerous substitute.
3. **Shared core extraction.** Move registry/provenance/session/cache functions behind versioned interfaces, retaining current entry points. Existing 22 Hub and 36+8 input contracts must retain their meaning; add migration, stale-data, ownership, expiry and cancellation fixtures. Introduce no resident listener automatically.
4. **Reports and recovery.** Validate populated provider exports, metric definitions, clock associations, archive interruption and journal recovery. Test missing/truncated files, producer exit, disk-full handling and coordinator restart with fixtures. Missing evidence stays visible.
5. **Keymap module.** Integrate the label contract and supplied Pro artifacts without remapping profiles. Validate all cells, baseline hashes, source freshness, conflicts and the three diagram views.
6. **Recipes and optional video.** Add installation/diagnosis dry-runs, rollback manifests, benchmark phases, approved recorder control and synchronized comparison. Test retention, cancellation, clock drift, recovery and capture overhead before game use.
7. **Game continuation proposal.** Report passed/failed gates and offer the next scoped game checks. Deferred MFG/FrameWarp or gameplay work requires its own scope; acceptance in menus does not prove those features.
8. **Cyberpunk highest Ultra+ VRAM benchmark.** Only after preceding work and the continuation message, inventory the effective stack and define the exact compatible highest preset/settings. Preserve the current configuration; this later benchmark setting change is distinct from no-graphics-change input tests. Use the built-in scene rather than a save, record PT/SR/RR/FG, resolution/HDR/cache and provider scope, take matched repeated measurements and stop on instability. Restore the selected baseline afterward. Record VRAM allocation versus budget/pressure and video overhead separately. Previous short PT21 Fast evidence is not the requested highest-level result.

## Delivery and rollback

Each gate ends with an evidence ledger, known limitations, rollback and a small next boundary. Share only requested, sanitized source/docs/results in the canonical GitHub repository; private recovery exports, logs and video remain local or in explicitly selected private Drive storage. No public raw logs, game binaries, saves, credentials or personal paths.

Adopting this proposal changes no installed profile or runtime. Roll back new toolkit modules by stopping their session, preserving newer work and restoring only their owned source/settings changes. Keep the working source baseline and the current failed/partial state separately. Follow [repository operating standard](OPERATING-STANDARD.md), [input guide](AGENT-GAME-INPUT.md), [measurement procedure](GAME-PERFORMANCE-MEASUREMENT.md) and [device registry](INPUT-DEVICE-REGISTRY.md).
