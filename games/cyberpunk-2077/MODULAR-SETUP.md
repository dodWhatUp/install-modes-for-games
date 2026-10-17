# Cyberpunk 2077 — Modular Setup and Quick Tests

**Historical install guide; superseded by the 2026-10-10 clean rebuild and 2026-10-11 F12 mapping update:** the active installation is the [clean ReShade/RenoDX/Ultra+ rebuild](CLEAN-REBUILD.md). Vortex's six old packages are disabled; the fresh required framework/Ultra+ files have a private manual deployment manifest. ReShade owns `dxgi.dll` directly. The old two-file controller and FrameWarp switch scripts are deliberately stopped because they address the removed stack. The September instructions below are historical; do not use them to redeploy old packages over current files.

Deployment checkpoint: 2026-09-20. The framework, Ultra+, QoL and separate ReShade/RenoDX packages below have been deployed and their files verified. RHI installation remains pending. No game launch or runtime test has been performed; the user will do the final tests. Read [History](HISTORY.md) for subsequent results and the [catalog](MOD-CATALOG.md) for source/version notes.

The aim is to change one mod without undoing unrelated mods. Each component has an explicit file list, source, version, hashes, dependencies and a before/after snapshot. Downloads and binary recovery copies stay in private storage; this repository holds only sanitized instructions and tools.

## What is ready at this checkpoint

| Component | State | What it adds |
|---|---|---|
| Vortex 2.6.3 / Cyberpunk extension 0.13 | Installed and configured for hardlink deployment | Package enable/disable and deployment |
| RED4ext 1.30.0 | Deployed; file hashes verified | Loader for UltraTool and ArchiveXL |
| redscript 0.5.31 | Deployed; file hashes verified | Required scripting foundation for ArchiveXL and Real Vendor Names |
| ArchiveXL 1.27.3 | Deployed; file hashes verified | Loads the supplementary Ultra+ lighting removals in its `.xl` file |
| Ultra+ 9.3.7 | Deployed; file hashes verified; first-launch profile reviewed | Requested engine graphics/performance tuning |
| Better Loot Markers 1.4.0 | Deployed; all 9 payload files verified | More useful loot icons through existing CET |
| Real Vendor Names 2.1.0 | Deployed; script hash verified at the extension-selected path | Recognizable shop labels on the map |
| ReShade 6.8.0 add-on host / RenoDX 0.2026.0916.2204 for Cyberpunk | Both enabled; file hashes verified; RenoDX disable/enable filesystem test passed | Separate post-processing host and game-specific HDR/color profile |
| Microsoft .NET 8.0.31 Desktop Runtime x64 | Installed | Desktop runtime required by RHI |
| RHI 2.7.5 | Installer downloaded; user installation pending after automatic approval review blocked execution | Requested graphics installation/maintenance tool |

File verification establishes deployment contents. It does not prove startup, appearance, performance or compatibility with the installed neural-rendering setup. Pending entries must not be treated as installed merely because their payloads are available.

The final comparison checked all 330 pre-existing baseline files: 329 hashes remained unchanged, and the sole difference was the reviewed `LoadReshade = true` line in `OptiScaler.ini`. ReShade settings and the Ultra+ first-launch profile were added separately. The RenoDX off/on filesystem test preserved ReShade, Ultra+, existing NR files and settings; this verifies selective file switching, not in-game operation.

## Who controls which files

| Owner | Assigned work | Boundary |
|---|---|---|
| Vortex | RED4ext, redscript, ArchiveXL, Ultra+, Better Loot Markers and Real Vendor Names | Hardlink staging is on the game drive. Use Vortex enable/disable followed by Deploy; do not also enable these same payloads through the private controller |
| Private component controller | Enabled ReShade host and RenoDX add-on as separate binary components | Own only its recorded DLL/add-on files. Capture mutable settings without making their deletion/restoration part of routine binary toggles |
| RHI | Pending manual installation; no deployed game files assigned at this checkpoint | Keep protected automatic updates off. It must not replace controller-owned graphics files, custom OptiScaler/CET controls or the native NVIDIA runtime set |
| Existing native game and custom host | Native DLSS SR/RR/FG, current OptiScaler NR consumer, CET and the existing graphics controls | Preserve their prior snapshots, binding files, personal NR slots and update hold |

The [current Cyberpunk guide](https://wiki.redmodding.org/cyberpunk-2077-modding/for-mod-users/users-modding-cyberpunk-2077/getting-started/vortex-mod-manager) recommends Vortex. RHI complements this package workflow as the requested graphics tool; two tools must not both deploy or update the same file. If ownership moves between tools, first preserve the live state, stop the old owner's deployment, then import and verify the exact replacement ownership.

The loaders use separate files: existing custom OptiScaler owns `bin/x64/dxgi.dll`; existing CET uses `bin/x64/version.dll`; RED4ext uses `bin/x64/winmm.dll` and `red4ext/RED4ext.dll`. The configured OptiScaler plugin chain uses `[Plugins] LoadReshade = true` to load `bin/x64/ReShade64.dll`, which hosts `bin/x64/renodx-cp2077.addon64`. ReShade must not be renamed over `dxgi.dll`. This RenoDX add-on handles game-specific shaders/color; it does not replace the existing neural consumer.

Vortex's Cyberpunk extension placed Real Vendor Names at `r6/scripts/real-vendor-names-2.1.0-game-relative (V2077)/realVendorNames.reds`. Its deployed script hash matches the verified source; the relocation is recorded in the private receipt. Manage this package through Vortex instead of adding a duplicate at the original archive path.

## Independent changes and snapshots

The [component controller](../../scripts/Manage-ModComponents.ps1) supports `Import`, `Status`, `Plan`, `Enable`, `Disable`, `Snapshot`, `CaptureCurrent` and `Recover`. Its private root mapping supplies actual game and settings locations; no personal machine paths belong in this guide. The following controller workflow applies only to files it owns; Vortex packages use Vortex deployment and their recorded before/after snapshots.

1. **Import** a verified component manifest and its payload into private storage. Import alone does not install it.
2. **Plan** the change. Review additions, replacements, dependencies and conflicts before deployment.
3. Close the game, store/launcher, relevant mod managers, helpers and shader compilers. Never swap a loaded DLL.
4. **Enable** the selected component. Preserve its current state immediately before mutation and verify the after-state hashes. Keep the last working baseline separately.
5. **Disable** that component later to restore its own previous files. Other disjoint components remain installed. A required dependency cannot be removed while active dependents still need it.
6. Use **Snapshot** before a new test to preserve owned files and captured settings without changing game files. If an intentionally edited owned file causes a hash mismatch, review it and use **CaptureCurrent** to accept that revision while preserving the previous payload and original rollback baseline. Do not bypass unexplained drift. Use **Recover** only for the controller's recorded interrupted transaction.

For example, Better Loot Markers can be disabled without removing Real Vendor Names. Removing Real Vendor Names does not require disabling Better Loot Markers. Removing redscript first is inappropriate while Real Vendor Names or another redscript mod remains active. Two mods that edit the same file or setting are not independent merely because they have different names.

Snapshots should include the files/settings actually affected, source URLs, version, hashes, and whether each file was added or replaced. Keep launch options, game settings and graphics-driver configuration when a stage changes them. Better Loot Markers creates its own settings file after configuration; preserve it during future switches rather than resetting it unintentionally.

Mutable settings persist across normal component toggles. The reviewed Ultra+ profile was seeded once at `bin/x64/plugins/cyber_engine_tweaks/mods/UltraPlus/UltraPlusConfig.ini`; preserve the user's subsequent edits. Capture this file, the game's user `UserSettings.json`, ReShade settings/presets and the relevant OptiScaler settings alongside binary snapshots. A capture is recovery evidence, not an instruction to restore old settings whenever a binary is disabled. Restoring a prior settings state is a separate, explicit operation. With Vortex hardlinks, editing a deployed package file can also edit its staging counterpart; preserve those changes before redeployment or upgrade.

For Vortex rollback, disable the smallest selected package and Deploy. Better Loot Markers and Real Vendor Names can be toggled independently. Disable Ultra+ before removing ArchiveXL; disable both ArchiveXL and Real Vendor Names, plus any other dependents, before removing redscript. Remove RED4ext only after its dependent plugins are disabled. Preserve the existing CET installation and controls because other active mods use them. Do not restore the entire game snapshot merely to remove one independent mod.

For visual rollback, disable `renodx-cp2077-2026.0916.2204` independently to retain the ReShade host. Disable RenoDX before `reshade-6.8.0`, because the add-on depends on that host. Re-enable ReShade before RenoDX. Settings and the existing OptiScaler/NR stack remain in place throughout these binary toggles.

## Graphics boundaries

Keep the [existing custom-host update hold](../../examples/cyberpunk-2077/UnifiedControls/UPDATE-READINESS.md). The prepared dynamic-resolution update failed FG eligibility/manual-resolution restoration checks; installing new tools does not resolve those failures. Do not run its old installer or put an upstream stock DLL over the custom build.

Use one engine/PT tuning layer: the requested Ultra+. The deployed and read-back-verified first-launch profile is:

```ini
[UltraPlus]
internal.mode = PT21
internal.quality = Fast
internal.denoiserMode = Vanilla
internal.streaming = Vanilla
internal.autoQualityEnabled = false
internal.autoConfirmMenu = false
internal.restoreGraphicsMenuEnabled = false
internal.graphicsMenuOverrides = Off
internal.showFps = false
internal.showVram = false
internal.simpleMode = false
```

The exact keys and value types were checked against the bundled 9.3.7 parser. Advanced mode (`simpleMode = false`) exposes manual controls; switching to Simple mode reapplies automatic quality/streaming defaults. Ultra+ applies its engine profile on startup even when automatic menu confirmation and saved-menu restoration are off. PT21/Fast is therefore an intentional rendering change, not a passive installation. This profile does not choose the game's native DLSS quality or FG mode. Ultra+ Auto Quality is disabled; it is distinct from dynamic DLSS resolution and an FPS limiter. The existing dynamic-resolution update hold still applies.

**DLSS 310.1 transition caveat:** the [Ultra+ author](https://theultraplace.com/games/cyberpunk2077/) requires DLSS 310.6 or newer for RR Clean. Start on Vanilla. The bundled code can automatically select and save RR Clean when native Ray Reconstruction changes from off/NRD back to on; no supported configuration switch suppresses this transition. After changing RR off/on, open **grave/tilde (` / ~) → Ultra+ → Advanced** and verify **Denoiser: Vanilla** while the native runtime remains 310.1. The reviewed seed alone does not guarantee Vanilla persists through that transition. A runtime update needs separate validation.

Avoid generic performance INIs and overlapping PT/lighting packs. The included `.xl` lighting removals use ArchiveXL; the core Ultra+ CET/UltraTool code alone is not evidence those supplementary removals loaded. Measure rendered FPS, displayed FG FPS and VRAM separately.

ReShade/RenoDX is enabled through the documented plugin chain. Use the separate controller components for binary rollback and retain mutable settings for the next test. Do not add a second neural consumer, Feeder, or competing FG implementation. Check HDR/tonemapping and shader overlap in the combined output; do not stack an additional automatic HDR conversion over the chosen game/RenoDX path.

Preserve the current controls: F5 Quick Save, F6 Quick Load, F9 native DLSS quality, Delete full graphics controls, F12 compact controls, F11 personal NR slots, F10 NR toggle, F7 NR 25%/100%, and grave/tilde (` / ~) for CET/Ultra+. CET uses `VK_OEM_3` (`0xC0`), so Shift is not required. The current `ReShade.ini` sets the ReShade overlay to Home (key code 36). Ultra+ needs no additional hotkey. Keep F8/Page Up/Page Down unbound. Limited HUD is deferred because its default F6/F8 bindings conflict with this arrangement.

## Short test sequence

The user will perform the runtime tests; none have been run by the assistant. Use the same save, scene, weather and resolution for comparisons, and preserve a separate copy of saves before gameplay-mod experiments. Take a settings snapshot before the first launch because Ultra+ can write settings when it runs. These deployed packages can be tested while the separate RHI application installation is pending.

1. Launch the finalized package, check the framework/CET/UltraTool logs for load or script errors, and inspect Ultra+ Advanced: PT21, Fast, Vanilla denoiser, Vanilla streaming. Do not enable RR Clean on the current 310.1 runtime.
2. Check the installed QoL components: loot icons in motion and scanner transitions; vendor names on the map. Verify the existing hotkeys still work.
3. Check menus, moving HUD, lighting, HDR highlights/blacks, loading, alt-tab and clean shutdown. Verify ReShade and the Cyberpunk RenoDX add-on actually load.
4. For quick comparisons, close the game and relevant processes, snapshot the current settings, then toggle only Ultra+ through Vortex or only the RenoDX binary component through its controller. To test without ReShade, disable its dependent RenoDX component first. Revisit the same scene and record base FPS, displayed FPS, VRAM and visible differences. Retain settings and unrelated packages between tests.

When a test fails, preserve its logs and disable the smallest relevant component. Recheck the same scene. A successful startup or loaded overlay alone does not establish neural evaluation, generated-frame delivery or long-session stability.

For a first playthrough, retain the focused QoL pair and original game balance. Defer wider HUD, AI, combat and cyberware changes until the base package is understood. See [curated recommendations](RECOMMENDATIONS.md) for first-playthrough, later-play and experimental choices.
