# Pathfinder: Kingmaker — categorized comparisons

## Spell clarity and conditional automation — reviewed 2026-10-12

**Decision:** Kingmaker Tactics is the strongest verified match for configurable combat automation. UI Extensions offers modest readability changes. No verified Kingmaker mod was found that rewrites the whole spellbook into concise beginner descriptions, compares all spells against the selected enemy, or supplies a compact recommendation dashboard.

This is a targeted update to the existing Kingmaker record. It is upstream research and a bounded source inspection, not an installed or gameplay-tested mod profile. The earlier broad review below remains historical. These recommendations concern Pathfinder: Kingmaker, not Wrath of the Righteous.

### Quick comparison

| Need | Candidate | Useful capability | Decision-changing limit |
|---|---|---|---|
| Conditional combat actions | [Kingmaker Tactics](https://www.nexusmods.com/pathfinderkingmaker/mods/420) | Ordered conditions and actions per companion; health/buff checks, spell and item actions, target selection | Real-time only; some enemy-stat rules use information not revealed by Inspect; very new |
| Repeated buff preparation | [Kingmaker Buff Bot](https://www.nexusmods.com/pathfinderkingmaker/mods/119) | Saved buff profiles; skip an already-present buff; optional combat-start casting | Does not choose the best tactical spell for the situation |
| More explicit preparation sequences | [PathfinderAutoBuff — Kingmaker](https://www.nexusmods.com/pathfinderkingmaker/mods/231) | Record or construct queues with caster, action and targets | Author cautions it may not work in combat; old release and targeting caveats |
| Existing interface readability | [UI Extensions](https://www.nexusmods.com/pathfinderkingmaker/mods/99) | Move Inspector, scale interface, show HP/pets, adjust combat information | Does not simplify spell descriptions or summarize weaknesses; author tested 2.0.x |
| Small organization conveniences | [Bag of Tricks guide](https://www.nexusmods.com/pathfinderkingmaker/articles/8) | Alphabetical spellbook sorting and selected interface conveniences | Broad cheat/tool package; enable only an explicitly selected convenience |

### Kingmaker Tactics: strong feature match, conditional recommendation

The author documents prioritized rules, AND/OR groups, party-wide rules, presets and six starter role packs. Available actions cover spells, abilities, items, toggles, movement and weapon sets. Conditions include party health, active effects, remaining resources and enemy defenses. Manual orders take priority, and each companion has a tactics toggle. Optional rules can maintain buffs outside combat. [Author description](https://www.nexusmods.com/pathfinderkingmaker/mods/420); [README](https://github.com/Gh05d/kingmaker-tactics).

For a conservative first configuration, the proposed examples are self-healing below a chosen health threshold and applying a specified missing party buff while reserving resources. These are configuration ideas, not imported or tested presets. Offensive area effects and enemy-stat targeting should remain manual when preserving the original information limits matters.

**Information-limit caveat — source inspected:** At upstream commit [0376b732c0a568b4c6ebf9c385609a2978efd81b](https://github.com/Gh05d/kingmaker-tactics/commit/0376b732c0a568b4c6ebf9c385609a2978efd81b), the [target resolver](https://github.com/Gh05d/kingmaker-tactics/blob/0376b732c0a568b4c6ebf9c385609a2978efd81b/KingmakerTactics/Engine/TargetResolver.cs) sorts enemies using their actual modified saves/AC. The inspected selection paths do not check whether Inspect revealed those numbers. Engine targeting restrictions can still apply; this does not establish unrestricted vision through fog. Default packs must be reviewed before claiming they preserve discovered-information-only play.

**Resources — source inspected:** The [cast validator](https://github.com/Gh05d/kingmaker-tactics/blob/0376b732c0a568b4c6ebf9c385609a2978efd81b/KingmakerTactics/Engine/ActionValidator.Cast.cs) checks castable slots, availability, class resources and charges. The inspected [executor](https://github.com/Gh05d/kingmaker-tactics/blob/0376b732c0a568b4c6ebf9c385609a2978efd81b/KingmakerTactics/Engine/CommandExecutor.cs) submits ordinary animated game cast commands. This supports ordinary action/resource handling in those paths, not an exhaustive certification of all behavior.

**Compatibility and practical limits:**

- Requires Kingmaker Enhanced Plus Edition **2.1.7+** and Unity Mod Manager **0.23.0+**.
- First uploaded **3 October 2026**; the current file is **KingmakerTactics-1.0.1.zip**, dated **6 October 2026**. Its changelog addresses periodic hitches and overly frequent evaluation during rest/global-map travel. These are author-reported fixes, not a benchmark from this review.
- Tactics pause in native turn-based mode.
- The author says offensive area targeting does not account for friendly melee characters in the blast; the default arcane pack disables Fireball/Lightning Bolt rules.
- In-combat consumables need the acting character's quick slots.
- The author documents Buff Bot coexistence, but duplicate buff rules need missing-buff conditions.

Source: [description](https://www.nexusmods.com/pathfinderkingmaker/mods/420) and [versioned files/changelog](https://www.nexusmods.com/pathfinderkingmaker/mods/420?tab=files).

Do not reuse the README's claim that any positive DC-minus-save margin means likely failure. A plain d20 calculation gives 50% failure at a margin of 11 and 70% at 15; immunities, spell resistance and special effects are separate. This is a mathematical clarification, not a verified percentage display in the mod.

### Buff Bot versus AutoBuff

**Buff Bot** remains the simpler curated starting point for repeating chosen buffs. Its official page documents profiles, skipping existing buffs, items/abilities-first behavior and a combat-start trigger. Version **King2.0** was last updated **19 April 2021**. The author also records historical execution fixes; current local compatibility is not established. [Source](https://www.nexusmods.com/pathfinderkingmaker/mods/119).

**AutoBuff** is a reasonable alternative when recording and replaying a particular sequence matters. The queue specifies caster, spell/ability and targets, and can preactivate an item or ability such as a metamagic rod. Favorite queues have a small execution panel. Version **0.2.0** was last updated **25 October 2021**. The author warns about combat use, certain spell targets and conflicts with other command-ending patches. Use the Kingmaker build. [Source](https://www.nexusmods.com/pathfinderkingmaker/mods/231); [author README](https://github.com/ilkar399/PathfinderAutoBuff).

Choose one buff workflow initially. Adding both is not necessary to obtain their shared benefit. No instant/free-casting or duration-extension mode is recommended.

### What can improve clarity now

**Native Inspect:** The official game update describes skill-gated information about creature strengths and weaknesses. Revealed information appears when hovering over the unit or its combat-log entry. The game also supports larger dialogue/description text. [Official patch 1.1](https://store.steampowered.com/news/posts/?appids=640820&enddate=1542733228&feed=steam_community_announcements).

**Native turn-based combat:** It gives time to compare actions without altering the numerical difficulty setting. The developer documents switching between real-time and turn-based play, including during combat. This is useful for learning or complex fights; no old turn-based mod is required. Timing and tactics differ between modes, so this is not a promise of identical practical difficulty. [Developer explanation](https://blog.playstation.com/2020/08/18/rpg-pathfinder-kingmaker-definitive-edition-launches-on-ps4-today/).

**Combat log:** Its attack-roll tooltip exposes relevant bonuses and penalties. Official Enhanced Edition notes also document spell-selection fields for spell resistance, descriptors and casting time. [Official notes](https://store.steampowered.com/news/posts/?appids=640820&enddate=1560777654).

**UI Extensions:** Version **1.2.3**, updated **16 November 2019**, allows Inspector placement, UI scaling, HP/pet displays and combat-information controls. The explicit tested game list is **2.0.x**. It is a modest readability candidate, not a rewritten tooltip system, and current-build compatibility remains a gate. [Source](https://www.nexusmods.com/pathfinderkingmaker/mods/99?tab=description).

### A short spell-reading method

This is a proposed external reading method, not a discovered mod feature.

| Read first | Decision question |
|---|---|
| Effect and eligible targets | Damage, control, healing or buff? Single target or area? Is this creature eligible, and can allies be affected? |
| Defense and save outcome | Does it test AC/touch AC or a Fortitude, Reflex or Will save? Does a successful save negate the effect or reduce it? |
| Immunity and resistance | Does the creature resist the damage type, have immunity to the effect, or have spell resistance relevant to this spell? |
| Casting time, duration and uses | Can it act in time, how long does it last, and what limited resource is being spent? |

Lower enemy saving throws generally favor spells testing that save when other factors match. A low save is not permission to ignore immunity or targeting restrictions. A damage-only ranking would also miss the value of preventing enemy actions.

The underlying terminology is explained in the [Pathfinder rules reference](https://legacy.aonprd.com/coreRulebook/magic.html). This is rules background; the game's own implementation and current spell description take precedence over tabletop differences.

### Exclusions and remaining gaps

- KingmakerAI is designed to change the challenge and depends on other rules/content mods. It is not the neutral convenience recommendation. [Author](https://github.com/Holic75/KingmakerAi/).
- Enhanced Inventory, Inspect Everything, ToyBox and Bubble Buffs results often concern Wrath. No Kingmaker port of their requested spell-comparison features was verified in this review. Kingmaker Tactics is the specifically verified exception: it really is a Kingmaker port.
- Kingmaker Bugfixes contains narrow text/UI corrections but also mechanical fixes. No verified all-cosmetic configuration was established here; it is not a blanket clarity recommendation.
- No automatic spell recommender or comprehensive plain-language spell rewrite was verified. This is the result of a bounded search, not proof that no unpublished or obscure project exists.
- No game installation, launch, settings change, save loading, benchmark or reminder was performed. Current build, existing loader/mods, combination stability and rollback remain installation gates.
- Proposed next useful work, if installation is requested: verify the current build and mod profile, snapshot relevant settings/saves, then try a minimal party-only Tactics configuration in real-time mode. A turn-based-only user gets no automated-turn execution from Tactics. A party-specific spell sheet needs the actual spell list; no character build is inferred here.


## Previous broad review — 2026-09-14

Reviewed 2026-09-14; Steam build 6757524; `Kingmaker.exe` present. Exact game patch and mod compatibility require confirmation before installation.

| Category | Options / recommendation | Dependencies / conflicts / save impact |
|---|---|---|
| Manager + mod menus | [Unity Mod Manager](https://www.nexusmods.com/site/mods/21) | Preferred runtime loader/manager; a Vortex download alone is insufficient. Back up the chosen injection/assembly path |
| QoL | [Kingmaker Buff Bot](https://www.nexusmods.com/pathfinderkingmaker/mods/119) vs manual pre-buffing | Strong repetition-reduction candidate; requires UMM, inspect spell/resource use and current patch compatibility |
| General tools / UI | [Bag of Tricks](https://www.nexusmods.com/pathfinderkingmaker/mods/26) vs original settings | Broad convenience/cheat tool; enable only chosen QoL functions. Wrong save/quest edits can persist after uninstall |
| Performance / save size | [Cleaner](https://www.nexusmods.com/pathfinderkingmaker/mods/39) vs retaining world loot/state | Conditional troubleshooting tool, not an automatic optimizer; cleanup may remove world items/state. Keep a full save backup |
| Abilities / magic / classes | [Call of the Wild](https://github.com/Holic75/KingmakerRebalance) vs vanilla classes | Adds tabletop-inspired classes, spells and feats; recommended for a new replay character. Saves become dependent on added blueprints |
| Mechanics / tactical combat | Native turn-based mode vs real-time-with-pause; [Proper Flanking 2](https://www.nexusmods.com/pathfinderkingmaker/mods/146) for deeper rules changes | Do not add obsolete turn-based mods to a game with native mode. Proper Flanking requires Call of the Wild and needs conflict review with other tabletop overhauls |
| Enemy behaviour | Original difficulty / encounter systems | Rule and class mods change combat, but no distinct enemy-AI improvement is certified here |
| Animation / graphics | Original visuals; optional cosmetic portrait assets | No validated animation or graphics overhaul selected; ReShade colour styling is optional, not a performance fix |
| DLSS | No verified SR/DLAA/RR/FG/MFG/NR integration selected | This game does not gain temporal inputs merely by adding an NVIDIA DLL |
| Added content | Official campaign DLC if owned; Call of the Wild is a systems expansion | No verified community campaign/total conversion found. New classes are not a new authored campaign |

### Previous recommended combinations

1. **First playthrough — Strong:** UMM + Buff Bot after testing; leave Bag of Tricks cheats off. Difficulty 2, Medium upstream/Low local confidence; low intended rendering cost.
2. **After familiarity — Optional:** selected Bag of Tricks conveniences; Cleaner only for a demonstrated save-state problem after backup. Difficulty 2–3; persistence risks outweigh a speculative performance gain.
3. **Replay — Strong candidate:** Call of the Wild, optionally its explicitly supported flanking rules, on a new character. Difficulty 3–4; substantial save dependency, no expected graphics improvement.

Rollback: restore UMM injection changes and the full mod profile; restore a pre-mod save for Call of the Wild or altered quest state. Removing a class blueprint DLL while continuing a dependent save is not a valid rollback. Kingmaker mods are not interchangeable with Wrath of the Righteous/Toy Box.
