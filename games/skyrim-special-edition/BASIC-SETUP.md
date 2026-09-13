# Skyrim basic setup — installation boundary

Updated 2026-09-14. **Manager ready; mod downloads and gameplay validation pending.** This is the authorized basic path, not an installed-mod list.

## Ready now

MO2 2.5.2 portable instance for Steam Skyrim SE, local INIs/saves, `00 - Baseline` and `01 - Basic - awaiting downloads`. The basic profile is selected. Existing game/ReShade files and saves are preserved; hashes are in [history](HISTORY.md). Built-in LOOT sorting is available in MO2, but no sorting or record cleaning was needed for an official-only plugin list.

## Download and install order

| Order | Exact target for the observed runtime | Original download page | Installation / verification |
|---|---|---|---|
| 1 | SKSE64 2.3.1 for Steam 1.7.104 | [SKSE author](https://skse.silverlock.org/) → [Nexus files](https://www.nexusmods.com/skyrimspecialedition/mods/30379?tab=files) | Inspect archive/readme; hash and record its root additions separately. Put scripts in an MO2 mod. Launch through SKSE only after baseline testing; verify reported runtime and extender version |
| 2 | Address Library v13, including 1.7.104 database | [Author files](https://www.nexusmods.com/skyrimspecialedition/mods/32444?tab=files) | MO2 Data mod; confirm `SKSE/Plugins/versionlib-1-7-104-0.bin`. Do not assume this repairs incompatible old DLLs |
| 3 | SkyUI 6.11 | [Author files](https://www.nexusmods.com/skyrimspecialedition/mods/12604?tab=files) | MO2 package; inspect plugin/asset layout, enable required plugin and test inventory, favourites and MCM |
| 4 | MCM Helper 1.6.3 for Steam 1.7.99+ / SkyUI 6+ | [Author files](https://www.nexusmods.com/skyrimspecialedition/mods/53000?tab=files) | MO2 package; confirm requirements and plugin log. Verify configuration saving with a compatible dependent mod when added |
| 5 | USSEP / engine or display fixes, only with exact support | [Comparisons](COMPARISONS.md) | Check current masters, runtime and release notes first. Engine Fixes beta and unofficial Display Tweaks patch remain gated; no performance improvement claimed yet |

The Nexus session is currently signed out. Complete sign-in in the prepared Nexus tab; do not paste a password into the repository or chat. Premium is not required by this plan, and no subscription/purchase was made.

## Before continuing

1. Reconfirm executable 1.7.104.0 and required DLC/masters. A changed runtime invalidates this pinned queue.
2. Close Skyrim and its mod tools before installing; take a fresh snapshot of root files, profile and external settings immediately before each mutation. Preserve any newer user changes alongside the earlier backup.
3. Test the current original launch, then SKSE, then the UI/foundation group. Use a temporary new/test save or a copy, never overwrite the original progress save during validation.
4. Record file hashes, exact archive versions, root ownership and logs. A visible manager or overlay proves neither mod activation nor performance.

## Graphics and gameplay expansion

Community Shaders with official Upscaling is the preferred DLSS target after compatibility verification. Its documented frame generation is FSR FG, not proof of NVIDIA DLSS FG/MFG or Ray Reconstruction. No graphics hotkeys were added by installing the manager. Existing ReShade Home and game bindings remain as they were.

Texture/UI skins, animation, combat, perks, magic and new quests are subsequent options in [comparisons](COMPARISONS.md). Do not activate empty placeholder mods or treat a download queue as an enabled load order.

## Rollback

At the present boundary, close MO2 and launch the existing Steam game; no game-root rollback is needed. After future SKSE installation, restore/remove only its manifested root files and return to the baseline profile/save. MO2 profiles alone do not undo root DLLs, driver settings or scripted changes already saved into a character.
