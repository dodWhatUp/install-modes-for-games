# DOOM: The Dark Ages — Curated Recommendations

These recommendations are deliberately separate from the complete [catalog](MOD-CATALOG.md).

## First playthrough / current safe baseline

**Core:** stock game, native HDR, native DLSS SR/RR/FG as exposed by the game, current driver, and enough texture-memory headroom. Do not add the paused neural stack.

**Strong:** use the simple `+com_skipIntroVideo 1` launch option only if the user wants it; it is easier to reverse than an extra mod. Benchmark the stock game before any performance guide.

**Optional:** none of the balance/randomizer packages by default. Preserve the intended combat and visual readability first.

## After learning the game

**Strong candidate:** selected Kaibz QoL, HUD, or input modules after reading the current changelog and checking overlap.

**Optional:** tiny tweaks or Improved Shield Charge Cooldown for a specific annoyance. These change balance and should not be silently included in a “performance” setup.

**Optional graphics taste:** KEEP THE DEAD or selected effect-removal changes, measured separately for memory/performance and readability.

## Post-game / replay

**Strong candidate:** Kaibz randomizer/custom gameplay on a new slot as its author recommends.

**Optional:** Brutal Dark Ages and broader gameplay combinations after checking loader/file conflicts.

## Experimental graphics combinations

1. **Stock high-quality:** native HDR + native DLSS/RR/FG. Recommendation **Core**, confidence **High**, difficulty **1**.
2. **1440p neural research:** pinned RenoDX/Feeder snapshot, native DLSS owners retained, no OptiScaler/Smooth Motion. Recommendation **Experimental**, operation confidence **Medium**, visual-quality confidence **Low**, difficulty **4**.
3. **4K neural research on 16 GB:** recommendation **Avoid**. It exhausted practical memory headroom and ended in a reported crash.
4. **Generic ReShade visual preset alongside the neural stack:** recommendation **Avoid until isolated**. It complicates color-space, order, and performance diagnosis.

The user has chosen option 1 for now. This is not a prompt to resume options 2–4.
