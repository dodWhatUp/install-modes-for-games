# Unified toolkit: preserved requests and continuation

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


Saved 2026-10-12 at the user's request before archiving the integration chat.
This is a retrieval/handoff map, not a new implementation or authorization.
Rich source masters and the stable GT-001–060 ledger remain their owners.

## Resume here

Read [the knowledge index](GAME-TOOLS-KNOWLEDGE-INDEX.md),
[preferences](../preferences/GENERAL.md), [master checklist](GAME-TOOLS-MASTER-CHECKLIST.md)
and the latest [installed receipt](GAME-TOOL-CONNECTIONS.md#2026-10-12--native-multi-image-canvas-redesign-installed).
Select only the records relevant to the new request. Recheck current source,
installed pointer, data ownership and active desktop owners; old acceptance
does not automatically apply after an update.

The saved baseline is **Hub 0.20.2 / Studio 2.2.0-unified.10**, retaining Game
Input 0.5-preview.3. Its exact 148-file authored-source package SHA-256 is
`5ebce6ad4e0c76bebe9310b0cc2c05cdb5718ff8315e8af3e9727e58c6a0edc0`.
Current pointer was `hub-0.20.2-5ebce6ad4e0c`; normal rollback/previous was
`hub-0.19.2-ac6b4b44a122`. The app was closed after desktop checks.
**Open Unified Game Tools.cmd** in the important-chat Downloads folder follows
the installed pointer; do not unzip an old package over installed files.

Keep **games, benchmarks, recording, game-input experiments and graphics changes
deferred** until a new explicit request selects a scope. The highest-compatible
Cyberpunk Ultra+ VRAM benchmark remains last, after earlier gates and a
user-facing continuation proposal. A menu/input check does not verify
MFG/FrameWarp third-person output. This archive request launches nothing.

## Requests, owners and unfinished boundaries

| Topic / stable requirement IDs | Owner | Preserve and continue |
|---|---|---|
| Modular unified toolkit, reusable services, efficient adapters; GT-001–009 | [Architecture](GAME-TOOLS-ARCHITECTURE.md), [Hub guide](UNIFIED-GAME-TOOLS.md) | Shared registry/workspace, offline coordination and existing AHK engines are retained. Extend common versioned contracts rather than duplicate collectors or destructively rewrite working features; broader live adapters/internal automation remain partial/planned. |
| Typed tool/game/feature catalog and manages/hosts/enables/dependency/conflict relationships; GT-002–007/041 | [Catalog/Hub](../examples/game-tool-hub/README.md), [overhead protocol](TOOL-RESOURCE-OVERHEAD.md) | Search/filter/detail and dependency-preserving plans exist. RHI, ReShade, RenoDX, OptiScaler, DLSS tooling, stores, managers and official mod kits need individually supported adapters. “DLSS SWITCHER” is not automatically identified as DLSS Swapper. |
| Per-tool/process/injected-feature/combination CPU/GPU/RAM/VRAM costs; GT-010–024/032 | [Comparison/reporting](OFFLINE-COMPARISON-REPORTS.md), [measurement](GAME-PERFORMANCE-MEASUREMENT.md) | Keep original provider-defined reports, units/scopes/frame classes, missing values, phases/cache, repeats, failures and dependency-preserving combinations. Bounded saved-summary imports/tables/charts/exports are not measured costs or a new complex lows/latency engine. |
| Effective FG/Dynamic MFG and memory warnings; GT-012–019 | [Mandatory gate](GAME-PERFORMANCE-MEASUREMENT.md#mandatory-benchmark-preflight--fg-and-memory), [Cyberpunk audit](../games/cyberpunk-2077/RUNTIME-VALIDATION.md) | Active/suspected/unverified Dynamic MFG or unknown effective FG blocks ordinary rendering-cost comparisons. Match Off or one known fixed multiplier and workload. Physical capacity, usage, budget/availability, RAM and commit differ. Stop on warnings; no mock/declaration supplies runtime PASS. |
| Coordination, first-failure/crash evidence and durable journal; GT-025–029 | [Procedures](AUTOMATION-OPERATING-PROCEDURES.md), [Sessions/evidence guide](../examples/game-tool-hub/README.md) | Offline flush/fsync/hash-chain/prefix recovery and selected saved-evidence intake exist. Live process/WER/provider heartbeats, clock calibration and causal diagnosis remain separate. Never replay a recovered journal as commands. |
| Optional crash-safe recording and synchronized side-by-side clips/charts; GT-030–033 | [Telemetry backlog](GAME-TELEMETRY-TOOL-PLAN.md), [architecture](GAME-TOOLS-ARCHITECTURE.md) | Established-recorder adapter, recoverable segments, retention/disk/privacy/overhead controls, shared seek/phase offsets/drift/gap warnings and player remain future stages. Default to reports/selected screenshots. Difficult game routes may remain future adapters. |
| Install/diagnose/rollback/help and opted-in gameplay automation; GT-034–041 | [Workflow](AUTOMATION-OPERATING-PROCEDURES.md#building-reusable-adapters), [operating standard](OPERATING-STANDARD.md) | Generic data-only dry-runs, diagnostic preparation and conditional rollback plans exist. Research/validate real product/game adapters. A recipe or catalog selection is not installation approval; preserve loaded-file ownership and current/known-good recovery. |
| Agent text, Enter, Escape and held keys in Skyrim/Cyberpunk; GT-042/043/060 | [Input ledger](AGENT-GAME-INPUT.md), [AHK integration](../examples/game-input/OVERLAY-STUDIO-INTEGRATION.md) | Supported observation plus guarded AHK, visible status, explicit Start/Stop and owned-key cleanup. Historical v0.3.1 menu/digit/caret/Backspace evidence does not verify arbitrary text/Enter/Escape/holds in the integrated build. No saves, graphics changes, unattended play or guard/anti-cheat bypass. |
| Picture Buttons/MIC/HUD, variants/library/context and overlays; GT-044–050 | [Picture contract](../examples/game-input/PICTURE-BUTTONS.md), [UI design](UNIFIED-UI-DESIGN.md), [overlay groups](OVERLAY-GROUPS.md) | Primary Picture and MIC connection-panel redesigns are installed. Keep preview separate from Save, drafts/columns/context controls and old callbacks. Advanced Picture/library and Key display/Status/Game Input redesigns plus broader device/DPI/runtime acceptance remain separate. MIC is still an external canvas program. |
| Azeron/reWASD/devices, layers and per-game labels/maps; GT-048–053/058 | [Controls](AZERON-GAME-CONTROLS.md), [device registry](INPUT-DEVICE-REGISTRY.md), [SPARSE6 assets](SPARSE6-OVERLAY-ASSETS-2026-10-11.md), [public R8 decision review](../research_outputs/input-controls/azeron-keybinds/r8/design-review/DECISION_REVIEW_HE.md), [private decision/evidence package](https://drive.google.com/file/d/1pRHVnfLdOIcEfsFuelxgjhzyNd26L1-j/view?usp=drivesdk) | Native software owns remapping. Preserve one shared layered base, effective binding provenance, Keys/Actions/Combined views, geometry/blank masks/outputs and reserved #19. Event-following is not a fresh snapshot or physical hold/release proof. Related keymap/asset chats retain their masters. |
| Intuitive modern/responsive UI and alternative layouts; GT-004/009/040/059 | [Design foundation](UI-AND-CONTENT-DESIGN.md), [implemented contract](UNIFIED-UI-DESIGN.md) | Keep goal/feature navigation, compact editable search/selection where appropriate, keyboard access, resize/scroll/sidebar/columns and readable hover labels. ? Identify UI markers are on actual interactive/noninteractive components with filters/copyable stable IDs. Hiding is not disabling; mode switches retain drafts. |
| Easy opening, in-place updates, old-data compatibility and opt-in cloud; GT-001/055–059 | [Open/update guide](UNIFIED-GAME-TOOLS.md), [knowledge maintenance](KNOWLEDGE-MAINTENANCE.md) | Retain stable double-click entry, immutable pointers/guarded updater, existing profiles/features and separate view data. Supported additive migrations preserve IDs/unknown fields; unknown formats need reviewed handling. Cloud sync is future opt-in, not automatic upload. |

The original PureDark/NVIDIA MFG/FrameWarp request, Skyrim downgrade/loader work
and paid-release access belong to [Skyrim history](../games/skyrim-special-edition/HISTORY.md)
and the [private-release index](PUREDARK-ARCHIVE-2026-10-07.md). Preserve those
dated records; they are not renewed permission to download/install paid mods.
[Related-workstream sources](GAME-TOOLS-KNOWLEDGE-INDEX.md#source-masters-and-linked-workstreams)
include the benchmark, game-label, overlay and Pro continuity owners. Do not
request already-received material again or merge their independent master data.

## Lessons and acceptance limits

[Input history](AGENT-GAME-INPUT.md) preserves focus races, tool trigger limits,
Steam overlay/screenshot correlations, modifier/locale concerns, AHK lifecycle
and loader fixes. These do not establish one universal cause of input failure.
Cooperative ownership cannot control unrelated apps/chats; observe after each
bounded action and respect provider/user-input guards.

[Native UI acceptance](GAME-TOOL-CONNECTIONS.md#2026-10-12--native-multi-image-canvas-redesign-installed)
preserves locale-safe Hotkey VK reading, native dropdown popup-height sizing,
one-shot non-looping repaint and visible MIC Modern/Classic radio choices.
The earlier saved-Modern startup loop required one wrapping owner and idempotent
geometry. 707 focused checks and bounded installed visual/navigation acceptance
are historical scoped evidence, not completion of every requirement. Broad
popup/focus/all-DPI acceptance and unrelated outer-heading wrapping remain future.

Ultra+ memory screenshots and suspected Dynamic MFG masking are evidence, not
a proved OOM cause or equal-cost result. The latest RED4ext screenshot shows a
denied log-rotation rename; the lock-holder/access-rule cause is unknown.
Cyberpunk repair was not performed during the MIC/editor or preservation work.

## Private archive coverage

Alias **UNIFIED-TOOLKIT-CHAT-20261012** preserves all ten returned pages:
81 distinct turns and 629 distinct visible user/assistant messages at the initial
snapshot, including interrupted/returned in-progress turns. No older cursor
remained. Original text, message/turn IDs, statuses, page cursors and chronological
user-request copies are private, not public repository data. The snapshot includes
the archive request and initial replies; later replies/final receipts postdate it.
Returned historical statuses are not rewritten as completion.

All **seven explicitly referenced local attachments** were copied/byte-verified:
six screenshots and one pasted instruction file. Prior bounded related-source
indexes, benchmark review evidence and the earlier private message package are
copied with provenance. Whole related/unrelated account histories, deleted or
inaccessible material, tool calls/outputs and reasoning are excluded. This is
an available-message projection, not an account-wide raw export.

Before/current knowledge snapshots, exact installed authored-source and private
acceptance receipts are included. A refreshed source export adds this map/data
record, not a new installed release. Entry hashes and the convenient Downloads
ZIP copy must be verified before archiving completion. Personal/native/game
recovery checkpoints stay separately owned; hash/copy verification is not a
functional restore test. No Drive/GitHub upload, sharing change, profile restore,
app/game launch, scheduler or cross-chat message occurs from this request.

## Future continuation

Recover the relevant GT IDs, strongest current source and latest receipt.
Prepare goal/exclusions/versions/scope, fresh preservation, proportionate tests,
stop/cancellation and smallest rollback. Key display could be the next native
editor slice, followed by Status/Game Input; advanced Picture/library is another
scoped choice. Do not execute any stage merely because this plan exists.

Append new requirements/evidence without renumbering GT IDs or replacing rich
masters; record exact revisions and coverage. Project instructions route relevant
future work to this map. Outside this project, supply the index/source locator
or use the existing game-modding-history skill. This is file-based retrieval,
not account-wide automatic memory or background monitoring; see
[official Codex instruction scope](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

## Verification receipt — 2026-10-12

The private ZIP passed size/hash verification for all **80 entries** and the
convenient Downloads copy is byte-identical: 19,102,190 bytes, SHA-256
`599f0c6d19e33e561afcb30a1b0a990c9c5a36ff68f9d9d0c9bebd4c86ad239b`.
The chronological message projection SHA-256 is
`b378aaa24a7278adbb951d0994e335eec4f6cb3532130ad2b1ae8abd7dd7dfd4`.
Seven attachment copies were verified; none of the seven referenced paths was
missing. The refreshed 150-file authored-source package passed entry/hash and
current-source checks, SHA-256
`a8d052099b8ab8309778a3ca963708ea0f5d3ccce91d12cd4be432ed8d6a96be`.
The retained exporter passed 61 synthetic contracts; no app/game/capture test
ran during preservation. A concurrent PoE2 index addition was separately
checkpointed and retained. Functional restore remains untested.

These final receipt lines and the corresponding data-record result postdate
the immutable ZIP/source package; their included continuation copies are the
preceding revision. Exact private locators and coverage are in the local private
FINAL-RECEIPT.json/MANIFEST.json. No new release was installed or uploaded.
