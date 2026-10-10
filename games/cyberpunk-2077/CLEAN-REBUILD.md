# Cyberpunk 2077 — Clean rebuild, 2026-10-10

Current configuration: the user selected removal of the prior mods and a fresh **ReShade + game-specific RenoDX HDR + restrained Ultra+** installation, following the supplied research text. Installation verification and short runtime layer/combined benchmarks passed; longer gameplay, frame pacing and latency remain incomplete. See [runtime evidence](RUNTIME-VALIDATION.md). This supersedes the older FrameWarp, modular controller and OptiScaler descriptions.

## Installed files and ownership

| Component | Version | Ownership / dependency |
|---|---|---|
| [ReShade full add-on](https://reshade.me/) | 6.8.0 | Sole `bin/x64/dxgi.dll` owner; hosts RenoDX |
| [RenoDX Cyberpunk HDR](https://github.com/clshortfuse/renodx/releases/tag/nightly-20261009) | nightly-20261009 | Sole `renodx-cp2077.addon64`; game-specific shader/HDR profile |
| [Ultra+ X](https://www.nexusmods.com/cyberpunk2077/mods/10490?tab=files) | 10.0.0 rc7 | `UltraPlus` CET mod, `UltraTool` RED4ext plugin, engine memory configuration and lighting `.xl` |
| [CET](https://github.com/maximegmd/CyberEngineTweaks/releases/tag/v1.37.1) | 1.37.1 | `version.dll`, ASI/resources; hosts Ultra+ and GraphicsHotkeys |
| [RED4ext](https://github.com/wopss/RED4ext/releases/tag/v1.30.0) | 1.30.0 | `winmm.dll` and RED4ext; hosts UltraTool, ArchiveXL and AudioPoolFix |
| [ArchiveXL](https://github.com/psiberx/cp2077-archive-xl/releases/tag/v1.27.4) / [redscript](https://github.com/jac3km4/redscript/releases/tag/v0.5.31) | 1.27.4 / 0.5.31 | Required support for the included lighting `.xl`; no unrelated gameplay scripts |
| [AudioPoolFix](https://www.nexusmods.com/cyberpunk2077/mods/34270?tab=files) | 1.0.2 | Ultra+ X dependency; explicitly targets game 2.31 |
| [GraphicsHotkeys](../../examples/cyberpunk-2077/GraphicsHotkeys/README.md) | Existing F9 revision | Reuses CET to control the game's native DLSS settings |
| Cyberpunk native NVIDIA files | DLSS 310.1 / Streamline 2.7.1 | Eleven original, NVIDIA-signed files restored as a coherent baseline; native FG remains the sole FG implementation |

Removed from the live game: OptiScaler/NR and its backend/forwarder, FrameWarp/presenter, DisplayCommander remnants, duplicate ReShade host, Lilium effects, old Ultra+ 9.3.7, Better Loot Markers, Real Vendor Names and old generated mod-script cache. Prior files remain in private snapshots/quarantine. Vortex's six old packages are disabled, with their staging originals preserved. RHI and UltraPlusManager remain available for other games; only Cyberpunk ownership records were reconciled. The new payload is recorded by a private per-file deployment manifest.

## Starting profile

- Ultra+: **Advanced → PT21 → Fast**, **Vanilla streaming**, **NRD with DLSS** denoiser matching saved RR off. Automatic quality, automatic menu confirmation and graphics-menu overrides are off. Extended draw distance/fog, mesh LODs and Virtual Photography are off. Memory configuration uses stock visibility distances and a restrained decompression allocation.
- The PT21 profile is a path-tracing tuning choice. It can be expensive relative to raster rendering; no measured FPS or VRAM improvement is claimed. RC7 is a release candidate. Its advertised High/Insane streaming memory reduction is not a measured benefit of this Fast/Vanilla profile.
- Saved native settings retained: 3840×2160 borderless, HDR10 PQ, saturation 0, midpoint 2, DLSS Ultra Performance/Legacy preset, RR off, global RT off, native FG x2, dynamic resolution off. Ultra+ may apply its engine tuning on launch; the saved RT flag does not prove the resulting runtime state.
- Runtime correction: seeded native `RayTracedPathTracing=true` before launching the already-selected PT21 profile. This single graphics-value change kept RR off and NRD DLSS through restart/confirmation/benchmark. Starting PT false allowed a transition to RR true/RR Clean; an immediate console RR-off read did not persist. Keep the original PT-off settings recovery point. The author PT21 mode deliberately leaves conventional `RayTracing=false`.
- RenoDX starts with the author's defaults. No additional cosmetic ReShade effects were installed. Verify Windows HDR and the display peak/paper-white calibration. Per-game Auto HDR/RTX HDR conversion should be off for the chosen native HDR + RenoDX path; global/per-game driver overrides were not changed or revalidated here.
- **If enabling RR later:** native 310.1 is below the Ultra+ RR Clean/Sharp requirement (310.6+). Select **Vanilla denoiser** in Ultra+ Advanced and recheck after RR transitions. A newer coherent runtime set requires a separate compatibility review.
- Dynamic SR stays off. The saved 30-FPS DRS target is inactive; there is no newly enabled FPS cap, Dynamic SR controller or NR consumer.

## In-game shortcuts

The DLLs and Ultra+ load with the game. These keys open controls or change a supported setting; they do not install/unload a DLL.

| Key | Action |
|---|---|
| **Delete** | Open/close ReShade; select the direct **RenoDX** tab for HDR controls; physically verified |
| **Grave/tilde (` / ~)** | Open/close CET and the Ultra+ window; `VK_OEM_3`, no Shift required |
| **F9** | Cycle native DLSS **DLAA → Quality → Balanced → Performance**; close CET first and load gameplay with DLSS selected |
| **F5** | Native Quick Save |
| **F6** | Native Quick Load; recovered from saved F9 to avoid the DLSS-control collision |

The saved Ultra Performance mode is outside the four-mode F9 cycle; the first press selects Quality. Allow the adapter's two-second cooldown. F9 refuses fixed-quality changes while native dynamic resolution is on. Home and old NR controls F7/F10/F11/F12 are unavailable with their consumers removed. F8/Page Up/Page Down remain unbound. Configuration readback is verified; actual input handling and engine-resolution recreation still require gameplay validation. No device firmware, Azeron/reWASD profile or Steam Input layout was altered.

## Evidence and next test

Final static verification passed: **133 deployed paths**, all **11 native NVIDIA signatures**, exactly one RenoDX add-on, RED4ext plugins `ArchiveXL/AudioPoolFix/UltraTool`, and CET mods `GraphicsHotkeys/UltraPlus`. All **224 captured save/stock files** compared byte-identical. Only `quickLoad.value` in UserSettings changed from `IK_F9` to `IK_F6`; reversing that one value reproduces the exact pre-change file hash. All other saved graphics settings and input defaults are preserved.

Subsequent user-authorized runtime checks supersede the installation-only handoff: stock/HDR/Ultra/full benchmarks completed at 148.53/149.46/149.60/148.68 average game-reported FPS. Stock/HDR use PT off; Ultra/full use PT21, so this is not a matched PT speedup comparison. RenoDX exposure visibly changed output and was reset, and CET/Ultra+ opened/closed. Combined adapter use peaked at 14228 MiB in the resource capture; individual frame lows, FG delivery classes and latency are not measured yet. Loaded-save controls and final restoration remain in progress in [runtime validation](RUNTIME-VALIDATION.md). An overlay alone does not prove rendering or presentation. Preserve a new snapshot before any closed-game layer change, and stop an unstable test before saving.

## Recovery

Private workspace contains `CLEAN-REBUILD.md`, staging `clean-rebuild-20261010`, install/verification receipts, deployment hashes and the guarded `Restore-PreviousStack.ps1` script. Running that script without switches only previews the rollback; `-Apply` snapshots the then-current state, quarantines the newly owned files, restores the affected originals from `before-clean-rebuild-20261010-033605`, and merges only Cyberpunk RHI/UltraPlusManager records. Saves and current UserSettings are preserved. Vortex's old packages remain disabled; its whole database is not replaced. Preview/source hashes were checked; actual rollback was not executed.

Snapshot `before-clean-rebuild-20261010-033954` preserves the state immediately before file replacement; `before-quickload-f6-20261010-034403` preserves the native keybinding edit. Older known-good baselines remain separate. Restoring the pre-rebuild state returns to its recorded incomplete/conflicting stack, not a proven stable configuration.

Old `Manage-Cyberpunk.ps1` and `FrameWarp-Control.ps1` now stop with a guide pointer. Their old shortcuts cannot switch this new stack. Do not re-enable old Vortex frameworks/Ultra+ over the manually deployed copies. Do not use the historical RHI OptiScaler install/update/uninstall path: its shared-folder/native-DLL ownership failures are recorded in [History](HISTORY.md).
