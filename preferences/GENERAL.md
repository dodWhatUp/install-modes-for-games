# General User Preferences

Last confirmed: 2026-09-02

These are defaults, not permission to ignore a game-specific conflict or a newer explicit request. More specific preferences override general ones.

## Decision and safety preferences

- For this game-modding knowledge base, the default GitHub destination is `dodWhatUp/install-modes-for-games`. Confirm the authenticated GitHub identity before writing; never substitute another account or create a second similarly named repository.
- Show numbered options before a new modding path so the user can answer with the desired number. Include a warning beside any option likely to conflict, corrupt visuals, destabilize the game, or complicate rollback.
- Preserve a known-working state and take a just-in-time snapshot of files/settings likely to change.
- Prefer quick, reversible profile switching over reinstalling, where the files and tools permit it safely.
- Preserve stock files. Prefer side-by-side add-ons, installer manifests, and configuration deltas over blind replacement.
- Use offline/single-player paths for injectors and unsigned add-ons. Do not risk anti-cheat-protected play.
- Do not create reminders for paused experiments. Resume only when the user asks.

## Graphics and performance preferences

- Favor the best practical image quality while keeping enough VRAM and performance headroom for stability.
- Investigate missing NVIDIA features—newer DLSS models, Multi Frame Generation, Ray Reconstruction, and neural rendering—whenever a game has only part of the DLSS stack.
- Prefer the least problematic supported route: native game support or official NVIDIA override first, then a proven game integration, then OptiScaler/another bridge, and only then a synthetic-input experiment.
- Keep native DLSS components active when an add-on can safely add only the missing feature. Do not duplicate ownership of SR, RR, FG/MFG, or the swapchain.
- Consider performance/bug-fix mods by default unless they materially block graphics modding, overwrite the same settings, reduce desired quality, or introduce a larger compatibility risk. Explain that tradeoff.
- Re-research current graphics combinations after a meaningful game/tool update or when the last review is stale.

## Mod discovery preferences

For each game, maintain separate catalog sections for:

1. Frameworks, loaders, bug fixes, and performance.
2. Graphics, HDR, upscaling, ray tracing, and frame generation.
3. Quality of life, movement, traversal, and controls.
4. UI, menus, HUD, accessibility, and keybinds.
5. Gameplay changes and challenge/balance variants.
6. Large overhauls, added systems, expansion-scale content, and total conversions.
7. Cosmetic, audio, photo-mode, and other potentially interesting mods.

Keep the complete catalog separate from curated combinations. Curated recommendations should distinguish core/highly recommended, optional/interesting, experimental, and avoid; also separate first playthrough, after familiarity, and post-game.

## Evidence preferences

- Record failures as carefully as successes so later work does not repeat them.
- Use exact versions, hashes, effective resolution, process/API, relevant log evidence, performance/VRAM observations, confidence, and remaining unknowns.
- When a feature appears active, verify the actual input and output path. For temporal features, check motion vectors, depth, color/HDR contract, UI handling, frame evaluation, and recreation—not only the overlay.
