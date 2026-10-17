# Cyberpunk 2077

**Latest inspection, 2026-10-14:** ReShade/RenoDX/Ultra+ remains installed and OptiScaler/NR remains absent. Installed DLSS SR/RR/FG is already **310.9.1**, with Streamline **2.7.1**; all eleven NVIDIA signatures are valid and the three DLSS files match the verified official production SDK. Saved RR is now on; Ultra+ records PT21, Auto quality/streaming, RR Clean and auto quality targeting 30. These intervening changes were observed, not installed or runtime-validated by the monthly task. Steam was running, so no game files/settings were changed. The monthly automation now follows the current stack and cannot revive the removed NR package. See the [October 14 audit](cyberpunk-2077/HISTORY.md#2026-10-14--monthly-audit-reconciled-with-the-current-nativereshade-stack) for scope and uncertainty. The dated receipts below describe their original checkpoints.

**Current saved state, 2026-10-11 (stack last verified 2026-10-10):** the user-selected clean rebuild is installed: **ReShade 6.8.0 full add-on + Cyberpunk RenoDX nightly-20261009 + Ultra+ X 10.0.0 rc7**, with only the required CET/RED4ext/redscript/ArchiveXL/AudioPoolFix foundations and the existing F9 native-DLSS adapter. After a report of very low performance, the saved Ultra+ profile was restored to the previously measured Advanced/PT21/Fast, Vanilla streaming, NRD-DLSS configuration; native path tracing is on and conventional ray tracing is off. The saved DLSS Ultra Performance/Legacy, native FG x2, 4K HDR10 PQ and DRS-off choices were retained. The edit is statically verified; the next game launch and current performance are not yet validated. OptiScaler/NR, FrameWarp, old visual/QoL mods and duplicate hooks remain absent. Native DLSS 310.1/Streamline 2.7.1 remains in place. The prior combined run reported 148.68 game-reported average FPS and 14228 MiB peak adapter use; it did not separate base/generated frames, and the run's effective fixed-x2 versus Dynamic MFG mode is unknown. See [current guide and recovery](cyberpunk-2077/CLEAN-REBUILD.md), [runtime evidence](cyberpunk-2077/RUNTIME-VALIDATION.md) and [restore history](cyberpunk-2077/HISTORY.md).

**Current controls, statically configured 2026-10-11:** F12 is configured for the CET/Ultra+ overlay; Delete opens ReShade → Add-ons → RenoDX; Home is the user-wide OptiScaler menu default, but OptiScaler is not installed in Cyberpunk. F9 cycles native DLSS quality with CET closed; F5 Quick Save and F6 Quick Load. The CET F12 binding was read back after a just-in-time snapshot; runtime key response remains untested. Old NR shortcuts and private FrameWarp/graphics switch scripts are inactive.

**Current environment:** Cyberpunk 2.31 / Steam build `20383525`, Phantom Liberty, x64 D3D12, RTX 5070 Ti 16 GB, driver 617.42. Saved profile is 4K borderless HDR10 PQ, saturation 0, DLSS Ultra Performance/Legacy, native path tracing on, RR off in the measured run, conventional RT off, native FG x2 and DRS off. Ultra+ runtime effects and per-game driver HDR overrides need validation after settings restoration. Earlier records below are historical and do not describe the current file ownership.

**Historical state, 2026-10-07:** native-only DLSS restoration was preserved; experimental [FrameWarp/XPAR 1.8.5](cyberpunk-2077/FRAMEWARP.md) was added with ReShade 6.8.0 as its host. That experiment was removed by the October 10 rebuild.

**RHI recovery, 2026-09-22:** RHI's OptiScaler install/update path recursively removed Cyberpunk's shared `bin/x64/plugins` tree, deleting CET, GraphicsHotkeys, Ultra+ and Better Loot Markers, while also replacing the protected proxy/native NVIDIA runtime set and removing RenoDX. The complete RHI attempt was preserved, the verified personal-slots 0.7.7 host/native runtimes/CET/Vortex payload/RenoDX stack was restored, and ReShade/Lilium settings were preserved byte-for-byte. RHI still tracks Cyberpunk ReShade/RenoDX but no longer claims its OptiScaler host; do not use RHI to install, update or uninstall OptiScaler for this profile until its shared-folder cleanup is fixed. CET now opens with the grave/tilde (` / ~) key instead of Insert. Static verification passed; user runtime validation is pending.

**Modular installation, 2026-09-20:** Vortex 2.6.3/Cyberpunk support 0.13.0 manages RED4ext 1.30.0, redscript 0.5.31, ArchiveXL 1.27.3, Ultra+ 9.3.7, Better Loot Markers 1.4.0 and Real Vendor Names 2.1.0. ReShade 6.8.0 and the Cyberpunk RenoDX visual profile are installed through the existing OptiScaler plugin route with independent file toggles. Per-layer hashes/snapshots and a selective graphics rollback test passed; combined gameplay remains untested. RHI 2.7.5 manual installation is pending after automatic installer execution was blocked; .NET 8.0.31 is installed. See [modular setup](cyberpunk-2077/MODULAR-SETUP.md) and [history](cyberpunk-2077/HISTORY.md). The existing host/native runtimes and controls remain protected; the update hold below remains in force.

**Monthly check, 2026-09-15:** NR v0.8.4 prerelease downloaded/checksum-verified and custom source port staged. **Installation held:** the prepared dynamic controls fail the newer FG/manual-resolution restoration requirements, and engine integration is unverified. The game/store are closed; process availability is no longer the blocker. Current installed v0.7.7/F9 setup remains unchanged. See [readiness](../examples/cyberpunk-2077/UnifiedControls/UPDATE-READINESS.md).

**Current shortcut override, 2026-09-14:** the user changed Quick Load to **F6**; Quick Save remains **F5**. The existing native DLSS quality shortcut is now **F9**, configured and read back in CET with its Lua labels updated. Other graphics keys are unchanged. This supersedes earlier F6/Quick Load descriptions below. The next user-initiated launch loads this binding; live F9 validation remains pending. See [history](cyberpunk-2077/HISTORY.md).

**Historical Dynamic SR extension, 2026-09-14:** the uninstalled OptiScaler/CET candidate includes a **30 rendered FPS** Dynamic DLSS target and 50–100% bounds through native DRS. The candidate uses F12, which the current CET/Ultra+ profile owns; do not co-install until its menu key is changed. Actual dynamic input sizes and NR/FG stability remain unverified.

**Prepared update, 2026-09-14:** [Unified OptiScaler controls](../examples/cyberpunk-2077/UnifiedControls/README.md) on NR v0.8.3 with production Streamline 2.14.1 / DLSS 310.9.1, SR L and RR F. Build/isolated checks passed. **Not installed:** Batman/Steam were running; the guarded installer made no game/driver changes. Live scale/MFG/NR verification remains pending. Monthly updates are active on the 14th at noon. The installed state below is the preceding revision.

**Latest change (2026-09-13, evening):** F11 now recalls four personal NR settings slots; Save Settings stores the selected slot. F8/Page Up/Page Down are unbound and the OptiScaler FPS overlay starts off. F7 retains its confirmed 25%/100% toggle. F6 notification calls were moved into CET's drawing event. NVIDIA App's disabled overlay was re-enabled and its FPS statistics appeared at Cyberpunk startup. See [history](cyberpunk-2077/HISTORY.md) for the test boundary.

Historical September status: **Personal NR slots and F6 notification repair were installed; build/export/C++/Lua checks passed. Those consumers are absent after the October 10 rebuild**.

Supporting records:

- [History](cyberpunk-2077/HISTORY.md)
- [Preferences](cyberpunk-2077/PREFERENCES.md)
- [Mod catalog](cyberpunk-2077/MOD-CATALOG.md)
- [Curated recommendations](cyberpunk-2077/RECOMMENDATIONS.md)
- [Sanitized evidence](../evidence/CYBERPUNK-2077.txt)

## Historical environment — September 2026

Evening snapshot supersedes the original graphics settings below: native DLSS **Performance**, saved native MFG **x4**, native **HDR10 PQ**, and native DRS off. NVIDIA App **11.0.9.251** shows a per-game **Dynamic MFG, up to 6x** override, native SR override set to use the game setting, Smooth Motion off, and global RTX HDR on. These are observed settings, not proof of every path being active. The repair did not change the game's native graphics options or driver overrides.

- Cyberpunk 2077 2.31, Steam build `20383525`, Phantom Liberty installed
- Real executable: `bin\x64\Cyberpunk2077.exe`
- 64-bit Direct3D 12; single-player game without an anti-cheat path in this setup
- NVIDIA GeForce RTX 5070 Ti 16 GB, driver 616.56
- Windows build 26200
- 3840×2160 borderless; HDR disabled in the captured game profile
- DLSS Transformer/Auto selected, Ray Reconstruction enabled in configuration, native DLSS Frame Generation x2 selected, Reflex enabled
- Native DLSS SR/RR/FG runtimes 310.1 and Streamline 2.7.1 left untouched

The captured configuration had the global ray-tracing switch off even though path tracing and RR sub-options were saved as enabled. Those sub-options are not evidence that RT/RR was active in the last scene.

## Historical installed ownership map — September 2026

| Layer | Owner | Input source | Current evidence |
|---|---|---|---|
| SR/DLAA | Cyberpunk native DLSS via OptiScaler pass-through | Engine color/depth/motion/jitter/exposure | Native files unchanged; runtime pending |
| Ray Reconstruction | Cyberpunk native DLSSD | Engine RT/RR inputs | Native files unchanged; inactive while global RT is off |
| FG/MFG | Cyberpunk native Streamline/DLSSG | Engine depth/motion/UI/pacing | Latest saved native x4; driver Dynamic MFG override; actual interpolation needs verification. Installed OptiScaler FG disabled/external |
| Neural rendering | OptiScaler-DLSSNR 0.7.7 personal-slots build | Native temporal inputs | Creation/evaluation observed; interactive slot validation pending |
| HDR/tonemap | Cyberpunk native | Native swapchain/tonemap | Latest saved mode HDR10 PQ; original snapshot was SDR |
| Proxy/swapchain injection | OptiScaler `dxgi.dll` | D3D12 process-local hook | Current personal-slots build loaded and evaluated NR |
| Native quality hotkey | CET 1.37.1 `version.dll` + GraphicsHotkeys Lua | Cyberpunk native settings API; no separate SR/FG implementation | F6 bound; Lua and panel-protocol mock tests passed; engine/overlay compatibility untested |

## Historical directory layout — September 2026

```text
<Steam>\steamapps\common\Cyberpunk 2077\bin\x64\
├─ Cyberpunk2077.exe
├─ dxgi.dll                    # OptiScaler-DLSSNR 0.7.7 + extended controls
├─ OptiScaler.ini              # conservative Cyberpunk profile
├─ version.dll                 # CET 1.37.1 loader; does not replace dxgi
├─ global.ini                  # official CET loader configuration
├─ plugins\cyber_engine_tweaks.asi
├─ plugins\cyber_engine_tweaks\ # CET resources/config/bindings + GraphicsHotkeys
├─ nvngx.dll_dlssnr.dll        # open-source forwarder from the release
├─ nvngx_dlssnr.dll            # NVIDIA-signed 310.8 RTX 50 runtime
├─ OptiScaler\                 # complete release backend folder
├─ Remove_OptiScaler.bat       # upstream-generated partial uninstaller
├─ nvngx_dlss.dll              # native Cyberpunk SR, unchanged
├─ nvngx_dlssd.dll             # native Cyberpunk RR, unchanged
└─ nvngx_dlssg.dll             # native Cyberpunk FG/MFG, unchanged
```

## Why this path was selected

Cyberpunk already supplies native DLSS temporal inputs, RR, and RTX 50 MFG. It therefore does not need DLSS5-Feeder or estimated ReShade motion vectors. The selected fork adds one experimental neural-rendering consumer while preserving the game's richer native SR/RR/FG contracts and assigning only one owner to frame generation.

The current upstream Cyberpunk compatibility entry accepts a `dxgi.dll` proxy. The DLSSNR fork also warns that a `d3d12.dll` proxy can disable Cyberpunk's RR option. `dxgi.dll` was absent before installation, while the documented `dbghelp.dll` alternative would collide with a stock game file on this installation.

## Installed conservative configuration

See the reusable minimal delta at [OptiScaler-DLSSNR-conservative.ini](../examples/cyberpunk-2077/OptiScaler-DLSSNR-conservative.ini).

```ini
[Upscalers]
Dx12Upscaler=dlss

[FrameGen]
External=true
Enabled=false
FGInput=nofg
FGOutput=nofg
FGNvngxReplacement=None

[ProcessFilter]
TargetProcessName=Cyberpunk2077.exe

[DlssNr]
Precision=0
Enabled=true
RunBeforeSR=true
FinishedPicture=false
DeferredDLSS=false
ResidualAcrossRR=false
ResidualFG=false
Passes=1
WorkingScale=1.0
AutoCapture=false
```

This begins with one FP8 pass before SR at the game's active DLSS input resolution. Finished-picture placement, multipass, residual-across-RR, residual FG, OptiScaler FG, and automatic captures remain off to keep the first runtime boundary attributable and reduce cost.

## Verification boundary

Static installation is not proof that DLSS Neural Rendering evaluates. The next test must:

1. Start Cyberpunk and load a repeatable moving gameplay scene, not only the settings menu.
2. Confirm `OptiScaler.log` names `Cyberpunk2077.exe`, `dxgi.dll`, the RTX 5070 Ti, and the expected native DLSS paths.
3. In this archived, uninstalled NR candidate, open the full OptiScaler menu with `Home` or the compact window with `F12` only in a game without Ultra+; confirm one neural pass becomes ready and evaluates repeatedly.
4. Compare the same scene with NR on/off without rapidly toggling while native FG is active.
5. Record base rendered FPS separately from displayed x2 FG FPS, frame pacing, latency, VRAM, HUD/motion artifacts, loading, alt-tab, and shutdown.
6. Test native FG off before investigating an NR/FG crash. Test RT/RR only as a later, separate setting group because global RT was off in the captured baseline.

The original fork has community reports of Cyberpunk device removal when NR or render scale is repeatedly toggled while native FG is active. Leave the saved conservative settings stable during the first run.

## Custom controls installed 2026-09-13

| Key | Action |
|---|---|
| Delete | Open/close the full OptiScaler menu |
| F12 | Open/close a small DLSS Neural Rendering window with a native DLSS SR control |
| F11 | Cycle model preset hints 0 → 1 → 2 → 3 → 0, with a notification |
| F10 | Enable/disable Neural Rendering, with a notification |
| F7 | Toggle NR working scale 25% ↔ 100% only |
| F8 | Request NR before/after SR, or combined RR+SR when active |
| F9 | Cycle native DLSS: DLAA → Quality → Balanced → Performance; also available beside NR settings in F12 |
| F6 | Native Quick Load, selected by the user on 2026-09-14 |
| Grave / tilde (` / ~) | Historical CET overlay key for the September 2026 NR-era configuration (`VK_OEM_3`) |
| Page Up | Show/hide the FPS overlay |
| Page Down | Cycle information modes while the FPS overlay is visible |

The compact window offers NR on/off, numeric model preset, style, intensity, working scale, before-SR placement, pass count, and **Save Settings**. OptiScaler changes remain session settings until saved. F7 scales NR dimensions, not screen resolution; F8 refuses to override active Finished Picture/Deferred DLSS experiments. F8/F7 have a one-second debounce. Numeric F11 presets remain undocumented model hints, distinct from F6's native SR quality modes.

This uses the local source patch on upstream v0.7.7 commit `e237f895623742b761f9e5f00067cb3dc62619f4`, build stamp `e237f89+f7-25-100`. The current proxy SHA-256 is `298D93C3D648330E279B614FC4B822FE38D87EC33516EFED90537664E9E9A090`. All 946 export names and ordinals match the preceding build, which matched the original release. See the [reusable controls and source patch](../examples/optiscaler-dlssnr/README.md).

F6 is supplied by the approved, narrowly scoped [GraphicsHotkeys CET adapter](../examples/cyberpunk-2077/GraphicsHotkeys/README.md). It has a two-second cooldown, checks the active upscaler/player, and attempts rollback if the native API rejects or fails to apply a change. It makes no startup graphics changes and does not force a disk save. CET's optional graphics/gameplay patches are off. File ownership and mock behavior are verified; actual key handling, native buffer recreation, and the CET/OptiScaler overlay combination still require a gameplay test.

A log from the original proxy's earlier run, discovered during this update, records neural feature creation, readiness, composition, and GPU timing at a 1920×1080 model/input size. This is partial runtime evidence for the original install, not validation of the custom hotkeys or a complete stability/visual-quality test.

## Rollback

1. Stop Cyberpunk and `REDprelauncher`.
2. First run the current private `Restore-F7.ps1 -Game Cyberpunk` from `f7-controls-20260913/before-f7-20260913-141908`. It restores the preceding DLL/INI/Lua/bindings and preserves the current files. Then undo the earlier F7–F9 with `restore-f7-f9.ps1` from private snapshot `cyberpunk-before-f7-f9-20260913-131843`. It validates ownership, preserves the current DLL/INI, quarantines the 22 added CET files, and restores the compact-only pair. No native/Steam settings are restored by that script. To undo the earlier compact controls too, exit Steam and run `restore-compact-controls.ps1` from `cyberpunk-before-compact-controls-20260913-123542`. For full removal, then use the original installation snapshot's guarded restore script. Follow this order because the older scripts expect their exact preceding hashes.
3. If using the upstream remover instead, also remove the separately supplied `nvngx_dlssnr.dll`, `nvngx.dll_dlssnr.dll`, release documentation/redist files, and any leftover log only after checking the ownership manifest; the generated remover does not cover every release file.
4. Do not replace the native `nvngx_dlss.dll`, `nvngx_dlssd.dll`, `nvngx_dlssg.dll`, or `sl.*.dll`; this installation did not modify them.
5. Restore `UserSettings.json` only if a later game run changed settings that should be reverted, then verify files in Steam and launch stock.
