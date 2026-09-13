# Skyrim Special Edition — comparisons and setup

Reviewed 2026-09-14. Local runtime **1.7.104.0**, Steam build **24914197**, x64 Direct3D 11. ReShade 6.8.0.2155 is already present as `dxgi.dll`. No SKSE loader was present in the initial root inventory. Only the four free Creation Club packages and the official expansions were observed; the paid Anniversary Upgrade is **not assumed owned**.

## Current-runtime foundation

| Component | Why / choice | Exact support boundary | Priority / difficulty |
|---|---|---|---|
| [Mod Organizer 2 2.5.2](https://github.com/ModOrganizer2/modorganizer/releases/tag/v2.5.2) | Recommended manager: explicit mod priority, profiles and virtual file deployment | Use a dedicated local instance outside the game and cloud sync; root hooks need separate ownership | Core / 2 |
| [Vortex](https://www.nexusmods.com/about/vortex/) | Alternative for easier Nexus Collections | Use one deployment manager per game; do not deploy the same files through Vortex and MO2 | Alternative / 2 |
| [Wabbajack](https://www.wabbajack.org/) | Install a maintained whole list when its overall design is wanted | Not a basic patch; list-specific runtime, DLC, space and download requirements | Optional replay / 3–4 |
| [SKSE64 2.3.1](https://skse.silverlock.org/) | Script extension and entry point for SkyUI/plugins | Author explicitly matches Steam 1.7.104; 2.2.6 is not the right Steam runtime here | Core / 2 |
| [Address Library v13](https://www.nexusmods.com/skyrimspecialedition/mods/32444?tab=files) | Address database for dependent DLLs | Includes `versionlib-1-7-104-0.bin`; database availability does not make old DLL layouts compatible | Core when required / 1 |
| [SkyUI 6.11](https://www.nexusmods.com/skyrimspecialedition/mods/12604) | Searchable inventory, favourites and Mod Configuration Menu | Match current SkyUI scripts/SWF files; do not automatically install SkyUI 5-era interface patches | Core / 1 |
| [MCM Helper 1.6.3](https://www.nexusmods.com/skyrimspecialedition/mods/53000?tab=files) | Persistent configuration support for dependent mods | Author file supports Steam 1.7.99+ and requires SkyUI 6+ | Core for compatible MCM mods / 1 |
| [USSEP](https://www.afkmods.com/Unofficial%20Skyrim%20Special%20Edition%20Patch%20Readme%20%2B%20Credits.html) | Broad quest/object fixes; preferred once masters match | Inspect current requirements and existing saves; it makes some balance/interpretive changes too | Strong / 2 |
| [SSE Engine Fixes](https://github.com/aers/EngineFixesSkyrim64/releases) | Engine bug/performance fixes | Latest observed GitHub asset is 7.0.21-beta5, 2026-08-23; beta status and exact 1.7.104 support require package/log review. Do not follow obsolete Part 2 instructions blindly | Strong candidate, gated / 2 |
| [SSE Display Tweaks](https://www.nexusmods.com/skyrimspecialedition/mods/34705) | Frame pacing, borderless and high-FPS physics | Original-page features are documented; exact 1.7.104 binary is not established here. [Unofficial 1.7.104 patch](https://www.nexusmods.com/skyrimspecialedition/mods/189737) is a separate experimental option | Strong candidate, gated / 2 |
| [LOOT](https://loot.github.io/) / [xEdit](https://tes5edit.github.io/) | Sort metadata / inspect and resolve record conflicts | Sorting does not create missing compatibility patches. Do not automatically clean everything | Strong tools / 2–3 |

Foundation candidates have low intended GPU cost. No local performance measurements or modded launch success are implied. Exact installed files and hashes belong in [HISTORY](HISTORY.md), not in this candidate list.

## Performance: compare the actual bottleneck

| Option | Expected benefit | Cost/conflict | Decision |
|---|---|---|---|
| Runtime-matched Engine Fixes + Display Tweaks | Fix engine behaviour and pacing; support controlled high FPS | DLL compatibility and shared display settings | First choice after runtime verification; do not uncap physics with unsupported DLLs |
| [eFPS](https://www.nexusmods.com/skyrimspecialedition/mods/54907) | Exterior occlusion reduces unnecessary draws | Added/modified buildings need matching occlusion patches; bad combinations can hide objects | Optional after city/world list is final |
| [Skyrim Project Optimization](https://www.nexusmods.com/skyrimspecialedition/mods/14084) | Interior occlusion | Interior overhauls may need patches | Alternative area-specific optimization, not the same function as eFPS |
| [SSE FPS Stabilizer](https://www.nexusmods.com/skyrimspecialedition/mods/38438) | Adjust supported settings in response to load | Visible quality variation; runtime gate and competing dynamic settings | Optional; not a substitute for fixing an overloaded mod list |
| 2K textures, moderate grass, capped distant detail | Preserve VRAM and CPU headroom | Less microdetail than huge texture/LOD packs | Recommended starting budget on 16 GB, especially with graphics injection |
| Unexplained INI/FPS bundles | Uncertain | May remove visual quality, change the same settings, or misrepresent gains | Avoid blanket installs; compare one documented change at a time |

## Graphics and every DLSS type

**Best practical target:** [Community Shaders](https://www.nexusmods.com/skyrimspecialedition/mods/86492), a modest texture base, and its [official Upscaling feature](https://www.nexusmods.com/skyrimspecialedition/mods/156952). This balances extensible graphics with an engine input path. It is a preference-based selection, not a measured winner on this machine.

The latest GitHub release observed is [CS 1.8.4](https://github.com/community-shaders/skyrim-community-shaders/releases/tag/v1.8.4), dated 2026-08-27. General text saying “latest Steam” is insufficient to certify 1.7.104. No explicit matching release statement was established in this review. Keep this stage gated until the exact DLL and dependencies pass support checks. Do not substitute CS Lite or copy one DLL from another package without a separate compatibility review.

| Feature / comparison | Choice and tradeoff | Ownership / status |
|---|---|---|
| DLSS SR vs DLAA | Start Quality for performance; DLAA for native-resolution anti-aliasing if headroom allows | Official CS Upscaling provides the integration; gated for this runtime |
| FSR SR vs DLSS SR | DLSS is the preferred RTX 5070 Ti starting point; FSR is an alternative to compare | One active temporal upscaler |
| Frame generation | Published Upscaling page documents **FSR Frame Generation**, including with DLSS SR | Do not label this NVIDIA DLSS FG; test after base pacing, in supported windowed/borderless mode and refresh rate |
| NVIDIA DLSS FG / MFG | Not verified for the selected current package | No promise of x3/x4/x6 generation merely because this GPU supports other games' MFG |
| Ray Reconstruction | No validated RR integration selected | Shader lighting or SSGI is not path tracing and does not create RR inputs |
| DLSS neural rendering | No Skyrim-specific validated NR combination selected | Experimental research only; do not add Feeder/OptiScaler over the preferred CS path automatically |
| CS vs [ENB](http://enbdev.com/download_mod_tesskyrimse.html) | CS preferred for this modular setup; ENB is an alternative for a particular authored cinematic preset | Separate profiles; never two shader cores. Runtime, ENB-upscaler variant and proxy requirements must be checked |
| CS vs ReShade alone | CS changes engine rendering; ReShade mainly changes the finished image | Preserve existing ReShade initially; later use the exact chain in [CS FAQ](https://github.com/community-shaders/skyrim-community-shaders/wiki/FAQ) |
| [Skyland AIO](https://www.nexusmods.com/skyrimspecialedition/mods/34179) vs [Skyrim 202X](https://www.nexusmods.com/skyrimspecialedition/mods/2347) | Skyland 2K is the cohesive baseline pick; 202X suits higher-detail/parallax customization with more VRAM/asset-order work | Select one base, then intentional overrides; no blanket 8K recommendation |
| HDR Display feature vs SDR | [CS HDR Display](https://www.nexusmods.com/skyrimspecialedition/mods/179371) is a separate output experiment | One tonemapper; check display HDR and luminance, not just a 10-bit buffer |

Do not install superseded standalone Light Limit Fix/Dynamic Cubemaps features when the selected CS version already includes them. The current official Upscaling page lists DLSS/FSR, not XeSS; do not infer XeSS from old generic CS descriptions. Generated FPS is not rendered FPS.

## UI, menus, configuration and QoL

| Choice | What changes | Comparison / conflicts | Tier |
|---|---|---|---|
| SkyUI + MCM Helper | Inventory search, favourites, settings | Preferred basic UI; establish these before reskins | Core |
| [TrueHUD](https://www.nexusmods.com/skyrimspecialedition/mods/62775) | Actor/boss information | Optional HUD extension, not a whole inventory replacement; verify runtime and HUD skin | Strong after foundation |
| [NORDIC UI](https://www.nexusmods.com/skyrimspecialedition/mods/49881) | Broad visual reskin | Compare with plain SkyUI; require a skin matching SkyUI 6.11 and selected HUD | Optional; version-gated |
| [QuickLoot IE](https://www.nexusmods.com/skyrimspecialedition/mods/120075) | Loot preview without opening the full container interface | Prefer as a candidate over old RE/EE packages, but verify 1.7.104; EE skins do not automatically work with rewritten IE | Strong candidate |
| [Wheeler](https://www.nexusmods.com/skyrimspecialedition/mods/97345) | Radial equipment/spell selection | Compare with SkyUI favourites; more dependencies/input overlap, especially controllers | Optional, runtime-gated |
| [Immersive Equipment Displays](https://www.nexusmods.com/skyrimspecialedition/mods/62001) | Display carried equipment on characters | Cosmetic utility; not new weapon mechanics; needs matching plugin and skeleton requirements | Optional |

Do not assign graphics F6/F7/F10–F12 to spell wheels or combat by default. The full graphics menu preference is Delete where supported; CS's documented default is End. No custom NR slots or live SR shortcut is claimed installed by adding an INI alone. ReShade Home remains its own menu.

## Animation and movement

| Option | Goal | Compare / dependency / risk | Tier |
|---|---|---|---|
| [Open Animation Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/92109), observed 3.2.1 | Conditional animation framework with editor | Preferred framework candidate over old DAR; install only with chosen animation packs and required fixes | Strong; runtime-gated |
| [Pandora Behaviour Engine+](https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus) | Generate behaviour output required by selected mods | OAR and Pandora do different jobs. OAR replacers do not all require generated behaviours | Optional dependency / 3 |
| [Nemesis](https://github.com/ShikyoKira/Project-New-Reign---Nemesis-Main) | Alternative behaviour generator | Use when the chosen package specifically supports/requires it; one final generated output, not two conflicting outputs | Alternative / 3 |
| [True Directional Movement](https://www.nexusmods.com/skyrimspecialedition/mods/51614) | Modern third-person movement and targeting | Preferred over a full combat conversion for a modest change; validate requirements and animation output | Strong later / 3 |
| [Precision](https://www.nexusmods.com/skyrimspecialedition/mods/72347) | Melee collision/hit feedback | Adds mechanics as well as presentation; compare against vanilla hit behaviour in narrow rooms | Optional later / 3 |
| Vanilla first-person combat | Preserve familiar control and timing | Smallest compatibility surface; no need to install a third-person stack when playing first person | Core first playthrough |

Animation frameworks alone do not add new authored moves. Generated behaviour/skeleton output belongs in its own MO2 mod. Preserve its matching inputs and regenerate after changing the animation set.

## Enemy behaviour and civilian AI

| Comparison | Recommended use | Important boundary |
|---|---|---|
| [Blade and Blunt](https://www.nexusmods.com/skyrimspecialedition/mods/34549) vs [Valravn](https://www.nexusmods.com/skyrimspecialedition/mods/53869) | Blade and Blunt for a Simonrim-style resource-management profile; Valravn for an alternative integrated combat rebalance | Choose one. Both change balance; neither is a bug-fix-only install. Blade and Blunt's observed 4.0.3 still requires dependency/runtime review |
| [AI Overhaul SSE](https://www.nexusmods.com/skyrimspecialedition/mods/21654) vs [Immersive Citizens](https://www.nexusmods.com/skyrimspecialedition/mods/173) | AI Overhaul is the preferred patchable civilian-schedule candidate for a growing list | They are primarily civilian AI alternatives, not interchangeable enemy combat mods; NPC appearance/AI records and town layouts require patches |
| Original enemy behaviour | First playthrough recommendation | Avoid masking combat changes as performance improvements |

## Unique abilities, perks, magic and tools

| Comparison | Best fit | Conflict / save consequence |
|---|---|---|
| [Vokrii](https://www.nexusmods.com/skyrimspecialedition/mods/26176) vs [Ordinator](https://www.nexusmods.com/skyrimspecialedition/mods/1137) | Vokrii for modest perk expansion; Ordinator for many new build identities | One perk-tree owner. Start a dedicated character or follow the author's respec process; disabling the plugin is not a complete save rollback |
| [Mysticism](https://www.nexusmods.com/skyrimspecialedition/mods/27839) vs [Apocalypse](https://www.nexusmods.com/skyrimspecialedition/mods/1090) | Mysticism for rebalanced vanilla magic plus additions; Apocalypse for a broader spell toolbox | Not identical: overhaul vs added spells. They can require compatibility/perk patches; do not combine by default |
| [Wintersun](https://www.nexusmods.com/skyrimspecialedition/mods/22506) vs original blessings | Religion/favour progression for roleplay after familiarity | Additional persistent mechanics; separate save/profile |
| [Experience](https://www.nexusmods.com/skyrimspecialedition/mods/17751) vs original levelling | Exploration/quest-driven progression for a replay | Runtime-gated DLL and progression changes; not a first-run convenience patch |
| [Spell Perk Item Distributor](https://www.nexusmods.com/skyrimspecialedition/mods/36869) | Give supported NPCs selected spells/perks/items through dependent mods | Framework only; it does not add a spell collection by itself. Review every distribution file and current runtime support |
| [SunHelm](https://www.nexusmods.com/skyrimspecialedition/mods/39414) vs built-in Survival Mode | SunHelm for configurable needs; built-in mode for a simpler supported option | Choose one needs/cold system. Extra dependencies and UI integration; more friction is intentional gameplay |

## Extending the game: authored content

| Project | Actual type / why choose it | Dependencies and rollback |
|---|---|---|
| [Beyond Skyrim: Bruma](https://www.nexusmods.com/skyrimspecialedition/mods/10917) | New region/quests in Cyrodiil; preferred lore-oriented expansion candidate | This is Bruma, not a promise that all Beyond Skyrim provinces are released. Review masters and patches; restore pre-install save to remove |
| [Wyrmstooth](https://www.nexusmods.com/skyrimspecialedition/mods/45565) | Focused new island and questline; smaller commitment than a collection-centred overhaul | Check current author install instructions; dedicated save checkpoint |
| [Legacy of the Dragonborn](https://www.nexusmods.com/skyrimspecialedition/mods/11802) | Museum, collecting, quests and long-form progression hub | Plan before starting; extensive [official patches](https://www.nexusmods.com/skyrimspecialedition/mods/30980). Major version transitions can require a new game |
| [Enderal: Forgotten Stories SE](https://store.steampowered.com/app/976620/Enderal_Forgotten_Stories_Special_Edition/) | Total conversion with a separate world and campaign | Separate installation/profile and saves; requires Skyrim SE ownership. Never add as another plugin to the Skyrim list |

**Content pick:** Bruma or Wyrmstooth for extending Skyrim; Legacy for a collection-focused new character; Enderal for a distinct game. These are alternatives by goal, not an instruction to install all four together.

## Curated combinations

1. **First playthrough — recommended:** MO2 + matching SKSE/Address Library + SkyUI/MCM Helper; verified bug fixes; modest texture base. Difficulty 2, conditional until launch-tested. Leave original combat/perks/story intact.
2. **After familiarity:** first-playthrough profile plus verified CS/Upscaling, one HUD/loot improvement, and optionally TDM/Precision. Add one subsystem per test. Difficulty 3; Medium purpose confidence, Low exact-stack confidence.
3. **Replay with new builds:** select one combat overhaul, one perk overhaul and one magic approach; use their required patches. Add Bruma or Wyrmstooth after a stable checkpoint. Difficulty 4, new/copy save recommended.
4. **Collection campaign / total conversion:** Legacy-centred curated list on a new save, or Enderal separately. Difficulty 4; large disk/time cost and persistent dependencies.

## Reversal and validation

MO2 profiles isolate Data files, not every root DLL or external setting. Record SKSE root files separately. Before changing hooks, close Skyrim and relevant processes, snapshot ReShade, settings, launch options and saves, and preserve the baseline. Do not remove a scripted overhaul and continue the same save as if nothing happened.

Verify stock first, SKSE version next, SkyUI inventory and MCM next, then each fix. Test saves/load, a town, combat, interiors/exteriors and clean shutdown. Graphics validation adds moving foliage, HUD, water, alt-tab, resolution recreation and rendered/generated FPS. Hashes and file placement prove installation only.
