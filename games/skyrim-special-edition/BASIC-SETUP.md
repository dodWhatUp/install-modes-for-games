# Skyrim basic setup — installation boundary

Updated 2026-10-10. **MO2, Skyrim 1.6.1170, SKSE64 2.2.6, Address Library v13 and PureDark Build 19 Hotfix 1 are installed/enabled in a dedicated profile.** Startup succeeds; the earlier Not Authenticated gate no longer appeared after the user-operated login/loading step. The normal feature UI is accessible, but functional gameplay validation and later UI mods remain pending. This is the authorized selected path, not a blanket installed-mod list.

## Ready now

MO2 2.5.2 portable instance for Steam Skyrim SE, local INIs/saves, with `02 - PureDark 1.6.1170` selected. The prior baseline/basic profiles remain preserved. Matching SKSE scripts, Address Library and PureDark are enabled; ReShade 6.8 remains the root hook. Original saves and the full pre-downgrade 1.7.104 root are preserved privately; hashes and rollback are in [history](HISTORY.md). No sorting or record cleaning was needed for the official-only plugin list. Launch through the profile's SKSE entry, not Steam verification/update.

## Download and install order

| Order | Exact target for the observed runtime | Original download page | Installation / verification |
|---|---|---|---|
| 1 | SKSE64 2.2.6 for Steam 1.6.1170 | [SKSE author](https://skse.silverlock.org/) | **Installed/enabled.** Matching root binaries and 62 MO2-managed `.pex` scripts; SKSE recognized 1.6.1170 and loaded PureDark correctly |
| 2 | Address Library v13, All in One with 1.6.1170 database | [Author files](https://www.nexusmods.com/skyrimspecialedition/mods/32444?tab=files) | **Installed/enabled in MO2.** Confirmed `SKSE/Plugins/versionlib-1-6-1170-0.bin`; old Address Library initialization failure did not recur |
| 3 | PureDark AIO Build 19 Hotfix 1 | [Private archive index](../../docs/PUREDARK-ARCHIVE-2026-10-07.md) | **Installed/enabled.** Requested NVIDIA Dynamic MFG, first-plus-third-person FrameWarp, NR off. Latest FG startup failed and persisted None. Feature UI is accessible; moving gameplay is deferred |
| Later | SkyUI / matching MCM Helper | [SkyUI files](https://www.nexusmods.com/skyrimspecialedition/mods/12604?tab=files), [MCM Helper files](https://www.nexusmods.com/skyrimspecialedition/mods/53000?tab=files) | Not installed. The old 1.7.x queue is invalid for this runtime; refresh versions, masters and 1.6.1170 support before adding anything |
| Later | USSEP / engine or display fixes, only with exact support | [Comparisons](COMPARISONS.md) | Check current masters, runtime, input/swapchain ownership and release notes first; no performance improvement claimed yet |

The Nexus session was authenticated by the user and the two foundation archives above were downloaded from their official pages. No password or session secret is stored in this repository.

## Before continuing

1. Reconfirm executable 1.6.1170.0 and required DLC/masters. The retained newer Steam build metadata is not the effective executable version; an update invalidates this setup.
2. Close Skyrim and its mod tools before installing; take a fresh snapshot of root files, profile and external settings immediately before each mutation. Preserve any newer user changes alongside the earlier backup.
3. If authentication returns, complete the official PureDark/Patreon flow personally. With Skyrim's Steam overlay Off, agent F8 through the already-running AHK helper opens/closes PureDark; mouse page navigation/scrolling works, but direct keys, search typing and Skyrim menu/console input do not. The loaded helper is still v0.1, not the v0.2 source on disk. Keep the isolated reWASD test Off and original profiles unchanged. Autoload remains removed. Current scope is input/menu tests only; graphics/gameplay testing is deferred. The latest NVIDIA initialization failed `887A0004` and persisted None automatically. Preserve that state and close configuration writers before any later authorized restoration; inspect the effective backend on every future launch. Never overwrite original progression.
4. Record file hashes, exact archive versions, root ownership and logs. A visible manager or overlay proves neither mod activation nor performance.

## Graphics and gameplay expansion

PureDark is the user-selected NVIDIA MFG/PD FrameWarp target on the explicitly authorized 1.6.1170 downgrade. Startup resources/menu counters do not prove feature operation. Community Shaders remains a separate later option only after compatibility and ownership review; its documented frame generation is FSR FG, not proof of NVIDIA DLSS FG/MFG or Ray Reconstruction. ReShade uses Delete; PureDark F12, numpad `*` FG and numpad `+` FrameWarp; Home is reserved for a future compatible OptiScaler full menu. F12 is physically confirmed and agent-confirmed only through the narrow AHK route; other feature shortcuts are not runtime-verified.

Texture/UI skins, animation, combat, perks, magic and new quests are subsequent options in [comparisons](COMPARISONS.md). Do not activate empty placeholder mods or treat a download queue as an enabled load order.

## Rollback

For the current test settings, close Skyrim/MO2, preserve newer changes and restore the changed settings from private snapshot `20261010-gameplay-validation`. To revert the downgrade, close Skyrim/MO2/Steam and restore the complete root plus matching old mod folders, profiles, external configuration and Steam metadata from `20261007-103600-pre-downgrade-1.6.1170`; preserve the current downgraded state separately first. MO2 profiles alone do not undo the downgrade, root DLLs, driver settings or scripted changes saved into a character. No progression save was loaded in this validation attempt.
