# Cyberpunk 2077 — categorized comparisons

Reviewed 2026-09-14; Steam build 20383525. These are candidates, not new installations. [Existing history](HISTORY.md) governs the installed OptiScaler/CET profile and its incomplete gameplay validation.

| Category | Options and recommendation | Dependencies, conflicts and cost |
|---|---|---|
| Manager / foundation | [Vortex and REDmod](https://www.cyberpunk.net/en/modding-support) for supported packages; manual ownership for existing root hooks | REDmod does not replace CET, RED4ext or redscript requirements. Install frameworks only when selected mods need them. Do not deploy an archive as both legacy and REDmod |
| Performance / stability | Native graphics settings and DLSS first; compare one quality setting at a time | Avoid global performance INI bundles and old patch-1.x fixes; current NR costs extra GPU work. Do not treat MFG's display FPS as base FPS |
| Best practical graphics | Native RT/path tracing + native RR when performance permits; compare with raster/RT-light settings | High GPU/VRAM cost; 16 GB requires a measured texture budget. Existing NR is Experimental, not required for native DLSS |
| Menus / configuration | [Native Settings UI](https://github.com/justarandomguyintheinternet/CP77_nativeSettings) vs CET overlay | Native-looking menu for compatible mods; CET dependency. It does not configure every installed mod automatically |
| QoL / clothing UI | [Equipment-EX](https://www.nexusmods.com/cyberpunk2077/mods/6945) vs vanilla wardrobe | More outfit control; current author dependencies and archive/script versions must match 2.31. Start with vanilla wardrobe if extra slots are unnecessary |
| Enemy behaviour / combat | [Enemies of Night City](https://www.nexusmods.com/cyberpunk2077/mods/8467) vs stock difficulty | New enemy capabilities and rebalancing; replay recommendation only. Broader balance and scripting cost; exact 2.31 compatibility untested |
| World AI / mechanics | [Night City Alive](https://www.nexusmods.com/cyberpunk2077/mods/10395) vs original crowds | More emergent activity; not the same job as enemy combat tuning. Author documents quest interactions and late bike spawning; avoid on first story run |
| Unique abilities / tools | [Cyberware-EX](https://www.nexusmods.com/cyberpunk2077/mods/9429) vs original cyberware limits | More build flexibility at the cost of balance/save dependencies. Use a dedicated character and current requirement versions |
| Animation / movement | Preserve native movement for this first package; animation/camera replacements need a separate targeted selection | No standalone animation overhaul qualified in this review; Equipment-EX is not an animation system |
| Added content | [Phantom Liberty](https://www.cyberpunk.net/en/phantom-liberty) is the official expansion benchmark; ownership not assumed | No independently verified community campaign selected here. World activity, clothing and enemy overhauls are not a new campaign |

## DLSS ownership

Native game integration remains the preferred SR/RR/FG/MFG owner. The existing OptiScaler NR experiment uses real game inputs; keep its internal FG off. No Feeder or second RenoDX NR consumer. Native RR requires the appropriate ray-traced rendering path. Refer to [current recommendations](RECOMMENDATIONS.md) for the precise tested boundary; this catalog adds no new proof of feature delivery.

## Recommended combinations

1. **First playthrough — Core:** native graphics and original balance; current graphics experiment only if deliberately retained after testing. Optional Equipment-EX after the loader baseline works. Difficulty 1–2; Medium upstream confidence, existing NR remains conditional.
2. **After familiarity — Strong/Optional:** native settings UI and specific QoL modules; compare one visual change without adding AI overhauls. Difficulty 2–3.
3. **Replay — Experimental:** Cyberware-EX or Enemies of Night City first, then a separately tested world-activity mod. Do not start with all three. Difficulty 3–4; save/quest impact significant.

All new rows are untested locally. Review date applies to discovery; exact package versions must be resolved at installation. Restore both the prior save and mod profile when removing gameplay dependencies; restore root DLL/INI files through the existing guarded snapshot chain. Never replace the current custom hotkey binary through an automatic manager update.
