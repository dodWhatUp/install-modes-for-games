# Mod Catalogs and Recommendations

The catalog answers “what exists?” The recommendation file answers “what should be combined for this user, machine, game phase, and goal?” Keeping them separate prevents popularity from becoming an automatic install decision.

## Required catalog sections

1. Frameworks, official mod tools, loaders, patchers, and conflict managers.
2. Bug fixes, stability, shader-compilation, stutter, performance, and VRAM options.
3. Graphics: textures, lighting, HDR, color, RT, SR/DLAA, RR, FG/MFG, neural rendering, ultrawide, and photo mode.
4. Quality of life: repetition removal, travel, inventory, economy, progression conveniences, movement, and traversal.
5. UI/menu/HUD/accessibility/keybind and controller changes.
6. Gameplay balance, combat, AI, difficulty, randomizers, and system changes.
7. Full overhauls, new systems, new quests/campaigns, DLC-sized projects, and total conversions.
8. Cosmetic, animation, audio/music/voice, character, and other interesting changes.

## Every entry records

- original author/project URL;
- version or last update and repository review date;
- purpose and category;
- game/build/store requirements;
- loader, dependencies, install location, and configuration ownership;
- proxy, shader, chunk ID, SQL/database, save, anti-cheat, and file conflicts;
- performance/VRAM/image-quality impact where known;
- local state: untested, working, partial, or failed;
- source class and confidence.

“Most endorsed” is discovery input, not a quality or compatibility score.

## Expansion-scale definitions

- **Total conversion:** replaces most of the game's setting/assets/systems and usually provides a distinct experience.
- **New campaign/questline:** substantial playable authored content.
- **Systems overhaul:** broad changes to gameplay loops, AI, progression, or roleplay without a new campaign.
- **Graphics overhaul:** broad visual replacement/tuning only; do not call it a content expansion.
- **Framework/trainer:** enables modifications or practice; not itself an expansion.

If no qualifying expansion exists, say so and keep a dated research gap instead of filling the list with unrelated presets.

## Recommendation views

Each game should have these independent views:

- **First playthrough:** bug fixes, safe performance, accessibility, and low-spoiler QoL; preserve intended balance/story.
- **After familiarity:** repetition reduction, movement/UI improvements, optional graphics and moderate system changes.
- **Post-game/replay:** randomizers, major balance changes, trainers, alternate progression, model/audio swaps, and overhauls.
- **Graphics combinations:** complete ownership map for HDR, SR/DLAA, RR, FG/MFG, neural rendering, ReShade, and overlays.

Use recommendation tiers Core, Strong, Optional, Experimental, and Avoid, plus confidence, difficulty, stability, and rollback cost.

## Combination review

Before recommending a group, build a conflict table for:

- files/proxies owned;
- config keys edited;
- loader and order;
- shader/resource interception;
- native versus injected feature ownership;
- save/progression effects;
- UI and keybind collisions;
- performance and VRAM budget;
- uninstall and rollback order.

Prefer a smaller compatible combination over a longer list with unresolved overlap.
