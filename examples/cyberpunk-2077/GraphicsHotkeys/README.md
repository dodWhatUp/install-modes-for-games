# Cyberpunk native DLSS quality controls

Local adapter for Cyberpunk **2.31** and [CET 1.37.1](https://github.com/maximegmd/CyberEngineTweaks/releases/tag/v1.37.1), updated 2026-09-13. **F6** cycles native DLAA → Quality → Balanced → Performance; Auto/unfamiliar modes start at Quality. The same control is beside NR settings in the F12 compact window of the [matching OptiScaler build](../../optiscaler-dlssnr/f7-two-scale/README.md).

F7 belongs to NR 25%/100%; F8 is now unbound, and F9 remains Quick Load. Insert opens CET; Delete opens full OptiScaler controls.

Latest repair: the user's game log recorded `Tried to call ImGui from invalid event!` when the adapter tried to notify from onUpdate. Notifications now queue and render only in onDraw, with the selected native mode and confirmation result. `sr-last-result.txt` preserves the most recent result for diagnosis. This fixes feedback delivery; actual render-target changes still require runtime verification.

Install `init.lua` under `bin/x64/plugins/cyber_engine_tweaks/mods/GraphicsHotkeys/`. Merge `bindings.json` into CET's bindings, preserving other mods. F6 is `117 << 48`; Insert is `45 << 48`. CET owns `version.dll`; OptiScaler owns `dxgi.dll`. File separation is not proof of runtime compatibility.

The key and panel request use one adapter. Changes queue for onUpdate, require a loaded player and native DLSS, and refuse to compete with active dynamic resolution. Requests have a two-second cooldown and are blocked by CET's overlay. Native values are confirmed and read back after 0.5 seconds; rejected/apply failures attempt to restore the previous setting.

The panel channel accepts only `cycle|timestamp` in `sr-request.txt`; `sr-status.txt` contains a native-mode heartbeat. Both files are inside this mod's directory. Requests are consumed once and discarded on initialization. Malformed requests or timestamps outside three seconds are ignored. No arbitrary commands/setting names are accepted. The panel does not change ratio overrides. Native readback still needs render-dimension verification in game.

No startup graphics changes, direct UserSettings edits or immediate disk-save requests. Native game behavior governs persistence. NR is separately saved with OptiScaler Save Settings. DRS/RT/RR/FG are not enabled by this adapter.

Lua mocks in `test.lua` pass cycle order, cooldown, guards, rejection/apply rollback, startup cleanup, panel consumption, stale/future/malformed rejection and native status. Run from the repository root with Lua/Lupa; tests use fake settings and an in-memory file channel. CET's source sandbox was inspected for the io/os APIs used. Actual CET loading, panel input, buffer recreation and NR/FG interaction remain untested.

For the personal-slots/notification revision, first use its private `Restore-PersonalControls.ps1 -Apply`. Then use `Restore-F7.ps1 -Game Cyberpunk` from the F7 snapshot, followed by older rollback scripts if required. Generated channel/status files are inert without this adapter and preserved for inspection.

The native-settings API pattern was checked against the author's [AdvancedPathTracing settings module](https://github.com/codecrafting-io/AdvancedPathTracingCP2077/blob/main/Modules/GameSettings.lua). That broader mod was not installed.
