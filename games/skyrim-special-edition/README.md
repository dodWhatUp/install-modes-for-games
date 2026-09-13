# Skyrim Special Edition

Status: **MO2 installed and configured; basic mod downloads pending Nexus sign-in**. Reviewed 2026-09-14. No basic mods or DLSS were installed yet. See the [setup checklist](BASIC-SETUP.md).

## Observed environment

- Store: Steam; build 24914197.
- Relative executable: `SkyrimSE.exe`.
- Renderer: x64 / D3D11; runtime 1.7.104.0.
- Hardware at inventory: RTX 5070 Ti, 16 GB; driver 616.56.
- Display mode, active graphics settings, hooks and anti-cheat constraints must be rechecked before mutation. File presence does not prove a successful launch.

## Decision and records

[Categorized comparisons](COMPARISONS.md) explain competing options, dependencies and content scope. [Catalog](MOD-CATALOG.md) is discovery; [recommendations](RECOMMENDATIONS.md) are the selected starting points. [History](HISTORY.md) records actual work and [preferences](PREFERENCES.md) preserve the user's intent.

## Installation and verification boundary

Use the runtime-matched foundation and separate MO2 profile described in the comparisons. Preserve the existing ReShade root hook. Test the current baseline, then one layer, startup/menu transition, representative gameplay, save/load where relevant, and clean shutdown. Graphics hooks additionally require actual evaluation/presentation evidence and motion/UI checks.

## Rollback

Return to the baseline profile and preserved pre-mod saves. MO2 cannot undo root hooks: remove only recorded additions and restore hashed originals from the private snapshot.
