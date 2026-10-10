# Unified game tools architecture and build plan

Proposal, 2026-10-11. Combine the measurement Hub, optional AHK input module, overlays and keymap work through one shared coordination core. Preserve their working features and native device profiles. A single user interface can expose the modules without turning the entire project into one large AHK script.

The current boundary is consolidation and planning. Game input acceptance follows the tooling gates; MFG/FrameWarp remains deferred. The requested Cyberpunk highest-level Ultra+ VRAM benchmark comes last, after the earlier work and a user-facing continuation proposal. This plan does not activate recording, launch games, load saves, change graphics or schedule work.

The same-day extension makes individual tool/feature resource cost and combination interactions the primary analysis goal. Use the [typed catalog and overhead protocol](TOOL-RESOURCE-OVERHEAD.md), [knowledge and recovery index](GAME-TOOLS-KNOWLEDGE-INDEX.md) and [automation procedures](AUTOMATION-OPERATING-PROCEDURES.md). Extend the shared registry with managers, stores, official mod kits and scoped prepared capabilities; distinguish their external processes from the features they deploy or host inside a game.

## Architecture options

1. **Recommended: shared core with modular tools.** A small Python library supplies registry, sessions, capabilities, evidence and workflow state. Existing AHK handles hotkeys, pictures and guarded input; native Azeron/reWASD/Steam Input retain remapping; existing measurement/recording tools provide their specialized outputs. Benefit: reuse without discarding features. Main risks: interface migrations, key ownership and capture overhead. Difficulty 4/5; high design confidence, runtime confidence pending acceptance. Rollback: disable new modules and retain existing entry points, source and settings checkpoints.
2. **Keep separate tools with shared exports.** Standardize metadata and handoffs without a shared runtime or integrated panel. Benefit: quicker, smaller changes. Conflicts: manual coordination and duplicated state remain. Difficulty 2/5; high confidence for incremental adoption. Rollback: ignore the optional exports; original tools remain usable.
3. **Rewrite everything as one program.** Replace current implementations and potentially native integration surfaces. Benefit: one codebase. Conflicts: greater regression risk, duplicated specialized functions and harder rollback. Difficulty 5/5; low confidence relative to option 1. Rollback requires restoring every replaced component. Not recommended.

## Existing components and acceptance

| Component | Observed or recorded capability | Remaining boundary |
|---|---|---|
| Game Tool Hub 0.2.0 | Read-only Afterburner/RTSS connections, report imports, interface registry and 22 synthetic contracts with core panel acceptance | Populated game reports, runner, crash recording and comparison player |
| Game Tool Catalog 0.1.1 | Filterable typed catalog, dependency-preserving overhead plans and 35 pure tests | Read-only planning foundation; no external-tool execution or measured overhead acceptance |
| Overlay Studio 2 integration | Optional fifth tab and library wiring; 60 original methods retained; settings hash unchanged; saved picture preview observed after loader repair | Module Start/Stop/restart after the latest repair, HUD output and original-feature regression checks |
| GameInputModule v0.5-preview.3 | Native integrated-host validation, 36 module plus 8 host policy checks; installed and repository source match | Text, Unicode, Enter, Escape, hold/release and cancellation in each game |
| Historical Control Helper v0.3.1 | Partial agent-operated menus, one digit, caret and Backspace in both games | Does not validate the refactored host or extended actions |
| Azeron SHARED R5 | Four SOFTWARE profiles loaded; native events support three momentary selectors and release to BASIC outside games | Ordinary outputs, joystick/chords, gameplay prompts and native Import-dialog acceptance |
| Per-game keymap labels | Request and data-contract proposal in draft PR4 | Label generator implementation and acceptance |

Sources: [Hub evidence](GAME-TOOL-CONNECTIONS.md), [input integration record](../examples/game-input/OVERLAY-STUDIO-INTEGRATION.md), [draft keymap brief/PR4](https://github.com/dodWhatUp/install-modes-for-games/pull/4), and the requested benchmark/keymap chats. The follow-up owner report confirms all planned Pro material was already received in its separate workstream. Do not request it again; use that owner's handoff/revision for later scoped reconciliation. Its unseen code is not part of this acceptance claim. Follow [knowledge maintenance](KNOWLEDGE-MAINTENANCE.md) rather than replacing rich masters with summaries.

## Shared core and ownership

The shared core serves input, measurement, mod workflows, crash evidence and label rendering through versioned contracts. Front ends remain replaceable; a new adapter should add a capability to the common registry rather than copy discovery and logging into every tool.

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

## Keymaps and input devices

Retain native Azeron/reWASD features. Separate verified device geometry and physical positions, native outputs/layer gestures, effective game/mod bindings, and displayed actions/icons. One versioned mapping drives Keys, Actions and Combined views and the in-game picture overlay. Changing games must leave native output and geometry hashes unchanged.

Validate chat-returned JSON against known positions, outputs, baseline revision and cited binding evidence, then show a diff before rendering. Reject output changes or unknown IDs; retain Unknown/conflicting labels. Rebuild only affected views when a source revision changes. Include readable text, stable button numbers, selectors, hold behavior and return controls; icons must not be the only explanation.

Start with manual game/context/layer selection. Optional executable association changes labels only. Show an actual layer only from fresh reliable native evidence; otherwise show Selected or Unknown. AHK events cannot prove which physical device/button produced a shared key. Current SHARED R5 has dedicated SINGLE momentary selectors and returns to BASIC before another secondary bank; do not replace that with the historical V-tap/150 ms setup or assume nested transitions.

Acceptance includes all 120 visible digital cells agreeing with the source, unchanged native hashes when switching games, separate configuration versus gameplay/prompt status, and no synthetic events counted as physical activity. Analog/controller and unusual-device capabilities remain adapter-specific rather than promised universally.

## Mod installation and diagnosis workflows

Use one reusable recipe sequence: preflight → current-state snapshot → one scoped change → observed verification → evidence checkpoint → retain or rollback. A recipe declares supported game/build, exact input and hook owners, required stopped processes, save risk and expected component-specific evidence.

Provide dry-run, resumable boundaries, cancellation and a readable change list. Never swap loaded DLLs or treat an overlay as proof of FG/MFG/FrameWarp. Distinguish creation, evaluation, presentation, visual correctness and stability. On failure, preserve the first evidence, rank hypotheses by confidence, and change one layer at a time. Configuration advice and a running action are separate modes.

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
