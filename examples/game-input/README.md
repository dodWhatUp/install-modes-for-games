# GameInputModule — optional AHK v2 game-control adapter

v0.5-preview.1, 2026-10-10. Authored source only, not an interpreter or input driver. Native AHK 2.0.30 syntax checks and **36 no-input tests pass**. No GUI, lifecycle or game tests were run for this refactor. The [workflow/evidence guide](../../docs/AGENT-GAME-INPUT.md) separates the live-tested v0.3.1 baseline from prepared extensions.

## Files and quick start

- `GameInputModule.ahk`: include this file in the larger host. Loading/constructing it registers nothing. `GI_*` functions and the `GameInputModule` class are the namespace; check for collisions before inclusion.
- `Start-GameInput.ahk`: standalone launcher, not for inclusion in another host. Core mode by default. Optional `--extended` enables unverified prepared text/Enter/Escape/hold diagnostics.
- `HostIntegration.example.ahk`: isolated example with a host-owned submenu and manual enable. Not a patch to the user's existing tool; do not run alongside another helper.
- `baseline/ControlHelper-v031.ahk`: exact historical source, SHA-256 in the main guide. It owns its own tray/exit/global chords and must NOT be included in the larger tool.
- `OTHER-CHAT-HANDOFF.txt`: ready-to-copy request and integration/acceptance instructions.

AutoHotkey **v2** is required. Open only the desired standalone file normally through the supported UI, after exiting older helper versions. Confirm the visible version. No run-as-admin, UIAccess, startup entry, purchase or association change is needed. The legacy `../skyrim-special-edition/Skyrim-F12-Test.ahk` is now a compatibility launcher.

Developer no-input validation (interpreter path varies; keep the old helper stopped):

```powershell
& 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe' /ErrorStdOut /Validate .\Start-GameInput.ahk | Out-String
& 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe' /ErrorStdOut .\Start-GameInput.ahk --self-test | Out-String
```

Require explicit PASS output and exit 0; an empty run under SingleInstance Ignore is not a pass. Pure tests instantiate inert modules but create no GUI, hooks, running timers or input. They do not prove normal Start/Stop, game reception or crash-safe cleanup.

## Public host API

```autohotkey
#Include GameInputModule.ahk  ; adapt to the real host's module path
settings := GI_BuildSettings()
; settings.EnableExtended := true  ; explicit experimental opt-in only
module := GameInputModule(settings)
plan := module.BindingPlan()       ; inspect and reserve before starting
; After a real collision/ownership review, from a host-owned enable control:
module.Start(true)
; Host UI may call module.OpenEditor(), TogglePause(), ToggleIndicator(),
; ToggleSound(), Cancel(), Snapshot(), and Stop(). Stop keeps the host alive.
```

`Start(false)` refuses registration. `Start(true)` does not detect other scripts' hotkeys: the host must review `plan`. Start adds only exact-foreground target actions, its own status GUI/timer and a removable exit-cleanup callback. Stop disables only those registered actions, cancels its timer, destroys its GUIs and releases module-owned holds. The module does not edit tray items/tooltips, register global management chords, call ExitApp, change KeyHistory/recording, write settings or remap devices.

The larger host must reserve or safely remap these temporary triggers, and prevent overlapping output-key holds. Keep `GI_*`/class names unique. Do not mutate Settings/Targets while started; Stop before changing validated configuration. The registration methods restore a neutral HotIf context in their thread. Hook variants are turned Off, not deleted; do not assign them to a competing owner while the module owns them.

For a host-created one-shot request, `Arm(payload)` accepts `{Kind, Window, Target, ...}` for a live exact target, requires extended opt-in and a started/unpaused/idle module, copies allowed fields, stamps epoch/expiry, and sends nothing. Text also requires `Text` and `Transport` ("Raw keys"/"Unicode text"); Hold key requires `Key`, `HoldMs`, optional `Repeat`. `Kind` is Text/Enter/Escape/Hold key. Only an observed subsequent F3 release dispatches. The GUI prepares the same payload without disk files.

## Trigger map and bounds

Exact default executables: `SkyrimSE.exe`, `Cyberpunk2077.exe`. No wildcard, background-window send or automatic focus/launch.

| Trigger | Output / scope |
|---|---|
| F8 | Skyrim F12 / Cyberpunk Delete |
| F13 | Delete |
| F14 / F15 | Down / Up |
| F16 | vkC0 (console/CET panel toggle) |
| F17 / F18 | Left / Right |
| F19 | Esc (configured, live acceptance pending) |
| F20 / F2 | digit 1 / Backspace; only an observed safe field |
| F3 | Consume prepared action once; extended mode only |

Core presses use 150 ms with release/modifier/focus/pause-epoch checks and 800 ms cooldown. Trigger release times out after 3 seconds in this preview. The status panel is visible by default; READY/Sent are not game-response claims. The status timer never dispatches input.

Standalone only: Ctrl+Alt+F8 status; Ctrl+Alt+P pause; Ctrl+Alt+Esc exit; Ctrl+Alt+T prepare in extended mode. Integration should use existing host controls instead, preserving its tray and shortcuts. F2/F8 are temporary intercepts, not new saved game/graphics bindings.

Prepared literal text is 1–4096 printable characters with no embedded control/newline/Tab. Enter/Escape are separate actions. Holds request 250–2000 ms on arrows/Backspace/WASD, optional repeated down events, one final release. Cancel on focus loss/pause/Stop; no forced-kill guarantee or true analog support. Unicode and raw-key transports need separate live checks. No socket/file command reader, shell runner, credential handling, keylog, launch automation, anti-cheat bypass or all-desktop target exists.

## Integration acceptance and rollback

Use [OTHER-CHAT-HANDOFF.txt](OTHER-CHAT-HANDOFF.txt) and the guide's acceptance list. Preserve the larger tool's exact source/settings, own hotkeys, input observer, explicit recording privacy, device/layer truth and existing profiles. Synthetic activity must not masquerade as physical device/layer evidence. Keep one helper-family instance; opt in only for the authorized test, stop afterward.

No real games were launched by the integration work. No saves, graphics values, physical profiles, interpreter installs or global Codex settings were changed. Rollback is host Cancel/Stop and removal of only optional wiring while closed. The exact v0.3.1 baseline remains available; do not silently replace the larger host with it.
