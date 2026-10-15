# Measurement-tool connections and user control


## 2026-10-15 — Read-only planning and UMM instance adopted source 0.27

The adopted `0.27.0-preview.1` source adds four modern multi-game read tools:
opaque instance listing, explicit instance inspection, goal-plan DAG compilation
and ownership/conflict graphs. Registration is deliberately absent from MCP and
requires the local `Game-Instances.py register --confirm` route. The accepted
adapter reads reviewed UMM markers, `Info.json` and declared assembly presence;
it does not load code, infer enabled state or write a game/manager profile.

Candidate R9 passed the separate [Windows, source-package and external stdio
gate](AI-PLANNING-READONLY-WINDOWS-ACCEPTANCE-2026-10-14.md): 388 focused tests,
394-file verified source export, zero-skip exported packaging, embedded path and
credential refusals without echo, and accurate filtered pagination over five
synthetic game fixtures. The same record preserves R8, R5, R4 and the bounded
R6/R7 attempts as historical evidence. The fixtures stayed byte-identical and no job,
proposal or execution was created. No specific ChatGPT/Codex product UI,
production installation, real manager profile, game runtime, gameplay or
physical-device acceptance is established. After independent review, PR #9 merged the tested product and later receipt commit into canonical `main` as `ef38d94be4fb4847cbbeda5f8fe41455b267aeaa`; that publication does not expand the acceptance boundary. See [the 0.27 slice contract](AI-PLANNING-READONLY-SLICE.md).

## 2026-10-14 — AI Efficiency Foundation 0.26 Windows and stdio acceptance

The reconciled `0.26.0-preview.1` source adds dual-era MCP, a shared result envelope, manifest-verified search/fetch and resources, resume/change cursors, blocker explanations, batch status, catalog/report reads and an in-memory handoff capsule. The exact Preview passed native Windows 11 ARM64 launcher/Tk acceptance in a separate current-user profile. An independent external stdio client exercised modern `2026-07-28` and legacy `2025-11-25`, including one synthetic proposal that was rejected locally; no operation was approved or executed. See the [sanitized acceptance report](AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.md) and [canonical reconciliation](AI-EFFICIENCY-FOUNDATION-RECONCILIATION-2026-10-14.md).

Specific ChatGPT/Codex product-UI connection, production installation, real game/manager/device state and remote plugin transport remain separate. The first client-harness parsing failure was reconciled before a new isolated run; it did not create a Mods execution directory or trigger an automatic retry.

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


## 2026-10-12 — Native Multi Image Canvas redesign installed

Installed **Hub 0.20.2 / Studio 2.2.0-unified.10** through the existing guarded
in-place updater. The final 148-file authored-source ZIP was entry/hash-verified,
SHA-256 `5ebce6ad4e0c76bebe9310b0cc2c05cdb5718ff8315e8af3e9727e58c6a0edc0`;
manifest SHA-256 `a201ef4441a7baaaa597c2731f6e5250e07bf0e542d15ba76334d6c08e61db73`.
Current pointer is `hub-0.20.2-5ebce6ad4e0c`; normal rollback remains the pre-task
`hub-0.19.2-ac6b4b44a122`. Intermediate 0.20.0/0.20.1 sources are retained
diagnostic checkpoints, not the recommended rollback. The unchanged stable
bootstrap and Downloads **Open Unified Game Tools.cmd** still open the current
release; no uninstall/reinstall is needed. Other component versions are retained.

The MIC tab remains a connection/setup editor for the **separate** Multi Image
Canvas application, not a new external canvas engine. Modern groups shortcut
matching and visibility/slot connection, keeps status and the synchronization
warning visible, and reveals the full original guide with Show/Hide. Its visible
Modern/Classic radio choices preserve the same draft controls. Four actions
reflow to two rows below 850 logical pixels; a 700-pixel readable minimum uses
the existing Hub scroll viewport below that size. Go to Picture buttons is
navigation only. Save, manual toggle, Mark hidden and website retain their
original callbacks; no external MIC action was invoked during this acceptance.
Layouts/disclosure are session-only, not settings/profile migrations. Picture
drafts, manual columns, advanced features, overlays and input owners are retained.

**Corrections and evidence:** native Hotkey letter text followed the active
keyboard locale, making a saved shortcut appear dirty and potentially invalid
on explicit Save. Reading the owned widget's letter VK and comparing modifier
order/case semantically fixes that without changing the keyboard layout or saved
binding. Native dropdown height includes its popup; the shared layout helper now
preserves that sizing, including Picture Buttons' existing selectors. Actual
dropped-control rectangle assertions cover this contract. A one-shot deferred
repaint handles native tab visibility settling, without a layout/timer loop.
The embedded desktop provider still did not reliably expose the chooser popup;
that is not proven to be a universal native-control failure. MIC uses two visible
radio choices instead, leaving the other existing dropdowns intact.

**Tests:** 707 focused checks comprise final MIC 219, Picture editor 62, Picture
model 73, native feedback 73, Picture host 11, viewport 4, updater 33, Appearance
46, Hub 22, Modern UI 22, saved-Modern startup 1, Workspace 40, Compact UI 40 and
source export 61. The original full sweep had MIC 218; the final MIC rerun adds
the Classic draft-status visibility assertion after that last presentation fix.
Native fixtures use authored temporary settings/images with input hooks, MIC
shortcuts and Game Input disabled. They cover four widths, guide state, drafts,
navigation, IDs/marker positions, widget sizing, locale handling and unchanged
fixture settings/runtime state. Windows isolatedLab is not provisioned; these
were inert host-native fixtures, not a claimed Windows guest pass.

**Installed desktop acceptance:** the unchanged launcher exposed the actual
titled 0.20.2 Hub and owned native editor. Screenshot/readback observed Modern,
Classic and Modern again, the unchanged Ctrl+Alt+H shortcut, zero input events,
Show/Hide guide behavior and navigation to the four existing saved Picture slots.
No Save, shortcut emission, preview, capture or Game Input start occurred. Fresh
observation/target activation was required when geometry was stale or another
window occluded the app; no provider safety guard was bypassed. A pre-existing
outer Hub heading still wraps unnecessarily and broader native popup/focus,
DPI/physical-device and external MIC Hold acceptance remain future boundaries.

**Preservation and recovery:** private scoped checkpoints copied/byte-verified
154 files including 33 native storage files. Only three owned AHK source files
changed. After normal startup/shutdown, **150 persistent protected files** remain
byte-identical, including the native storage, settings, profiles, assets and
saved appearance/view files. One ephemeral overlay-selection relay is separately
scoped; its existing lifecycle expiry refresh is not a profile/mapping change.
Installed source hashes and updater pointers were verified after closure. Private
copies are not restore-tested, whole-system/onboard recovery or cloud backups.
Rollback requires normal closure and fresh ownership/hash checks using the
existing guarded updater and retained pre-task source baseline; do not restore
the entire native profile collection or an expired relay to undo UI code.

The app is left closed. Games, benchmarks, recording, graphics changes and
MFG/FrameWarp remain stopped/deferred. The supplied RED4ext screenshot documents
a separate Cyberpunk log-rotation rename denied by permissions; it does not
identify which process or access rule caused the denial, and no game repair was
performed in this desktop-only task. No Drive/GitHub publication or sharing
change occurred. These final acceptance notes postdate the immutable source ZIP.

## 2026-10-12 — Native Picture Buttons redesign installed

Installed **Hub 0.19.2 / Studio 2.2.0-unified.7**, Unified Panel 0.4.0,
Appearance 0.5.1 and Modern UI 0.1.1. The final 147-file authored-source ZIP
was entry/hash-verified, SHA-256
`ac6b4b44a122b623b8075eeb4a4c21a52856bd9340b4c9f258b0c09543a1414d`.
Current pointer: `hub-0.19.2-ac6b4b44a122`. The normal rollback target was
conditionally read-back to the pre-task baseline `hub-0.18.0-7a4a62aa8ef5`;
intermediate 0.19.0/0.19.1 versions remain immutable diagnostic evidence, not
recommended rollback targets. The stable bootstrap and convenient Downloads
**Open Unified Game Tools.cmd** remain unchanged. No reinstall is needed.

The first native editor now has Modern/Classic presentation, readable narrow
reflow, Show/Hide display settings, contextual Local/MIC fields and Timed
duration, explicit Fit columns, saved/unsaved state and cancellation-safe row
selection. Existing operational controls and callbacks are reused. Resizing
retains manually adjusted table columns; layout/disclosure are session-only.
The Hub resizes its exact owned native child using bounded display minima and
scrolls below those minima. Feedback markers track positions/visibility.
Advanced library/variants/context and the MIC/HUD/status/Game Input editors
retain their existing internals; this is not their completed redesign.

**Preservation:** after normal user-confirmed closure, a private checkpoint
copied and byte-verified 151 scoped files, including 33 native storage files.
Concurrent changes to two native profiles during preparation caused the first
installation attempt to refuse before mutation. A fresh checkpoint preserved
the newer revisions, and both earlier/current copies were retained. The
guarded updater changed only three of the six installed AHK code files.
Immediately after each final update, 148 protected files were unchanged.
After startup/shutdown, all **147 persistent protected files** remain
byte-identical, including settings, native storage, assets and saved Modern
appearance/views. The separate ephemeral overlay relay refreshed its expiry
timestamp through the existing lifecycle and ended at `Active = 0`; it is not
a changed mapping/profile or a persistent setting. Private checkpoints are
byte-verified copies, not whole-system/onboard/cloud recovery or restore-tested.

**Tests:** 480 focused fixture checks passed in the final regression: native
Picture editor 54, Picture model 73, native feedback 73, Picture host 11,
viewport sizing 4, Unified updater 33, Appearance 46, Hub 22, Modern UI 22,
saved-Modern startup 1, Workspace 40, Compact UI 40 and source export 61.
Native fixture checks exercise actual authored GUI controls at four widths,
draft/disclosure/source/Timed behavior, column preservation, selection
cancellation, preview creation/cleanup, feedback positioning and unchanged
fixture settings. A separate bounded Windows fixture visual pass observed
disclosure and caught/fixed bottom-action clipping. A malformed test BMP caused
an earlier decode modal; correcting the authored fixture resolved it.

**Startup diagnosis:** the first installed Hub stalled before exposing its
window. An explicit `deiconify()` alone did not solve it. Scoped callback
tracing showed continuous layout callbacks inside native startup's idle flush.
Generic Appearance wrapping and the Modern page's own wrapping were competing.
One wrapping owner per managed label, idempotent wrap changes and a retained
font removed this loop. The saved-Modern startup regression verifies a visible
window and advancing timer under a subprocess deadline. Exited, task-owned
diagnostic markers were privately copied and byte/owner-checked before release;
no foreign ownership marker or running edited window was force-closed.

**Installed acceptance boundary:** the unchanged stable bootstrap then exposed
the actual titled 0.19.2 Hub window and its owned AHK child. Accessibility
readback showed all four existing saved slots, Modern layout, original actions
and zero input events. The final live screenshot failed with monitor-capture
`0x80070057`; a disclosure click failed with unavailable coordinate geometry.
Fresh readback showed no disclosure change. These are incomplete live visual/
click checks, not a claimed pass or grounds for bypassing the control provider.
Supported Alt+F4 closed only the tested app normally; subsequent process and
lease checks verified cleanup. Game Input was not started. Games, benchmarks,
recording, graphics settings and MFG/FrameWarp checks remain stopped/deferred.
No Drive/GitHub publication or sharing change occurred.

Rollback only after normal closure and fresh ownership/hash verification uses
the existing guarded updater and retained pre-task source baseline. Do not
restore the whole native profile collection to undo presentation code, or
restore an expired relay heartbeat. The final acceptance notes postdate the
immutable source ZIP; they are a later local documentation revision.

## 2026-10-12 — Modern task workspace installed

Installed **Hub 0.18.0**, Workspace 0.4.0, Appearance 0.5.0, Compact UI 0.4.0
and Modern UI 0.1.0. Studio remains **2.2.0-unified.6**, with all six installed
AHK sources byte-identical. The user requested a fresh modern interface and
confirmed normal app closure; process checks verified closure before mutation.
The existing guarded updater applied the curated 143-file authored-source ZIP,
SHA-256 `7a4a62aa8ef5ddd917531643a700a2a05cdc5185c92d46e8f37496c623722caa`.
Current version pointer is `hub-0.18.0-7a4a62aa8ef5`; previous is
`hub-0.17.0-2113b77ff73f`. Immutable source inventory and pointer were read back.
This is an in-place update, not an uninstall/reinstall or data migration.

The new Modern surface provides four task groups/eight goal links, four short
categories, access to twelve feature workspaces, editable search, contextual
page detail disclosure, responsive cards, stable on-component UI-007 feedback
and shared secondary-action menus. Existing page instances, unsaved entries,
original commands, disabled states and original layouts are retained.
Home cannot forward hidden Tools action shortcuts. Navigation is not execution
authority. See [design contract](UNIFIED-UI-DESIGN.md#modern-task-workspace--2026-10-12-hub-0180).

**Preservation:** a just-in-time private checkpoint copied and byte-verified 149
scoped files across installed Studio/code/assets/settings, Hub data and native
device storage (including 31 native profile files). Before and after the update,
all 149 match the checkpoint hashes. The user's saved Compact view JSON is
unchanged. Earlier layout views/unknown fields remain supported. This is not
whole-system/onboard/cloud recovery; restore-testing was not performed. The
stable Desktop/Documents launchers remain in place and follow the new pointer.
Open normally and select **Interface → Modern** to retain the new presentation;
session-only preview does not overwrite the saved mode.

**Tests:** 285 selected Python fixture contracts passed: Hub 22, Hub/catalog 45,
Workspace 40, Appearance 46, Modern 20, Compact UI 40, Comparison panel 39 and
Unified updater 33. PowerShell 7 passed 61 source-export contracts. Following
the final geometry correction, Modern 20 and Appearance 46 were rerun on
Windows test-owned withdrawn roots. The isolated Linux guest passed 185 tests
across the five portable UI suites; a final focused pass reran Modern's 20
contracts and rendered seven visible snapshots, including 1360×880, 620×600,
620×430, a font-scaling sample, categories, search and an actual Comparison
panel with explicitly synthetic data. The screenshots are not performance
results. Scoped geometry guards assert one-column cards fill available width.

The visual pass found a genuine narrow-card regression: retaining the inactive
column's Tk `uniform` group prevented the active column from filling the window.
Removing that inactive group fixed the rendered narrow layouts. A missing guest
Pillow dependency initially prevented screenshots after the tests passed; the
renderer now uses the guest's existing ImageMagick against only its test-owned
X window, without installing another dependency or capturing the host desktop.
Retired search-card markers are pruned, and repeated layout/search switches
retain commands and do not leak markers. These are reusable UI lessons, not
game-input or GPU evidence.

**Remaining:** the native AHK editor internals are preserved, not a complete
responsive/modern rewrite. Individual feature forms and Comparison split-pane
ergonomics still need deeper design passes. Portable/withdrawn tests do not
establish a restarted production Windows/native AHK visual pass, physical
input, every DPI/monitor or game acceptance. The installed app remains closed;
the task-owned Linux guest was stopped normally, without force. Point-in-time
process checks found no Skyrim, Cyberpunk, OBS, PresentMon or installed AHK/Hub
session. Games, benchmarks, recording, graphics changes and MFG/FrameWarp tests
remain deferred. No Drive/GitHub publication or sharing change occurred.

Rollback through the existing Updates page uses the retained 0.17.0 immutable
source version after normal closure; it does not restore/reset private profiles
or overwrite newer user data. Keep the local private checkpoint and updater
transaction recovery. The source package captures the pre-install documents;
this post-install acceptance record is a later workspace revision. Do not claim
its bytes are already present in that earlier installed source archive.

## 2026-10-12 — Azeron layer event following

Installed **Hub 0.17.0** / retained **Studio 2.2.0-unified.6**, Overlay/Panel
0.2.0 and Azeron Layer 0.1.0. The immutable pointer is
`hub-0.17.0-2113b77ff73f`; preceding `hub-0.16.0-642061dfaee3` remains intact.
Curated source ZIP SHA-256:
`2113b77ff73fd46fa9c319d9a4c099defede0509aab6d8e4b40337c54eb81915`.
All **140** packaged source entries were size/hash-verified and the guarded
updater's current-source verification passed. Existing Desktop/Documents
launchers still use the stable entry point. No uninstall, app launch or startup
registration was needed. This receipt postdates packaging; it is not claimed
to be in that immutable ZIP or published GitHub/Drive state.

The [experimental follower contract](OVERLAY-GROUPS.md#2026-10-12--experimental-automatic-azeron-layer-following)
uses new timely native log events, not keyboard output, historical saved state
or process presence alone. Hold/release assets use the existing exact-reference
selection/relay, without writing native mappings. Manual mode is a session
toggle and saved manual layer selections remain intact. Additive UI follows the
compact-design foundation: one in-context control and visible source/state,
not another mapping/profile editor. Event-tracked is not a fresh native snapshot.

**22** new synthetic transition/UI-wiring tests, **53** existing overlay
selection/withdrawn-UI tests, **33** guarded unified-update tests, **61** source
export contracts and **4** inert AHK route contracts passed. Five banks,
sustained holds and release-to-BASIC, loss/staleness/restart, malformed/partial/
truncated/replaced logs, unknown/ambiguous profiles, drift, manual mode and Stop
are automated fixtures. No manual test or actual physical press was requested.

A separate read-only probe imported the actual installed module. Five reads
matched Azeron **2.0.2.442** and its running process, but saw **no fresh native
transition**, correctly staying Unknown/waiting instead of assuming BASIC.
The present PnP interfaces matched the native storage's Azeron VID/PID family;
interface count is not physical-device or active-layer proof. Existing port
metadata led to a refused endpoint and was not enabled/restarted. Native 2.0.2
message strings/historical logs support parser preparation, not current complete
event coverage. A separate supported window observation lacked useful accessible
active-layer text and its screenshot was not reliable target evidence; no UI
action or settings change followed. Unlogged transitions and physical timing
remain unverified. No universal telemetry/game acceptance is claimed.

Just-in-time private checkpoint alias **AzeronLayerFollow-20261012-r1** contains
**144** copied/hash-verified files: 11 Studio files, one Studio settings file,
99 Hub data/assets/relay files and 33 native storage files (**31 profiles plus
two global settings files**). Final before/after check confirms **143 unchanged**;
the only changed existing file is `StudioOverlayGroups.ahk`, with two explanatory
strings updated. The other five installed AHK source modules remain byte-identical.
All native profiles/settings, Studio INI and Hub records/assets/selections are
unchanged. BEFORE/INSTALL/AFTER receipts and the updater's separate immediate
source recovery are private. Copies are byte-verified, **not restore-tested**;
onboard firmware, whole-system recovery, games/saves and unrelated owners are
outside this checkpoint. No cloud publication/sharing change occurred.

The probe was stopped and no AHK/pythonw/game/benchmark/recording process was
present in the final scoped process read. This is point-in-time, not background
monitoring. The application remains closed. Next boundary is current live event
coverage when separately authorized; no manual/game/input test resumes here.
Rollback: disable Follow Azeron layer for that session, or use the existing
guarded previous-version updater while the app is normally closed. Preserve
later user changes; never restore all native profiles to undo this display feature.

## 2026-10-12 — self-service double-click launchers

The user's Desktop had no Unified Game Tools shortcut despite the earlier
reference to an existing shortcut. A real `GetFinalPathNameByHandleW` observation
also established that the nominal Local AppData installation and Hub registry
resolved into Codex's package LocalCache, while Studio settings remained at their
ordinary Roaming location. Explorer's external launch could not safely be assumed
to inherit that packaged-app path view. This is file-identity evidence, not a
reproduced external GUI failure.

Added `Create-UnifiedToolsLaunchers.py` and `Create-UnifiedToolsShortcut.ps1`:
inspect the exact installed manifest/bootstrap, resolve opened physical paths,
check inactive owners and cooperative source lease, checkpoint metadata,
recheck drift, repair only the proven same-data `data_dir` reference, then create
new access files without overwriting existing unrelated files. Data/source/profile
migration and app/input launch are absent. The command file quotes fixed runtime
and launcher paths, uses UTF-8, disables delayed expansion and refuses variable,
quote and newline injection; it requires no `.pyw` file association or PowerShell
policy change. Future curated exports include these authored preparation helpers.

Created/read back **Unified Game Tools.lnk** on the user's actual Desktop, plus
**Open Unified Game Tools.cmd** and **START HERE.txt** in a new Documents access
folder. Both target the same physical stable bootstrap and existing runtime;
updates keep the same front door. The previous installation metadata was copied
before its one-field path repair, with before/after hashes and readback. Current
Hub 0.16.0/Studio sources and immutable 135-file package remain unchanged.
All **12 access preparation tests** and **61 synthetic source-export contracts**
passed. Exact installed bootstrap dispatch was checked with spawning and Tk
windows mocked; current inventory verified. No actual app/game/input/capture
was started. The Desktop shortcut target, arguments and working directory were
verified through the Windows Shell COM readback. These files are for this
configured computer, not a standalone redistributable interpreter/installer.

Fresh historical readback found **132 of 134 protected files** still identical.
The two native GlobalStore/backup files had changed at 23:22:53 UTC, before the
launcher metadata checkpoint at 23:27:01 UTC; native Azeron was running. The
writer/cause was not proven. Do not attribute those changes to the launcher or
restore old values: this preparation does not write native storage. All 29
native profiles, Studio settings/pictures, Hub durable files and MIC data remained
identical to the previous protected checkpoint. Both newer native stores were
copied/hash-verified separately while leaving their originals untouched; those
copies are not restore-tested. The earlier all-134 result below is historical,
not a claim that the user's software never updates its own data.

Private access/shortcut/dispatch/audit receipts and scoped metadata/current-store
recovery are retained. Rollback is to remove only these newly created access
files; if reversing the metadata repair, inspect its exact after hash first and
restore only `data_dir`, not a stale whole pointer over later updates. No remote
publication, extra startup task, service or association registration was made.
The design foundation influenced the single clearly labeled Open action and
separation of opening from install/update and operational Game Input.

## 2026-10-12 — responsive update installed after normal shutdown

The user reported closing Unified Game Tools. A point-in-time CIM check found
no Hub Python/AHK owner, Skyrim, Cyberpunk, OBS, PresentMon or CapFrameX process;
the app was not force-closed. A fresh checkpoint copied/hash-verified all **134
protected user files**, installation state and saved view preferences before the
existing drift-guarded updater applied **Hub 0.16.0 / Studio
2.2.0-unified.6**. The existing launcher/data paths remain in use; no uninstall,
profile activation or operational migration was required.

Current immutable pointer: `hub-0.16.0-642061dfaee3`; retained previous pointer:
`hub-0.14.3-62e4142a7a4f`. The curated package has **135 files** (678,466 archive
bytes), SHA-256
`642061dfaee34e09de4e88ef50e35387c176bd74ccfb794e7c8a98772ce930ec`;
manifest SHA-256
`959f0bc2ed2436978745d3f9b39a10b055d1428022faef28e298aa76529a4d8d`.
Installed inventory and six owned deployed Studio sources passed readback.
All 134 protected originals and saved view preferences remain byte-identical;
timestamp preservation, device/onboard restore and whole-system recovery are
not claimed. The updater retains its own scoped recovery and previous release.
Use its normal guarded rollback, preserving newer private data/view choices.

Exact installed AHK sources passed **36 Game Input policy/configuration and
eight Studio integration self-tests**, exit 0 with empty warning/error output;
these start no GUI, hooks, input or timers. The earlier 1,181 Python passes,
three platform skips, 73 identification/73 Picture/four display-route fixtures
and 61 source-export checks remain the source regression boundary below.

After the other lab workflow finished, its accepted Linux guest was started
headlessly for a task-owned fixture. Only ten selected public installed-source
and fixture files were transferred, with exact byte/hash readback; no private
profiles/settings or host clipboard/input/display were shared. Guest-only Tk
dependencies were installed without altering the Windows runtime. **19 visible
Tk fixture checks passed**: real class-bound sidebar drag and Show/Hide mouse
events, preferred-width retention, small-width automatic collapse/explicit
Show, searchable layout, proportional table fit, hover text/state, Catalog
viewport reachability and unchanged page objects/unsaved fields across all
three interface modes. Seven actual guest images were fetched and inspected;
the fixture produced no Tk callback errors or diagnostic output.

This is **partial portable UI acceptance**, not the complete installed Windows
app or native AHK viewport. Tk exposed no AT-SPI tree on the private bus; the
test used its task-owned widget/event adapter and screenshots, not invented
semantic controls. Narrow labels/table headings still clip in some views, and
the hover image does not establish readable popup pixels despite the widget
text/state assertions. Those visual refinements, full heading-menu/divider
interaction, marker copy/filtering, native viewport, DPI/monitor and physical
keyboard acceptance remain separate. The app remains closed after installation.
Games, benchmarks, recording and operational Game Input stayed stopped.

Private receipts retain the fresh checkpoint, inspected archive/update,
installed preservation readback, AHK output and guest requests/images. This
acceptance entry postdates the immutable package; it is not automatically in
that archive or earlier GitHub/Drive copies. No remote publication occurred.

## 2026-10-12 — responsive workspace source update

Prepared **Hub 0.16.0 / Workspace 0.3.0 / Compact UI 0.3.0 / Appearance 0.4.0**.
The draggable sidebar, explicit Show/Hide, full-name hover hint, responsive
search/field/action layout, lower bounded minimum/resize grip and shared table
width controls are presentation-only extensions to existing panel instances.
View schema 1 gains only an optional bounded sidebar width; legacy files remain
accepted and unknown extension fields retain their existing preservation path.
The source includes pending **Studio 2.2.0-unified.6 / bridge 0.3.2** marker-type
filters and selectable ID confirmations, not a new native input transport.

Just-in-time recovery: 135 curated source files and 134 protected user files
were copied with hash readback, plus the current installation pointer, saved
view JSON and six installed owned Studio sources. Existing older recovery and
immutable releases remain separate. All 134 protected originals, saved view
JSON and installed pointer remained byte-identical at readback. This is a
scoped copy/hash audit, not a whole-system recovery or new activation test.

Final regression: **1,181 Python cases passed, three platform skips** across
34 suites; exact results are recorded privately per suite. New contracts check
explicit Show after automatic collapse, pane width roundtrip/legacy default,
atomic invalid-width refusal, toolbar/field reflow, public/stale hover hints,
retained edits/pages/callbacks and manual column ownership. Hidden owned AHK
fixtures passed 73 identification contracts, 73 Picture model checks and four
display-route checks with exit 0 and empty warning/error output. PowerShell 7
passed 61 source-export contracts. No clipboard/input/profile action was taken
against the production app. A table reset initially attempted to write Tk's
read-only column ID; it now restores writable geometry options only. The former
fixed two-row toolbar test was changed to verify actual narrow/wide wrapping
and unchanged callbacks; fixture cleanup drains pending theme work.

**Historical preparation boundary; deployment is now resolved by the entry
above.** At preparation, installed pointer still referenced
Hub 0.14.3 / Studio 2.2.0-unified.5. Its open AHK owner prevented a safe source
switch. The lab's Linux operation lock belonged to a live, separately owned
long-running acceptance job; it was not interrupted or cleared. Windows guest
is unprovisioned. No host keyboard/mouse takeover was substituted. Withdrawn
Tk/hidden AHK fixtures are not live resized-window/native desktop acceptance.
Next: normal app shutdown, inspect/apply the curated source package with drift
checks, restart, then separately verify narrow/wide render, actual divider drag,
hover, heading menu, marker filtering/copy and native viewport ownership through
a ready authorized GUI route. Do not launch games, benchmarks or recording.

Rollback after a later deployment uses the normal guarded source updater and
the retained previous immutable release; preserve current private data and
newer view choices first. No operational profile import or reset is required.

## 2026-10-12 — on-component identification and copy

Installed **Hub 0.14.3 / Studio 2.2.0-unified.5** through the guarded in-place
updater, retaining the existing front door, engines, data paths, settings,
profiles and overlays. The top **? Identify UI** toggles floating markers on
actual registered Hub/native Studio components. A marker copies only its stable
component ID and displays its name/confirmation; it does not invoke the original
button, edit the field or read its contents. Regular controls retain their
normal behavior. Identification is session-only and Off at startup. The older
searchable ID dialog remains source-compatible but is no longer the top-button
workflow. See [design contract](UNIFIED-UI-DESIGN.md).

The installed immutable pointer is `hub-0.14.3-62e4142a7a4f`. Its authored source
package contains 135 curated files, SHA-256
`62e4142a7a4f0a073b42827f33d373212a456c73bbd7bb4aa9e72ea1a85383cc`;
manifest SHA-256
`a82c037cb6e2d5431839c7173709b3543cd02574538f368edec58ac40965e966`.
Archive membership/hashes, installed inventory and all six deployed Studio
sources were read back and verified. This final acceptance documentation
postdates that immutable package; it is not automatically inside the package
or earlier Drive/GitHub copies. No publication, upload or sharing change was
performed.

Fresh private snapshots preserved **134 source files** before mutation and
**134 protected user files**, with original-byte/hash verification. The separate
historical 134-file recovery export and its new-copy restore/hash audit remain
available. Final readback confirms all 134 protected original files still
byte-identical, including 29 native Azeron profiles, the two native stores,
68 Studio settings fields, four picture slots, historical F7 picture, 97 durable
Hub files and independently owned MIC data. These are overlapping inventories,
not quantities to add together. Saved Professional/Compact/Classic view JSON
also remains byte-identical to this turn's baseline. Native-store timestamps
changed while bytes did not; timestamp preservation is not claimed. No active
profile migration, device/onboard restore or whole-system recovery test occurred.

Final regression: **1,149 Python cases passed, three explicit platform skips**
across 34 suites; **12 native identification contracts**, **73 Picture model
fixtures**, **four display-route contracts** and **61 PowerShell 7 source-export
contracts** passed. Windows PowerShell 5.1 execution was policy-blocked; its
policy was not changed or bypassed. Automated UI tests use test-owned roots,
fixtures and mocked clipboard/providers, not game acceptance.

Observed desktop checks cover installed top-row toggle, Hub ID copy/confirmation,
native marker visibility during viewport scrolling and a Picture name marker
showing `UI-101.fname` without editing the original field. Isolated native
Preview identification also showed its ID without opening the preview. Initial
native Tab3 placement and sibling hit-testing/repaint failures were repaired by
registration in the correct tab, explicit own-marker z-order and
`WS_CLIPSIBLINGS`; they were retested before deployment. The Boolean identification
bridge is limited to the validated owned native viewport, not arbitrary window
input. A still-running inert AHK test first caused a guarded update refusal;
waiting for test completion and normally closing the owned Hub allowed the
update. Only an exact-path-verified, unresponsive isolated UI fixture was
terminated, not the production Hub, native software or other user's processes.

Limits: not every advanced control, future dialog, layout/DPI/keyboard combination
or external application received live acceptance. Unregistered controls are not
assigned guessed IDs. The inherited native form is not a completed responsive
redesign. No games/saves, graphics settings, operational Game Input, benchmarks
or recording were started. Point-in-time process readback found no Skyrim,
Cyberpunk, OBS or PresentMon process; this is not background monitoring.

Rollback: preserve current private data, normally close only the owned Hub/Studio
being replaced and use the guarded previous-version rollback with retained
`hub-0.14.2-47408be43888` inventory; the earlier accepted
`hub-0.14.1-daa130e71c8a` and this turn's just-in-time source/user snapshots remain
available. Verify exact source ownership/hashes and protected data before and
after rollback. Do not uninstall, reset unrelated dirty files, overwrite private
profiles, switch loaded sources or force-terminate production applications.

## 2026-10-12 — selectable UI candidates and feature feedback

Installed **Hub 0.14.1 / Studio 2.2.0-unified.3** through the existing guarded
in-place updater. The stable front door and original app-data paths remain in
use; no uninstall or profile activation occurred. The final authored package
contains 134 curated files, SHA-256
`daa130e71c8a80518a1674d611fa48fbe817fd5d4b0a14c70954338dc189f0a0`.
Its installed pointer is `hub-0.14.1-daa130e71c8a`; the immutable source inventory
and six deployed Studio sources were read back and verified. This receipt
postdates the installed source bundle's documentation; no GitHub/Drive upload
was performed in this UI continuation.

The [design guide](UNIFIED-UI-DESIGN.md) records recovered MATAM preferences,
research links, distinct Professional/Compact/Classic presentations, permanent
feedback IDs and future native-form work. Compact patterns are optional design
candidates, not a mandatory global layout. The top-row **? Feedback IDs** supports
search, multi-selection, **Copy IDs** and **Copy feedback + layout**, without
capturing screenshots or sending anything. For example, `UI-103` targets the
Studio image/preview area and `UI-202` the saved-report import adapters.

Evidence:

- 34 Python regression suites: 1,139 cases, 1,136 passed and three explicit
  platform-dependent skips. Twenty-three new appearance contracts cover stable
  IDs/copy text, distinct modes, retained widgets/unsaved values/search, per-mode
  choices, future-schema/drift protection and theme-local hidden-tab behavior.
- Existing AHK inert checks: 36 input policy + 8 host integration, 73 Picture
  Module and 4 overlay contracts. A separate exact-copy installed profile-loader
  check passed with F7 enabled and F15–F17 disabled, without settings writes.
- Both Windows PowerShell 5.1 and PowerShell 7 passed 61 source-export contracts.
  The final ZIP's source/manifest entries were all size/hash verified.
- Actual desktop observations: all three presentation modes rendered; Studio
  retained its four saved slots. Owned native-form vertical and horizontal wheel
  scrolling visibly worked in the first 0.14.0 candidate; that wheel/bridge code
  is unchanged in 0.14.1. Feedback selection and Copy IDs produced its visible
  copied confirmation. Final 0.14.1's modern tab bar was correctly hidden and
  its non-modal feedback window appeared centered. No final desktop stderr was
  produced during these observations.
- Desktop testing caught a theme-local style loss not exposed by the first
  fixtures: switching ttk themes restored the old tab bar. The fix reapplies
  the hidden-tab style in the selected theme; a new round-trip test covers it.
  Another regression preserved original-page fallback when optional presentation
  modules are missing. No failing candidate was represented as accepted.

Preservation: the prior private 134-file manifest still matched **every original
byte**, including all 29 native profiles/two stores, 68 Studio fields, 97 durable
Hub files, F7 image, MIC settings/session/canvases and image dependencies. Native
GlobalStore files had changed modification times since the older recovery audit,
but identical bytes; this is not a claim that every timestamp remained unchanged.
Five additional unowned legacy Studio files also matched the just-in-time copy.
The only new user-data file is separate presentation preferences. Private current
checkpoints contain 141 files before the first update and 142 before the final
update; prior known-good recovery exports remain intact.

Limits: narrow/wide layout and reflow/scroll ownership have component tests;
the full controlled visible resize/keyboard matrix was not completed after user
input changed the layout/opened feedback. The user's final Classic choice was
left intact instead of overridden. Native AHK forms still use their familiar
fixed geometry with accessible scrolling, not a complete modern form rewrite.
No new game-input, gameplay, mod, benchmark or recording acceptance is claimed.
Games/capture were absent at final process inspection; only the unified Hub and
its owned Studio were running, with Game Input not auto-armed.

Rollback: Updates can explicitly restore its immediate previous source version,
0.14.0, without replacing data. For the pre-UI 0.13.2 baseline, use the retained
trusted dated 0.13.2 source package through the same guarded updater after owners
stop; do not restore a whole native profile/store to undo this presentation
change. Private source/data checkpoints retain both boundaries. Cloud recovery,
active profile import and unrelated experiments remain deferred.

## 2026-10-12 — installed profile and file preservation audit

**No active restoration was needed.** Hub 0.13.2 / Studio
2.2.0-unified.2 still use the original app-data and Studio locations. The
immutable release inventory, stable launcher and six deployed Studio source
hashes verify against the current installation receipt. The running owned
Studio was not replaced or restarted.

All four inspected pre-install/update checkpoints retain their verified copies:
138 + 138 + 141 + 141 files. Differences in the active locations are limited to
intended authored-source updates and the inactive overlay relay's expiry
timestamp. No saved layout, binding, preference or protected file is missing.
All 29 native Azeron profiles and two store files remain byte-identical, preserving
every field rather than reconstructing only key assignments. Native software
remains their owner; the Hub does not activate/import device profiles.

Studio's INI retains all 68 recognized fields: General, HUD and four picture
slots. The F7 Local/Hold picture is enabled; F15–F17 remain disabled. An isolated
exact six-file diagnostic copy executed the actual loader's 13 saved-profile
assertions and exited before any GUI, tray, hook or timer construction. It
returned exit 0 with no warnings; the live Studio process and settings bytes
were unchanged. This is loader/configuration acceptance, not game or full
runtime feature acceptance. Never run that diagnostic through a live installed
`#SingleInstance Force` host path.

All 97 durable Hub data files remain exact, including 90 images checked against
their registered hashes. The retained registry includes four games, one keymap,
five groups, three associations and three tool records. The F7 external image,
Studio INI and tool registry also match the earlier ten-file private recovery
checkpoint; all ten historical copies still verify. No saved Picture extension
sidecar/library or Studio3 settings was found at the inspected current or prior
locations. Absence is not evidence of successful Studio3 schema migration.

The new **private, local-only recovery export** contains 134 selected files:
129 durable Hub/Studio/native files, the F7 picture, three independently owned
MIC settings/session files and their one distinct external image. MIC's two
canvases, identities, shortcuts, placements, crops and other session fields are
preserved as original bytes. MIC coverage is newly included; historical MIC
byte-equivalence is not established. The archive is 7,727,523 bytes, SHA-256
`19101AF6DE1378FE43D2A82DACA60ACC5BD568ED3E4500BCEC72034D83FDB0E0`.
The shared User Data exporter/inspector restored all 134 entries into a **new
evidence directory**, and independent readback verified every restored/original
hash. No active destination was overwritten and no profile was activated.

Inspection also found an unused legacy-import logging defect: `ImportLegacy`
references `file` after renaming the local to `legacyIniFile`. It can throw
after replacing/saving slots; it is not a transaction or a full data migration.
Do not invoke it for this intact installation. An explicit future import needs
a separate snapshot, that fix and isolated acceptance first. Existing INI Save
rebuilds recognized fields; foreign/unknown INI keys and custom nondefault data
paths need separate compatibility work. Neither limitation affects the current
68-field/default-path configuration.

Coverage does not establish onboard-device recovery, remote-only exports,
whole-system restoration or restored native application behavior. Private
receipts/source locators and recovery files remain outside Git. Three existing
documentation files were copied/hash-verified before adding this receipt;
earlier immutable source/Drive checkpoints remain unchanged. Rollback is not
needed: active user data were never mutated. If later recovery is required,
preserve newer originals, inspect the private ZIP in **User data**, restore into
a new directory, and reconcile through each native owner before activation.

Point-in-time start/end checks found no Skyrim, Cyberpunk, OBS, PresentMon or
CapFrameX process. No games, saves, graphics changes, benchmarks, recording,
game input, MIC activation, native profile import, cloud transfer or remote
publication occurred. Remaining normal-restart UI and game acceptance from
earlier stages stays separate/deferred.

## 2026-10-11 — 0.10.0 offline provider health and scenario contracts

Requested scope: provider-health checks and editable scenario contracts using offline mocks, preserving AHK/features/settings/profiles and keeping games/benchmarks/recording stopped. [Hub 0.10.0](../examples/game-tool-hub/README.md#offline-provider-health-and-editable-scenarios--0100) retains eight tabs/Ctrl+1–8 and all earlier catalog/FG/report/comparison/import/journal/evidence/workflow features. Optional Sessions → Provider / scenario contracts, Readiness backend/panel 0.1.0, Coordinator/Sessions 0.4.0 and fixed `readiness inspect/save-scenario` / `session inspect-readiness` routes are added. Journal/AHK sources are unchanged. Workflow 0.1.0 accepts the new coordinator and shares its guarded publisher; no installer or arbitrary executor is added.

Provider declarations distinguish discovered/connected, approval, process/armed, writing records and cancelled/stopped/exited states. Strict checks cover version/capability/context, one declared mock clock, ordered target/run/phase records, complete writes, expected/actual cadence, future/stale data, gaps, drops and missing fields. Approval/process presence alone fails. **MOCK_HEALTHY** means consistent authored declarations, not an actual CSV, live connection or capture-health adapter.

Scenario schema 1 retains ID/revision, built-in versus route/action, requested workload versus declared readback, cache/process/visit provenance, repetitions, provider/frame class, distinct software/physical latency endpoints and meaningful-input/calibration declarations, tagged phases/actions, budgets and mandatory focus/provider/memory/cancel stops. Unsafe save/quest/graphics flags, keys/text/command payloads, unknown fields/schemas, duplicates, mixed modes and bad budgets are refused. Incomplete declarations remain BLOCKED; complete declarations are **PREPARED_NOT_AUTHORIZED**. Every result has execution none, authority/runtime verification false and FG preflight not performed. No optical latency, repeatability, safe route, compatibility or effective-FG proof is created.

The inert private editor supports direct paths/optional Browse and current unsaved previews. Edits invalidate old summaries; dirty-draft replacement requires explicit discard confirmation. BOM-normalized draft hashes remain distinct from original provenance. Copy aliases imported identities; Save NEW pins the original across the dialog and validates edited bytes, refusing overwrite/reparse/repository destinations through the existing fsync/readback/exclusive-publication/owned-failure-cleanup route. Incomplete but valid scenarios may be saved as blocked private copies. Journals contain compact status/kind/blocker counts/hash, not editor/phase content. This is not a runner, recorder, replay channel or new complex metric engine.

Final acceptance: **872 toolkit cases: 870 pass, two physical-symlink skips**, 25 suites. **87 new backend/editor/CLI cases** pass (59/19/9), plus one new full-Hub wiring case; retained full-Hub suite now has 44 cases. Existing 61 Sessions and 48/23/10 workflow cases pass. **11 separate PictureHost static checks** and **52 PowerShell 7 source-export contracts** pass. Withdrawn test-owned Tk roots and mocked providers/dialogs/clipboard are not live desktop/game acceptance. The first regression found the old exact button-list expectation, then it was updated without dropping old controls; final rerun passed. An initial discovery command ran zero tests because hyphenated filenames were not collected; it is not acceptance. Per-file runs own the counts. Hub/full-Hub suites were checked again after the final guide-text addition.

Recovery coverage: **16 preceding owned source/test/doc files copied and byte-verified**, plus an inventory of **11 unmodified protected baselines**. Before/after SHA-256/exact UTC tick checks preserve four AHK sources/modules, Studio settings, private Hub registry, two Afterburner configs, RTSS config, Ultra+ config and Cyberpunk settings. This is scoped preservation, not whole-system/profile restore testing. Rollback: preserve newer/unrelated edits and private drafts/journals, close only owned Hub sessions, restore only the 16 preceding owned files and ignore the two optional new modules/three tests/two examples. Do not reset/restart AHK or restore game/native profiles. Private receipts remain outside Git; old source/Drive packages stay immutable and no remote publication occurs.

Read-only enumeration found no SkyrimSE/Cyberpunk2077/obs64/PresentMon/CapFrameX at the check; this is not continuous monitoring. No game launch/input/save access, graphics/profile change, benchmark, recording, listener, scheduler or cross-chat message was performed. Remaining boundary: separately scoped real provider/readback and supported observation acceptance, later scenario adapters. Real comparisons retain the fail-closed FG/memory gate; MFG/FrameWarp and highest-compatible Ultra+ VRAM remain deferred.

## 2026-10-11 — 0.9.0 offline workflow dry-runs

Requested scope: continue installation/diagnostic dry-runs and rollback plans, preserving AHK/settings/profiles and leaving games/benchmarks/recording stopped. [Hub 0.9.0](../examples/game-tool-hub/README.md#installation-and-diagnostic-dry-runs--090) adds optional Sessions → Workflow dry-runs, data-only backend/panel 0.1.0, Coordinator/Sessions 0.3.0 and `workflow inspect/export` plus `session inspect-workflow`. All eight tabs/shortcuts, existing catalog/FG/comparison/import/journal/evidence routes remain. Journal 0.1.0 and AHK sources are unchanged. This is a generic offline slice, not researched per-game installation or operational product acceptance.

Strict bounded recipes retain declared target/layer/source identity, resource owners/dependencies, process/snapshot declarations, one-layer changes, original/current/after/backup hashes, six component-verification phases and typed diagnostic evidence/hypotheses. Unknown/conflicting ownership, missing hosts/cycles, process unknown/running, stale sources, drift/incomplete backups and memory warnings stay blockers. Diagnostics cannot mutate. Hypothesis ordering is declared support count, not likelihood or root-cause confidence. Even fully checked declarations return **PREPARED_NOT_AUTHORIZED**, execution none, runtime verification false and FG preflight NOT_PERFORMED. Prepared recipes do not activate tests or circumvent the unchanged comparison gate.

Private targets are displayed separately; portable reports alias imported IDs/paths and omit raw recipes/logs/config values. Shared coordinator capture/expiry/cancellation and compact durable outcome counts are reused; no arbitrary executor, listener, replay, launch, install, profile write or rollback action exists. Portable exports pin source identity, refuse overwrite/reparse/repository destinations, fsync/read back, publish exclusively and preserve foreign replacements during failure cleanup. No atomic power-failure or restored-behavior guarantee.

Final acceptance: **784 Python toolkit cases: 782 pass, two physical-symlink skips**. The **81 new fixture/withdrawn-widget/CLI cases** pass (backend/core 48, panel 23, CLI 10), covering declarations versus authority, ownership/dependency/hash/coverage conflicts, path/schema/resource bounds, diagnostics/ranking, conditional rollback, source/publication/dialog drift, cancellation/expiry, journal failure, optional-child cleanup and privacy. Retained Hub 22, Catalog 35, bridge 36, full Hub 43, FG inspector/policy 101, Comparison 63/panel 39/CLI 9, importer 42 (one skip)/panel 41/CLI 16, Journal 53 (one skip), Coordinator 47, Sessions panel 61/CLI 12, evidence backend 50/panel 21/CLI 12 pass in this run. **11 separate PictureHost source checks** and **50 PowerShell 7 source-export contracts** pass. Skips are not passes; no PowerShell policy change. Withdrawn test-owned Tk roots and mocked dialogs/clipboard/providers are not observed live desktop/game acceptance. After the last source guard additions, all three workflow suites were rerun; older sources/fixtures remain unchanged except explicit new-capability/button assertions.

Fresh checkpoint preserves **26 preceding files**: 15 scoped source/docs/tests plus 11 protected baselines, byte/time checked before mutation; prior 0.8.0 checkpoint remains separate. Coverage is copied/hash-verified, not whole-system/native-profile or restore-tested recovery. Rollback: preserve newer/unrelated source/private data, close only owned Hub sessions, restore scoped preceding Hub/coordinator/Sessions/exporter/tests/docs, then ignore only the two optional workflow modules/three tests/two generic examples. No AHK restart or global/native/game reset. Optional workflow failures leave existing Sessions usable.

Final protected readback: all **11 scoped baselines** retain exact SHA-256 and UTC modification ticks (decimal strings, not rounded JSON numbers): four AHK sources/modules, Studio settings, private Hub registry, two Afterburner configs, RTSS config, Ultra+ config and Cyberpunk settings. Direct non-mocked CLI export/session operations on the authored unknown recipe produce/read back a 3,846-byte portable BLOCKED plan and a five-record verified closed journal (`finished`, `writer_open=false`, runtime verification false); original recipe bytes are unchanged. These are authored examples, not actual incidents or runtime verification. Process enumeration at `2026-10-11T18:14:32.3608828Z` found no SkyrimSE/Cyberpunk2077/obs64/PresentMon/CapFrameX, not continuous monitoring. No game/input/graphics/profile change, AHK restart, benchmark, recording, resident watcher or scheduler was performed.

Repository guidance kept declarations, observed state, execution authority and backup coverage separate. Remaining: researched per-game/product recipes and adapters, actual authorized install/rollback acceptance, recorder capability/mock contracts, saved-video alignment/player and separately owned Studio/HUD/radial/keymap reconciliation. Live crash collection, AHK/device/game input acceptance, MFG/FrameWarp and Ultra+/resource benchmarks remain deferred. No Drive/GitHub publication, commit/push or other-chat message is included.

## 2026-10-11 — 0.8.0 saved crash-evidence intake

Requested scope: inspect status and build the next remaining **offline** stage. [Hub 0.8.0](../examples/game-tool-hub/README.md#saved-crash-evidence-intake--080) adds optional Sessions → Saved crash evidence, selected-file backend/panel 0.1.0, Coordinator/Sessions 0.2.0 and structured saved-evidence/inspect-evidence CLI. Journal 0.1.0 source/prefix checks are reused. All eight prior tabs/shortcuts, import/comparison/catalog/FG APIs and existing AHK source/settings/profiles remain. No game/input/graphics/benchmark/capture capability is added.

Selected Windows event XML, Hub journal JSONL and opaque text/log attachments yield hash-bound portable previews and new private packets. Bounded formats/counts/timeline, DTD/entity refusal, original bytes, fixed helper identity, drift/no-overwrite/reparse refusal and escaped script-free HTML are tested. Originals/messages/names/paths/Computer/SID stay out of portable results; the packet's originals/locator receipt are private, not public-source material. Manifest entries are read back; individual fsync/readback does not guarantee atomic whole-directory/power-failure recovery. Failure cleanup preserves concurrent replacements.

Timeline retains source time/order, unknown UTC, journal UTC backsteps, open ends/unverified tails and earliest **reported** timed failure/tied candidates, not first actual failure or causal order. Unknown-time failures are counted; cross-provider clock error is unmeasured. Reporting PID is not assumed game PID; exact AppName association is a declaration, not runtime verification. WER presence alone, an open journal or a faulting module is not a cause/crash verdict. No verified VRAM exhaustion, QPC/video alignment or live watcher/query is claimed. Primary Microsoft schema/crash references are linked in the Hub guide.

Final acceptance: **703 Python toolkit tests ran: 701 pass, two physical-symlink tests skipped**. Retained suites: Hub 22, Catalog 35, bridge 36, full Hub 43, inspector 34/policy 67, Comparison 63/panel 39/CLI 9, importer 41 pass/one skip/panel 41/CLI 16, Journal 52 pass/one skip, Coordinator 47, Sessions panel 61/CLI 12. New evidence backend 50, withdrawn panel 21 and CLI 12 all pass (**83 new cases**). Windows physical-symlink permission skips are not passes; deterministic reparse refusals pass. **11 separate PictureHost static checks** and **48 PowerShell 7 export contracts** pass. Windows PowerShell 5.1 policy was not changed. Withdrawn test-owned Tk widgets/mock dialogs/clipboard/providers are not installed/live desktop/game/resource acceptance. Initial discovery found zero hyphenated test files and was not counted; individual scripts were rerun. Early fixture expectation corrections retain meaningful privacy/ownership tests.

Two direct non-mocked CLI operations on an explicitly authored synthetic XML fixture create/read back a private packet and inspect through a fresh five-record closed journal (`finished`, `writer_open=false`, `runtime_verification=false`). The described events did **not** occur in a game. All four packet manifest entries match sizes/hashes; original fixture bytes remain. This is source-format acceptance, not a measured crash or memory diagnosis.

Fresh private checkpoint: **25 copied/hash-verified files** (14 preceding source/docs/tests, 11 protected baselines), separately retaining the prior 0.7.0 checkpoint. All **11 protected files** preserve exact bytes/UTC modification times: four AHK sources/modules, Studio settings, private Hub registry, two Afterburner configs, RTSS config, Ultra+ config and Cyberpunk settings. UTC ticks are decimal strings compared with preserved before-copy timestamps, not rounded JSON floats. This is scoped preservation, **not** whole-system/native-profile recovery or restore acceptance. Final successful process enumeration found no SkyrimSE/Cyberpunk2077/obs64/PresentMon at its observed boundary, not continuous monitoring.

Rollback: preserve newer/unrelated files and private packets/reports/journals; close only the owned Hub session; restore scoped prior Hub/coordinator/Sessions/exporter/tests/docs, then ignore/remove only the two new optional evidence modules/three tests. No native/AHK/game reset or host diagnostics. No game/save/input/graphics/profile change, AHK restart, recording, benchmark, resident/scheduled watcher, other-chat message, commit/push or Drive/GitHub publication occurred. Repository guidance kept private originals separate from portable evidence and deferred runtime acceptance.

Remaining offline stages: recipe dry-runs/reversible change manifests; established-recorder capability/mock contracts; saved-video clock/player work; separately owned Studio/HUD/radial/keymap reconciliation. Live crash heartbeat/process/WER collection and operational adapters remain planned. Actual AHK host/device/game acceptance, MFG/FrameWarp and resource/Ultra+ comparisons remain deferred; real rendering comparisons stay BLOCKED by the unchanged FG/memory gates.

Current scope, confirmed **2026-10-11**: learn and connect existing tools, expose useful user controls and prepare a lightweight management helper. Benchmark execution, game launches and capture activation remain deferred. Complex lows, latency and specialized analysis must come from established programs.

## Current connection evidence

Native tool rows below retain their dated connection observations, not a new live inventory. The current local authored build is Hub 0.9.0; its offline acceptance and exclusions are recorded in the latest section above.

| Tool / interface | Observed state | What is established | Remaining boundary |
|---|---|---|---|
| MSI Afterburner 4.6.7.16935 | Installed, running | Read-only `MAHMSharedMemory` connection returned 20 fresh source entries. Saved profile has history logging Off and begin/end recording/logging hotkeys unset. | No game/run association or benchmark acceptance. Source definitions and scope need preservation. |
| RTSS 7.3.5.28314 | Installed, running, read-only mapping connected | v2.21 mapping returned six app entries, zero statistics samples and no capture flags. Author's consumer confirms FPS scaling; provider calculates summaries/lows. | No populated game lows, accepted interval, exact low method or base/generated-frame coverage. No OSD/profile/statistics writes. |
| Intel PresentMon console 2.6.0 | Previously installed; older process still running | CLI collector is distinct from the GUI capture application. Historical process does not prove active recording or valid output. | No new frame CSV or latency validation. Inventory-only in learning mode; do not launch another collector. |
| NVIDIA App | Existing interface; launch and running-state refresh passed | Installed program is discoverable/openable. File version is displayed separately from its product version. | Interface connection only; no overlay/recording/optimization setting changed or latency export validated. |
| NVIDIA FrameView SDK | Installed collector, inventory-only | Existing bundled console identified; no standalone FrameView GUI was located. Hub launch stays blocked. | SDK installation is not a populated latency source or proof of the GUI analyzer. |
| Game Tool Hub 0.7.0 | Authored learning preview; optional offline Sessions/journal foundation | Existing readers/imports/registry, Catalog/FG and Comparison retained. Fixed saved-data dispatch and verified-prefix new-copy recovery; latest scoped receipt below. | Fixture/withdrawn-Tk acceptance, not current installed-host/game behavior. No live crash watcher/WER, runtime FG proof, tuning, profile writeback, capture or custom metric engine. |

Desktop sensor snapshots are connection evidence. They are not new Cyberpunk performance measurements. The source polling timestamp is retained; stale/unavailable values are marked rather than replaced. The provider does not promise an atomic batch across all sensors.

Historical 0.1.0 GUI evidence: Tools was opened; the later footer adjustment and remaining flows were then pending. A sensor-tab click encountered the supported tool's user-input guard. The 0.2.0 acceptance below supersedes those pending core controls without implying that the larger cross-game product is complete.

## 2026-10-11 — 0.4.0 read-only FG preflight

The later user-selected stage adds a [read-only check and mandatory FG policy](../examples/game-tool-hub/README.md#read-only-effective-fg-preflight--040) to the existing Catalog planner. Explicit native/driver reads are separate from browsing and the five-second sensor refresh. In-game proposals require fresh effective-FG evidence; blocked results suppress cases and return `comparison_ready=false`, with CLI exit 3. Copy rechecks rather than recycling a PASS. Optional adapter/source failures block the comparison without removing catalog browsing, manager-idle previews or the original five tabs.

The documented System32 NVAPI adapter reads global/app DRS mode, inheritance, raw count/target and driver version, never writes settings. Cyberpunk native saved selections and full-path renderer identity are separate fields. The initial inspector cannot verify runtime FG, delivery or every mod owner; real observations remain BLOCKED even when configuration is fixed. A hypothetical fully verified Off/fixed PASS is covered only by synthetic contract fixtures. No JSON/manual approval bypass or adaptive-experiment substitution is provided. The FG gate is not memory/workload/metric acceptance, continuous monitoring or permission to execute.

Review fixes include preserving canonical inspector identity during assessment and restoring prior module entries afterward; accepting immutable documented mode mappings; refusing malformed/mismatched/untrusted receipts and source drift; clearing a stale PASS label on failed plan preparation; and distinguishing superseded global Dynamic settings from inherited/applicable adaptive mode. Modules load from exact captured sibling source, not arbitrary catalog-selected code or bytecode caches.

One actual read-only Hub check at `2026-10-11T00:28:23.480556Z` returned trusted BLOCKED / exit 3. Current driver is 617.42; Cyberpunk's saved native selection is DLSS x2, while current global and exact-path application DRS mode is raw 4 (Dynamic). App raw frame count is 0; dynamic maximum raw count 5 and target raw 16777216 are inherited globally. Counts remain raw, not guessed delivered multipliers. This establishes current configured adaptive mode only—not live activation, fixed delivery or October 10 settings. Native settings bytes and modification time matched before/after; no game was launched or settings changed. Effective/runtime state remains unknown/not observed, so ordinary comparisons stay blocked.

Final local source tests pass: 230 Python contracts (Hub 22, Catalog 35, bridge 36, GUI/CLI 36, inspector 34, policy 67) and 42 source-export contracts in PowerShell 7. The current Windows PowerShell 5.1 invocation refused script execution under its existing policy; that policy was not changed/bypassed and a current 42-check pass is not claimed there. Original shortcuts/tabs, immutable imports, declaration-only records, stale-source refusal, malformed receipts, fresh Copy-plan blocking and inherited versus overridden Dynamic modes are covered by fixtures. The preserved real observation predates final nonfinite-JSON and wording refinements; its recorded source hashes/reasons remain frozen with that boundary, not promoted to final runtime acceptance.

Just-in-time copies cover the previous 53 curated authored files. Before/after inventories verified all 18 protected AHK/installed Studio/settings/Hub-registry/historical R5 files byte-identical. The existing AHK process was not restarted. Game input, saves, graphics, recording, MFG/FrameWarp acceptance and benchmarks remain deferred. Scoped rollback restores the previous Hub/bridge/panel source from that private checkpoint, preserving newer reports and private registry. The two new FG modules may remain unused by the prior Hub; do not restore a whole game/device/profile to remove this feature. Publication status is recorded separately in [distribution](DISTRIBUTION.md).

## 2026-10-11 — 0.3.0 catalog integration

The requested build stage adds Catalog to the existing Hub, not to the installed AHK host. All original five tabs and Ctrl+1 through Ctrl+5 retain their assignments; Catalog uses Ctrl+6. The same catalog engine supplies filtering, record details and dependency-preserving overhead proposals through GUI and CLI. Recorded installation fields are explicitly distinct from the Tools tab's current inventory.

| Check | Established result |
|---|---|
| Source-bound bridge | 24 pure contracts passed: bounded stable reads, exact sibling backend/version, detached records, strict JSON, filters and dependency plans, source drift/reload and validation work-budget refusal. No bytecode cache or private configuration write is part of loading. |
| Hub CLI | Nine integration contracts passed. Catalog status/list/show/plan return structured data without reading the private executable registry, live providers or processes, launching a program, importing reports or sending input. Invalid catalog/source syntax returns a structured failure. |
| Native Tk Catalog fixtures | Twelve contracts passed using only test-owned withdrawn roots. Actual widget callbacks cover filters, selection/details, copy with mocked clipboard, one-factor/2×2/blocked plans, stale-data refusal and explicit recovery. |
| Full Hub Tk fixtures | Eight contracts passed with mocked providers. Actual bound shortcut handler preserves tab order, normal Entry/Text editing and modal/top-level ownership; Catalog blocks remembered Tools/Reports actions. Missing optional module or invalid catalog does not break original tabs. Auto refresh remains Off. |
| Existing foundations and export | Original 22 Hub and 35 catalog tests passed unchanged. All 41 curated-source export checks passed in both PowerShell 7 and Windows PowerShell 5.1. |

The 29 integration contracts comprise the nine CLI, twelve panel and eight full-Hub cases above. These are isolated code/widget fixtures, not an observed live-desktop tour, input acceptance, resource-cost result or benchmark. No game, capture or graphics test was performed. Catalog references and declared capabilities remain inert, and every plan reports execution `none`; unmeasured CPU/GPU/RAM/VRAM values stay null. Highest Ultra+ and Skyrim MFG/FrameWarp remain gated.

Review fixes: compile captured optional-module source rather than using a loader that can consume stale bytecode; return source syntax failures as structured CLI errors; clear all obsolete displays after source drift, including failed plan preparation; and bound an estimated validation workload before the backend's graph scans. The workload guard is an estimate, not a hard runtime deadline. Larger catalogs should later use an indexed/worker adapter instead of raising limits silently.

Just-in-time source copies and private before/after inventories were retained. All 18 tracked repository/installed AHK, Studio settings, Hub registry and historical R5 artifacts stayed byte-identical; the existing AHK process was not restarted. No native profile migration was added or performed. Restore only the prior Hub source and optional catalog modules to undo this stage, keeping newer private reports/registry intact. The prior published r5 checkpoint contains Hub 0.2.0, not this local 0.3.0 continuation.

## 2026-10-11 — 0.2.0 control acceptance

| Control | Observed result |
|---|---|
| Tools / Sensors / RTSS / Reports / How to use | All five tabs opened through local Ctrl+number shortcuts; final footer was visible. |
| Refresh; optional refresh On/Off | Live readings refreshed. Checkbox and Ctrl+T both tested; final refresh is Off. No time-series files appeared. |
| RTSS application selection | Provider interval/count, update age and absence of instrumentation endpoints displayed. No latency inferred. |
| Copy status | Completion visible; authored summary excludes local paths/app identities and lists only source/app counts. |
| Save snapshot | Ctrl+S created a new private JSON; file readback confirmed the connection state. Overwrite refusal separately covered by contracts. |
| Import / select receipt / open original | Synthetic PresentMon CSV archived through the visible form; original strings `1.250`, `NA` and blanks preserved; receipt showed no recalculation. Original-open dispatched to its associated app and completion was observed. |
| Add / Register / Cancel | Unconfirmed registration refused; explicit interface checkbox allowed an existing Notepad registration in an isolated test profile; prior registry backup verified. Cancel hid the form and original user registry stayed byte-identical. |
| Open selected; collector blocks | NVIDIA App opened and Refresh showed Running Yes. PresentMon and FrameView SDK console selections both refused launch; no new collector appeared. |
| Close/reopen | Only Hub closed/reopened. Test imports/registrations remained in a separate private acceptance folder; final Hub uses the original profile with no draft. |

Twenty-two contracts cover MAHM preservation, RTSS offsets/bounds/version gates, unavailable statistics/stale live counters/tick wrap, endpoint presence without calculated latency, original report cells/definitions/hashes, bounded previews, immutable files, registry backups/duplicate refusal, known collector blocking, keyboard-layout mapping and draft refusal of action/confirmation fields. Fixtures are synthetic, never performance results. Afterburner root/profile and RTSS configuration hashes matched the just-in-time baseline; no game launch or benchmark/recording activation occurred. The historical elevated PresentMon process stayed present and was not silently terminated or resumed. No previous per-frame CSV was located.

Observed automation limits: a native file dialog produced an unavailable cached element/screenshot error; it was cancelled. Automated Unicode text did not appear in Tk entries. Direct path forms and an optional bounded startup JSON draft provide a supported file-based route; draft fields remain visible and do not execute an action or populate confirmation. Optional Browse/free-text input remains user-operated or separately verified. User-input guards were respected; no forced input or security bypass was added.

## Working methods

Prefer an existing API, SDK/shared memory or report export to reading repeated screenshots. Current Afterburner adapter uses the installed author's `SDK/Include/MAHMSharedMemory.h` v2 prefix. It opens only an existing `MAHMSharedMemory` mapping with `FILE_MAP_READ`, validates bounded sizes/counts and preserves names, units, source IDs, flags and original values. It does not use the hardware-control `MACM` interface or copy the SDK into Git. `FLT_MAX` and nonfinite values become unavailable; a reported zero remains zero. Live FPS counters are explicitly unscoped.

RTSS uses existing `RTSSSharedMemoryV2` with `FILE_MAP_READ`. Header offsets/counts/stride govern the bounded application array; newer fields require both version and size gates. The installed author's `RTSSSharedMemory.h` and `OverlayDataProviderInternal.cpp` establish packing and tenths-of-FPS conversion. Zero statistics count leaves average/lows unavailable; raw provider values are retained. Live-counter freshness uses the provider's tick period with wrap handling. Historical summary values retain their interval and are never promoted to a fresh run. No OSD ownership, locks, statistics buffers, latency markers or capture flags are written. Instrumentation endpoints are availability evidence only; the helper computes no latency deltas. Reads are best effort, not an atomic provider snapshot.

Read effective per-user settings from Afterburner's `Profiles/MSIAfterburner.cfg`, falling back to application defaults. The root default file alone is insufficient. Stored settings are configuration evidence, not proof of runtime recording state. The helper displays raw hotkey values instead of guessing their encoding. Proposed recording keys must be checked against native/mod bindings; Cyberpunk F9 already controls DLSS quality, so a guide's generic F9 recording suggestion must not be copied blindly.

Use supported Computer Use for observed ordinary-app controls. The previous `launch_app` route timed out while UAC was pending and did not leave Afterburner running after approval. A direct normal process launch subsequently opened it; UI/process readback confirmed success. Treat that as a launch-helper limitation observed in this session, not a proven Afterburner crash. Windows approval remains manual. No security setting was changed.

For future tools, register installed GUI executables and preserve their existing settings. Verify the exact program's exports before selecting it for a specific metric. The console collector and GUI analyzer may differ. OCR/accessibility are useful fallbacks for UI state; never use OCR labels alone as proof that a feature evaluated or a metric was captured. A future adapter can import documented summary fields without implementing the statistic again.

## User panel and agent integration

[Game Tool Hub source and launcher](../examples/game-tool-hub/README.md) provides Tools, Sensors, RTSS, Reports, How to use, Catalog and Comparison tabs. Auto refresh starts Off; opening the panel does not start or save a time series. Visible path forms, optional non-executing startup drafts and local keyboard shortcuts improve user/agent control. Console collectors remain blocked in learning mode.

The agent can use `inspect`, `snapshot --output`, `import-report` and read-only `catalog status/list/show/plan-overhead` with structured JSON results. There is no network listener or hidden input channel. The future larger AHK host can consume an explicitly requested snapshot or invoke the coordinator as a module/command; integration must preserve its input ownership, privacy, stop behavior and existing profiles. No automatic host wiring or global shortcuts were added here.

Imports preserve CSV/JSON/TXT/HML bytes plus source program, definition, UTC, size and SHA-256. No metrics are recalculated. Imports have no inferred run association. HML remains opaque until an established export/conversion path is validated. Local paths/receipts stay private; only authored code, methodology and sanitized evidence belong in Git. Existing raw test archives remain unchanged.

The PresentMon adapter recognizes documented v2-style headers only when that provider is declared. It previews at most five original rows and preserves application/PID/swapchain, timing convention and frame type when supplied. Documented GPU, display, input, instrumented and PC-latency fields retain units/endpoints; absent/blank/NA fields stay unavailable. Provider version is user-declared, not inferred from headers. Software input-to-display fields are not optical camera/animation latency measurements. NVIDIA App has no metric export adapter yet; FrameView SDK collector is not launched to obtain one.

Rollback: close Game Tool Hub, preserve its private imports, and remove only the optional authored helper/launcher. No game or Afterburner/RTSS configuration restore is required for this connection work. Closing the panel does not terminate other applications or the historical idle collector.

## Next learning steps

Current continuation: the [master checklist](GAME-TOOLS-MASTER-CHECKLIST.md) consolidates 60 source-linked requirements from saved plans and bounded related-chat review. [Offline comparison/reporting](OFFLINE-COMPARISON-REPORTS.md) now includes two reviewed saved-summary import adapters; broader provider formats and trustworthy missing measurement context remain the next offline boundaries, not a resumed game benchmark.

1. Core panel/read-only connections are accepted; optional native Browse/free-text automation remains separate. Keep capture controls absent.
2. Before using populated RTSS statistics, preserve exact provider low method, interval and frame coverage. Current SDK connection does not establish those game measurements.
3. Validate actual saved PresentMon/NVIDIA or analyzer output and choose any further adapter by documented export capability. No real latency CSV exists in this evidence set. Installation or recording requires a separate requested action; no installer/service was added here.
4. Add explicit user-controlled settings adapters only for requested supported actions, with snapshots, visible state and rollback. Keep hardware tuning, game/profile changes and capture activation separately scoped.
5. Resume game scenarios and performance validation only after an explicit user request.

Primary references reviewed 2026-10-11: [MSI monitoring/OSD guide](https://www.msi.com/blog/msi-afterburner-on-screen-display/), [Intel PresentMon 2.6.0 console field definitions](https://github.com/GameTechDev/PresentMon/blob/v2.6.0/README-ConsoleApplication.md) and [NVIDIA's standalone FrameView application](https://www.nvidia.com/en-us/geforce/technologies/frameview/). Installed RTSS SDK/profile evidence governs this exact configuration; a generic guide does not establish current tool state.

## 2026-10-11 — 0.5.0 offline comparison and reporting

The current user selected a master checklist and saved-data comparisons only. The [checklist](GAME-TOOLS-MASTER-CHECKLIST.md) reconciles 60 stable requirements from local plans/current chat and bounded supported reads of five related chats, preserving source ownership, R8/Pro owner-report limits and unimplemented work. It is not a full account/message/attachment audit.

Hub 0.5.0 adds optional Comparison as the seventh tab; previous tabs, Ctrl+1–6, readers, original-byte imports, executable registry and Catalog/FG semantics are retained. The [Comparison 0.1.0 contract](OFFLINE-COMPARISON-REPORTS.md) supports explicit normalized provider-summary loading, metric selection, raw runs/definitions/blockers, eligible repeated-run means/min/max, A/B and dependency-preserving additive 2×2 contrasts, selected-metric copy and exclusive new JSON/HTML exports. Unknown/mismatched workload, coverage/settings/definitions/components, memory pressure and FG states block inference. Missing values and failed/incomplete runs remain present. No custom raw-frame low/latency engine, original-report universal normalizer, collector, video player or shared action listener is added.

All **339 Python toolkit contracts pass**: Hub 22, Catalog 35, bridge 36, full Hub/catalog integration 39, FG inspector 34, policy 67, comparison core 58, panel 39 and CLI 9. Separately, all **11 PictureHost source checks** pass; this does not deploy/restart the AHK host or validate Picture UI/game behavior. **43 source-export contracts pass under PowerShell 7.** The existing Windows PowerShell 5.1 policy was not changed/bypassed; no new 5.1 pass is claimed.

Widget tests use withdrawn test-owned native Tk roots, mocked providers/dialogs/clipboard and actual callback routing. They exercise optional failures, preserved shortcut ownership, raw-only blocked data, nulls, selected-metric exports and changed-source invalidation, including the real Canvas redraw callback. They are not observed live-desktop focus/resize, full native-profile regression or game acceptance. A direct non-mocked offline CLI also exported the labeled synthetic 13-run/four-resource fixture to new JSON and HTML files: 16 case-summary rows, interrupted run retained, execution none. These are demonstration numbers, not measured costs.

Real rendering/injected-feature imports remain **BLOCKED** regardless of imported FG declarations: original-report hashes are declared associations and normalized-file byte identity is not trusted runtime FG evidence. The existing configuration-only FG inspector/policy is unchanged. Only matched non-rendering manager-idle imported summaries or labeled synthetic exercises can have eligible metrics at this stage.

A just-in-time private snapshot preserved 22 existing source/document/configuration files before scoped changes. Before/after hashes and modification times verify all **11 tracked protected files** unchanged: four AHK source/modules, Studio settings, private Hub registry, two Afterburner configurations, RTSS configuration, Ultra+ configuration and Cyberpunk settings. This is scoped byte-preservation evidence, not a new native-device/whole-system backup or tested restore. No existing profiles were imported or migrated. A pre-existing user Cyberpunk process was observed and left untouched; no agent game launch/control, save access, graphics change, benchmark or recording was performed.

Rollback: preserve private reports/registry, close only the Hub being replaced, restore the immediately preceding Hub source/exporter/integration tests/docs from the local snapshot, and remove/ignore only this build's new optional comparison source/tests/guides/fixture if desired. Do not reset unrelated dirty files, restore native/game settings or restart AHK. Next useful offline boundary: a documented provider-specific original-report-to-summary adapter with byte-verified associations. Crash journal/recovery, synchronized video, broader coordinator and input acceptance remain tracked future work; they require their own scoped acceptance.

## 2026-10-11 — 0.6.0 saved-report import adapters

The user selected offline saved-report adapters for Comparison, with existing features/profiles preserved and games, benchmarks and recording stopped. Hub 0.6.0 adds **Import saved reports**, a preview/assignment wizard and `inspect-saved-report`/`import-saved-reports` CLI routes sharing [importer 0.1.0](../scripts/GameToolReportImport.py). Comparison core 0.1.1 keeps schema 1 and strict complete-run validation; only non-complete run start/configuration identity may be null, with bounded import provenance and explicit metadata-incomplete reasons.

Supported intake is Cyberpunk native `worldBenchmarkSummary` JSON and the exact PresentMon GUI statistics CSV writer layout. Raw per-frame CSV, arbitrary analyzer JSON, HML and undocumented Afterburner text are not guessed. Cases begin unassigned; baseline/a roles and the tested factor are explicit declarations, not inferred filenames or observed components. Multi-select assignment/removal supports repeated reports. Source preview hashes bind import, every source is validated before output, a fresh exclusive private bundle preserves original bytes and verified hashes, and the receipt's normalized hash binds the subsequent panel load. Existing normalized loading, selected-metric copy/export and original Reports intake remain available; no registry/profile migration or action listener is added.

**442 Python toolkit tests passed; one further test skipped** because physical symlink creation was unavailable without changing Windows privileges. Deterministic reparse-point rejection passed separately. Suite breakdown: original Hub 22, Catalog 35, bridge 36, full Hub/catalog 39, FG inspector 34, policy 67, comparison core 63, existing panel 39, existing CLI 9, importer 41 passed/1 skipped, new import panel 41 and new import CLI 16. The separate **11 PictureHost source checks** and **44 PowerShell 7 source-export contracts** pass. No current Windows PowerShell 5.1 pass is claimed and its policy was not changed. Tests use authored format fixtures, temporary files and withdrawn native Tk roots/mocked dialogs—not observed foreground UI, installed-host, device or game acceptance.

Direct non-mocked CLI acceptance created a private two-source **synthetic format-fixture** bundle, then selected-metric JSON/HTML exports. Both retain two raw runs and zero contrasts, execution none, with the expected coverage/configuration/components/FG/memory blockers. Those numbers are not game measurements. Source drift, oversized integers, duplicate report bytes, wrong layouts, existing destinations, final-file verification failure, post-publication source drift and a concurrent replacement were tested. Review repaired the final-failure cleanup to use explicit successful completion rather than the number of linked files; it never removes a concurrent user's replacement.

Four existing Cyberpunk 2.31 `summary.json` files were inspected **read-only** through the final CLI, with hashes and modification times unchanged. Average/min/max FPS, elapsed seconds and counts match the source values. Their native FG/MFG fields are saved requests only, not effective runtime evidence; two report sets have different PT declarations. They lack UTC windows/complete settings/cache/warning state and cannot establish a comparable workload or measured mod cost. No actual local PresentMon GUI stats report was available, so that adapter is source-layout fixture acceptance only. The [offline guide](OFFLINE-COMPARISON-REPORTS.md#saved-report-adapters--hub-060) records pinned primary writer/statistic sources and distinguishes capacities from usage, presented intervals from base/displayed frames and provider percentiles from lows.

All imported rendering reports remain **BLOCKED**. Unknown UTC/settings stay null, unknown memory-warning state stays unverified, and effective FG/Dynamic MFG cannot be promoted by source fields or a manual toggle. Import-time archive identity is not trusted measurement provenance or continuous archive verification. The existing FG policy/inspector is unchanged; no game test is implied by successfully parsing a historical file.

A just-in-time private snapshot captured **28 existing files** (17 source/docs/tests plus 11 protected files). Current before/after hashes, sizes and modification times confirm all **11 tracked protected files** unchanged: four AHK sources/modules, Studio settings, private Hub executable registry, two Afterburner configurations, RTSS configuration, Ultra+ configuration and Cyberpunk settings. This is scoped preservation, not full native/onboard-profile or system recovery. Read-only process checks found no SkyrimSE, Cyberpunk2077, obs64 or PresentMon at the start/end checks; this is point-in-time, not monitoring. No game/save/settings/input/profile/capture/benchmark action occurred.

Rollback: preserve private reports/registry, close only the Hub being replaced if it is running, and restore this task's prior Hub/panel/core/exporter/tests/docs from its before-change snapshot. Remove/ignore only the new optional importer/tests/authored format fixtures if desired. Do not reset unrelated dirty files, restore native/game settings or restart AHK. Source packaging is local only; no Drive/GitHub upload or sharing change. Further offline adapters should start with actual saved exports and documented semantics. Effective runtime FG, game input, crash recording and benchmarks remain deferred.

## 2026-10-11 — 0.7.0 offline coordination and journal

The user selected shared coordination and crash-safe journaling possible without a game. Hub 0.7.0 adds optional **Sessions / Ctrl+8**, [Coordinator 0.1.0](../scripts/GameToolCoordinator.py), [Journal 0.1.0](../scripts/GameToolJournal.py), [panel 0.1.0](../scripts/GameToolSessionPanel.py) and structured `session` routes. Existing seven tabs, shortcuts, providers, imports, catalog planning and fail-closed FG/memory reporting gates remain. No AHK code is installed/migrated, no profile changes or global input hooks are introduced, and no hidden listener/executor starts.

The fixed registry exposes only saved-report inspection and normalized saved-comparison inspection, reusing existing backends. Explicit fresh sessions have named scope/owner/action identities, bounded phase labels, monotonic expiry, cancellation and compact path-free outcomes. Lifetimes and cancellation gate result acceptance; bounded synchronous reads are not hard-preempted. Cooperative ownership applies to the journal/session, not the entire desktop. Writer-close failure retains the handle for an explicit cleanup retry and reports `writer_open`, never promoting failed cleanup to finished status. Old journals and recovered copies cannot reopen, replay or resume actions.

Each acknowledged journal record is flushed/fsynced and has ordered sequence, UTC, monotonic clock identity and a SHA-256 chain. Strict byte/work/schema limits reject malformed/duplicate/nonfinite/deep data and verify only the complete prefix before first damage. Write/fsync failure poisons the writer. Recovery checks the inspected source hash and identity, stages/verifies a prefix and publishes into a new exclusive destination; original evidence and concurrent replacements are preserved. Hashes are identity/integrity evidence, not authentication or runtime FG permission. An open/interrupted journal is not a game-crash diagnosis; unacknowledged evidence and some storage/power failures can still be lost. No heartbeat, process/WER/log collector, recorder or synchronized player is implemented by this foundation.

Final regression: **618 Python toolkit tests passed, with two additional physical-symlink creation tests skipped** without changing privileges. Deterministic reparse refusal is tested. Breakdown: original Hub 22, Catalog 35, bridge 36, full Hub integration 43, FG inspector 34/policy 67, comparison core 63/panel 39/CLI 9, importer 41 passed plus 1 skipped/import panel 41/import CLI 16, journal 52 passed plus 1 skipped, coordinator 47, Sessions panel 61 and Sessions CLI 12. **11 separate PictureHost source checks and 46 PowerShell 7 export contracts pass.** No current Windows PowerShell 5.1 acceptance or policy change is claimed. UI tests use withdrawn test-owned Tk roots and mocked dialogs/providers/clipboard, not observed foreground UI, installed-AHK, physical-device or game acceptance.

Harmless authored child interruption demonstrates two acknowledged records surviving termination, readable live evidence, a refused competing OS writer lock, lock release after child death and exact-prefix recovery. Injected short-write/fsync/close failures, UTC-overflow and backwards/expired clocks, in-flight cancellation, pre-open special-file refusal, source/module drift, no-overwrite and replacement ownership are covered. These are helper/fixture faults, not an intentionally crashed game or exhaustive storage-failure test. A bundled Windows runtime read also confirmed unchanged file identity/size/mtime while pathname and handle `ctime` differed; source verification uses consistent object identity/size/mtime plus content hash, not that inconsistent field.

Two direct non-mocked CLI operations inspect authored synthetic report/comparison fixtures, each producing a valid five-record closed journal with `writer_open=false` and `runtime_verification=false`. The comparison is a labeled arithmetic exercise, not a cost measurement. Original test-source bytes are retained. Portable status excludes raw report/journal data and local paths; unknown loader errors use fixed path-free reason codes. Fixture report declarations cannot establish effective FG or override memory/workload gates.

The just-in-time private snapshot contains **24 existing files**: 13 source/docs/tests and 11 protected files. SHA-256/size/UTC-time checks confirm all **11 protected files unchanged**: four AHK sources/modules, Studio settings, private Hub registry, two Afterburner configurations, RTSS configuration, Ultra+ configuration and Cyberpunk settings. This is scoped preservation, not complete native/onboard or system backup/restore acceptance. Start/end read-only process checks returned no SkyrimSE, Cyberpunk2077, obs64 or PresentMon; they are point-in-time observations, not monitoring. No game/save/input/graphics/profile/benchmark/recording action occurred.

Rollback: preserve private journals/reports/registry, close only the owned Hub session, restore the immediately preceding Hub/exporter/integration tests/docs from this task's snapshot and remove/ignore only the new optional coordinator/journal/panel sources/tests. Keep unrelated dirty files and native/AHK/game settings. Curated source packaging is local only, with private journals/inventories excluded; no Drive/GitHub publication or sharing change. Next useful offline boundary: bounded crash-evidence intake/status packets and later established-recorder capability contracts, not activating live capture. GT-028/030/031 and game/input/benchmark acceptance remain deferred.
