# Pathfinder: Kingmaker — categorized comparisons

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

## Recommended combinations

1. **First playthrough — Strong:** UMM + Buff Bot after testing; leave Bag of Tricks cheats off. Difficulty 2, Medium upstream/Low local confidence; low intended rendering cost.
2. **After familiarity — Optional:** selected Bag of Tricks conveniences; Cleaner only for a demonstrated save-state problem after backup. Difficulty 2–3; persistence risks outweigh a speculative performance gain.
3. **Replay — Strong candidate:** Call of the Wild, optionally its explicitly supported flanking rules, on a new character. Difficulty 3–4; substantial save dependency, no expected graphics improvement.

Rollback: restore UMM injection changes and the full mod profile; restore a pre-mod save for Call of the Wild or altered quest state. Removing a class blueprint DLL while continuing a dependent save is not a valid rollback. Kingmaker mods are not interchangeable with Wrath of the Righteous/Toy Box.
