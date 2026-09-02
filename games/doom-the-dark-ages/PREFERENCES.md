# DOOM: The Dark Ages — Preferences and Constraints

Last confirmed: 2026-09-02

These override general preferences for this game.

## Current preference

- Do not install or launch DOOM now. The game is intentionally absent after the canceled recovery download.
- Keep the neural-rendering experiment paused indefinitely and do not remind the user.
- Preserve the private crashed-state snapshot so a future explicit request can resume from evidence rather than repeat discovery.

## Future graphics preference

- Preserve native HDR, DLSS SR, Ray Reconstruction, Frame Generation/MFG, and stock Streamline unless a selected test explicitly changes one owner.
- On this RTX 5070 Ti 16 GB system, do not recommend the Feeder/neural path at a 4K backbuffer. Begin any explicit future retry from exclusive 2560×1440 with measurable VRAM headroom.
- Prefer a game-specific RenoDX HDR profile over a generic HDR upgrade if a current, supported profile exists. Verify whether native HDR must be enabled or disabled for that exact profile.
- Treat OptiScaler-on-Vulkan neural rendering as unproven for this game until upstream support and feature-specific logs demonstrate otherwise.
- Use only one neural consumer and one frame-generation owner.

## Interaction preference

On an explicit resume request, show the numbered choices in [NEXT-OPTIONS.md](NEXT-OPTIONS.md), refreshed against current releases, and wait for the selected number before installing. Warn clearly that choices 2–4 are experimental.
