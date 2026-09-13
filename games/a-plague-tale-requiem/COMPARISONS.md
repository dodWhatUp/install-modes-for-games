# A Plague Tale: Requiem — categorized comparisons

Reviewed 2026-09-14; Steam build 11415435. [Local history](HISTORY.md) records title-scene NR operation, not full gameplay stability.

| Category | Options / recommendation | Tradeoff / limit |
|---|---|---|
| Management / foundations | Native menus and a manifest for the existing OptiScaler files | No general-purpose mod loader required for the current stack |
| Performance | Native DLSS Quality vs Balanced/Performance | Tune the actual game render mode; F7 NR scale is a separate operation, not DLSS render resolution |
| Graphics / DLSS | Native SR/FG baseline vs [existing OptiScaler-DLSSNR](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass) experiment | One SR bridge/NR consumer; keep native FG ownership. NR adds work; no RR integration or MFG upgrade verified in this review |
| Menus / configuration | Native graphics menu plus current compact/full NR controls | No verified F6 live-SR adapter; [control history](PREFERENCES.md) describes older mappings, general preference does not mean every existing game was migrated |
| QoL / accessibility | In-game difficulty, subtitles and accessibility options first | No independent QoL mod selected; avoid trainers during a first story run |
| Animation / enemy AI | Original authored behaviour | No verified standalone animation or AI overhaul found in this review |
| Abilities / magic / tools / mechanics | Original upgrades and authored mechanics | No sourced add-on introducing a new ability system selected; trainers are not content |
| New campaign / expansion | Original campaign and built-in replay options | No qualifying community campaign/total conversion verified; do not import Innocence mods |

## Recommended combinations

1. **First playthrough — Core:** native DLSS and original story/gameplay. Difficulty 1; High confidence in documented native integration, no new local gameplay test.
2. **After familiarity — Experimental:** compare one NR pass with NR off in the same moving scene, preserving native FG and disabling it only as a separate diagnostic if needed. Difficulty 3; Low confidence in long gameplay.
3. **Replay — Optional:** use existing replay tools; no invented expansion list. Multipass/finished-picture NR remains Experimental, not a content recommendation.

Sources: [upscaler compatibility](https://github.com/optiscaler/OptiScaler/wiki/Compatibility-List), [official game](https://www.focus-entmt.com/en/games/a-plague-tale-requiem), and dated local records. Exact native/HDR/FG delivery must be tested rather than inferred from DLL presence. Roll back using the newest controls snapshot first and then the original installation manifest; preserve current settings before either operation.
