# Batman: Arkham Knight — categorized comparisons

Reviewed 2026-09-14; Steam build 13250859. [The latest local history](HISTORY.md) takes priority: Luma + OptiScaler DLAA/NR passed short gameplay checks; the old Feeder profile crashed and stays disabled.

| Category | Options / selection | Conflict, cost and confidence |
|---|---|---|
| Management / UI tools | Author's TFC workflow for [Arkham Knight Community Patch](https://www.nexusmods.com/batmanarkhamknight/mods/5); manifests for root graphics hooks | Vortex downloading a package does not mean TFC installed it. Match the Steam build and preserve modified UPK/TFC assets |
| Bug fixes / gameplay | Community Patch vs original game | Broad package, not automatically a low-risk FPS patch. Inspect current modules and restoration instructions; untested locally |
| Best graphics | Preserve current [Luma](https://github.com/Filoppi/Luma-Framework) + one OptiScaler NR consumer; stock is the fallback | Local DLAA/NR input evidence is stronger than generic ReShade instructions. Sustained gameplay still unproven |
| Colour / post-processing | [ReShade](https://reshade.me/) preset vs current Luma colour pipeline | Optional artistic choice; one tonemapper/preset, avoid double contrast and duplicate hooks |
| QoL / menus | Existing enlarged overlay menus; Community Patch's documented features only after selection | Menu readability change is recorded separately; font changes do not fix rendering inputs |
| Animation / abilities / tools | Original combat/movement first; selected Community Patch/debug options only for replay | Model skins do not add character abilities. No dedicated moveset package qualified here |
| Enemy AI / mechanics | Original difficulty and NG+ vs a separately reviewed gameplay patch | No verified independent enemy-AI overhaul selected; do not list a trainer as an AI improvement |
| New content | Official challenge/story DLC and NG+; inspect owned content | No verified community campaign/total conversion found in this review. Cosmetic model replacement is not new story content |

## DLSS: what actually works here

Current local Luma supplies native-resolution DLAA inputs to OptiScaler and one NR pass. Quality/Balanced/Performance SR and F6 are unavailable in the recorded implementation. RR has no established input integration; FG/MFG is disabled because the tested FP16/scRGB presentation is unsupported by the chosen Streamline path. Preserve the 90 FPS cap and report parked-scene measurements as observations, not averages. See [controls](CONTROLS.md).

## Recommended combinations

1. **First playthrough — Core:** original gameplay and a working stock fallback. Existing graphics trial is Optional/Experimental. Difficulty 1 stock, 4 exact Luma chain; confidence Medium for short runtime.
2. **After familiarity — Optional:** add the Community Patch only after auditing affected assets against the actual Steam build. Difficulty 3, untested; compare with stock before further changes.
3. **Replay — Optional:** challenge content, selected debug/practice features and one cosmetic set. Difficulty 2–3; keep a copied save and original asset backups.

Rollback: restore asset patches with their own manifests and restore the associated save where required. The existing full Luma restore script targets the previous Steam library and must be revalidated after the move; do not run an old Feeder/Full script against the current Luma layout. This documentation review changes no game files.
