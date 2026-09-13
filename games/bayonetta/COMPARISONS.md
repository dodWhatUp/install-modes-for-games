# Bayonetta — categorized comparisons

Reviewed 2026-09-14; Steam build 1824749, 32-bit D3D9. [Existing catalog](MOD-CATALOG.md) retains the source links and tested helper history.

| Category | Options / selection | Tradeoff / conflict |
|---|---|---|
| Manager / foundation | Explicit asset manifest; author's installer for a selected package | No Skyrim-style manager required. Existing graphics crosses x86/x64, so arbitrary root DLLs are unsafe |
| Performance | Original renderer vs existing dgVoodoo/ReShade/helper chain | Original path has less overhead. Historical NR pass is an image change, not a proven FPS improvement |
| Best graphics | Original presentation for play; existing full-resolution neural profile for comparison | Technical 4K delivery was observed; 67% helper scale produced black captures. Do not repurpose general F7 25% as proven safe here |
| UI / controller | [Proper PS4 Button Prompts](https://www.nexusmods.com/bayonetta/mods/59) vs original Xbox prompts | Select according to actual controller; texture replacement and disk/VRAM footprint need review |
| QoL | [No-Intro](https://www.nexusmods.com/bayonetta/mods/82) vs original intro | Small convenience candidate; preserve each replaced file |
| HUD / effects | [No-HUD-No-Effects](https://www.nexusmods.com/bayonetta/mods/113) vs normal HUD | Photo/capture option; shader hook overlap with the current chain must be tested |
| Animation / appearance | [Bayonetta 2 Models](https://www.nexusmods.com/bayonetta/mods/42) vs original models | Cosmetic replacement, not Bayonetta 2 combat or campaign |
| Enemy / abilities / mechanics | [BayonettaTrainer V2](https://www.nexusmods.com/bayonetta/mods/63) for practice vs original balance | x86 tool using dinput8; broad cheats/practice controls, not a first-run recommendation or AI overhaul |
| Added content | Original difficulties and challenge progression | No verified new campaign/total conversion found; skins and trainer functionality do not qualify |

## DLSS classification

The previously tested helper performs full-resolution neural/DLAA processing using screen-derived inputs. It does not establish lower-resolution DLSS SR, RR, FG or MFG. Modern 64-bit NGX cannot simply be dropped into the 32-bit executable. No second OptiScaler/Smooth Motion owner alongside the preserved Feeder setup.

## Recommended combinations

1. **First playthrough — Core:** original balance and controller-appropriate prompts; No-Intro Optional. Difficulty 1–2; candidate packages untested.
2. **After familiarity — Optional:** one model/HUD preference, with original assets saved. Difficulty 2–3; no performance promise.
3. **Replay/practice — Optional/Experimental:** Trainer V2 separately from graphics debugging; neural helper only with its exact known profile. Difficulty 3 trainer, 5 helper; historical technical evidence is not a fresh sustained-play test.

Rollback asset mods by restoring their original files; restore graphics through the exact recorded helper snapshot, not generic DLL deletion. Back up saves before trainer changes. Do not automatically change global security settings to run a helper.
