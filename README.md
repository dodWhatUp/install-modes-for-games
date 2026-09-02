# Install Mods for Games

A practical, evidence-based knowledge base for game modding: graphics injection and upscaling, HDR, performance, quality of life, UI/controls, gameplay changes, overhauls, and expansion-scale projects.

This repository records both the method and the outcome. A feature is not marked working because an overlay appeared; it is marked working only when the relevant log proves that frames were created, evaluated, and delivered without breaking the game.

## Canonical GitHub repository

The permanent GitHub destination for this project is [`dodWhatUp/install-modes-for-games`](https://github.com/dodWhatUp/install-modes-for-games). When game-modding history is connected, uploaded, or updated through GitHub, use this repository rather than creating a duplicate or publishing through another account. Follow [GitHub Connection and Publishing](docs/GITHUB-PUBLISHING.md) before changing a remote or pushing.

## Tested games

See the [game index](games/README.md) for detailed history, catalogs, and recommendations.

| Game | Renderer and path | Result | Guide |
|---|---|---|---|
| Hogwarts Legacy | 64-bit DX12, native DLSS/Streamline, OptiScaler at the shipping executable | Working baseline; native DLSSG kept separate from OptiScaler's neural-rendering experiment | [Hogwarts Legacy](games/HOGWARTS-LEGACY.md) |
| Bayonetta | 32-bit DX9 → dgVoodoo2 DX11 → ReShade/Feeder → 64-bit RenoDX host | Working; logs prove thousands of delivered and evaluated 4K frames | [Bayonetta](games/BAYONETTA.md) |
| DOOM: The Dark Ages | 64-bit Vulkan; native DLSS/RR/FG; experimental ReShade/Feeder private NGX path | Experiment paused after a later 4K crash; game currently not installed by user choice; resumable history preserved | [DOOM: The Dark Ages](games/DOOM-THE-DARK-AGES.md) |
| Other UE4/UE5 games | Depends on API, bitness, native temporal-upscaler support, launcher, and anti-cheat | Reusable install/diagnostic method, not a universal drop-in | [Generic Unreal guide](games/GENERIC-UNREAL-ENGINE.md) |

## Read this first

1. Use these methods only in offline or single-player games. ReShade add-ons and proxy DLLs may trigger anti-cheat.
2. Back up the exact game folder and user configuration before changing anything.
3. Install one layer at a time and launch-test after every layer.
4. Never combine OptiScaler, DLSS5-Feeder, NVIDIA Smooth Motion, or two ReShade/proxy DLL chains unless the projects explicitly document that combination.
5. Download binaries only from the upstream projects. This repository intentionally contains no ReShade, NVIDIA, OptiScaler, RenoDX, dgVoodoo2, or Feeder binaries.

The fastest route is [Start Here](docs/START-HERE.md), followed by [Components and Compatibility](docs/COMPONENTS.md), the [Operating Standard](docs/OPERATING-STANDARD.md), and [Safe Workflow](docs/SAFE-WORKFLOW.md).

## How this repository remembers and decides

- [Agent rules](AGENTS.md) make future work search prior attempts before changing a game, present numbered choices, snapshot at the last safe moment, and update lessons after a run.
- [General preferences](preferences/GENERAL.md) capture the user's default quality, performance, safety, discovery, and recommendation preferences.
- General techniques live in `docs/`; game-specific exceptions, failures, preferences, catalogs, and recommendations live under that game's folder.
- Complete mod catalogs are kept separate from curated combinations for first playthrough, later play, and post-game/experimental use.
- [Feature Decision](docs/FEATURE-DECISION.md) distinguishes native inputs from bridge/estimated inputs and prevents duplicate SR/RR/FG/neural ownership.
- [Quick-Switch Profiles](docs/QUICK-SWITCH-PROFILES.md) defines reversible local profiles without publishing proprietary files.
- [Catalogs and Recommendations](docs/CATALOGS-AND-RECOMMENDATIONS.md) defines the requested mod categories, ratings, combinations, and playthrough stages.
- [Performance and VRAM](docs/PERFORMANCE-AND-VRAM.md) defines the default performance review and memory-headroom checks.
- [Cross-Thread Lessons](docs/CROSS-THREAD-LESSONS.md) consolidates the relevant earlier conversations into durable, corrected conclusions.
- [GitHub Connection and Publishing](docs/GITHUB-PUBLISHING.md) fixes this project's canonical account, repository, remote checks, and safe push procedure.

The current DOOM experiment is explicitly paused. This repository stores a resume boundary but does not schedule reminders or restart it automatically.

## What “DLSS 5” means here

NVIDIA announced DLSS 5 as a neural-rendering model. Some experiments in this repository used early community integration paths that call NVIDIA NGX through OptiScaler or RenoDX/DLSS5-Feeder. Those paths are unofficial, version-sensitive, and not equivalent to a game shipping native DLSS 5 integration.

## Repository policy

- Documentation, small configuration examples, scripts, and short sanitized log excerpts are included.
- Game files, proprietary DLLs, driver packages, downloaded archives, full diagnostics, save files, and personal paths are excluded.
- Version numbers describe the September 2026 test environment. Always read the current upstream documentation before installing newer builds.
- Current mod lists are discovery records, not permission to install every entry. Each game records conflicts, confidence, local test state, and review date.

## Sources

See [Sources and Downloads](docs/SOURCES.md). ReShade specifically asks users to link to its official site instead of redistributing its binaries or shader files.
