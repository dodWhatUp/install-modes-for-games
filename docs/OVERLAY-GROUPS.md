# Overlay groups — Hub / Studio

## Hold-to-show over other applications — 0.27.8 preview

**Other applications…** on the overlay page chooses a fallback map group for
foreground applications without a game association. Choose **Off** to restore
association-only behavior. The destination uses the shared SPARSE6 group, so
other applications get the shared key layout while recognized games retain
their own action maps. The fallback group is explicit; an ambiguous game match
still refuses display rather than substituting an unrelated action map.

This uses **Studio trigger instead** and the existing picture slot. Holding
physical #19/F24 shows the map; releasing hides it. Layer changes select
content without showing the map. The current fade, opaque centered appearance,
continuous layer replacement and input owner are retained. The fallback also
works over the toolkit's own windows through Studio; the Hub's passive renderer
keeps its own-window guard. No new hotkey, injected key or profile is created.

The optional private `overlay-fallback.json` stores one registered group ID or
null (Off). Save checks the current registry and prior sidecar bytes, keeps the
previous sidecar, and commits atomically. Search/cancel does not save. Existing
overlay registry, executable associations, JSON maps and native profiles remain
unchanged. Older source releases ignore this separate preference, so source
rollback does not require downgrading the overlay registry.

Every relay still names the actual foreground executable, expires promptly and
requires the exact image hash and current native layer/profile/output identity.
Missing, stale, foreign or corrupt sources refuse display. First physical layer
press/release after launch still initializes the native event tracker. Tests
cover other-app/game priority, own windows, expiry, native/image mismatch,
selection persistence and editor cancellation. Physical holds over actual apps
need separate user acceptance. Windows secure desktops and exclusive-fullscreen
presentation are outside this normal-desktop acceptance scope.

## Visual map builder and chat exchange — 0.27.6 preview

[Keymap documents](KEYMAP-DOCUMENTS.md#visual-builder--0276-preview) now covers
visual R8 map construction, separate key/action labels, native read-only generation,
one/multi-game JSON packages, source history, explicit game associations and
fixed-map links to existing Studio picture buttons. The selected-file chat workflow
exports a bounded request and reviews action-only proposals before draft adoption.
There is no API dependency or automatic transmission. The same guarded renderer,
hold/release owner, continuous layer presentation and optional fade remain shared.

## Optional show/hide fade — 0.27.5 preview

Overlays → **Show/hide transition…** opens a compact editor with **Smooth
show/hide** and one **Fade duration (ms)** control, 20–400 ms. Save commits the
choice for later launches; Cancel leaves it unchanged. Turning the option off
restores immediate show/hide while retaining the chosen duration. The separate
private preference defaults to Off/120 ms when absent; configuring this feature
does not rewrite the map registry, native profiles or legacy Studio settings.

The Studio route includes optional validated fade durations. The alpha presenter
keeps one decoded surface while visible, changes global opacity with
[UpdateLayeredWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-updatelayeredwindow),
and releases that surface on hide. A short-lived timer runs only during a fade.
Full visibility still reaches the configured map opacity. Valid layer swaps retain
the current window, opacity progress and held release token; they do not restart
the fade. Rapid repress reverses a pending fade-out on the same window. Logical
release takes effect immediately even while the last pixels fade away.

Explicit Hide, pause, shutdown and invalid display context hide immediately.
Freshness, foreground and image identity are checked during the animation; a
rejected held map can recover only through the existing same-hold route owner.
External MIC and legacy picture rendering retain their own behavior. The option
applies to routed Studio maps, not the Hub's pinned Explore window.

Headless AHK fixtures cover the transition clock, reversal, continuity, guard
failure, disposal and exact host lifecycle using virtual presentation. The actual
Tk editor's validation, save/reopen, cancel and toggle behavior passed inside the
Linux guest. Native Windows visual/physical acceptance follows installation;
these checks do not measure compositor frame timing or physical input latency.

## Continuous layer presentation — 0.27.4 preview

The user reported seeing the desktop between maps while holding #19 and changing
layers. The active route destroyed the old picture before decoding and showing
its replacement. Routed alpha maps now prepare the replacement surface off-screen
and commit it to the same visible HWND with one `UpdateLayeredWindow` call. Valid
layer updates do not destroy, hide or re-show that window, nor alter its held
trigger, generation or release token. A legacy-to-alpha handoff shows the prepared
new frame before disposing the old legacy window.

A layer changing during snapshot validation gets a bounded fresh validation
retry. Inactive, stale, foreign, invalid-hash or continuously changing selections
still fail closed; this is not an indefinite stale-map fallback. Initial show,
release-to-hide, explicit Hide, pause and optional clear gaps keep their owners.
No device/game binding, registry geometry or source map is changed.

Headless virtual-window tests cover continuity through preparation/commit/disposal,
same-window layer swaps, legacy handoff, failure ownership and release state. A
fixture executes current host ShowLocal/HideCurrent code with virtual presentation;
native GDI+ pixel/resource and hold/route checks remain separate. These establish
the operation sequence, not measured compositor frames; physical flicker acceptance
follows installation and remains private with the exact runtime identity.

Destination follow-up, 2026-10-19: the user reported smooth changes with no
background flash while #19 stayed held through repeated #2 NUMBERS/BASIC and #1
MENUS/BASIC changes. This is user-reported physical acceptance for this variant;
all-game/all-layer coverage and measured compositor timing are not established.
This acceptance note postdates the immutable 0.27.4 source package. Exact runtime
identity and the direct reply remain in private receipts.

## Hold stability repair — 0.27.3 preview

The destination user reported occasional hiding before #19 was released. The
native Studio log confirmed HIDDEN before UP. The route previously treated a
whole-second expiry as authoritative, could mix values from successive INI reads,
and forgot its active slot after a transient rejection while the key stayed down.

The publisher now includes millisecond expiry, retaining legacy seconds for old
readers. Studio parses one bounded snapshot, accepts heartbeat-only replacement,
and continues checking foreground, image identity, activity and freshness. A real
rejection still hides the map. Fresh valid data can restore only the same captured
Hold press; release, explicit Hide, pause, another press or route Off prevents
restoration. Recovery updates the existing release token. Toggle/Timed retain
their previous semantics. Suspensions/resumptions are recorded in the existing
actions/errors log; no additional keyboard logging, input hook or remapping exists.

Headless checks reproduce the old second-boundary rejection, validate both relay
formats and rejection guards, and exercise held recovery/cancellation. A separate
headless fixture executes exact current host Down/Up/Show/Hide methods to verify
release after recovery. These are software checks; repeat physical acceptance
after installation and retain the user's earlier report as a failed old variant.

Destination follow-up, 2026-10-19: the user reported the repaired 15-second #19 hold
stayed visible through repeated #2 NUMBERS/BASIC changes and hid on release. This
is user-reported physical acceptance for the repaired variant, not an all-game,
all-layer or reboot-startup test. This acceptance note postdates the immutable
0.27.3 source package; exact runtime identity and scope remain in private receipts.

## Centered key/action maps and editable sources — 0.27.2 preview

[Editable game overlays](KEYMAP-DOCUMENTS.md) adds a display-only JSON map editor,
retained source history, explicit import/export and two background styles. The
destination-selected default is Combined, 35% width, centered and fully opaque.
Opaque buttons with clear gaps is optional through the existing Studio route.
Game/native bindings and #19 hold visibility retain their existing owners.

## 2026-10-19 — Layer-detection latency investigation

The user's selected visibility rule remains **#19 held to show, released to
hide**. A possible additional layer signal would identify the map only; it would
not make layer buttons display the overlay. The current five BASIC layer
controls use Single Press Layering, with no keyboard output and disabled Long
and Double actions. Their retained `featureDelay` field is not an active
long-press threshold for this configuration.

The inspected Azeron 2.0.2.442 renderer stores one action type per activation;
its macro step types are Button, Mouse, Delay, XInput, DInput and DPad. A supported
simultaneous native Layering-plus-Keyboard assignment was not identified. This
is an editor/schema finding, not a proof about every possible firmware/backend
capability; the compiled backend was not decompiled or modified. The
[official manual's layering and macro sections](https://site-835705.mozfiles.com/files/835705/Azeron_Cyborg_Manual_V6_5.pdf)
describe those as separate modes.

[reWASD Shift mode](https://www.help.rewasd.com/basic-functions/shift-mode.html)
explicitly documents executing a Jump-key mapping with Shift activation through
Postpone the mapping. It is an alternative remapping owner, not an extra checked
box on the existing native profile. Its
[Azeron support guidance](https://help.rewasd.com/how-to-remap/supported-devices.html)
describes Exclusive mode and ignoring the other native mappings. Device,
license, profile migration, layer-signal consumption and hardware latency would
need their own acceptance; no reWASD configuration was activated by this study.
A shared signal alone does not identify which layer changed: a direct adapter
needs distinct layer information, release/return handling and synchronization.

The installed software path has a 50ms follower wait, a 100ms Hub callback and a
200ms Studio refresh. These are approximate schedules, not measured physical
latencies or hard bounds. The [AutoHotkey timer documentation](https://raw.githubusercontent.com/AutoHotkey/AutoHotkeyDocs/v2/docs/lib/SetTimer.htm)
explains timer granularity and delayed callbacks. Initial #19 key-down reads the
prepared relay directly; it does not wait for the next 200ms refresh before
opening an already-selected map.

A Windows headless fixture used the installed follower, exact copied profiles,
the registered images, selection/relay functions and the Studio relay reader.
It supplied synthetic fresh native-format log events, represented the Hub's Tk
callback with a 100ms Python thread, and ran a separate 200ms AHK reader without
hotkeys or any GUI. QPC timestamps followed
[Microsoft's interval-measurement guidance](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps).
Six warm-ups and 48 measured trials completed without pipeline errors:

| Endpoint from beginning a synthetic event append | Median | 95th percentile |
|---|---:|---:|
| Validated follower state ready | 44.763 ms | 77.705 ms |
| Fresh relay published | 139.302 ms | 190.009 ms |
| Studio relay read and image identity validated | 207.577 ms | 350.105 ms |

The Studio read itself took a median 2.063ms. Separate 50-sample work checks
measured a median 12.380ms for native process-identity discovery and 0.851ms for
one profile read/hash/JSON parse. They are work costs, not game-input delays.
The private receipt retains raw trials, exact revisions, initial harness errors
and bounded child cleanup. Fourteen protected live profile/settings/store files
remained byte-identical.

These results exclude physical actuation/USB, native layer execution/native log
flush, actual Tk scheduling, image decode/window creation, compositor/display
presentation and gameplay input latency. No direct-key hardware A/B comparison
was performed. A potential next optimization is reducing polling/redundant reads
and publishing state changes promptly while retaining native identity/hash and
stale-state protections. It was not deployed by this research request.

## 2026-10-19 — Saved button-controlled visibility

Hub **0.27.1-preview.1**, Studio **2.2.0-unified.11** and the Studio groups
adapter **0.1.1** retain the existing picture slot as the visibility owner.
Choosing the Studio display target prevents automatic Hub rendering. Layer
events update the selected map; they do not open a picture. A Hold slot opens
from its own key-down and hides on key-up, including when the selected layer
changes while the picture is held.

The groups editor now saves an explicit opt-in in the private
`overlay-groups-route.ini` sidecar. Absent settings remain Off. A recognized
schema, enabled Local slot and absolute relay path are required before restoring
the route at launch. Invalid settings remain unarmed and are logged; unknown
schemas are preserved. Explicit Off persists, while normal shutdown stops the
timer without cancelling the saved choice. Fresh relay, image hash, foreground
identity and stale-state checks are unchanged. The sidecar neither changes a
native mapping nor creates a hotkey; that still belongs to the selected slot.

The user explicitly selected **hold to show / release to hide** and authorized
the previously unused physical button **#19** as the overlay control across the
six shared software layers. Its machine-local adaptation uses a dedicated
consumed picture trigger. Historical instructions keeping #19 unassigned remain
the old baseline; this request authorizes this scoped exception. Existing game
outputs, layer controls and original unrelated profiles remain preserved.

Eleven headless AHK checks cover default Off, saved restoration, shutdown,
explicit Off, unknown-field preservation, disabled/invalid slots, invalid paths
and unknown schemas. The 54 overlay, 11 picture-host and 33 unified-update
regression checks passed. This is separate from the user's physical button,
foreground/game and Windows sign-in acceptance; the private machine receipt
records those results and exact source/package hashes. This maintained entry
postdates the immutable source package.

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

## Selected layer buttons can show the map — 0.27.9 preview

Open **Show with layer buttons…** on the Overlay page. Check any of the verified
momentary selectors (#1 MENUS, #2 NUMBERS, #28 NAV, #30 SYMBOLS, #36 TOOLS on the
current shared setup), then Save. All choices start unchecked. Cancel never
saves; Select none plus Save returns to dedicated-button-only visibility.

The active checked layer and the existing Hold picture key are independent
visibility owners. Releasing one keeps the map visible while the other still
requires it. Selected-to-selected transitions reuse the current frame; adding
the dedicated hold to an already visible layer does not recreate it. A return
to BASIC hides only when the dedicated key is also released. Nested selectors
follow the native active layer, not an inferred inventory of physically held
buttons. Only the automatic route gains this choice; fixed picture guides and
Toggle/Timed slots retain their own rules. Explicit Hide or another picture
slot suppresses that native event until a new layer event.

The optional private `overlay-layer-show.json` stores exact native base/target
profile revisions and outputs, with atomic optimistic saves and prior-byte
recovery. Choices come from the registered BASIC profile's actual momentary
selectors. An Event-tracked native hold, current profile/output revisions,
foreground identity, relay expiry and image hash are still required. Manual
selection, regular profile switching, unknown/stale data and bad optional
settings cannot auto-open a map. The dedicated key remains independent.

No additional keyboard output, hook, native import or game binding is created.
The existing asynchronous event/selection/display timers are reused: this is
not a zero-delay or measured latency claim. Existing show/hide fades apply.
Older builds ignore the separate preference; clear the choices or use the
guarded previous build to roll back. Automated state/GUI checks and actual
physical-device acceptance remain separate.

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
### Relay file contention repair — 0.27.11 preview

An installed DOOM test reported intermittent appearance. The scoped Studio log
showed repeated inactive/stale suspension and Windows sharing error 32 during a
fade. A private concurrent-file fixture reproduced collisions between reading
the relay and replacing it atomically; this is not evidence of dropped Azeron
physical events or a DOOM rendering defect.

The Studio reader now uses an explicitly closed `FileOpen` snapshot with shared
read/write/delete access and up to 15ms of retries for Windows errors 5/32/33.
The Hub retains atomic replacement, with at most 50ms of retries for the same
contention errors. Original expiry, exact foreground, native revision, image
hash, hold ownership and release rules remain unchanged. Persistent contention
still fails closed; no cached stale map or longer lifetime is introduced.
OS errors now have a specific handoff status instead of the generic refusal.

A headless Windows test paced at the fade reader cadence passed 575 atomic
publications / 448 reads with zero I/O errors. An intentionally unpaced reader
stress test still exceeded the bounded publisher retry in 11 attempts; that
limit is retained rather than allowing stale display. Python publication/error
tests, real AHK shared-handle replacement, freshness/hold, selected-layer,
routing, transition and map-selection regressions passed. These checks do not
establish physical DOOM acceptance; the user must retry the physical hold.
No native profile, game binding, map label or visibility preference is changed.

Sharing semantics: [AutoHotkey FileOpen](https://github.com/AutoHotkey/AutoHotkeyDocs/blob/v2/docs/lib/FileOpen.htm)
and [Microsoft CreateFile sharing](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

## Overlay response time — 0.27.12 preview

The user confirmed reliable appearance after 0.27.11, but reported slow opening
and layer changes. The old path combined a 50ms native follower wait, a 100ms
Hub wait, a 200ms Studio timer and repeated registry parsing/image decoding.
The response update requests 20ms native/Hub intervals and a 15ms Studio timer.
These are scheduling requests, not guaranteed physical latency; Windows timer
granularity and application load still apply. No global timer resolution,
process priority, device polling rate or native profile is changed.

The Store compares freshly read registry bytes before reusing its validated
parse and returns independent copies to callers. Image metadata is bounded to
16 exact content hashes, with current file bytes hashed on every use. Studio
similarly reuses at most 16 small dimension records after current hash checks;
it does not cache an old permission to show or retain additional pixel surfaces.
The Hub publishes the relay before updating its inspector; unchanged text is
refreshed at most four times per second, with immediate state/layer updates.
Foreground, native identity/revision/freshness, asset integrity, TTL and release
ownership remain enforced. Same-path/size/mtime rewrites and independent drafts
are covered by headless regression tests. Frame continuity is retained.

A serial candidate/baseline/candidate private file fixture observed candidate
medians of about 122/134ms versus 368ms for the installed baseline. Earlier
runs varied with machine load. These endpoints are synthetic native-log arrival
to validated AHK relay read; they exclude physical device/mapper delay, real
foreground acquisition, GUI, raster presentation, fade and compositor. No game
launch or physical input was performed. They do not establish game-frame latency.
The user selected a 60ms show/hide fade instead of 120ms; the existing app control
continues to expose that preference. Physical acceptance follows installation.

Timer behavior: [AutoHotkey SetTimer](https://github.com/AutoHotkey/AutoHotkeyDocs/blob/v2/docs/lib/SetTimer.htm).
## Live response diagnosis — 0.27.13 preview

The user reports both opening and layer changes are still slow on 0.27.12.
Earlier headless timing improvements are therefore not physical acceptance.
The actual Studio log shows inactive/stale suspension and later recovery while
the dedicated hold remains active. A passive four-second relay observation
outside that hold saw a roughly 46ms heartbeat, so the requested 20ms schedule
does not establish a 20ms live publication interval.

0.27.13 distinguishes a publisher's inactive reason, expired heartbeat age,
invalid expiry and unsupported schema without relaxing their refusal. The
existing bounded actions log now has millisecond timestamps and overlay-only
handler, layout/preparation/presentation, configured fade and first-nonzero-draw
timings. These timestamps are software endpoints, not physical/display latency.
No new keyboard hook, full-key history, capture, input injection, persistent
trace file or external transmission is added.

Log entries remain immediate in memory, but their edit control is rebuilt by
the existing UI tick only when the Status tab is selected. A hotkey, fade step
or layer swap no longer synchronously redraws a hidden log control. Expiry-age
messages retain category deduplication so their changing numbers cannot flood
the 70-entry ring. Existing diagnostics copy includes the retained entries.

The 60ms fade, polling values, native profiles, game bindings, maps and visibility
choices are preserved. A short physical retest is required to distinguish the
actual inactive reason, native-to-handler delay and draw/fade delay. The delay
is unresolved until that evidence is reviewed; a diagnostic build is not a
claim that the latency is repaired.


### BASIC-only refusal after a native setting change — 2026-10-20

The installed 0.27.13 diagnostics identified an exact native revision refusal
when BASIC was selected. The user's next report narrowed the symptom: held
layers displayed their maps, while BASIC did not display through the dedicated
hold key. A comparison with the previous private native master found one
change: input #24 `analogSettings.upperLimit` changed from 512 to 251. All key
outputs, layer controls and the #19/F24 binding remained identical. This was a
full-file identity mismatch, not evidence that BASIC needs a held layer button.

A reviewed data-only reconciliation retained the current native bytes, updated
BASIC's exact file fingerprint, derived a new keymap revision using the existing
contract builder rule, and updated the five editable documents' revision
references together with the private native contract and runtime registry.
Actions, geometry, 180 images, visibility choices, native/game profiles, source
code and the 60ms fade were preserved. Previous documents and registry revisions
remain available for recovery. No integrity guard was weakened.

An isolated file fixture reproduced the exact old rejection and passed 44
game/layer routing checks after reconciliation, including returns to BASIC. A
further unreviewed native change was still refused. These checks are not
physical input or presentation acceptance. The follower requires a new live
layer event after a refusal; the pending physical check taps/releases #2, then
holds #19 alone and checks NUMBERS-to-BASIC while #19 remains held. The earlier
slow-response report remains unresolved until a physical retest. Machine-local
bindings index the exact snapshot, diff, checks and application receipt.


Physical follow-up, 2026-10-20: the user confirmed that both BASIC and NUMBERS
work correctly after reconciliation. The requested check used #19 alone in
BASIC, then held/released #2 while #19 remained held to return from NUMBERS to
BASIC. This is user-reported acceptance of that visibility/layer sequence; the
foreground application was not specified. The earlier speed complaint remains
unresolved. No further product, profile, image or setting change was made.


### Prepared layer frames and prompt fade entry — 0.27.14 preview

The user requested faster, possibly immediate layer changes and a shorter but
more perceptible show/hide transition. Actual 0.27.13 Studio diagnostics showed
56–174ms preparing/presenting maps and a further timer wait before the first
nonzero fade frame. These are observed software phases, not complete physical
input or display latency measurements.

The existing relay now supplies up to eight preparation hints for the selected
group's current context and view. They do not select or verify another native
layer. Studio prepares at most one image per 100ms idle slice, with no picture,
physical hold or fade active. It reuses scaled premultiplied pixels through an
eight-entry / 32MiB cache. Each use still checks current file bytes against its
exact SHA-256; fresh native identity, TTL, foreground and hold ownership remain
required. Leases keep a visible surface valid if its cache entry is evicted.
Source changes, geometry/context changes and cold misses are handled through
the existing validated rendering path. Shutdown releases the cache.

Layer swaps retain the same visible window and opacity, with no new layer
animation. Show starts synchronously at a faint 4% of the requested opacity,
then uses a linear entry ramp; hide keeps smooth endpoints. The animation uses
[QueryPerformanceCounter](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps)
for elapsed time. Existing scheduling intervals and integrity/lifetime rules
remain unchanged. Windows scheduling and native event delivery still limit
response; no zero physical latency or exact frame deadline is promised.

The destination's requested shorter setting is 48ms, previously 60ms. The
existing **Smooth show/hide** control and 20–400ms duration entry remain the
user's controls; turning it off gives immediate show/hide after validation.
No added settings page, native/game remapping, input hook or graphics change
is required. The BASIC revision reconciliation and existing visibility choices
remain in place.

Four preparation-hint tests and 12 real GDI/file plus idle-owner checks cover
filtering, bounds, unchanged selection, byte drift, shared leases, eviction and
no-show preparation. Existing hold, route, native, relay, frame and fade checks
pass. A private authored-map fixture measured roughly 21–24ms cold preparation
and 0.5–1.1ms verified cache acquisition; these are headless image costs, not
game-frame latency or GPU/CPU cost attribution. Local Windows GUI lab support
is not provisioned, so these file/controller checks create no GUI or input.
Installed warmup and a physical hold/layer retest remain separate acceptance
steps. Exact scoped source/update and preservation evidence stay private.


Physical response follow-up, 2026-10-20: the user reports that **opening and
layer changes are noticeably faster** after the requested DOOM/#19/#2/#1 retest
on 0.27.14. This supersedes the pending qualitative response check above. It
establishes user-reported improvement, not measured physical/compositor latency,
zero-delay behavior or broader game compatibility. The current 48ms preference
remains adjustable through the existing transition control. No additional
source, settings, native/game profiles or map assets were changed to record
this acceptance. Exact user-report evidence is indexed privately.

## Alternate overlay view — 0.27.20 preview

**Choose a keymap or overlay → Alternate view…** configures a second display
look. A normal #19 hold opens the saved normal view immediately. Tap/release it,
then press and hold again within the adjustable window to use the alternate
look. Release hides it, unless another configured show owner is still held.
The default window is 300 ms, adjustable from 150–600 ms; intervals below 60 ms
are ignored as bounce. No waiting period is inserted before the first display.
Key repeat is never a second press. A long first hold does not arm a delayed
double press. Optional view-toggle mode changes the selected look but does not
pin visibility. Focus/game identity changes reset the gesture state.

The alternate can use Key first (key + action), Action first, Action only or Key
only, or a snapshot of a saved global/game appearance preset. The default is Key
first, while each game's normal choice remains saved. Current game, native
layout, layer, context, comments and action/key data remain the same. Settings
can use global defaults or an explicit game override; no native/game remapping.

An optional 2–4-button keyboard/mouse combination shows the alternate while all
its buttons remain held. Lists include left/right/middle/back/forward mouse
buttons. Keyboard capture stays inside its explicit dialog; system/mouse keys
can be selected from the lists. Clear all four fields to disable the combination.
Wheel scrolling has no sustained release state and is not a Hold button. These
observed combination inputs pass through; existing picture triggers retain
their own suppression setting. The combination never steals another picture
slot. Releasing one visibility owner keeps another real held owner active.
Explicit Hide blocks a still-held combination until it is released and pressed
again. Fixed picture guides retain their existing route and controls.

Saved preset pixels are prepared in a worker before the optional settings file
is committed. Normal registry selection and images remain active. Source drift,
stale/concurrent settings or cancellation preserve the prior settings. Preset
snapshots remain independent of renaming/deleting the library preset. If a map
source changes, save alternate settings again to prepare its new preset images;
an unavailable/stale optional target falls back to normal display. Exact matching
views use the existing published pixels. Native revision, foreground, expiry
and displayed-image hash checks still apply to every actual show.

Normal and alternate layer images receive bounded idle preparation. The scaled
surface cache allows up to 16 entries within the unchanged 32 MiB limit. Display
replacement reuses the current window and retains existing fade/hold ownership;
no layer switch restarts the show/hide animation. These software checks do not
establish physical button latency or compatibility with every game/compositor.

The optional private `overlay-alternate.json` owns scoped gesture/look settings
and immutable derivative references. Source maps, appearance presets and native
profile files retain their existing owners. Save creates a preceding settings
copy; code rollback uses the prior immutable release and preserves later data.
The older release ignores this optional sidecar. Nothing is uploaded or synced.

## Retained image capacity — 0.27.21 preview 2

The registry permits up to 1,024 image records so retained map families and
four views of new maps can coexist. Other manifest collections remain capped
at 512; the 1 MiB JSON, depth, image, reference and hash checks remain intact.
Imports still validate the combined registry before writing assets or state.
Registries above 512 images require this reader. Before downgrading, restore
the paired preceding registry and map sources; preserve newer data separately.
