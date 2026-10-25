# Default controls for graphics add-on installations

Follow the current [general preferences](../preferences/GENERAL.md). The 2026-10-11 F12 owner is the game-specific engine integration interface selected for the stack; Ultra+ shares that interface when hosted there. ReShade uses Delete and OptiScaler uses Home. The 2026-09-13 request changes NR model resolution to **F7: 25% ↔ 100% only**. Earlier F9 cycles are historical.

For requested installs, bind a supported game-specific engine integration's dedicated menu/interface to F12. When Ultra+ is served through that interface (as Cyberpunk uses CET), F12 opens the one shared interface; never bind a second F12 menu. Check game/mod conflicts and record unavailable actions or explicit game-specific exceptions.

| Key | Meaning |
|---|---|
| Delete | ReShade overlay/menu, including ReShade-hosted add-on panels |
| Home | Full OptiScaler menu |
| F12 | Game-specific engine integration menu/interface; Ultra+ shares this interface when hosted there (e.g. Cyberpunk CET) |
| F11 | Personal NR settings slots 0–3; Save Settings saves the selected slot |
| F10 | NR on/off |
| F8 | Unbound by user request |
| F7 | NR model dimensions 25%/100% only |
| F6 | Live native DLSS quality where an engine adapter exists |
| Page Up / Page Down | Unbound; use NVIDIA statistics instead |

When neither Ultra+ nor a game-specific engine interface is used, preserve existing game-specific F12 actions only after checking for conflicts; the selected integration interface owns F12 otherwise.

F7 is explicitly user-selected. F6 is the general implementation choice for separate SR. Cyberpunk has a [game-specific override](../games/cyberpunk-2077/PREFERENCES.md): on 2026-09-14 the user moved Quick Load to F6, so the native DLSS quality shortcut moved to F9. Preserve native game bindings and current game-specific exceptions. Do not bind the same action in two components.

**Dynamic SR default, 2026-09-14:** target 30 real rendered FPS only when native or mod-provided FG/MFG is supported and enabled and the engine SR controller is verified. With FG off/unavailable, use fixed/manual DLSS SR. Put an explicit dynamic On/Off control, target/bounds and manual quality/render-scale controls in the existing panel. Turning dynamic mode off restores the saved manual setting; choosing manual quality/scale or its game-specific shortcut exits dynamic mode. Keep DLSS enabled and preserve the user's manual override until explicitly changed. This controls internal DLSS render resolution, not NR scale, display resolution or a hard FPS cap. Validate FG transitions and persistence using [Dynamic DLSS SR](DYNAMIC-DLSS-SR.md).

During a requested installation or controls update:

1. Identify the owner for Ultra+, ReShade, OptiScaler, NR scale, placement and native SR. Bind the selected game-specific engine interface to F12; in Cyberpunk set CET `overlay_key` to F12 when Ultra+ is present. Set ReShade `[INPUT] KeyOverlay=46,0,0,0` and OptiScaler `[Menu] ShortcutKey=0x24`; preserve separate owners. Do not assign F12 to a second menu when the integration interface or Ultra+ is present. A changed NR model size is not a changed game render resolution. Percentages describe each image dimension: 25% × 25% is 6.25% of the NR pixels.
2. Configure existing runtime settings, or extend the exact compatible source build. Changing an INI key cannot replace a hard-coded multi-step cycle. Preserve focus/key-release handling, notifications and a cooldown for model recreation.
3. Leave F8/Page Up/Page Down unbound. Bind F6 only where the game adapter applies a real native quality setting. OptiScaler resolution-query overrides alone do not force engine render-target recreation.
4. Put the native SR control beside NR settings when a supported adapter can receive a request. Display unsupported status otherwise. Do not install Cyberpunk's CET adapter into other games.
5. Snapshot files and external settings immediately before mutation, preserve known-good baselines, and install with the game/launcher/helpers stopped. Record new hashes and the first rollback step.
6. Save NR selections through OptiScaler **Save Settings** into the selected personal settings slot. Keep model hints separate from slot numbers. Validate independent slots and restart persistence; do not claim ordinary upstream Save Settings already supplies this behavior. Native settings remain under game ownership. ReShade preset saving does not save another add-on's state.
7. Report compilation, helper evaluation, input testing and gameplay evidence separately. Runtime validation checks actual dimensions, recreation, UI/motion, FG interaction and persistence.

Cyberpunk now has a [personal-settings-slot revision](../examples/optiscaler-dlssnr/personal-slots/README.md) over the earlier [F7 patches](../examples/optiscaler-dlssnr/f7-two-scale/README.md). The 2026-10-07 full-menu migration is recorded below; all other control behavior retains its game-specific evidence and verification boundary. Each game retains its own consumer; no DLL is universal.

## 2026-10-07 installed-configuration migration

With the affected games/helpers closed, a private just-in-time snapshot preserved all changed INIs, hashes, Steam library metadata and relevant manifests. ReShade was changed from Home to Delete for Skyrim Special Edition, both Bayonetta processes and Batman: Arkham Knight, plus residual Witcher 3 and Devil May Cry 5 folders. OptiScaler was changed to Home for A Plague Tale: Requiem, Path of Exile 2 and Batman: Arkham Knight, plus the residual Hogwarts Legacy folder. Cyberpunk 2077 was running and not mutated; its current ReShade configuration already used Delete and no current OptiScaler INI existed. Static readback passed; no game was launched for runtime hotkey verification.

## 2026-10-18 persistent OptiScaler Home setting

The user explicitly requested Home permanently. On the current destination, Cyberpunk's pre-existing F5 v0.1.32 INI used Insert and RHI's global OptiScaler setting also used Insert. With the game closed and a private snapshot preserved, the installed INI was changed to `[Menu] ShortcutKey=0x24`, and RHI Settings > Component Settings > OptiScaler was changed to Home (`OsHotkey=Home`). Global manager defaults must be reconciled as well as per-game files, because later INI deployment can reapply the manager's key. Original package templates and preserved source masters were not edited. Static readback passed; live in-game input remains untested. The comparison/install task stays deferred.

## 2026-10-11 Ultra+ mapping audit

The recorded installations already use ReShade Delete and OptiScaler Home where those components are present. The October 7 audit found the full OptiScaler menu on Home in existing profiles; compact OptiScaler controls remain on F12 in Requiem and Batman because neither has Ultra+. Skyrim's separate PureDark F12 binding is also preserved. Cyberpunk has ReShade 6.8.0, RenoDX, CET and Ultra+ X: after the user closed the game, I snapshotted CET `bindings.json` and changed `cet.overlay_key` from grave/tilde (`54043195528445952`) to F12 (`34621422135410688`). Its F9 DLSS shortcut is unchanged. Installed ReShade remains Delete. RenoDX `bin/x64/renodx-cp2077.addon64` was present (2,856,960 bytes; SHA-256 `4FE58B9500A9F065FDE4FF64BEB2F48B6C63FFDA3D9AFEC089F02B5ACA6D6620`), so no duplicate HDR payload was added. Configuration was read back; live input was not tested.
