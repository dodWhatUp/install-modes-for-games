# Game tools knowledge and recovery index

Reviewed 2026-10-11. Start here for research, game-mod work, PC assistance and automation-tool development. Use the maintained repository for procedures and sanitized evidence, private Drive archives for recovery, and the original authors for current software. A dated backup is not automatic synchronization or proof of runtime acceptance.

## Read for the requested task

| Task | First sources | Practical boundary |
|---|---|---|
| General research or PC automation | [Preferences](../preferences/GENERAL.md), [automation procedures](AUTOMATION-OPERATING-PROCEDURES.md), exact app/tool history | Read-only inspection first; old results must match the current build |
| Build or extend the toolkit | [Architecture](GAME-TOOLS-ARCHITECTURE.md), [catalog and overhead protocol](TOOL-RESOURCE-OVERHEAD.md), existing source/tests | Preserve source masters, interfaces, profiles and evidence states |
| Install or diagnose game mods | [Operating standard](OPERATING-STANDARD.md), [feature decision](FEATURE-DECISION.md), exact game's history/catalog | Scope, snapshot, one owner/layer, observed verification and rollback |
| Control a mod menu or test keyboard input | [Agent game input](AGENT-GAME-INPUT.md), [installed Studio record](../examples/game-input/OVERLAY-STUDIO-INTEGRATION.md) | Historical menu success is not extended input acceptance; stop after the task |
| Measure tool or stack overhead | [Overhead protocol](TOOL-RESOURCE-OVERHEAD.md), [measurement procedure](GAME-PERFORMANCE-MEASUREMENT.md), [tool connections](GAME-TOOL-CONNECTIONS.md) | Match workload, preserve metric definitions, separate process and injected-feature costs |
| Device profiles and game labels | [Azeron controls](AZERON-GAME-CONTROLS.md), [device registry](INPUT-DEVICE-REGISTRY.md), [draft label brief](https://github.com/dodWhatUp/install-modes-for-games/pull/4) | Native mappings own input; label changes must not remap outputs |
| Crash evidence and video comparisons | [Architecture recovery and video sections](GAME-TOOLS-ARCHITECTURE.md), exact game history | Future optional modes; no guaranteed preservation of the unflushed tail |
| Backup or publish | [Distribution](DISTRIBUTION.md), [GitHub procedure](GITHUB-PUBLISHING.md) | Source bundles and private recovery backups are different artifacts |

Search exact game/executable/feature/DLL/error before acting. Prefer current observed evidence over general advice; refresh upstream support when versions or experimental reviews change. Carry only the relevant records into a task, not unrelated account history.

## Source masters and linked workstreams

The canonical knowledge repository is [dodWhatUp/install-modes-for-games](https://github.com/dodWhatUp/install-modes-for-games). The local configured Studio 2 remains the installed host; the equivalent authored integration is [here](../examples/game-input/AzeronOverlayStudio.integrated.ahk). Separate previews and source workstreams must not overwrite it automatically.

| Workstream | Recorded source | Current meaning |
|---|---|---|
| This integration and consolidation chat | [Input ledger](AGENT-GAME-INPUT.md), [validation JSON](../examples/game-input/VALIDATION.json), [architecture](GAME-TOOLS-ARCHITECTURE.md) | Source integration installed; host acceptance partial; extended game input pending |
| “סקריפת לבנצמארק” | [Hub](../examples/game-tool-hub/README.md), [issue 3](https://github.com/dodWhatUp/install-modes-for-games/issues/3), [private Hub source/evidence](https://drive.google.com/file/d/1gNLyNVTaUP54zlxCdc27ArihOvfo157F/view) | Hub 0.2.0 connection/core controls, not a completed benchmark runner |
| “סקריפט ליצירת תמונה מותאמת למשחק ספציפי” | [draft PR4](https://github.com/dodWhatUp/install-modes-for-games/pull/4), [private installation report](https://drive.google.com/file/d/1aPG87HJnHa7J6RGZUTdnPKCs8Z0GYQEE/view) | Four SHARED R5 profiles loaded; label generator and general gameplay outputs pending |
| “Create Azeron Overlay Apps” | [canonical preview record](https://github.com/dodWhatUp/install-modes-for-games/blob/main/docs/OVERLAY-STUDIO-3-PREVIEW-2026-10-10.md), [draft PR2](https://github.com/dodWhatUp/install-modes-for-games/pull/2) | Separate source/preview lineage, not an installed Studio 3 upgrade |
| “Game Keybind Analysis” | [R1 editable master](https://github.com/dodWhatUp/install-modes-for-games/blob/main/research_outputs/input-controls/azeron-keybinds/AI_MASTER.json), [R2 extension](https://github.com/dodWhatUp/install-modes-for-games/blob/main/research_outputs/input-controls/azeron-keybinds/extensions/2026-10-10-r2/R2_UPDATE.md), [native R5 schema](https://github.com/dodWhatUp/install-modes-for-games/blob/main/research_outputs/input-controls/azeron-keybinds/stage-b/native-v2/SCHEMA_NOTES.md) | Research masters and native-format schema are distinct from derivative images/workbooks and runtime acceptance |
| Newer R6 design candidate | [R6 README](https://github.com/dodWhatUp/install-modes-for-games/blob/1bccb8793f3ad26187a69bcb170b601b2f990eed/research_outputs/input-controls/azeron-keybinds/stage-b/native-v2/r6/README.md), [publication manifest](https://github.com/dodWhatUp/install-modes-for-games/blob/1bccb8793f3ad26187a69bcb170b601b2f990eed/research_outputs/input-controls/azeron-keybinds/stage-b/native-v2/r6/PUBLICATION_MANIFEST.json) | COMPACT/SPARSE variants and HTML prototype; not installed/imported/physical/game acceptance; R1/R2 and R5/live changes preserved |
| “Create a shared game menu layer” | [Cyberpunk overview](../games/CYBERPUNK-2077.md), [history](../games/cyberpunk-2077/HISTORY.md), [control procedure](AZERON-GAME-CONTROLS.md) | Game/context-specific observations, not universal bindings; detailed local binding JSON is not published in this pass |
| “Fix Cyberpunk Ultra+ VRAM crashes” | [latest Cyberpunk history](../games/cyberpunk-2077/HISTORY.md), [runtime validation](../games/cyberpunk-2077/RUNTIME-VALIDATION.md) | Earlier pressure/broken-stack diagnosis is historical; OOM cause was not proven |
| “בדוק והתקן בנצ׳מרק למעבד” | Related-chat installation summary | Cinebench installation was reported; no benchmark result is adopted here |

Chat identity/retrieval details belong in the private source index. Coverage is this conversation's recorded work plus bounded relevant turns and saved artifacts in the named related chats, not every account or archived chat. Direct history for “Create Azeron Overlay Apps” and “Game Keybind Analysis” was rate-limited; canonical saved records are the recovery route. No accessible Space was returned by the connected Pages listing. “המשך קליטת הודעות Pro” was identified but not content-reviewed; the separately mentioned Pro artifacts remain unreconciled. No message was sent to another chat.

## Private recovery references

- [Current authored source/knowledge checkpoint r4](https://drive.google.com/file/d/1TYp7eEQMXugertEkDJ2711dRHHujnJB8/view): 47 curated files and hash manifest for current input integration, Hub, catalog, procedures and templates. Archive entries and downloaded Drive bytes matched. Source-only coverage and pending runtime gates remain explicit; the receipt/final link postdate the immutable package.

- [Current private GameTools recovery checkpoint](https://drive.google.com/file/d/1BNk-LCA2gIaTd-t7D4vIB6QuL13e4hxR/view): installed Studio2 source/settings/picture, original host recovery, Hub registry and bounded source index. Source/copy/archive hashes and Drive byte readback matched; restore remains untested. See [coverage and receipt](DISTRIBUTION.md).

- [Existing game-modding export folder](https://drive.google.com/drive/folders/1uQuBbrDS0bSVibb-1kj2arZfjVfnrFLy): dated source/guidance exports and the new backup receipt in [distribution](DISTRIBUTION.md).
- [Azeron recovery start page](https://drive.google.com/file/d/1YazzDmaOkWb_ximHZfe-PfU3J3gTj3G_/view) and [existing private controls folder](https://drive.google.com/drive/folders/1VC1i0sh2GLrCnQpO0pjjbA6dnks6tpEr): profiles, diagrams and historical references.
- [SHARED R5 native export](https://drive.google.com/file/d/1DbjhZdzBhXJ1FwWKvcY-_h_9-CrTHCwG/view) and [pre-install recovery archive](https://drive.google.com/file/d/1WCXcUaEDYjrJdUruxGRXV36HhpMvwZVD/view): preserve their exact native schema and import requirements; the application's Import dialog remains unaccepted.
- [Studio 3 exact-source package](https://drive.google.com/file/d/1COZhma8Ur8iFWc1bkuAqOd4lwIudLY5z/view) and [earlier overlay/MIC source archive](https://drive.google.com/file/d/1Cqek3Lk_VjKTPO7g6m2tjySpIcMNGZl3/view): source delivery checkpoints, not personal settings/device recovery or native runtime acceptance. PR2 contains an earlier LayerPictures candidate; exact Studio3 code has not been represented as already committed there.
- [Historical GameInputModule package](https://drive.google.com/file/d/1xCE9ycIyf0m6IYUfrXng57bSbxq5PQnJ/view): dated preview.1 source and exact v0.3.1 baseline, not the current installed preview.3 integration.
- [PureDark archive index](PUREDARK-ARCHIVE-2026-10-07.md): paid-release recovery stays private and separate; no binaries are duplicated into public source bundles.

A source ZIP alone cannot restore pictures, MIC configuration, native mapper/onboard exports, tool settings or game binaries/saves. Follow each package's coverage and restore instructions. Hash inventories establish identity, not that file contents were backed up. Do not restore a whole profile/store to undo one optional module.

R6 is a separately published design/prototype source, not a newly applied profile or replacement master. Reserved button #19 has no emitted overlay trigger. Later labels must preserve the exact chosen variant/layer outputs, omit joystick drawing and retain unknown actions. Installation needs a selected family, current live-state recovery and scoped acceptance; publication is not installation authority.

## Reuse in future chats

Repository routing is linked from `AGENTS.md` and preferences. Read relevant records explicitly in an already-running or different-project chat; this does not silently modify global Codex settings or every chat's context. OpenAI documents `AGENTS.md` as project guidance and MCP as a controlled tool connection, not automatic global memory or authority. [Project instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [MCP tool design](https://developers.openai.com/plugins/build/mcp-server).

Copy-ready request:

> Use the canonical game-tools knowledge index, current preferences and the exact game/tool history. Preserve existing source masters, features and profiles. Separate tested, upstream-supported, inferred and unknown states. Inspect through supported tools first; execute only my requested scope, with a current-state snapshot, exclusive input ownership where needed, observed verification and a documented rollback. Use existing metric providers and private recovery archives. Do not resume deferred game tests, recording or benchmarks merely because a procedure exists.
