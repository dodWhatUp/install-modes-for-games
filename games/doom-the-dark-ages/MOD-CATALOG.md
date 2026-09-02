# DOOM: The Dark Ages — Mod Catalog

Last reviewed: 2026-09-02. “Untested” means not tested locally; it is not a judgment that the mod is bad.

| Mod/tool | Category | Purpose | Important requirements/conflicts | Local state | Confidence |
|---|---|---|---|---|---|
| [Kaibz Mod (Advanced Options)](https://www.nexusmods.com/doomthedarkages/mods/27) | QoL, UI, input, gameplay, randomizer/overhaul | Broad configurable package: skip sequences/popups, HUD/input tweaks, gameplay customizer, AI randomizer, DLC options | Large surface area; choose modules carefully, read current changelog, use a new save for randomizer when instructed | Untested | Medium, current author page |
| [Console Unlocker](https://www.nexusmods.com/doomthedarkages/mods/12) | Framework/tool | Exposes console for diagnostics and settings | Console changes can invalidate comparisons; record every command | Untested | Medium |
| [Optimization and upgrade guide](https://www.nexusmods.com/doomthedarkages/mods/5) | Performance | Menu/console tuning including lower-VRAM and RT-off options | Quality compromises; its 4 GB presets are not a high-quality 16 GB recommendation; avoid combining unknown console edits | Untested | Low–Medium |
| [Intro Skip](https://www.nexusmods.com/doomthedarkages/mods/16) | QoL | Skips startup video | Redundant with `+com_skipIntroVideo 1`; use only one method | Prior launch option worked; mod untested | High for launch-option method |
| [cookn's tiny tweaks](https://www.nexusmods.com/doomthedarkages/mods/40) | QoL/gameplay | Selectable small gameplay changes | Requires Atlan Mod Loader; modules may alter balance | Untested | Medium |
| [PD Mod Pack](https://www.nexusmods.com/doomthedarkages/mods/85) | QoL | Collection of convenience changes | Inspect overlap with Kaibz/tiny tweaks before installing | Untested | Low–Medium |
| [Improved Shield Charge Cooldown](https://www.nexusmods.com/doomthedarkages/mods/36) | Gameplay | Shorter shield-charge cooldown, optional compensation | Changes combat balance | Untested | Medium |
| [Brutal Dark Ages](https://www.nexusmods.com/doomthedarkages/mods/91) | Gameplay/visual effects | More aggressive gameplay-particle presentation | Post-game taste; may overlap visual/performance experiments | Untested | Medium |
| [KEEP THE DEAD](https://www.nexusmods.com/doomthedarkages/mods/24) | Graphics/gameplay presentation | Longer-lived gore/corpses | Potential memory/performance cost; relevant on a VRAM-constrained graphics stack | Untested | Medium |
| [Realistic pickups and interactables](https://www.nexusmods.com/doomthedarkages/mods/109) | Gameplay presentation | Less game-like pickup/interactable visuals | Can reduce readability/accessibility | Untested | Medium |
| [Annoying effect be gone](https://www.nexusmods.com/doomthedarkages/mods/14) | Graphics | Removes fog, flares, bloom, blur, and some reflections | Large artistic change; removing RT reflections is not a pure clarity fix | Untested | Medium |
| [Blood Preset (ReShade)](https://www.nexusmods.com/doomthedarkages/mods/11) | Graphics/ReShade | Color/clarity preset | Conflicts with the current stock/no-ReShade goal and shares the global Vulkan concern | Untested | Low |
| RenoDX + DLSS5-Feeder experiment | Experimental graphics | Adds a community neural-rendering pass | Do not combine with OptiScaler/Smooth Motion; 4K failed on this 16 GB setup; estimated vectors and HUD processing | Partial: technical 1440p success, later 4K crash | High for local history, Low for recommendation |

## Expansion-scale status

No verified new campaign, total conversion, or Skyrim-scale content expansion was found in this review. Kaibz Advanced Options is a broad systems/gameplay overhaul and randomizer, but it is not a new campaign. Keep the expansion category open and re-check after major mod-kit releases.

## Compatibility groups to resolve before installation

- Select one owner for overlapping QoL/gameplay changes: Kaibz, tiny tweaks, PD pack, or an explicitly audited combination.
- Select one intro-skip method.
- Keep gameplay/persistence mods separate from graphics baseline testing so performance and crash causes remain attributable.
- ReShade presets, RenoDX, Feeder, global Vulkan registration, and other overlays require a hook/order review before combination.
