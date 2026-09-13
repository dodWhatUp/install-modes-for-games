# Quake II — categorized comparisons

Reviewed 2026-09-14; Steam build 20742936. Both original `quake2.exe` and remaster `quake2ex_steam.exe` are present; do not treat them as the same mod target.

| Category | Options / recommendation | Compatibility / cost |
|---|---|---|
| Foundation / manager | Remaster's built-in systems vs [Yamagi Quake II](https://www.yamagi.org/quake2/) for classic mods | Separate engine/data profiles; match game-DLL ABI and renderer. No MO2 required |
| Performance / stability | Remaster defaults vs maintained classic source port | Prefer the engine matching the desired mod; preserve config/save folders, don't replace all engines in place |
| Best graphics | Remaster for cohesive updated presentation; separate [Quake II RTX](../quake-ii-rtx/COMPARISONS.md) for path-traced lighting | RTX costs much more GPU time and does not automatically run remaster campaigns/mods |
| UI / controls / accessibility | Remaster native menus and accessibility vs classic-config tuning | Preferred first run: remaster. Config/console changes belong to their engine profile |
| Animation / enemy behaviour | Remaster's updated presentation/behaviour vs classic experience | Original and remaster have different gameplay feel; select deliberately before adding replacement game modules |
| Abilities / tools / mechanics | Original arsenal; mission-pack weapons and supported classic game modules | A custom game DLL replaces gameplay ownership; do not combine unrelated modules as ordinary add-ons |
| DLSS | No verified remaster DLSS integration selected | Use the separately documented RTX-fork route for DLSS research, not a blind proxy in the remaster |
| New content | [Remaster package](https://store.steampowered.com/app/2320/Quake_II/): base game, mission packs, Quake II 64 and Call of the Machine | These are official/included content, not community mods. Best immediate content choice |
| Community content | Classic maps/episodes through compatible source ports; [Yamagi installation/mission-pack support](https://github.com/yquake2/yquake2/blob/master/doc/020_installation.md) | Check each map's engine and licensed data requirements. Availability does not imply RTX/remaster compatibility |

## Recommended combinations

1. **First playthrough — Core:** remaster and included content; no third-party foundation needed. Difficulty 1, High source confidence, not locally launch-tested.
2. **After familiarity — Strong:** Call of the Machine and mission packs; compare classic via Yamagi in a separate directory. Difficulty 1–2.
3. **Replay — Optional:** author-supported custom episodes/game modules or the separate RTX visual profile. Difficulty 2–4 depending on engine/asset conversion.

Rollback: return to the original engine/config/save profile; custom game modules and their saves stay paired. Never upload original PAKs in the repository or Drive export.
