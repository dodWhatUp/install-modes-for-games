# Bayonetta — History

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
