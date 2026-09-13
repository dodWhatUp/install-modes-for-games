# NieR:Automata — categorized comparisons

Reviewed 2026-09-14; Steam build 7020666; `NieRAutomata.exe` present. All candidates untested on this installation.

| Category | Options / recommendation | Requirements / conflicts / cost |
|---|---|---|
| Manager | [NAMH](https://www.nexusmods.com/nierautomata/mods/140), observed 4.4, vs manual manifests | Preferred helper for supported asset packages; do not let a helper silently replace a deliberately selected injector |
| Performance / display | [Current Special K/FAR guidance](https://github.com/Kaldaien/FAR) vs stock patched game | Old FAR packages target different game revisions. Measure current patched game before adopting old fixes; do not downgrade automatically |
| Best graphics | [LodMod](https://github.com/emoose/NieRAutomata-LodMod) + selective [HD Texture Pack](https://www.nexusmods.com/nierautomata/mods/5) | LodMod improves distant detail/shadow options and can increase CPU/GPU cost. Textures add VRAM use; use the proper Special K injection path |
| Texture alternatives | GPUnity HD Texture Pack vs [4K AI-Enhanced LITE](https://www.nexusmods.com/nierautomata/mods/760) | Prefer authored HD base for fidelity; AI pack is an aesthetic alternative with overlapping files. Do not call both additive |
| QoL / controls | [NAIOM](https://www.nexusmods.com/nierautomata/mods/12) vs original controller input | Strong mouse/keyboard candidate, unnecessary for a satisfactory controller setup. Build and input wrapper compatibility must match |
| UI / menus | Special K overlay / NAMH utilities; [HD fonts fix](https://www.nexusmods.com/nierautomata/mods/723) only with its texture dependency | These configure their own components; no universal gameplay MCM |
| Animation / enemy behaviour | Original combat and animation timing | No selected independent AI/animation overhaul; do not uncap through an unverified old patch |
| Abilities / tools / mechanics | Original chips and combat progression | No new mechanic package qualified. A weapon model replacement changes appearance, not necessarily its attacks |
| Added content | Official DLC challenge content if owned; story routes/replay | No verified community campaign/total conversion found in this review |

## DLSS and hook ownership

No verified engine-integrated DLSS SR/DLAA/RR/FG/MFG or NR path was selected. ReShade/Feeder is a separate experiment, not a prerequisite for the recommended texture/LOD setup. LodMod can use XInput/DInput/DXGI wrappers; Special K and input mods may also hook the process. Different filenames do not prove compatibility. Follow the current author chaining instructions and log the actual modules.

## Recommended combinations

1. **First playthrough — Core/Strong:** patched stock game, NAIOM for mouse users, modest texture improvements. Difficulty 2; Medium purpose confidence, Low exact-stack confidence.
2. **After familiarity — Optional:** LodMod with measured distances/shadows and one texture base. Difficulty 3; increased quality can reduce FPS.
3. **Post-game — Optional/Experimental:** cosmetic sets or separately tested higher-FPS/HDR experiments. Difficulty 3–4; no new campaign claimed.

Rollback: restore proxy ownership, Special K configuration, injected textures and original replacement files. Revert any gameplay patch with its pre-change save when applicable. Do not share game archives in the Drive package.
