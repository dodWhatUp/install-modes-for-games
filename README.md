# Install Mods for Games

A practical, evidence-based guide to graphics injection and upscaling experiments with OptiScaler, ReShade, RenoDX, DLSS neural rendering, frame generation, and related tools.

This repository records both the method and the outcome. A feature is not marked working because an overlay appeared; it is marked working only when the relevant log proves that frames were created, evaluated, and delivered without breaking the game.

## Tested games

| Game | Renderer and path | Result | Guide |
|---|---|---|---|
| Hogwarts Legacy | 64-bit DX12, native DLSS/Streamline, OptiScaler at the shipping executable | Working baseline; native DLSSG kept separate from OptiScaler's neural-rendering experiment | [Hogwarts Legacy](games/HOGWARTS-LEGACY.md) |
| Bayonetta | 32-bit DX9 → dgVoodoo2 DX11 → ReShade/Feeder → 64-bit RenoDX host | Working; logs prove thousands of delivered and evaluated 4K frames | [Bayonetta](games/BAYONETTA.md) |
| DOOM: The Dark Ages | 64-bit Vulkan → ReShade/Feeder → private D3D12 NGX path | Working technical integration at 2560×1440; feature 18 evaluated and 16,200+ frames delivered | [DOOM: The Dark Ages](games/DOOM-THE-DARK-AGES.md) |
| Other UE4/UE5 games | Depends on API, bitness, native temporal-upscaler support, launcher, and anti-cheat | Reusable install/diagnostic method, not a universal drop-in | [Generic Unreal guide](games/GENERIC-UNREAL-ENGINE.md) |

## Read this first

1. Use these methods only in offline or single-player games. ReShade add-ons and proxy DLLs may trigger anti-cheat.
2. Back up the exact game folder and user configuration before changing anything.
3. Install one layer at a time and launch-test after every layer.
4. Never combine OptiScaler, DLSS5-Feeder, NVIDIA Smooth Motion, or two ReShade/proxy DLL chains unless the projects explicitly document that combination.
5. Download binaries only from the upstream projects. This repository intentionally contains no ReShade, NVIDIA, OptiScaler, RenoDX, dgVoodoo2, or Feeder binaries.

The fastest route is [Start Here](docs/START-HERE.md), followed by [Components and Compatibility](docs/COMPONENTS.md) and [Safe Workflow](docs/SAFE-WORKFLOW.md).

## What “DLSS 5” means here

NVIDIA announced DLSS 5 as a neural-rendering model. Some experiments in this repository used early community integration paths that call NVIDIA NGX through OptiScaler or RenoDX/DLSS5-Feeder. Those paths are unofficial, version-sensitive, and not equivalent to a game shipping native DLSS 5 integration.

## Repository policy

- Documentation, small configuration examples, scripts, and short sanitized log excerpts are included.
- Game files, proprietary DLLs, driver packages, downloaded archives, full diagnostics, save files, and personal paths are excluded.
- Version numbers describe the September 2026 test environment. Always read the current upstream documentation before installing newer builds.

## Sources

See [Sources and Downloads](docs/SOURCES.md). ReShade specifically asks users to link to its official site instead of redistributing its binaries or shader files.
