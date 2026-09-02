# Bayonetta — Mod Catalog

Last reviewed: 2026-09-02.

| Mod/tool | Category | Purpose | Important requirements/conflicts | Local state | Confidence |
|---|---|---|---|---|---|
| dgVoodoo2 + ReShade + DLSS5-Feeder + x64 RenoDX helper | Experimental graphics | D3D9→D3D11 bridge and full-resolution neural processing | Complex x86/x64 chain; 100% work resolution; no OptiScaler/Smooth Motion; estimated vectors; proxy audit | Working technical 4K run | High for operation |
| [Proper PS4 Button Prompts](https://www.nexusmods.com/bayonetta/mods/59) | UI/controls | Replaces Xbox prompts with PS4 prompts | Large texture package; match controller preference | Untested | Medium |
| [No-Intro](https://www.nexusmods.com/bayonetta/mods/82) | QoL | Skips startup/splash videos | Verify current game build and exact replaced files | Untested | Medium |
| [No-HUD-No-Effects](https://www.nexusmods.com/bayonetta/mods/113) | UI, photo mode, graphics | ShaderToggler controls for HUD, motion blur, DOF and effects | Shader/hook overlap with ReShade/Feeder needs a separate compatibility test | Untested | Medium |
| [BayonettaTrainer V2](https://www.nexusmods.com/bayonetta/mods/63) | Framework, practice, gameplay | Extensible x86/Lua trainer with practice, input, timer and cheat functions | Uses `dinput8.dll`; not a first-playthrough default; validate signature/source and conflicts | Untested | Medium |
| [Bayonetta 2 Models Modpack](https://www.nexusmods.com/bayonetta/mods/42) | Cosmetic/character overhaul | B2 character models in story mode | Cosmetic asset replacement; inspect archive conflicts | Untested | Medium–Low |
| [World of Vibrance](https://www.nexusmods.com/bayonetta/mods/83) | Graphics/ReShade | Color-oriented ReShade preset | Shares ReShade/effect chain; HDR and neural-order review required | Untested | Low |
| [Wickedly Vivid ReShade](https://www.nexusmods.com/bayonetta/mods/103) | Graphics/ReShade | Removes/changes LUT/vignette and increases contrast/color | Same proxy/effect-order concern; artistic preference | Untested | Low |
| [Photorealistic Bayonetta ENB](https://www.nexusmods.com/bayonetta/mods/74) | Graphics/ENB | ENB visual preset | Likely proxy collision with dgVoodoo/ReShade; do not combine without a documented chain | Untested | Low |

## Expansion-scale status

No verified new campaign, total conversion, or expansion-scale quest/content mod was found. BayonettaTrainer V2 is an extensible gameplay/practice framework, and model/audio packs can substantially change presentation, but neither is a full-game expansion.

## Compatibility groups

- The working neural profile already uses D3D9 and DXGI/D3D11 hook layers. Treat ENB, ShaderToggler, and extra ReShade presets as separate profiles until tested.
- Select one visual color preset and verify effect order/HDR.
- Back up `system_data` and game files before model, audio, or trainer changes.
