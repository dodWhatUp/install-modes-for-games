# Overlay groups — Hub / Studio

## 2026-10-12 — Experimental automatic Azeron layer following

Hub **0.17.0**, Overlay/Panel **0.2.0** and Azeron Layer **0.1.0** add a read-only
native-log follower for inspected **Azeron 2.0.2.442**. The existing Overlays page
adds **Follow Azeron layer (experimental, this session)**, default On when
automatic overlay selection is enabled. Turning it Off retains the old manual
selected layer. Saved selections/formats, native mappings, gestures, settings,
input owners, picture triggers and assets are not rewritten.

Only new timely UUID-valued `Switch layer on toggle hold`, `Switch layer` and
`active profile reported` messages establish state. Start at EOF: historical
logs and assumed BASIC are never current evidence. Background reader cadence
is 50 ms; Hub refreshes every 100 ms while following. These are configured
cadences, not measured latency. Exact native profile ID, current file SHA-256
and registered keymap identity must match. The same selection feeds the
existing Studio display relay if that optional route is enabled; original
Hold/Toggle/Timed/release ownership remains unchanged.

State is **Event-tracked**, not **Observed/snapshot-verified**. A quiet held
interval retains the tracked layer while the same process/event stream is
readable. Process exit/restart, log replacement/truncation, uninterpreted context
changes, delayed/out-of-order/malformed events, backlog, unknown profiles or
changed profile bytes invalidate it. A stalled reader expires after 500 ms.
Unknown tracking hides the passive map, not a misleading manual fallback.
Pinned Explore is still an explicit selected snapshot. Closing Hub stops the
reader; there is no service, firmware/HID write, keyboard inference, debug-port
activation, native IPC command, remapping or profile import.

This is an **experimental diagnostic-output adapter**, not an official Azeron
SDK or a guarantee that every native transition is logged. Unlogged changes
cannot be detected. Matching log-message strings in the current installed app
and historical hold/release pairs were inspected, not live physical acceptance.
The current read-only probe found the exact build/process, but **no fresh layer
event** and correctly stayed Unknown/waiting. An existing diagnostic-port
reference was stale/refused; it was not enabled or restarted.

Automated acceptance: **22 synthetic transition/UI-wiring cases** and **53
existing selection/withdrawn-UI cases** passed. Tests cover all five secondary
banks, sustained hold and release to BASIC, stale/disconnected/restarted readers,
old/delayed/future/malformed/partial/truncated logs, backlog, unknown profiles,
revision drift, manual mode and Stop. Synthetic native profile/store bytes stay
unchanged. An inert Tk root/mocked renderer was used; no manual button tests,
games, benchmarks or recording. **Physical timing and full live event coverage
remain unverified.** [Installed receipt](GAME-TOOL-CONNECTIONS.md#2026-10-12--azeron-layer-event-following)
owns scoped preservation and rollback. Disable only Follow Azeron layer, or use
the existing guarded previous-version update; do not overwrite native profiles.

[Azeron 2.0.2 release notes](https://azeron.com/pages/software-changelog-2-0-2)
document native tracking fixes, not a public telemetry SDK. Third-party
remappers requiring profile changes were not installed.

## Historical 0.11.0 baseline

App-side display implementation, 2026-10-11. This extends the existing Hub and optional Studio picture module, not a separate remapper. Installed Studio **2.0.0-beta** remains unchanged; the owner-held Picture Buttons preview is the base of the new **2.2.0-groups-preview.1** source. The separate Studio 3 preview remains a source lineage, not an installed replacement. Hub retains the original eight pages/Control+1–8 and adds Overlays without a new global shortcut.

## Common use

Open the existing Hub's Overlays page (`--overlay-page`). Import a validated private manifest, associate the real gameplay executable, explicitly select the native layer/context/view, then opt into automatic selection/display. The game must be foreground; background games and excluded launchers do not select a map. Full path matches outrank basenames, then priority; conflicting equally ranked mappings display nothing. Stable IDs persist across PID changes. No match, focus loss, app-owned windows, stale state, missing/corrupt images or profile mismatch hide the passive map. Another game's old action map is never a fallback.

In the historical baseline native telemetry was **not implemented**; states were
**Selected** or **Unknown**. The newer event follower above does not provide a
fresh native snapshot or reWASD adapter. A saved profile, keyboard event or app
process alone is not physical-layer evidence. The trusted in-process boundary
retains **Observed**, **Stale** and revision-mismatch fixtures; imported JSON/CLI
cannot claim observations. Native mappings and game bindings are never edited.

One editable native selector combines choose/search with explicit Add new. Typing filters but does not create/save; Escape restores the committed ID; Enter commits an existing value. Games/groups use contextual creation; context creation validates an ID. Executable selection uses one editable control with a Choose menu for Browse or running-window candidates. Candidates are never foreground selection evidence. Required association details, keymap references, exclusions, priority and cycle order are available in the contextual advanced editor. Groups can share assets and rendering geometry. Return to Auto clears a per-game override; cycling follows the explicitly enabled saved order. View controls persist separately from enablement; Reset view never changes mappings or operational settings. Status/override/errors remain visible even when details are hidden.

**Peek** is passive and held; **Explore** is an explicitly opened, pinned interactive *selected snapshot*, not a live native observation. Hub registers no new hotkey. For keyboard-held Peek, choose `Studio trigger instead` in Hub and explicitly enable the optional Studio route for an existing local picture slot. It starts Off, preserves Hold/Toggle/Timed/release ownership and consumes a fresh, hash-checked display-only relay. Do not invent a #19/F13/F15 trigger. Original MIC/HUD/slots and advanced appearance library remain independent. The installed host requires a separately scoped supported upgrade before it can consume this route.

## Asset contract 1

The strict Python validator is [GameToolOverlay.py](../scripts/GameToolOverlay.py); [template](../examples/game-tool-hub/overlay-manifest.example.json) contains placeholders, **not activatable assets**. `schema` and `capabilities` publish the contract/version. Unknown fields, future versions, duplicate IDs, ambiguous group assets, wrong references and arbitrary commands are refused.

| Collection | Required fields / meaning |
|---|---|
| Manifest | `schema_version:1`, `kind:overlay_manifest`, `games`, `keymaps`, `assets`, `groups`, `associations` |
| Game | `id`, readable `label` |
| Keymap | `id`, `label`, exact installed `revision`, `outputs_sha256`, `geometry_sha256`, `atlas_revision`, `family`, `layers`, `visible_positions`, `hidden_positions`, `blank_masks`, `joystick_drawn:false` |
| Layer | `id`, fresh installed `profile_id`, actual native file `profile_sha256` (never candidate UUIDs) |
| Asset | `id`, `label`, relative local `path`, byte `sha256`, `keymap_id`, `layer`, `context`, `view:Keys/Actions/Combined`, matching `profile_id`, `evidence:effective_config/published_default/unknown` |
| Group | `id`, `label`, `game_id`, exact `keymap_id`, ordered `asset_ids`, `rendering` |
| Rendering | `size_mode:Pixels/Screen width %/Screen height %/Original %`, `size_value`, `opacity:5..100`, one-based `monitor`, `anchor:TopLeft/TopRight/Center/BottomLeft/BottomRight`, `offset_x`, `offset_y` |
| Association | `id`, `game_id`, gameplay `executables` (absolute paths or exact basenames), `excluded_executables`, exact `keymap_id`, `default_group`, ordered `cycle_groups`, `cycle_enabled`, `priority:-100..100` |

All 29 R8 digital positions, including #36/#37/#38/#41, remain source-derived. #19 is hidden/unassigned; the stick drawing is omitted without changing its configuration. Each layer supplies its complete blank mask. Build a **private** exact template with [Build-OverlayContract.py](../scripts/Build-OverlayContract.py) from the pinned R8 design and fresh installed native files. It reuses the Atlas family/bank/position-map contract, not a guessed remapping. `outputs_sha256` fingerprints the canonical design maps; `geometry_sha256` fingerprints its position map; native file hashes separately identify installed revisions. This is configuration identity, not effective gameplay or firmware verification. Source/default/effective/unknown action labels must remain distinguishable in generated images; the app validates declared references, image bytes and decoding, not semantic correctness of every rendered label.

Imports decode PNG/JPEG pixels (16 MiB, 16 MP, 8192 maximum side), check SHA-256, and publish content-addressed managed copies before activation. No SVG/HTML/code execution. Linked source images are copied so moving a source does not break the import. Repeated identical assets deduplicate. Conflicts default to **stop** with no registry change; explicit **keep**/**replace** applies to conflicting IDs only. Referenced combinations must remain valid. Registry writes use an exclusive cooperative lock, expected preceding hash, fsynced temp file, atomic replacement and readback; each preceding state has a content-addressed recovery copy. A crash may leave unreferenced asset bytes or a lock; inspect rather than silently delete/replay. This sidecar is new/additive, not a rewrite/migration of the Studio INI or legacy view-only groups. Unsupported/future schemas stop rather than guess a migration. Private exports retain original IDs/references/images and revalidate; never publish personal profiles/assets/executable paths as source.

## Structured operations

From an extracted release, use a verified Python with Tk/Pillow. Commands below use paths relative to that release; private locators in the completion handoff identify this tested package exactly. `D` denotes an explicitly selected private store directory (normally `%LOCALAPPDATA%\GameToolHub`). All writes require its current `store_sha256` from `list`, or `absent` for a new store. CLI edits are read by an already-open Hub on the next 250 ms poll; CLI never launches the Hub or displays/injects independently.

```text
python scripts/Game-Tool-Hub.py overlay --directory D schema
python scripts/Game-Tool-Hub.py overlay --directory D capabilities
python scripts/Game-Tool-Hub.py overlay --directory D list
python scripts/Game-Tool-Hub.py overlay --directory D inspect --id association-id
python scripts/Game-Tool-Hub.py overlay --directory D status
python scripts/Game-Tool-Hub.py overlay --directory D foreground
python scripts/Game-Tool-Hub.py overlay --directory D validate --source private/manifest.json
python scripts/Game-Tool-Hub.py overlay --directory D import --source private/manifest.json --expected-sha256 HASH --conflict stop
python scripts/Game-Tool-Hub.py overlay --directory D association --source private/association.json --expected-sha256 HASH
python scripts/Game-Tool-Hub.py overlay --directory D selection --source private/selection.json --expected-sha256 HASH
python scripts/Game-Tool-Hub.py overlay --directory D select --source private/group.json --expected-sha256 HASH
python scripts/Game-Tool-Hub.py overlay --directory D cycle --source private/group.json --expected-sha256 HASH
python scripts/Game-Tool-Hub.py overlay --directory D auto --source private/group.json --expected-sha256 HASH
python scripts/Game-Tool-Hub.py overlay --directory D display --source private/display.json --expected-sha256 HASH
python scripts/Game-Tool-Hub.py overlay --directory D visibility --source private/view.json --expected-sha256 HASH
python scripts/Game-Tool-Hub.py overlay --directory D export --output private/NEW-export --expected-sha256 HASH
```

Small write payloads: selection `{ "game_id":"game-id", "layer":"BASIC", "context":"gameplay", "view":"Combined" }`; group `{ "game_id":"game-id", "group_id":"group-id" }` (`group_id:""` for auto/cycle); display `{ "enabled":true, "display":true, "display_target":"hub" }` (or `studio`); visibility `{ "details":false, "associations":true }`. Association uses the exact row schema above. No input payload/command-runner endpoint exists. Status/list contain private paths/IDs where relevant: do not automatically upload them.

Foreground observation uses documented [GetForegroundWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getforegroundwindow) and QueryFullProcessImageNameW, closes handles and rechecks window identity. Null/racing/inaccessible foreground fails closed. Bounded 250 ms polling was chosen instead of [SetWinEventHook](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwineventhook), avoiding hook/callback lifecycle complexity; CPU/resource cost is not benchmarked. Passive windows use NOACTIVATE/click-through and [ShowWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow) without foreground calls. Native Tk combobox keyboard behavior is reused; a future web host should follow the [editable-combobox accessibility pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/).

## Install / update / rollback

This builder does **not** upgrade or launch the installed host. Verify the package SHA-256 from the private acceptance receipt, extract into a NEW versioned folder, then run `scripts/Install-GameToolsRelease.ps1 -Mode Inspect`. It verifies every source member against `MANIFEST.json`. `-Mode Stage -Destination NEW-directory` copies only those verified members and activates nothing. Launch the existing Hub through its included launcher when separately desired. Requirements: Windows, Python 3.11+ with Tk and Pillow; optional AHK v2.0.30. No interpreter download, startup registration, listener/service, scheduler or new profile is installed.

For an explicitly approved Studio upgrade: close all AHK hosts normally; reconcile installed source/version against this release; create a fresh expected-file hash JSON keyed by `AzeronOverlayStudio.ahk`, `GameInputModule.ahk`, `OverlayStudioGameInput.ahk`, `StudioPictureModule.ahk`, `StudioOverlayGroups.ahk` (`absent` when genuinely absent). Run the verified installer with `-Mode UpgradeStudio -Destination existing-Studio-directory -ExpectedInstalledManifest private/expected.json`. It refuses running AHK, linked paths, mismatched/newer source and missing expected hashes, copies/hash-checks source plus current settings before source mutation, writes only those five owned AHK files and starts nothing. Existing Studio settings/shortcuts/profile files remain untouched. Keep prior known-good recovery separately. Installation can be partial on I/O/concurrent failure: preserve the checkpoint and inspect; never treat an error as no change.

Rollback: stop only the optional display route/Hub normally; preserve later source/settings/assets; restore only changed named AHK files from the just-in-time `groups-before-*` checkpoint. Leave added modules unused when their original state was absent. Restore prior Hub source by selecting the preceding versioned folder; recover only the new overlay sidecar from its preceding hash copy if explicitly needed. Do not roll back all native profiles/settings or erase assets to undo a display module. Source/package integrity is not a real-host restore test.

## Requirement-to-test receipt

| Requirement | Implemented acceptance / boundary |
|---|---|
| Foreground/path/PID restart/ambiguity/alt-tab/exit/own windows | Pure selection fixtures; one Windows passive NOACTIVATE/click-through integration; no game compatibility claim |
| Native profile/layer/revision/context/view | Exact-reference fixtures, fresh/stale/mismatch mock provider. Real native observation unavailable; explicit selection retained |
| Groups/default/cycle/manual/Return to Auto | Shared Store/choose tests; restart/readback/CLI-list agreement |
| Images/import/export/recovery | Missing/corrupt/hash/ref/duplicate/size/path/conflict/additive/round-trip tests; future schema refused, no legacy routing inferred |
| Compact search/create/cancel/keyboard | Withdrawn native Tk fixtures; query/Enter/Escape stable-ID and explicit commitment tests; complex manifests use disclosed data editor |
| Visibility vs enablement / narrow/DPI | Persist/reset independent-state fixtures; selector scaling/long-label and monitor geometry cases. Full legacy Studio UI translation/DPI usability not claimed |
| Passive Peek / pinned Explore | Owned-renderer fixtures; actual Windows no-focus passive test. No global new shortcut, no live installed AHK relay acceptance |
| Studio/HUD/pictures/tray/shortcuts | All 60 original method source checks, original five tabs, existing input modules preserved; native inert route/syntax/picture fixtures. Existing runtime/extended game checks still pending |
| Preservation | Scoped source copies + protected installed AHK/settings/Hub registry/native storage hash inventory/readback; no whole-system/onboard-firmware recovery claim |
| Package/update | Exact curated source bytes; inspect/stage/upgrade/drift/rollback mocks. Installed upgrade and actual recovery not performed |

Detailed passing/failure/skip counts and exact source/package hashes belong to the immutable private acceptance receipt. The first legacy picture run failed at a pre-existing expected count of two versus three inherited/own references; the saved baseline reproduced it identically. The assertion was corrected to retain all three, not weaken the deletion guard. Initial full-Hub tests also required additive ninth-tab expectations; all original eight shortcut contracts were retained. Prepared templates, mock observations and source preservation are not live Atlas/assets/native/game acceptance. Games, benchmarks, recording and input experiments remain stopped/deferred.
