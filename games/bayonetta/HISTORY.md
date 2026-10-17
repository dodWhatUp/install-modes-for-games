# Bayonetta — History

## 2026-10-07 — Both ReShade overlays moved to Delete

- User set ReShade = Delete and OptiScaler = Home as the cross-game rule. Bayonetta's proven chain has two ReShade hosts and no OptiScaler, so both the x86 game and x64 helper overlay bindings were migrated.
- Bayonetta and its helper were closed; both INIs were exclusively writable. Private snapshot `20261007-110500-before-reshade-delete-optiscaler-home` preserved the prior files and Steam metadata without replacing the known-good graphics baseline.
- Changed exactly `KeyOverlay=36,0,0,0` to `KeyOverlay=46,0,0,0` in each file. Game-host hash `795CF34002DD0F0EA68CBCF825BFB60666A5F0F6436E80655ACE00EE7BBC202F` → `5DD69F5A510252208344A4D3E4AC2347FB374B99E356A712CDC5C46B549C73FE`; helper hash `DDE9E846F94F6D2A525616E2674518378E894231F95BF50E375F54D26D750CDE` → `2591C77E30C83CC9B586BDB9598F939E8BB53A8350865CE878D8305B26C36E4A`.
- Byte-preserving comparison and static readback passed. No proxy, feeder, helper, NGX, preset, save or renderer setting changed. Runtime Delete handling remains pending.
- Rollback: with both processes closed, restore each matching INI from the named snapshot; do not interchange the x86 game and x64 helper configurations.

## Current documented baseline

- The Steam PC executable was locally confirmed as 32-bit D3D9.
- Working graphics path: x86 dgVoodoo2 D3D9→D3D11, x86 ReShade/Feeder in the game, shared texture/fence transport, and an x64 helper containing ReShade, RenoDX DLSS5, and NGX.
- Positive evidence: a 3840×2160 DLAA feature became ready; frames through at least 3,600 were delivered; RenoDX created feature 18 and repeatedly completed inline evaluations; shutdown was clean.
- The proven path used 100% work resolution. A 67% experiment produced black captures and was rejected.

## Important exception

Modern NVIDIA NGX and the tested RenoDX neural add-on are 64-bit. They cannot be loaded directly into Bayonetta's 32-bit process. The helper boundary is essential, not optional layout complexity.

## Security/system lesson

Windows Smart App Control blocked the locally built/helper workflow with error 4551. Disabling a global protection was a user-authorized system decision and must never become an automatic installation step. Future work should prefer signed/reputable releases and record security consequences explicitly.

## Feature limitation

This stack proved a full-resolution neural/DLAA pass; it did not add an upscaling performance gain or MFG. Feeder is incompatible with Smooth Motion/OptiScaler, so any FG experiment must be a separate profile.

## 2026-09-14 — Library comparison review

Added [categorized comparisons](COMPARISONS.md) covering manager/foundations, performance, graphics/DLSS, QoL/UI, animation, AI, abilities/mechanics and actual content extensions. No game files changed or new gameplay tests were performed by this review. Earlier local evidence remains stronger than generic recommendations; historical control mappings and unresolved validation boundaries are preserved. See the [14-game guide](../../docs/INSTALLED-GAMES-MOD-GUIDE.md) for scope and installed-library checks.
