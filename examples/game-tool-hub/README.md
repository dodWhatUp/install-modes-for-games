# Game Tool Hub — learning preview / unified workspace

Current source extension: [MO2 registered-profile read adapter — Hub 0.28.0-preview.1](../../docs/MO2-READ-ADAPTER.md), based on the adopted [0.27 UMM planning source](../../docs/AI-PLANNING-READONLY-SLICE.md). Exact product commit `c0809f7ac99a776390e131859991105c2f4c88f4` passed bounded synthetic Windows, source-package and external stdio acceptance. Modern multi-game clients reuse the existing opaque instance and inspection tools; registration of exact MO2 roots remains local, and AI receives no path or new authority. MO2 declaration reads do not establish virtual deployment, conflict winners, runtime or gameplay, and planned-versus-installed comparison remains blocked. The source is not installed or adopted into `main`; see the [acceptance boundary](../../docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.md).

## Display-only automatic overlay groups — 0.11.0

The new Overlays page extends all eight existing tabs and shortcuts. Use the [asset contract, API examples, acceptance boundaries and supported install/rollback](../../docs/OVERLAY-GROUPS.md). Compact native selectors, independent Show/Hide preferences, additive managed images, exact game/keymap/profile/layer/context/view matching, manual override/cycling and Return to Auto share one engine. Foreground observation changes displayed assets only. Native layer telemetry is unavailable: explicit layers stay Selected/Unknown, never inferred from a common key. No new global shortcut or #19 trigger is registered.

This builder prepares Hub 0.11.0 and optional Studio **2.2.0-groups-preview.1** source; installed Studio **2.0.0-beta** remains unchanged. Passive Peek and explicit pinned Explore are separate; the optional AHK relay reuses an existing picture trigger and starts Off. The SPARSE6 owner creates/registers actual assets after receiving the exact private package/installed-revision contract. MFG/FrameWarp, game input, benchmarks and recording remain deferred. Earlier sections below describe their dated acceptance, not completion of this new live integration.

## Offline provider health and editable scenarios — 0.10.0

Sessions → **Provider / scenario contracts** opens the optional [editor/check view](../../scripts/GameToolReadinessPanel.py) using the fixed [backend](../../scripts/GameToolReadiness.py). Existing eight tabs, Ctrl+1–8 shortcuts, reports/imports, Catalog, Comparison, FG gate, journals/evidence and workflow dry-runs remain. Coordinator/Sessions 0.4.0 add one fixed read-only `readiness` capability; Journal 0.1.0 and AHK remain unchanged. No provider connection/launch, capture, scenario runner, game input, settings change or recording is performed by this feature.

Start with the authored [provider mock](provider-health.example.json) or [scenario mock](scenario.example.json). Enter its path and select **Load path**, or use optional **Browse**. Nothing is read automatically when opening the view. The editor contains private data; the result panel and **Copy checked summary** omit imported provider/target/run/scenario/phase identifiers and file paths. Do not put personal drafts in Git or the source exporter.

- Provider checks distinguish discovery, connection, approval, process-start, arming, fresh records and stopped/cancelled/exited states. Require declared version/capabilities/context, complete writes, at least two ordered records, target/run/phase equality, one mock monotonic clock, freshness and declared cadence; show intervals, drops and missing fields. Approval/process presence alone fails. Gaps, stale/future/wrong-context output, partial writes and missing data produce **BLOCKED**. A consistent authored fixture returns **MOCK_HEALTHY**, not live verification or permission to capture. This slice checks declarations, not real CSV/provider adapters.
- Scenario schema 1 retains a stable identifier/revision, built-in versus route/action mode, requested workload and separately declared readback, cache/visit/process evidence, repeats, provider/frame class, latency endpoint/calibration/meaningful-input declarations, bounded phases/actions and mandatory stop policy. Cost, latency and stability purposes remain separate. Rotation, translation, HUD and animation are distinct tags; optical latency is not inferred from software fields.
- Edit JSON in place, then **Preview draft** to check current unsaved content. Edits invalidate old results. Unknown fields, duplicate JSON keys, unsupported schema versions, arbitrary commands/keys/text, save/quest/graphics flags, disabled stop conditions, mixed modes, duplicate phases and duration/deadline violations are refused. Incomplete/mismatched workload/cache/provider/latency evidence remains **BLOCKED**. Structurally complete declarations return **PREPARED_NOT_AUTHORIZED**; live route/repeatability/save safety and effective FG remain unverified.
- **Save NEW scenario** explicitly writes a new private JSON outside the repository. It pins the selected original hash across the dialog, validates the edited bytes, refuses overwrite/reparse paths/repository destinations, flushes/readbacks and publishes exclusively through the shared workflow publisher. Source file and profiles stay untouched. Incomplete but structurally valid drafts can be saved as blocked plans. Copy/save refuse stale originals or drafts; unsaved edits cannot be silently replaced by Load. **Discard edits and load** requires confirmation if dirty. Saving does not automatically select or run the copy.

Every result says execution `none`, execution-authorized/runtime-verification false, and FG preflight `not_performed`. A prepared scenario cannot unlock real rendering comparisons or waive the existing FG/memory gate. Files labeled Mock are authored examples, not actual captures, measurements, game-specific routes or compatible-mod recommendations. Schema 1 has no implicit migration of unknown future formats; deliberate source reload is not a live-settings readback.

Fixed CLI routes (paths below are placeholders; use private destinations):

```powershell
python scripts/Game-Tool-Hub.py readiness inspect --source examples/game-tool-hub/provider-health.example.json
python scripts/Game-Tool-Hub.py readiness inspect --source examples/game-tool-hub/scenario.example.json
python scripts/Game-Tool-Hub.py readiness save-scenario --source <original-scenario.json> --expected-sha256 <original-hash> --draft <edited-draft.json> --output <NEW-private-scenario.json>
python scripts/Game-Tool-Hub.py session inspect-readiness --source <contract.json> --expected-sha256 <source-hash> --journal <NEW-private-session.jsonl>
```

Exit 0 means a valid mock/preparation or new-copy receipt, **not runtime acceptance**; exit 3 means declared blockers, exit 2 means invalid/stale/refused input or destination. A journal records compact status/kind/blocker counts and source hashes, never the editor/phase plan. No Start Capture, Apply, Run Scenario, replay, automatic retry, shell payload or arbitrary plugin selector exists. Missing optional code leaves existing Sessions usable. Use the [current receipt](../../docs/GAME-TOOL-CONNECTIONS.md#2026-10-11--0100-offline-provider-health-and-scenario-contracts) for mock coverage, preserved baselines and exact rollback; older sections retain their own historical scope.

## Installation and diagnostic dry-runs — 0.9.0

Sessions → **Workflow dry-runs** opens the optional inert [view](../../scripts/GameToolWorkflowPanel.py). Choose a saved recipe explicitly, inspect its private local change list and portable [planner](../../scripts/GameToolWorkflow.py) result, Reload when intentionally accepting a revised recipe, then Copy or Export a new JSON outside the repository. The existing eight tabs and shortcuts remain. No Install, Apply, Launch or Rollback execution control exists; no catalog record can choose Python code. Missing optional workflow code does not disable Sessions or the original Hub.

The authored [installation](workflow-installation.example.json) and [diagnostic](workflow-diagnostic.example.json) examples intentionally contain unknowns and stay **BLOCKED**. They are not researched Skyrim/Cyberpunk recipes, measured incidents, compatibility recommendations or installed-profile exports. Copy a recipe to private storage before adding personal facts; do not put private recipes/settings into Git.

Schema 1 requires exactly the illustrated keys. Unknown fields, commands, duplicates and non-finite values are refused:

| Record | Accepted declarations / purpose |
|---|---|
| `kind`, `target`, `layer` | Installation or diagnostic; game/executable/build/API and one layer's version/hash plus upstream revision/hash/freshness. Null is unknown. These do not verify the real target, compatibility or source freshness. |
| `resources` | Stable IDs, hook/configuration/host kinds, owners or null, expected owner and required resource IDs. Unknown/conflicting owners, missing hosts, invalid references and cycles prevent preparation. No inferred compatibility chain or competing FG owner. |
| `processes` | Game, launcher, store, helper and compiler roles: `unknown`, `declared_stopped` or `declared_running`. Installation needs all five stopped declarations, never treated as current process observations. |
| `snapshot` | Current/known-good coverage and whether they differ. `inventory_only` and `declared_copied` are not byte verification. A distinct known-good state needs separate preservation; nothing is copied/restored by this planner. |
| `changes` | One component's add/replace/configure records, relative target, resource/owner, original/current/expected-after hashes and original-backup hash/coverage. Absolute paths, traversal, device names and alternate streams are refused. No setting values, DLLs or commands are consumed. |
| `checks` | Creation, evaluation, delivery, presentation, visual correctness and stability. Installation lists all six phases. Unknown results are expected before testing; even `declared_pass` is not runtime verification. |
| `observations`, `hypotheses` | Typed declared observations/source hashes, support/contradiction references, hypothesis categories and typed evidence requests. No raw logs or arbitrary inference text. Ranking: support count descending, contradictions ascending, then source order—not likelihood, causal proof or generated confidence. |

Unknown/conflicting owners, stale sources, process declarations, hash drift, incomplete recovery, unscoped changes, memory warnings and declared verification failure remain visible as blockers. Diagnostic recipes cannot contain mutations. Overlay presence, a faulting module or memory warning does not establish cause; [measurement guidance](../../docs/GAME-PERFORMANCE-MEASUREMENT.md) retains the exact Ultra+ warning/VRAM-scope procedure.

`PREPARED_NOT_AUTHORIZED` means only that declarations satisfy proposal checks—not ready to install, observed backups, restore-tested recovery, current live preflight or permission. Other statuses: `BLOCKED`, `EVIDENCE_REQUEST_ONLY`. Every result has execution `none`, runtime verification false, FG preflight `NOT_PERFORMED` and cause verification false. Real comparisons still require the unchanged Dynamic-MFG/effective-FG/memory gate.

Rollback is **conditional**, not an action: preserve first evidence and failed state; obtain scoped authority and freshly verify file owners stopped; reidentify live target/owners/dependencies; refuse drifted/newer/unrelated files; restore only the layer's original from a verified matching backup or remove only its new file if ownership and exact expected-after hash match; verify restored bytes/behavior and retain a resumable boundary. Unknown/failed declarations block this proposal too. A plan cannot promise a recovery artifact or silently restore a native profile.

Reads reuse the coordinator's bounded regular-file/reparse/identity checks. Limits: 1 MiB JSON, 64 records per collection, depth 12, 8,192 decoded values. Dependency traversal is bounded; target duplicates are case-insensitive. Originals are not rewritten. Portable results use generated aliases instead of imported identifiers/paths; private local targets are displayed separately, excluded from Copy/Export. New portable exports stage/fsync/read back, pin source identity across dialogs/publication, publish exclusively and verify bytes. Failure cleanup removes only still-identical owned output and retains foreign replacements. This is not an atomic power-failure or restore guarantee.

CLI routes run before registry/provider/UI reads:

```powershell
python -B scripts/Game-Tool-Hub.py workflow inspect --source private-recipe.json
python -B scripts/Game-Tool-Hub.py workflow export --source private-recipe.json --expected-sha256 RECIPE_SHA256 --output NEW_PRIVATE_PLAN.json
python -B scripts/Game-Tool-Hub.py session inspect-workflow --source private-recipe.json --expected-sha256 RECIPE_SHA256 --journal NEW_PRIVATE_JOURNAL.jsonl
```

Use actual selected files/hash, not literal placeholders. Export parents must already be ordinary directories outside the repository. Exit 0: offline proposal/evidence; 3: declared blockers (a blocked plan can still be exported); 2: refusal. `session inspect-workflow` uses Coordinator 0.3.0's fourth fixed read-only capability, finishes only its fresh owned journal, and records source hash/verdict/counts—not private paths/recipe contents. Cancellation/expiry/durability failure prevent acceptance; a journal cannot replay a recipe.

See [0.9.0 scoped acceptance](../../docs/GAME-TOOL-CONNECTIONS.md#2026-10-11--090-offline-workflow-dry-runs). Per-game researched recipes, operational adapters, actual install/rollback/game acceptance, live crash collection and recording remain separate. AHK source/settings/profile baselines are not migrated or restarted.

## Existing Hub controls

Open `Start-GameToolHub.ps1` with PowerShell. It uses installed Python/Tk, preferring the bundled Codex runtime. No packages, drivers or services are installed. The GUI starts in learning mode; optional auto refresh is off.

- **Tools:** installation/running status and executable file versions, open an installed interface, register another installed interface, copy status without paths, save an immutable private connection snapshot. File versions may differ from product versions (observed for NVIDIA App).
- **Sensors:** read existing Afterburner names/units/values through `MAHMSharedMemory` using `FILE_MAP_READ`. No control mapping or new collector. Counters have no run association; desktop values do not validate game FPS/lows/latency.
- **RTSS:** read existing `RTSSSharedMemoryV2` with read access only. Application/PID, provider interval/count, recording flags and RTSS-calculated average/1%/0.1% lows are preserved. Tenths of FPS become FPS by unit conversion only. Stale live counters remain unavailable; historical intervals and endpoint presence do not validate a game benchmark or measured latency.
- **Reports:** archive a chosen CSV/JSON/TXT/HML as original bytes with source program, definitions and SHA-256. PresentMon v2 CSV preview retains at most five original rows plus documented GPU/latency fields, endpoints and frame type where present. Blank/NA values stay intact. No percentile, low or latency calculations. HML and unrecognized formats remain opaque.
- **Catalog:** browse/filter/sort recorded tools, games and features, inspect provenance/relationships and prepare FG-gated overhead proposals through the existing catalog engine. Explicit read-only FG checks and fresh in-game plan/copy checks block unknown or adaptive effective FG. SHA-256-bound source changes require explicit reload. Links and capability records are inert data; no action executor is present. Recorded installation is not fresh Tools inventory.
- **Comparison:** import supported original Cyberpunk summary JSON/PresentMon GUI statistics CSV without hand-normalizing, or load existing normalized saved-summary JSON; view provider-defined metrics, raw runs/blockers, repeat means/ranges and eligible A/B or dependency-preserving 2×2 contrasts; copy/export the selected metric to a new local JSON/HTML file. Original bytes are archived privately. No collector or complex metric engine is added. Synthetic fixtures are labeled; all real rendering/injected-feature imports remain BLOCKED pending trusted runtime FG coverage.
- **Sessions:** explicitly start an offline session, record checkpoints, inspect saved reports/comparisons through fixed read-only capabilities, then finish or cancel. Inspect journals and recover their verified complete prefix into a new evidence-only file. **Saved crash evidence** opens an optional offline selected-file preview/private-packet view; **Workflow dry-runs** opens installation/diagnostic change and conditional rollback previews. Neither view requires an active session. No replay, resume, game control, provider launch or recording is enabled.
- **How to use:** user controls, supported boundaries and next integration steps. Existing recording/hardware settings are read, not edited. Windows approvals remain manual.

Private data defaults to `%LOCALAPPDATA%/GameToolHub`. `tools.json` contains the user's registered executable paths. Registry changes preserve a previous copy. Imports use separate unique directories; changing source files are rejected with their partial evidence retained. No upload is automatic. Close the GUI to stop optional refresh; other tools stay open.

Save snapshot creates a uniquely named connection JSON inside the private data directory. Add tool and Reports accept visible direct-path forms, with optional Browse buttons. Registration never launches the program and requires an interface-only confirmation. Known collectors remain blocked even if given a different name in the panel. NVIDIA App is an interface launch connection; the installed FrameView SDK is an inventory-only collector, not evidence of a standalone FrameView GUI or populated latency export.

Local shortcuts, active only while the Hub is focused:

| Shortcut | Action |
|---|---|
| Ctrl+1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 | Tools / Sensors / RTSS / Reports / How to use / Catalog / Comparison / Sessions; previous seven assignments preserved |
| Ctrl+R | Refresh readers/tool status; on Catalog, Comparison or Sessions, refresh only that tab's selected source/status |
| Ctrl+T | Toggle optional refresh on Sensors/RTSS; no time series saved |
| Ctrl+O | Open selected interface; collectors blocked |
| Ctrl+A | Show registration form (normal select-all retained in text fields) |
| Ctrl+C | Copy status without paths; Catalog record, Comparison selected-metric report or Sessions compact summary (normal text copy retained in text fields) |
| Ctrl+S | Save a new private snapshot |
| Ctrl+I | Import the visible report draft; incomplete drafts request missing fields |
| Ctrl+E | Open selected archived original in its associated application |
| Alt+F4 | Close only the Hub |

Windows shortcuts use virtual-key letters so a Hebrew/other active keyboard layout does not change the intended action. Modal dialogs retain input ownership.

On Catalog, Comparison and Sessions, Ctrl+O/A/S/I/E do not trigger remembered Tools/Reports actions. Normal text-field select-all/copy remains available. These tabs have no launch, registration, capture, input or graphics controls. Original actions remain on their original tabs.

Agent interface, using the installed Python executable:

```text
python scripts/Game-Tool-Hub.py inspect
python scripts/Game-Tool-Hub.py snapshot --output <new-private-file.json>
python scripts/Game-Tool-Hub.py import-report --source <existing-report.csv> --provider <program-name> --definition <documented-method>
python scripts/Game-Tool-Hub.py --form-file <private-draft.json>
python scripts/Game-Tool-Hub.py catalog status
python scripts/Game-Tool-Hub.py catalog list --category graphics --sort name
python scripts/Game-Tool-Hub.py catalog show rhi
python scripts/Game-Tool-Hub.py catalog fg-preflight --scope in-game --game cyberpunk-2077
python scripts/Game-Tool-Hub.py catalog plan-overhead --scope in-game --game cyberpunk-2077 --factor cp-renodx-hdr --factor cp-ultra-pt21
python -B scripts/Game-Tool-Hub.py compare-report --source examples/game-tool-hub/comparison-fixture.example.json
python -B scripts/Game-Tool-Hub.py compare-report --source <existing-normalized.json> --metric <metric-id> --output <new-local-report.html> --format html
python -B scripts/Game-Tool-Hub.py inspect-saved-report --source <existing-provider-summary.json>
python -B scripts/Game-Tool-Hub.py import-saved-reports --baseline <baseline-summary.json> --a <changed-summary.json> --output-directory <new-private-folder>
python -B scripts/Game-Tool-Hub.py session capabilities
python -B scripts/Game-Tool-Hub.py session inspect --source <existing-private-journal.jsonl>
python -B scripts/Game-Tool-Hub.py session inspect-report --source <saved-summary.json> --expected-sha256 <source-sha256> --journal <new-private-journal.jsonl>
python -B scripts/Game-Tool-Hub.py session compare --source <normalized-summary.json> --metric <metric-id> --expected-sha256 <source-sha256> --journal <new-private-journal.jsonl>
python -B scripts/Game-Tool-Hub.py session recover --source <interrupted-journal.jsonl> --expected-sha256 <inspected-sha256> --output <new-recovered-evidence.jsonl>
python -B scripts/Game-Tool-Hub.py saved-evidence inspect --source <saved-events.xml> --source <saved-journal.jsonl>
python -B scripts/Game-Tool-Hub.py saved-evidence packet --source <saved-events.xml> --output-directory <new-private-folder>
python -B scripts/Game-Tool-Hub.py session inspect-evidence --source <saved-events.xml> --expected-sha256 <source-sha256> --journal <new-private-journal.jsonl>
python scripts/tests/Test-GameToolHub.py
python scripts/tests/Test-GameToolCatalogBridge.py
python scripts/tests/Test-GameToolHubCatalog.py
```

`--data-dir <private-directory>` goes before the command. Configure `GAME_TOOL_PRESENTMON` or the private registry to identify an existing console executable. PresentMon console is inventory-only in learning mode: opening it with no capture arguments can start ETW collection. The panel does not resume the older idle collector or stop it silently.

## Offline coordination and crash-safe journal foundation — 0.7.0

Sessions is an optional eighth tab. Opening it is inert: no journal, listener, provider or task starts. New session requires a new explicitly selected JSONL file in an existing ordinary directory. It records a named owner/session, bounded labels, checkpoints, a cooperative lifetime and compact action outcomes. Its only operational capabilities inspect saved summaries or compare saved normalized summaries through the existing backends. Returned data retains those backends' unknown values and FG/memory gates; the journal does not certify runtime evidence.

The [coordinator](../../scripts/GameToolCoordinator.py), [journal](../../scripts/GameToolJournal.py) and [panel](../../scripts/GameToolSessionPanel.py) share versioned interfaces. Ownership is cooperative and local to the journal/session; it is not a desktop-wide lock and cannot stop another app/chat. Expiry and cancellation are checked at operation boundaries. Bounded synchronous reads are not forcibly preempted mid-call. Finish/Cancel and Hub close release only this session. No arbitrary command, executable adapter, typed-input payload, automatic task replay or persisted approval is accepted. Sessions does not replace the AHK host or its tray, shortcuts, settings or native profiles.

Journal records carry an ordered sequence, UTC, monotonic nanoseconds and a clock identity, with a SHA-256 chain. Each successful append is flushed and fsynced before acknowledgement. Limits are 64 KiB per record, 16 MiB per journal and 4,096 records. Duplicate fields, unsupported schemas, corruption and sequence/clock changes stop verification at the first damaged record. A write/durability failure poisons the writer; further actions cannot continue on that writer. Hashes detect changes, not authenticate an author. UTC is wall-clock evidence; monotonic times can be related only within the same clock identity, not used to assert synchronized videos or equal game scenes.

Inspect is read-only. Recovery publishes only the verified complete prefix into a new no-overwrite copy, checks source drift and retains the original. The receipt records both hashes and excluded tail bytes; recovered data is evidence only, never an executable session. An open valid journal means no terminal event was recorded—not proof that a game crashed. Process-interruption recovery is not a guarantee against every disk, power-loss or storage-controller failure; unflushed/unacknowledged evidence may be lost. Live heartbeat/process/WER/log collection, crash-cause diagnosis, recording and synchronized video playback remain separate future work.

Use private paths for journals and retain the recovery receipt with the original when needed. Coordinator-generated event data is compact/path-free; the lower-level journal accepts private metadata and callers must not add typed text, credentials, raw logs or personal identifiers. Journals are excluded from authored source exports. Session CLI one-shot read actions explicitly create and close a new journal, without loading the executable registry or live readers. Inspection returns exit 3 for structurally damaged evidence; invalid requests/no-overwrite/drift errors return 2. A saved comparison BLOCKED verdict remains exit 3 and is not overridden by successful journaling.

Rollback is source-only: close the owned Hub session, preserve its private journals/reports, then restore the just-in-time Hub source and remove/ignore only these optional modules. Do not restore or reset game/AHK/native settings. The current connection receipt records tests and exact preservation coverage; fixture acceptance is not live game or installed-host acceptance.

Optional [`form-draft.example.json`](form-draft.example.json) is a bounded local startup draft for report path/provider/definitions and tool path/name. Copy it privately and supply actual paths. It only populates visible fields: no launch, import, registration, approval or capture is executed, and interface confirmation cannot be prefilled. It helps when supported Computer Use cannot enter text into Tk fields; agent commands remain the preferred non-UI route for imports/inspection. No runtime file watcher, input server or hidden click channel exists.

The read-only sensor adapter uses the installed author's `SDK/Include/MAHMSharedMemory.h` layout v2 prefix: validates signature, sizes/counts, bounded mapping, unavailable `FLT_MAX` and provider timestamp. It preserves original source IDs and flags. Samples are best effort rather than an atomic batch; no time-series file is created by auto refresh. This is an authored adapter, not a copied SDK binary/header.

The RTSS adapter follows the installed author's `RTSSSharedMemory.h` and `OverlayDataProviderInternal.cpp`: header offsets/strides, Windows packing 8, version/extent gates and documented FPS scaling. It writes no OSD, locks, statistics/capture flags or profiles. Latency instrumentation is endpoint availability only; supported programs must calculate latency. PresentMon definitions follow its [2.6.0 console documentation](https://github.com/GameTechDev/PresentMon/blob/v2.6.0/README-ConsoleApplication.md). Declared provider version remains separate from schema recognition.

Current evidence and next boundaries are in [tool connections](../../docs/GAME-TOOL-CONNECTIONS.md). Rollback: close only Game Tool Hub and remove its optional launcher/source after preserving private reports. No Afterburner/RTSS/game-profile restore is required for this helper alone.

## Integrated read-only catalog and overhead-plan foundation

The [read-only catalog engine](../../scripts/Game-Tool-Catalog.py) uses [portable catalog records](catalog.example.json) to describe components, game-specific features, typed relationships and declaration-only capabilities. Hub 0.3.0 connects it through a [source-bound bridge](../../scripts/GameToolCatalogBridge.py) and optional [Catalog panel](../../scripts/GameToolCatalogPanel.py). The existing standalone CLI remains supported. Shared engine functions supply filtering, details and dependency plans; the GUI does not reimplement metric or dependency calculations.

Open Catalog with Ctrl+6. Browse records offers Kind, Category, Game, Evidence, Recorded install, Relationship, Search and Sort controls. Select a record to inspect exact provenance, related components, notes, declaration-only capabilities and unmeasured metric fields. Source references are inert text. Copy details copies data; it does not open a program/browser or grant access.

Prepare comparison has separate scope/game/factor fields. Select one factor, or two for a 2×2 preview, then Prepare plan. A blocked result explains its compatibility/dependency gate. Copy plan exports the current data-only proposal. There is no Run button, application action, installer or collector. Native baselines, required hosts/loaders and unresolved gates retain the catalog engine's meaning.

The bridge hashes the exact bounded JSON bytes and exact sibling backend, validates both and returns detached data. Changed/missing/invalid sources refuse further results until explicit successful reload; prior plans/selections are cleared. A conservative graph-scan work budget rejects overly expensive integration catalogs before backend validation; this is not a hard runtime deadline. No catalog validation or FG observation is added to the existing five-second sensor-refresh loop. Optional Catalog failure is contained and leaves the original Hub tabs usable. `--catalog-file <existing-catalog.json>` optionally selects a different read-only catalog before the command; the default shipped example remains unchanged. Catalog status/list/show do not read the private executable registry or live providers; explicit FG checks and in-game plan/copy requests additionally inspect the FG sources described below.

## Read-only effective-FG preflight — 0.4.0

Open Catalog → Prepare comparison → **Check FG (read only)**. Preparing an in-game proposal also checks automatically; Copy plan performs a fresh check instead of trusting an old displayed PASS. Editing the target or changing the selection invalidates the previous plan. Browsing, reloading, opening the Hub and manager-idle plans do not trigger driver/settings inspection.

The exact sibling [inspector](../../scripts/GameFgInspector.py) reads bounded Cyberpunk saved FG fields and the installed Windows system NVAPI's documented global/app DRS mode, inheritance, raw count/target and driver version. Supply the real rendering executable's full local path for an unambiguous profile lookup; an optional native JSON path is configuration evidence only. Paths stay in the local form/arguments and are not saved or exported. Skyrim's native/PureDark FG-owner adapter is not implemented and remains unknown. No graphics, driver, mod, native/AHK profile or private Hub registry is written; no DLL is injected into a game, and no app/game/collector is launched.

The pure [policy](../../scripts/GameFgPreflight.py) distinguishes native selection, driver configuration, effective mode and runtime coverage. **BLOCKED** suppresses comparison cases and sets `comparison_ready=false` when Dynamic MFG is active/configured, effective FG is unknown, or current trusted evidence is missing, stale, future-dated, mismatched, conflicting or configuration-only. A superseded global Dynamic setting is not itself the applicable per-game mode. Disabled driver override means use the application's choice, not FG Off. Raw frame-count fields are not assumed to be delivered multipliers. **PASS** requires verified inactive Dynamic MFG and effective Off/known fixed multiplier, and is only the FG gate—not memory/workload/metric acceptance or permission to execute. **NOT_APPLICABLE** is limited to non-rendering manager-idle scope.

Important initial boundary: inspector 0.1.0 has **no runtime FG/owner probe**. Its real observations therefore remain **BLOCKED**, even if saved settings and driver configuration appear fixed. This prevents premature comparison rather than pretending to establish delivery. A separately reviewed runtime adapter is the next boundary; no game test or benchmark is resumed by this feature. Receipt validity is at most 120 seconds, and a receipt is a point-in-time observation, not continuous monitoring. Imports/manual checkboxes/JSON cannot override the gate. The in-process provenance seal detects accidental copied/tampered evidence; it is not a security boundary against local Python code.

```text
python scripts/Game-Tool-Hub.py catalog fg-preflight --scope in-game --game cyberpunk-2077 --executable <actual-rendering-executable>
python scripts/Game-Tool-Hub.py catalog fg-preflight --scope process-idle
python scripts/tests/test_game_fg_inspector.py
python scripts/tests/test_game_fg_preflight.py
```

Hub `catalog fg-preflight` and `plan-overhead` return exit **3** for a blocked result, **2** for invalid catalog/request errors and **0** for a successful eligible preview/check; JSON always reports execution `none`. There is still no Run button/executor. Standalone `Game-Tool-Catalog.py` remains a structural planner only: its prepared result does not certify effective FG and must not bypass the Hub gate. No automatic settings correction, imported-evidence switch, unchecked force-PASS option or adaptive-experiment conversion exists.

Primary API contract: NVIDIA's pinned [DRS declarations](https://github.com/NVIDIA/nvapi/blob/70d337db9186e968eab622f7e786de7e437faf3d/nvapi.h) and [driver setting enums](https://github.com/NVIDIA/nvapi/blob/70d337db9186e968eab622f7e786de7e437faf3d/NvApiDriverSettings.h). These describe configuration reads, not proof of the installed game's runtime support.

```text
python scripts/Game-Tool-Catalog.py validate
python scripts/Game-Tool-Catalog.py list --category graphics
python scripts/Game-Tool-Catalog.py list --game skyrim-special-edition --installation unknown --sort name
python scripts/Game-Tool-Catalog.py show rhi
python scripts/Game-Tool-Catalog.py plan-overhead --scope process-idle --factor rhi
python scripts/Game-Tool-Catalog.py plan-overhead --scope in-game --game cyberpunk-2077 --factor cp-renodx-hdr --factor cp-ultra-pt21
python scripts/tests/Test-GameToolCatalog.py
```

Plans preserve required native/shared hosts and dependencies in every Off/On comparison. They separate an idle manager's process usage from its deployed in-game payload, block unresolved chains and keep unmeasured CPU/GPU/RAM/VRAM fields null. The highest Ultra+ preset and Skyrim MFG/FrameWarp remain gated. Prepared plans are not authorizations or measurement results. See the [overhead protocol](../../docs/TOOL-RESOURCE-OVERHEAD.md), [architecture](../../docs/GAME-TOOLS-ARCHITECTURE.md) and [knowledge index](../../docs/GAME-TOOLS-KNOWLEDGE-INDEX.md).

Catalog 0.1.1 contains 34 components, two games, seven features, 25 typed relationships and seven declared capabilities. Primary-source links include stores/managers and official authoring tools. These records are not a fresh installed/running inventory. Hub 0.4.0 passes 230 Python contracts: original Hub 22, Catalog 35, bridge 36, GUI/CLI 36, inspector 34 and FG policy 67. Forty-two source-export contracts pass under PowerShell 7; the current Windows PowerShell 5.1 invocation was blocked by its script execution policy, which was not changed. The historical 0.3.0 checkpoint passed 110 Python and 41 export contracts in both PowerShell engines; those receipts are not relabeled as current 0.4.0 acceptance. See [tool connections](../../docs/GAME-TOOL-CONNECTIONS.md): fixtures/withdrawn Tk widgets and one read-only driver observation are not live game FG, input, benchmark or complete profile regression. This local continuation is not included in the previously published r5 source archive.

AHK source, Studio settings, native profiles and the private Hub executable registry are not migrated or edited by the catalog module. Rollback: close only the Hub instance being replaced, preserve its private reports/registry and restore the just-in-time prior Hub source. Remove/ignore only the two optional catalog integration modules if desired. Do not reset native/game settings or run an AHK diagnostic as part of catalog rollback.

## Offline comparison continuation — 0.5.0

Use the [offline reporting guide](../../docs/OFFLINE-COMPARISON-REPORTS.md), [exact normalized dataset/API contract](COMPARISON-DATASET.md) and [60-item master checklist](../../docs/GAME-TOOLS-MASTER-CHECKLIST.md). Comparison is optional and constructor-inert with respect to dataset/clipboard/dialog reads; its source failure leaves the original tabs available. At least three complete non-null reports per case/metric and matching definitions/workload/settings are required. Failed/cancelled/incomplete runs and missing values remain visible; no unsupported significance or root-cause claim is made.

The [shipped fixture](comparison-fixture.example.json) is synthetic, not a game/tool measurement. Real imported reports are eligible only for matched non-rendering manager-idle scope in this version; original report hashes are declared associations, not byte-verified measurements. Game/injected-feature reports stay raw-only BLOCKED even when imported JSON claims FG Off/fixed. This layer neither supplies nor bypasses the existing trusted FG gate.

Changed normalized source bytes require explicit reload before numeric redraw, copy or export. Export JSON/HTML preserves the selected metric, escapes HTML text, refuses existing destinations and never opens/uploads the result. Existing report archive intake remains unchanged; arbitrary CSV/HML files require a separately reviewed provider adapter rather than inferred grouping.

This continuation is local source only, not part of the published r5 archive. Current fixture/preservation/export evidence is in [tool connections](../../docs/GAME-TOOL-CONNECTIONS.md). Games, benchmarks, recording, extended input acceptance, MFG/FrameWarp, crash journaling and synchronized video remain outside this build stage. No AHK host restart or profile deployment is required.

## Saved-report import continuation — 0.6.0

For the later saved crash-evidence continuation see [0.8.0](#saved-crash-evidence-intake--080); this section retains the historical report-import acceptance boundary.

Comparison → **Import saved reports** previews explicitly selected Cyberpunk native benchmark summary JSON or PresentMon GUI statistics CSV. Assign each file to baseline/a; no case, timestamp or game identity is inferred from its filename. **Create import and load** writes a new private bundle with original bytes, source hashes, a manifest and generated `comparison.json`, then uses the existing source-bound comparison loader. Existing destinations and unsupported/raw-frame layouts are refused. The original Reports archive and normalized JSON loader remain available.

No manual normalization is required for these two adapters. Missing UTC/settings/runtime FG/memory evidence stays unknown, so imported game summaries remain raw-only **BLOCKED**, not advertised as a performance result. Cyberpunk's capacity fields are not VRAM/RAM usage. PresentMon's provider percentiles are not slowest-frame lows or base FPS. The [offline guide](../../docs/OFFLINE-COMPARISON-REPORTS.md) records exact layouts, source evidence, CLI exit meanings and limitations. Inspection is read-only; copying/archive creation requires the explicit import action. No AHK/profile migration, game test, benchmark, capture or upload is part of this continuation.

The four examples in `import-fixtures/` are authored **synthetic format samples**, not measured runs. The current [acceptance receipt](../../docs/GAME-TOOL-CONNECTIONS.md#2026-10-11--060-saved-report-import-adapters) records 442 Python toolkit passes/one skipped physical-symlink test, 11 separate PictureHost source passes and 44 PowerShell 7 export contracts. Withdrawn Tk tests do not establish foreground/game behavior. Four pre-existing Cyberpunk reports were inspected without changes; no actual PresentMon stats capture was available. Reopen the optional Hub to load the new source; do not restart the AHK host or migrate profiles for this addition.

## Saved crash-evidence intake — 0.8.0

Open **Sessions (Ctrl+8) → Saved crash evidence → Select saved files**. The optional view is inert until selection and starts no session, Event Viewer query, process watcher or game. [Evidence backend 0.1.0](../../scripts/GameToolCrashEvidence.py)/[panel 0.1.0](../../scripts/GameToolEvidencePanel.py) reuse Journal 0.1.0 source/prefix checks. Coordinator 0.2.0 adds `inspect_crash_evidence` for explicitly started journals. Sessions panel 0.2.0 retains prior controls and owns only its optional child windows. All eight tabs/shortcuts remain.

Inputs: Windows event XML (`Event` with Microsoft namespace, or `Events` wrapper), Hub journal JSONL, and UTF-8/UTF-16-BOM opaque text/log attachments. Binary EVTX/minidumps/custom plugins are unsupported. Extension auto detection selects format only, never game/run/time. Bounds: eight sources, 16 MiB/source, 32 MiB total, 2 MiB XML, 256 XML events, 8,192 timeline entries and bounded XML depth/nodes/text; DTD/entities refused. Existing summary-reader limits stay unchanged.

Portable preview/copy/JSON/escaped script-free HTML omit source filenames/paths, raw logs/messages, Computer/SID, unknown providers and application/module strings. Exact known AppName on Application Error/1000 can declare a Skyrim/Cyberpunk association, not verify a runtime target. XML Execution/ProcessID is the **reporting** process, not presumed game PID. Missing/invalid/non-UTC/raw timestamps remain null. Seven-digit UTC precision does not imply accuracy. See [Microsoft event schema](https://learn.microsoft.com/en-us/windows/win32/wes/eventschema-systempropertiestype-complextype).

Timeline retains source order/time, journal UTC backsteps, unverified tails and open ends. Earliest **reported** timed failure includes equal-time candidates; untimed failures stay visible and cross-provider clock error is unmeasured. Application Error/1000 is a reported failure; WER/1001 alone is report presence, not a crash verdict. Unknown events stay unclassified; text remains opaque. No cause, verified VRAM exhaustion, first actual failure, QPC/video alignment or live heartbeat/WER watcher is claimed. [Microsoft crash guidance](https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/troubleshoot-application-service-crashing-behavior) explains the faulting-module limitation.

**Create private packet** requires a fresh directory outside the repository: portable `evidence.json/html`, exact originals under generated aliases, a **private** source-locator receipt, and hash/size manifest written last. Originals/receipt may contain private data; no automatic upload/open/public export. Sources are rechecked before/after export. Individual flush/fsync/readback is not an atomic-directory/power-failure guarantee: missing manifest or mismatched entries means incomplete export. Existing paths, drift and unsafe links are refused; failure cleanup removes only owned linked files, preserving replacements.

Copy/export rechecks pinned preview hashes; drift requires explicit refresh/selection. CLI hashes are optional for direct one-shot preview/packet (one per source in order if supplied), mandatory for journaled inspection. Routes run before registry/live readers: exit 0 means evidence-only processing, not diagnosis/performance PASS; exit 2 means refusal. Packets cannot override FG/memory gates or replay actions.

[Current receipt](../../docs/GAME-TOOL-CONNECTIONS.md#2026-10-11--080-saved-crash-evidence-intake) owns tests/rollback. This is local source/withdrawn widget acceptance, not an installed UI/game crash test or full live companion. Restore only owned Hub/coordinator/panel/exporter changes from the fresh checkpoint, preserving newer/unrelated sources and private packets. No AHK restart/profile/settings reset is needed. Games, benchmarks and recording remain deferred.
