# Skyrim Special Edition Recommendations

Recommendations researched 2026-09-14; current installation boundary reconciled 2026-10-10. These are staged choices based on [comparisons](COMPARISONS.md), not a claim of local test success.

## First playthrough — recommended

MO2 + matching SKSE, Address Library, SkyUI and MCM Helper. Start with the smallest supported set. Difficulty and exact conflicts are detailed in the comparison guide; test each added layer before continuing a valued save.

## After familiarity

An independently verified Community Shaders/Upscaling profile, then selected HUD or movement improvements. This is an alternative to the user-selected PureDark stack, not permission to combine competing upscalers or FG owners. Expected benefits are qualitative. Keep alternate file/configuration owners in separate profiles and retain a restore point.

## Post-game / replay / experimental

One combat/perk/magic family and Bruma or Wyrmstooth; Legacy or Enderal as separate larger paths. Persistent classes, quests, progression and overhauls need a dedicated new/copy save. No additional purchase is assumed.

## Graphics combination

Use the [graphics/DLSS comparison](COMPARISONS.md) to choose one owner for each upscaler, frame generator and tonemapper. Preserve native features where available. Unsupported SR/RR/FG/MFG/NR stays off; only actual resource/evaluation evidence can establish support.

## Current boundary

The selected PureDark path is installed in a separate 1.6.1170 profile with matching SKSE/Address Library. With Skyrim's Steam overlay Off, the existing user-run AHK F8 → F12 route opened/closed PureDark through agent input on two launches; overlay mouse navigation/scrolling worked. Direct keys/search typing and Skyrim menu/console input still failed; foreground activation was needed for one repeat shortcut. Recommend only this narrow menu probe, not general game control. Keep the separate reWASD test inactive and existing profiles intact; its earlier Notepad success did not establish Skyrim control. The latest NVIDIA backend startup failed `887A0004` and persisted FG None automatically; verify the effective backend on each future launch. Current scope is input/menu tests only: graphics diagnosis and independent MFG/FrameWarp motion/performance tests are deferred. Skyrim is left at main menu with FG Off, autoload removed, NR off and saves untouched. Native first-plus-third-person mode does not require an extra camera mod, but its actual gameplay behavior and optional camera-mod compatibility remain separate unverified experiments. See history for checkpoints and exact rollback.
