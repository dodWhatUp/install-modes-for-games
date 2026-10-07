# Skyrim Special Edition

Status: **MO2, SKSE64 2.3.1 and Address Library v13 installed for Steam 1.7.104**. PureDark AIO Build 19 Hotfix 1 is installed/configured but disabled because PureDark confirmed that the current build is not compatible with Skyrim 1.7.x. Reviewed 2026-10-07. See [history](HISTORY.md) and the [setup checklist](BASIC-SETUP.md).

## Observed environment

- Store: Steam; build 24914197.
- Relative executable: `SkyrimSE.exe`.
- Renderer: x64 / D3D11; runtime 1.7.104.0.
- Hardware at inventory: RTX 5070 Ti, 16 GB; driver 616.56.
- Display mode, active graphics settings, hooks and anti-cheat constraints must be rechecked before mutation. File presence does not prove a successful launch.

## Decision and records

[Categorized comparisons](COMPARISONS.md) explain competing options, dependencies and content scope. [Catalog](MOD-CATALOG.md) is discovery; [recommendations](RECOMMENDATIONS.md) are the selected starting points. [History](HISTORY.md) records actual work and [preferences](PREFERENCES.md) preserve the user's intent.

## Installation and verification boundary

Use the runtime-matched foundation and separate MO2 profile described in the comparisons. Preserve the existing ReShade root hook. Keep the installed PureDark mod disabled until an upstream release explicitly supports 1.7.104/1.7.x; do not treat a present archive as compatibility evidence. Test the current baseline, then one layer, startup/menu transition, representative gameplay, save/load where relevant, and clean shutdown. Graphics hooks additionally require actual evaluation/presentation evidence and motion/UI checks.

## Rollback

Return to the baseline profile and preserved pre-mod saves. MO2 cannot undo root hooks: remove only recorded additions and restore hashed originals from the private snapshot.
