# A Plague Tale: Innocence — categorized comparisons

Reviewed 2026-09-14; Steam build 4336652; `APlagueTaleInnocence_x64.exe` present. Information-only; no local graphics test performed.

| Category | Options / recommendation | Requirements / limits |
|---|---|---|
| Manager / foundations | Manual manifest for selected shader files | No verified universal mod manager/loader needed |
| Performance | Native settings and a sensible frame cap | No author-backed performance package qualified in this review; presets may trade away image quality |
| Best graphics / HDR | Game-specific entry in the [RenoDX mod list](https://github.com/clshortfuse/renodx/wiki/Mods) vs original SDR | HDR candidate, not locally validated; follow its linked exact game profile. One tonemapper; inspect existing hooks first |
| Alternative graphics | [ReShade](https://reshade.me/) colour preset vs [geo-11 stereo fix](https://helixmod.blogspot.com/2022/11/a-plague-tale-innocence-dx11.html) | Colour styling and stereoscopic 3D solve different problems; geo-11 is not DLSS. Do not combine proxies without author instructions |
| DLSS SR/DLAA/FG/MFG/RR/NR | No verified integrated route selected | Feeder would be a separate synthetic-input experiment, not native upscaling; no DLL rename creates the missing feature |
| QoL / UI / configuration | Native subtitles, controls and graphics menus; ReShade controls only if selected | No game-wide MCM equivalent verified |
| Animation / enemy behaviour | Original cinematic animation and enemy systems | No qualifying separate overhaul found |
| Abilities / magic / tools / mechanics | Original story progression | No verified new mechanics package selected; a cheat table would not be an expansion |
| Added content | Original campaign / replay | No verified new campaign or total conversion found in the [game catalog](https://www.nexusmods.com/games/aplaguetaleinnocence/mods) |

## Recommended combinations

1. **First playthrough — Core:** original game, preferred accessibility settings. Difficulty 1, conservative recommendation.
2. **After familiarity — Optional:** game-specific RenoDX HDR profile if an HDR display/output is confirmed. Difficulty 3, Medium upstream/Low local confidence, GPU impact unmeasured.
3. **Post-game — Experimental:** stereo or neural-rendering research in separate profiles, never both initially. Difficulty 4–5; no authored content extension verified.

Rollback: snapshot executable-adjacent hooks, presets and user settings; remove only manifested additions and restore originals. No save changes are needed for a pure graphics comparison. Requiem packages are not interchangeable with Innocence.
