# Batman: Arkham Knight Mod Catalog

**Latest status, 2026-09-13 late evening:** ReShade + Luma + OptiScaler DLSS-NR now works in short local gameplay checks. The old Feeder stack remains disabled after startup crashes; stock fallback is preserved.

| Candidate | Purpose | Requirements/conflicts | Local state | Confidence |
|---|---|---|---|---|
| [Luma Batman, build 649](https://github.com/Filoppi/Luma-Framework/releases/tag/latest-649) | Engine motion/depth/color and jitter for DLAA | Exact Batman build; bundled ReShade; no Feeder; upstream WIP | Installed, alone and with OptiScaler NR tested in a loaded scene | High for input path; medium for short runtime, low for sustained play |
| [OptiScaler DLSS-NR](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass), custom v0.7.7 | D3D11-to-D3D12 DLAA + one NR consumer | Owns dxgi.dll; LoadReshade, Luma D3D12 workaround and shared-resource settings; no second NR owner | Installed, evaluated/composed real inputs; live controls passed | Medium for exact tested chain |
| Luma bundled ReShade 6.8.0.1 | Luma host | ReShade64.dll loaded by OptiScaler | Installed, addon registered and cleanly unregistered | High for loading; Home opening unverified |
| Signed NVIDIA SR/NR runtimes | DLAA reconstruction and neural inference | Package SR 310.6, actual cached SR 310.9; NR 310.8 and matching forwarder | Loaded/evaluated in game | High for runtime identity |
| DLSS FG/MFG via Streamline 2.14.1 | Generated frames | Current FP16/scRGB output is unsupported; requires another validated presentation path | Disabled, FG payload not installed | High for documented format restriction; Batman FG untested |
| RenoDX-derived NR consumer | Alternative neural owner | Would replace OptiScaler NR, not coexist as another consumer | Not installed; unnecessary for the working OptiScaler route | No Batman comparison |
| [120 fps mode](https://www.nexusmods.com/batmanarkhamknight/mods/3269) / direct MaxFPS edit | Raises cap to 120/144 or a chosen limit | INI-only; replacing author's whole file may overwrite unrelated settings | Local MaxFPS remains 90; no edit | High for setting existence; runtime untested |

**Current controls:** custom v0.7.7 supports the verified Delete/F12/F11/F10/F8/F7 actions; F6 remains unavailable. See [controls](CONTROLS.md). The following rows describe the older disabled Feeder profile.

Last reviewed: 2026-09-13. This was a targeted installation review, not a complete mod survey.

| Mod/tool | Category | Purpose | Requirements/conflicts | Local state | Confidence |
|---|---|---|---|---|---|
| [ReShade](https://reshade.me/) 6.8.0 | Framework/graphics | Add-on host and scene buffers | x64 full add-on build, owns dxgi.dll | Installed/static pass | High for installation |
| [DLSS5-Feeder](https://github.com/jlrouzies-fr/DLSS5-Feeder/releases/tag/v1.16.0-beta.1) | Graphics/input bridge | Synthetic DLAA contract for a game without DLSS | Working depth + one MV provider; exact supported neural consumer | Installed; isolated helper passed | Medium for chain, untested in game |
| [Dagherbou OptiScaler DLSS-NR](https://github.com/Dagherbou/OptiScaler_DLSSNR/releases/tag/v0.2.0-dlssnr) with local F9 patch | Neural graphics/controls | DLAA and NR consumer; cycle model dimensions | Signed runtimes; winmm.dll; no second neural consumer or competing FG | Installed; four 300/300 helper runs | Medium; game and keyboard input unverified |
| [LumeniteFX Kernel](https://github.com/umar-afzaal/LumeniteFX) | Motion estimation | Optical-flow vectors | Runs before Feed, provider 3 | Configured; game compilation pending | Medium |
| [Arkham Vision](https://www.nexusmods.com/batmanarkhamknight/mods/37) | Visual preset | Author's stylized NR/ReShade presentation | Author reports Feeder use and labels OptiScaler untested; its extra DX11 bridge advice conflicts with Feeder's current guidance | Not installed | Author report only |

## Other catalog categories

Performance/bug fixes, QoL/movement, UI/controls, gameplay, and cosmetic/audio mods were not researched or installed during this request. No expansion-scale mod was verified in this targeted review; this is not a claim that none exists.

## Historical Feeder compatibility groups (disabled)

- ReShade owns `dxgi.dll`; OptiScaler owns `winmm.dll`.
- Only OptiScaler DLSS-NR owns neural processing. No RenoDX/Chicken/extra DX11 bridge alongside it.
- Estimated motion is not engine-native object motion. Expect additional GPU/VRAM cost and possible HUD/motion artifacts until checked.
- No save format changes are intended; crashes can still interrupt a running game. Preserve saves and test safely.

## 2026-09-14 — Library comparison review

Added [categorized comparisons](COMPARISONS.md) covering manager/foundations, performance, graphics/DLSS, QoL/UI, animation, AI, abilities/mechanics and actual content extensions. No game files changed or new gameplay tests were performed by this review. Earlier local evidence remains stronger than generic recommendations; historical control mappings and unresolved validation boundaries are preserved. See the [14-game guide](../../docs/INSTALLED-GAMES-MOD-GUIDE.md) for scope and installed-library checks.
