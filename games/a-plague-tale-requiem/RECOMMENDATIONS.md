# A Plague Tale: Requiem Recommendations

**Controls update, 2026-09-13:** use F7 for NR 25%/100%; native live SR is not implemented. The revised binaries are installed and statically verified; interactive testing remains pending. Treat earlier F9/F7 instructions below as the previous build. Restore this revision with private Restore-F7.ps1 before invoking the earlier rollback chain. [Dynamic SR feasibility](../../docs/DYNAMIC-DLSS-SR.md) is research, not an enabled FPS controller.

Reviewed 2026-09-13. These recommendations distinguish observed title-scene success from untested gameplay.

## First playthrough

- **Core:** original DLSS SR and game graphics controls. Stock title launch passed; full gameplay confidence remains untested in this task. Difficulty 1; rollback is the original game profile.
- **Experimental, user-selected:** installed OptiScaler NR with one FP8 pre-SR pass and scale 1.0. Expected benefit is adjustable neural lighting/detail; cost is extra GPU work and possible temporal artifacts. Difficulty 3; confidence High for title-scene creation/recreation, Low for gameplay stability. Restore with the private manifest script if necessary.

## Later play

- **Optional:** compare F9 model scales and F8 placement in the same repeatable gameplay scene, allowing every change to settle. Keep native FG fixed during the first comparison. Save a preferred combination only after inspecting motion and HUD.
- F11 exposes undocumented numeric model hints. Compare visually; do not infer quality tiers from their numbers.

## Post-game / experimental

- Multipass, finished-picture NR and residual processing remain separate experiments, disabled in the installed profile. They can increase VRAM, processing cost and visual risk.
- **Avoid:** adding Feeder to this native DLSS contract, loading another NR consumer, or assuming an INI ratio override provides a safe F7 game-resolution switch.
- F7 needs a Requiem-specific implementation and runtime evidence before recommendation.

## 2026-09-14 — Library comparison review

Added [categorized comparisons](COMPARISONS.md) covering manager/foundations, performance, graphics/DLSS, QoL/UI, animation, AI, abilities/mechanics and actual content extensions. No game files changed or new gameplay tests were performed by this review. Earlier local evidence remains stronger than generic recommendations; historical control mappings and unresolved validation boundaries are preserved. See the [14-game guide](../../docs/INSTALLED-GAMES-MOD-GUIDE.md) for scope and installed-library checks.
