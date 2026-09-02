# Performance, Frame Pacing, and VRAM

Performance work is a default part of mod research, but a “performance mod” is not automatically safe or visually free.

## Establish the baseline

Record the same repeatable scene with:

- rendered/base FPS and frame time;
- displayed/generated FPS separately;
- 1% low or a useful frame-time trace;
- GPU utilization, clock, power and temperature;
- dedicated VRAM used/budget and system RAM;
- resolution, internal scale, RT, textures, output/HDR mode, FG multiplier and frame cap;
- shader-compilation or traversal-stutter context.

Do not compare a static menu to moving gameplay or generated FPS to base FPS.

## Performance-mod selection

Prefer, in order:

1. Current official patches and in-game settings with known visual cost.
2. A current game-specific bug/stutter/streaming fix with documented scope.
3. A maintained integrated graphics/performance profile.
4. Carefully selected engine/console edits, one group at a time.

Reject or isolate a performance package when it:

- overwrites a chosen visual overhaul's configuration;
- disables buffers or features needed by DLSS, RR, FG, HDR, ReShade, or RenoDX;
- reduces texture/geometry/RT quality beyond the user's preference;
- bundles unrelated gameplay/security/network changes;
- sets files read-only and prevents the game/mod manager from saving;
- lacks an exact uninstall/rollback.

## VRAM headroom

“Allocated” and “actively used” are not always the same, but near-budget operation is risky for injectors. Full-resolution color, depth, motion, history, UI, cross-API shared textures, neural models, generated frames, captures, and swapchain recreation can require large temporary allocations.

- Tune for the highest transient/recreation demand, not only the first successful frame.
- Lower the actual output/backbuffer when full-resolution add-ons allocate from it; lowering only a game-internal percentage may not change bridge memory.
- Texture-memory limits can create headroom but may increase streaming/pop-in. Measure both stability and image quality.
- Disable automatic diagnostic captures unless collecting one intentionally.
- Test a resolution change, alt-tab, loading transition, and enough moving gameplay to cross normal allocation peaks.

The DOOM 4K experiment on a 16 GB RTX 5070 Ti reached roughly 15.4/16.3 GB before a later recreation failure. This is strong evidence to keep that add-on stack at 2560×1440, but it is not proof that every crash was solely VRAM.

## Frame generation and latency

FG/MFG improves display smoothness but does not raise simulation/input sampling at the same rate. Aim for a comfortable base rendered rate—often at least roughly 50–60 FPS for action games—before increasing the multiplier. Measure latency and pacing with the selected Reflex/cap/v-sync path. Multiple present hooks, overlay blockers, HUD fixes, cross-API bridges, and duplicate FG owners can erase the benefit.
