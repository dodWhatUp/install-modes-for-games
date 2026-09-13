# Cyberpunk 2077

**Prepared update, 2026-09-14:** [Unified OptiScaler controls](../examples/cyberpunk-2077/UnifiedControls/README.md) on NR v0.8.3 with production Streamline 2.14.1 / DLSS 310.9.1, SR L and RR F. Build/isolated checks passed. **Not installed:** Batman/Steam were running; the guarded installer made no game/driver changes. Live scale/MFG/NR verification remains pending. Monthly updates are active on the 14th at noon. The installed state below is the preceding revision.

**Latest change (2026-09-13, evening):** F11 now recalls four personal NR settings slots; Save Settings stores the selected slot. F8/Page Up/Page Down are unbound and the OptiScaler FPS overlay starts off. F7 retains its confirmed 25%/100% toggle. F6 notification calls were moved into CET's drawing event. NVIDIA App's disabled overlay was re-enabled and its FPS statistics appeared at Cyberpunk startup. See [history](cyberpunk-2077/HISTORY.md) for the test boundary.

Status: **Personal NR slots and F6 notification repair installed; build/export/C++/Lua tests passed; new build starts and evaluates NR. Interactive slot save/recall and F6 render-size verification pending**.

Supporting records:

- [History](cyberpunk-2077/HISTORY.md)
- [Preferences](cyberpunk-2077/PREFERENCES.md)
- [Mod catalog](cyberpunk-2077/MOD-CATALOG.md)
- [Curated recommendations](cyberpunk-2077/RECOMMENDATIONS.md)
- [Sanitized evidence](../evidence/CYBERPUNK-2077.txt)

## Current environment

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

## Installed ownership map

| Layer | Owner | Input source | Current evidence |
|---|---|---|---|
| SR/DLAA | Cyberpunk native DLSS via OptiScaler pass-through | Engine color/depth/motion/jitter/exposure | Native files unchanged; runtime pending |
| Ray Reconstruction | Cyberpunk native DLSSD | Engine RT/RR inputs | Native files unchanged; inactive while global RT is off |
| FG/MFG | Cyberpunk native Streamline/DLSSG | Engine depth/motion/UI/pacing | Latest saved native x4; driver Dynamic MFG override; actual interpolation needs verification. Installed OptiScaler FG disabled/external |
| Neural rendering | OptiScaler-DLSSNR 0.7.7 personal-slots build | Native temporal inputs | Creation/evaluation observed; interactive slot validation pending |
| HDR/tonemap | Cyberpunk native | Native swapchain/tonemap | Latest saved mode HDR10 PQ; original snapshot was SDR |
| Proxy/swapchain injection | OptiScaler `dxgi.dll` | D3D12 process-local hook | Current personal-slots build loaded and evaluated NR |
| Native quality hotkey | CET 1.37.1 `version.dll` + GraphicsHotkeys Lua | Cyberpunk native settings API; no separate SR/FG implementation | F6 bound; Lua and panel-protocol mock tests passed; engine/overlay compatibility untested |

## Directory layout

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
3. Open the full overlay with `Delete` or the compact neural window with `F12`, and confirm one neural pass becomes ready and evaluates repeatedly.
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
| F6 | Cycle native DLSS: DLAA → Quality → Balanced → Performance; also available beside NR settings in F12 |
| F9 | Native Quick Load, preserved |
| Insert | CET overlay (separate from both OptiScaler menus) |
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
