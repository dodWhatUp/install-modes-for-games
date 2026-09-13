# Quake II RTX — categorized comparisons

Reviewed 2026-09-14; Steam build 17873149; `q2rtx.exe` present. This is separate from Quake II's remaster.

| Category | Options / recommendation | Requirements / limits |
|---|---|---|
| Engine / manager | Stock [NVIDIA Q2RTX](https://github.com/NVIDIA/Q2RTX) vs [Q2RTX-MOD](https://github.com/mstewart248/Q2RTX-MOD) | Upstream NVIDIA repository is marked discontinued. Keep the community fork in an isolated directory and pin its actual release |
| Best graphics | Native path-traced Q2RTX lighting | Substantial GPU load; start with a repeatable scene and enough VRAM headroom |
| Performance / DLSS | Stock resolution/quality settings vs community fork's documented DLSS integration | DLSS belongs to this fork; do not claim the stock Steam build supplies it. Measure actual render and output dimensions |
| RR / FG / MFG / NR | No verified implementation selected in this review | Ray tracing alone does not prove Ray Reconstruction; the DLSS SR claim does not establish FG or NR |
| UI / configuration | Engine menus and documented console variables | Different forks can expose different settings; use a separate config and avoid copying unknown cvars |
| QoL / controls | Native input and engine configuration | No independent convenience loader needed |
| Animation / enemy AI | Original engine/game module behaviour | No verified independent AI or animation overhaul selected |
| Abilities / mechanics | Compatible mission-pack/game module support only | Must match the chosen fork's binary interface; no automatic remaster compatibility |
| Added content | Licensed original Quake II campaign data; individually supported custom maps/mission packs | Not all remaster content is RTX-ready. No new authored campaign is claimed for the fork itself |

## Recommended combinations

1. **First playthrough — Core:** stock RTX renderer and supported campaign data. Difficulty 1–2; High upstream purpose confidence, local launch untested.
2. **After familiarity — Experimental:** isolate Q2RTX-MOD, compare DLSS with native rendering at identical lighting settings. Difficulty 3; Medium upstream/Low local confidence.
3. **Replay — Optional:** compatible community maps after testing textures/materials and game modules. Difficulty 3–4; content compatibility uncertain until checked.

Rollback: select the untouched Steam engine and its original config/save directory. Do not overwrite the stock game DLL or share proprietary PAK content. A generic DXGI proxy is not a Vulkan integration.
