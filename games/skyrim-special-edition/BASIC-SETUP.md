# Skyrim basic setup — installation boundary

Updated 2026-10-07. **Manager, SKSE64 2.3.1 and Address Library v13 are installed; clean foundation gameplay validation and later UI mods remain pending.** This is the authorized basic path, not a blanket installed-mod list.

## Ready now

MO2 2.5.2 portable instance for Steam Skyrim SE, local INIs/saves, `00 - Baseline` and `01 - Basic - awaiting downloads`. The basic profile is selected. SKSE scripts and Address Library are enabled there; PureDark Build 19 Hotfix 1 is installed/configured but disabled because its current binary does not support runtime 1.7.x. Existing game/ReShade files and saves are preserved; hashes are in [history](HISTORY.md). Built-in LOOT sorting is available in MO2, but no sorting or record cleaning was needed for an official-only plugin list.

## Download and install order

| Order | Exact target for the observed runtime | Original download page | Installation / verification |
|---|---|---|---|
| 1 | SKSE64 2.3.1 for Steam 1.7.104 | [SKSE author](https://skse.silverlock.org/) → [Nexus files](https://www.nexusmods.com/skyrimspecialedition/mods/30379?tab=files) | **Installed.** Root binaries and 62 MO2-managed `.pex` scripts are hashed in history. SKSE recognized runtime 1.7.104 and injected; clean main-menu/gameplay validation remains pending |
| 2 | Address Library v13, including 1.7.104 database | [Author files](https://www.nexusmods.com/skyrimspecialedition/mods/32444?tab=files) | **Installed/enabled in MO2.** Confirmed `SKSE/Plugins/versionlib-1-7-104-0.bin`. This does not repair PureDark's confirmed 1.7.x incompatibility |
| 3 | SkyUI 6.11 | [Author files](https://www.nexusmods.com/skyrimspecialedition/mods/12604?tab=files) | MO2 package; inspect plugin/asset layout, enable required plugin and test inventory, favourites and MCM |
| 4 | MCM Helper 1.6.3 for Steam 1.7.99+ / SkyUI 6+ | [Author files](https://www.nexusmods.com/skyrimspecialedition/mods/53000?tab=files) | MO2 package; confirm requirements and plugin log. Verify configuration saving with a compatible dependent mod when added |
| 5 | USSEP / engine or display fixes, only with exact support | [Comparisons](COMPARISONS.md) | Check current masters, runtime and release notes first. Engine Fixes beta and unofficial Display Tweaks patch remain gated; no performance improvement claimed yet |

The Nexus session was authenticated by the user and the two foundation archives above were downloaded from their official pages. No password or session secret is stored in this repository.

## Before continuing

1. Reconfirm executable 1.7.104.0 and required DLC/masters. A changed runtime invalidates this pinned queue.
2. Close Skyrim and its mod tools before installing; take a fresh snapshot of root files, profile and external settings immediately before each mutation. Preserve any newer user changes alongside the earlier backup.
3. Test the current original launch, then SKSE, then the UI/foundation group. Use a temporary new/test save or a copy, never overwrite the original progress save during validation.
4. Record file hashes, exact archive versions, root ownership and logs. A visible manager or overlay proves neither mod activation nor performance.

## Graphics and gameplay expansion

PureDark is the user-selected NVIDIA MFG/PD FrameWarp target, but Build 19 Hotfix 1 is disabled until PureDark publishes explicit 1.7.104/1.7.x support. Community Shaders remains a separate later option only after compatibility and ownership review; its documented frame generation is FSR FG, not proof of NVIDIA DLSS FG/MFG or Ray Reconstruction. Existing ReShade Home and game bindings remain as they were.

Texture/UI skins, animation, combat, perks, magic and new quests are subsequent options in [comparisons](COMPARISONS.md). Do not activate empty placeholder mods or treat a download queue as an enabled load order.

## Rollback

At the present boundary, keep the PureDark mod disabled. To remove the foundation, disable the SKSE scripts and Address Library MO2 mods, then delete only the manifested root additions `skse64_loader.exe` and `skse64_1_7_104.dll`; restore snapshot `20261007-095312-pre-skse-puredark-b19hf1` if necessary. MO2 profiles alone do not undo root DLLs, driver settings or scripted changes already saved into a character.
