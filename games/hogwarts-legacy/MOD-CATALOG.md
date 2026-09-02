# Hogwarts Legacy — Mod Catalog

Last reviewed: 2026-09-02. Catalog entries are candidates; only rows marked working were locally tested.

| Mod/tool | Category | Purpose | Important requirements/conflicts | Local state | Confidence |
|---|---|---|---|---|---|
| [Ultra Plus](https://www.nexusmods.com/hogwartslegacy/mods/660) | Graphics, performance, bug fixes, overhaul | Integrated streaming, RT, lighting, quality and performance profiles | Author says not to combine with Ascendio, Cinematic Ultra, SLPF, or other Engine.ini mods; choose texture tier by VRAM | Working baseline; older local setup than current upstream 13.3.4 | High locally, refresh before update |
| [Ascendio III](https://www.nexusmods.com/hogwartslegacy/mods/69) | Performance/engine tweaks | Alternative FPS/stutter and RT tuning | Alternative to Ultra Plus, not an add-on to it; older 3.1.0 release | Untested | Medium |
| [OptiScaler](https://github.com/optiscaler/OptiScaler) | Graphics/upscaling/neural | Intercepts native temporal-upscaler inputs | Install beside real executable; one FG owner; separate from RenoDX/Feeder experiments | Working conservative baseline | High for recorded build |
| [RenoDX game list/profile](https://github.com/clshortfuse/renodx/wiki/Mods) | HDR/graphics | Upstream list marks a Hogwarts Legacy Unreal profile working | Distribution may be via current RenoDX Unreal channel; separate profile required before combination with OptiScaler/ReShade | Untested locally | Medium upstream |
| [Blueprint Apparate Modloader](https://www.nexusmods.com/hogwartslegacy/mods/56) | Framework | Loads multiple Blueprint logic mods without a DLL hook | Chunk/load-order conflicts still possible; do not load the same mod through Apparate and UE4SS | Untested | Medium |
| [Apparate UI](https://www.nexusmods.com/hogwartslegacy/mods/1335) | UI/mod management | In-game UI for Apparate | Requires Apparate and UICore; chunk 1310 conflict risk | Untested | Medium |
| [Mouse Controls for Broom](https://www.nexusmods.com/hogwartslegacy/mods/61) | Movement/controls/QoL | Full mouse broom control including ascent/descent | Choose one normal/inverted variant; reset bindings if needed; Steam Cloud may restore input settings | Untested | Medium |
| [Broom and Mount Controls Remapping](https://www.nexusmods.com/hogwartslegacy/mods/358) | Movement/controls | Alternative mouse/controller layout | Alternative to other broom-control packages; reset/remap controls | Untested | Medium |
| [Skip Merlin Trials](https://www.nexusmods.com/hogwartslegacy/mods/2139) | QoL | Complete nearby trials or skip ending animation | Apparate dependency; chunk 1049; reported interaction with UICore | Untested | Medium |
| [Night Curfew](https://www.nexusmods.com/hogwartslegacy/mods/1748) | Gameplay/roleplay system | Prefects and penalties during castle curfew | Newer official-mod-system port exists; legacy version requires Apparate and can conflict through SQL/chunks/minimap changes | Untested | Medium |
| [Azkaban](https://www.nexusmods.com/hogwartslegacy/mods/1786) | Gameplay/roleplay system | Consequences for witnessed Unforgivable Curses | SQL merge/load-order and save/quest behavior require review | Untested | Medium |
| [AnyTimeCompanion](https://www.nexusmods.com/hogwartslegacy/mods/841) | Gameplay | Spawn classmates as companions | Balance varies and companion dependencies/updates must be checked | Untested | Medium–Low due age |
| [Lore Friendly Apparition](https://www.nexusmods.com/hogwartslegacy/mods/1162) | Movement/traversal | Restricted world teleportation | Requires Apparate; known border/out-of-bounds and broom issues | Untested | Medium |
| [The Walking Mod](https://www.nexusmods.com/hogwartslegacy/mods/765) | Movement/QoL | Walking/auto-walk behavior | Requires Apparate; author notes possible broom-challenge behavior | Untested | Low–Medium |

## Expansion-scale status

No verified Skyrim-scale new campaign or total conversion was found in this review. Night Curfew, Azkaban, companions, and apparition add meaningful roleplay/gameplay systems and can form an “immersive Hogwarts” overhaul profile, but they are not a full expansion. Official in-game mod ports may supersede older legacy-loader versions; verify before installing.

## Compatibility groups

- Graphics/performance baseline: choose Ultra Plus **or** Ascendio/other Engine.ini packs.
- Graphics injection: use separate OptiScaler and RenoDX test profiles until exact compatibility is proven.
- Logic loader: load a given mod through Apparate **or** UE4SS, never both.
- Audit `.pak/.utoc/.ucas` chunk IDs and SQL payloads before combining gameplay systems.
- Back up saves before curfew, prison, companion, season, or progression-changing mods.
