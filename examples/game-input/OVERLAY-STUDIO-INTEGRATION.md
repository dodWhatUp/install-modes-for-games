# Installed Overlay Studio integration — 2026-10-11

Host: existing **Azeron Overlay Studio 2.0.0-beta**, not the separately archived 3.0 preview. The local source matched the exact legacy hash `A9D943F2F950AB8702BC2493109CE8B9EE9EBB16EBBD6E2A59E2C406A3A844A7`, and its saved settings contained an enabled F7 local Hold picture plus key-display HUD. Disabled F15/F16/F17 slots remain disabled and unchanged.

## What is integrated

- The actual host includes `GameInputModule.ahk` and `OverlayStudioGameInput.ahk`. A sanitized, equivalent authored host is retained as `AzeronOverlayStudio.integrated.ahk` in this folder.
- All four existing tabs and their functionality remain. Optional **5. Game Input** adds Start, Stop, pause, indicator, prepare and cancel. The host's own tray keeps its original items and adds a submenu. The module is **Off at launch**, and extended input requires an explicit checkbox before Start.
- Only while enabled, host-owned Ctrl+Alt+T prepares an action; Ctrl+Alt+Esc stops **the module only**, leaving Studio alive. These are reviewed temporary controls, not a saved game/device profile.
- Start checks enabled host triggers, output collisions and MIC output/management feedback. Disabled picture slots are not treated as active collisions. Host key capture/rebind/pause/shutdown and saved MIC-shortcut changes stop the module before changing ownership. Existing input-HUD `MinSendLevel=1` remains intact; no payload text is added to the host log.
- No INI schema, image path, slot, native/device profile, registry setting, startup entry, elevation, interpreter installation, game setting or save is changed by the integration code.

Module v0.5-preview.3 retains the v0.5-preview.2 Stop→Start registration fix: AHK retains disabled variants, so registration uses explicit `On T1`. This matches the [official AHK Hotkey contract](https://github.com/AutoHotkey/AutoHotkeyDocs/blob/v2/docs/lib/Hotkey.htm). Current native syntax and pure policy checks are not GUI or game acceptance.

An intermediate integration check exposed another real issue under the active Hebrew keyboard layout: `GetKeyName("t")` returned a localized character although its virtual key stayed 84. The collision checker now uses stable virtual-key identities, including Esc/Escape aliases and modifier order, without changing the keyboard layout or saved labels. The failed no-input diagnostic was stopped separately; no game was running.

## Verification boundary

Native AutoHotkey 2.0.30: integrated-host syntax exit 0; 36 module policy tests and 8 integration policy tests rerun after the latest repair. The actual host/module/adapter and repository equivalents match. Saved Studio settings remain hash-identical. A read-only profile check passed 13 assertions. These checks ran with the host stopped; the retained `#SingleInstance Force` can replace a live instance before a diagnostic argument branch. Do not transfer v0.3.1 historical live results to this integrated host.

At preparation time, another active chat was operating desktop dialogs for Game Tool Hub. No input was sent into that dialog and neither game was launched concurrently. Acquire exclusive desktop-test ownership before runtime checks; do not confuse cross-chat focus races with game rejection. Do not disable supported control-tool user-input guards.

## Observed host failures and repairs

- First normal launch failed because adapter-local `menu` shadowed AHK's case-insensitive `Menu()` constructor. Renamed that local to `trayMenu`, closed only the failed owned instance and repeated the checks.
- The host then displayed four F17/disabled slots rather than the unchanged saved profile. Original `LoadConfig()` reused `A_Index` inside a nested property loop. Capturing `slotNumber` before that loop restored readback of F7/enabled and F15/F16/F17/disabled, without writing the INI. The normal host subsequently displayed the correct picture/HUD settings and its two-second saved-picture test appeared and hid. HUD output itself was not visually confirmed.
- Module Start then failed with **Target window not found** while setting transparency on its own newly created hidden indicator. Preview.3 scopes `DetectHiddenWindows true` to that operation and restores the prior value in `finally`; no global policy or saved setting changes. Native validation and 36+8 policy checks passed afterward. The host reopened on the fifth tab with Game Input Off; Start after this repair was not exercised before the user's consolidation request.

All 60 original methods remain, but source preservation is not acceptance of every legacy feature. Actual module Start/Stop/restart, indicator, cleanup, HUD output and extended game receipt remain pending. No game was launched during these host checks. The new request places the [shared-toolkit proposal](../../docs/GAME-TOOLS-ARCHITECTURE.md) before further input acceptance; recording and highest-level Cyberpunk Ultra+ VRAM testing come later.

The current collision review covers Studio's active bindings, not a complete native-mapper audit. Confirmed SHARED R5 TOOLS outputs include F2/F3/F8; reserve or resolve those diagnostic overlaps before arming. Extended `BindingPlan()` outputs also need an explicit complete declaration before a future common key-reservation service can rely on them.

## Exact rollback

Private checkpoint identifier: `OverlayStudio-GameInput-20261011`, separate from the historical module and game snapshots. It preserves the original host, settings and current game configuration/save hash manifests. These private paths/configs are not part of this public source folder.

Stop Game Input through tab/tray, close Studio normally, preserve any newer source, then restore only the original `AzeronOverlayStudio.ahk` from `before/host`. The two optional module files can remain unused. Do not restore all Azeron/reWASD profiles, game files, Steam settings or saves. Original Studio settings need no restoration if still unchanged. If newer settings differ, reconcile them rather than replacing them blindly.

Restoring the original host also restores its observed nested-`A_Index` loader defect; the original source checkpoint is a recovery artifact, not a claim that this profile loaded correctly before repair.

## Runtime test scope

Test Start/Stop/restart and existing picture/HUD availability first. Then each game separately: main menu only, safe mod search text, harmless Credits Enter, Escape return and bounded caret holds with release verified. No Continue/Load/New, console submission, graphics controls or benchmarks. Keep Unicode acceptance separate from ASCII; menu holds do not establish movement gameplay. Stop module after the authorized task.
