# A Plague Tale: Requiem

**Latest change (2026-09-13):** the rebuilt `e237f89+f7-25-100` controls are installed: F7 = NR 25%/100%, F8 = placement. Native SR switching remains unavailable and is shown as such in the compact menu. Current build/export checks passed. The title-scene runtime evidence below applies to the preceding build; new F7 input is untested.

Status: **OptiScaler-DLSSNR installed; neural creation/evaluation and live resolution/placement changes confirmed in the animated title scene. Full gameplay validation pending.**

## Environment

- Steam build 11415435; window version 1.6.0.0 (20230706_1126).
- Real executable: `APlagueTaleRequiem_x64.exe`, x64, native DirectX 12.
- RTX 5070 Ti 16 GB, driver 616.56, Windows 11 build 26200; 3840×2160 output.
- Stock DLSS SR file 2.4.12, native FG 3.1.1, Streamline 1.5.4. These files were retained unchanged.
- OptiScaler reports effective DLSS 310.9; the on-disk native SR file remains 2.4.12. Do not conflate runtime-reported and file versions.
- First-run settings use Steam's per-app `remote/settings` and `remote/inputprofile` binary files. The Documents game folder was empty at installation.
- The title run supplied 1920×1080 render inputs to 3840×2160 SR, with engine depth/motion and linear HDR color. Linear HDR input does not establish display HDR output.
- Native FG capability is present; active FG delivery, display HDR mode, and gameplay quality settings remain unverified. Steam and NVIDIA overlays were loaded; no anti-cheat or pre-existing injection mod was found.

## Selected stack and ownership

The user explicitly chose OptiScaler with the community DLSS Neural Rendering extension and custom controls. [OptiScaler's compatibility list](https://github.com/optiscaler/OptiScaler/wiki/Compatibility-List) lists Requiem's DLSS input path. No Feeder is needed.

| Layer | Owner |
|---|---|
| Proxy | Custom OptiScaler-DLSSNR v0.7.7 as `dxgi.dll` |
| Temporal SR | Game DLSS contract through OptiScaler's DLSS backend |
| Neural rendering | One FP8 pass, signed NVIDIA 310.8 model, default before SR |
| FG | Native game path; OptiScaler external mode, internal FG disabled |
| HDR/tonemap | Original game path; no ReShade, RenoDX, or extra tonemapping |

Based on [v0.7.7](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/releases/tag/v0.7.7), commit `e237f895623742b761f9e5f00067cb3dc62619f4`, with the locally available compact/resolution/placement controls implementation. All 946 exported names/ordinals match the upstream release. See [configuration delta](../examples/a-plague-tale-requiem/Controls.ini) and [exact source patch](../examples/a-plague-tale-requiem/compact-resolution-placement-v077.patch).

## Controls

| Key | Function |
|---|---|
| Delete | Full OptiScaler menu |
| F12 | Compact Neural Rendering-only window |
| F11 | Cycle numeric NR model hints 0, 1, 2, 3 |
| F10 | Enable/disable NR |
| F7 | Toggle NR working scale 25% ↔ 100% only |
| F8 | Switch NR before/after SR |
| F6 | Unassigned; no verified engine-level live SR quality adapter |
| Page Up / Page Down | FPS overlay toggle / information mode |

F7 changes only the NR model's own dimensions. Before SR its base is the render input; after SR its base is the upscaled output. F8 at 50% was verified to move from a 960×540 pre-SR model to a 1920×1080 post-SR model, keeping the game at 1920×1080→3840×2160. Layout shortcuts have a one-second guard and can briefly pause while recreating the model.

F11 model hints have undocumented visual meaning. They do not cycle native DLSS Quality/Balanced/Performance, and do not bundle the F7/F8 values. **Save Settings** persists the current combination. Full and compact menus are mutually exclusive.

The separate live SR shortcut would need a Requiem-specific engine/menu integration that actually recreates its render targets. OptiScaler's ratio override only affects resolution queries; changing that value is not proof of an immediate engine resolution change. No memory patch or keyboard macro was installed to simulate this.

## Verification and limits

Stock first launch reached the animated title scene and exited normally. The modded title run created the DLSS and NR features, recorded readiness after submission, composition, repeated GPU timing, and successful model recreation after F9/F8. This proves a functioning neural path in that scene, not a full gameplay stability result.

Delete and F8–F12 were verified, including the full preset-hint cycle, NR off/on, mutually exclusive menus and closing the compact window. Mouse Save Settings persisted the tested default combination; default values serialize as `auto` and match this custom build's source defaults. Modded Alt+F4 released the feature and unloaded OptiScaler normally. After exit, all 22 original root files and 64 immutable mod files matched their recorded hashes.

Gameplay motion, HUD, native FG delivery, alt-tab/resolution recreation, output HDR, and long-run image quality still need testing. First-run telemetry selection was left to the user. No campaign save was created by the agent.

## Rollback

Private snapshot: `requiem-before-optiscaler-20260913-131853`. It preserves all original root files, Steam configuration and per-app settings, NVIDIA DRS state, hashes, and the added-file ownership manifest. The clean baseline remains separate from the installed state.

Exit Requiem and Steam. First run private `Restore-F7.ps1 -Game Requiem` from `f7-controls-20260913/before-f7-20260913-141908` to restore the previous custom DLL/INI. Then run the original snapshot's `Restore-Requiem.ps1`. It validates mod identities, preserves the current mod files/INI, and removes only the 65 added files. Original files and current user settings remain intact. `-WhatIf` passed. Raw snapshots and binaries stay outside publishable files.

See [history](a-plague-tale-requiem/HISTORY.md), [preferences](a-plague-tale-requiem/PREFERENCES.md), [catalog](a-plague-tale-requiem/MOD-CATALOG.md), and [recommendations](a-plague-tale-requiem/RECOMMENDATIONS.md).
