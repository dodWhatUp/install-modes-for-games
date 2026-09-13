# Game-Modding Operating Standard

This is the repeatable procedure for short fixes and long, multi-layer experiments.

## 1. Recover context

Search this repository before researching or changing files:

```powershell
rg -n -i "<game>|<executable>|<feature>|<error>|<dll>" games docs evidence
```

Read the latest history entry and its confidence. A previous failure can rule out a path; a previous success identifies a baseline, not a guarantee after updates.

## 2. Inventory the live system

Record:

- game/store build and real rendering executable;
- 32/64-bit and D3D9/11/12, OpenGL, or Vulkan;
- GPU, driver, monitor mode, output resolution, HDR state, and VRAM;
- native SR/DLAA, RR, FG/MFG, Reflex, dynamic resolution, and frame-cap settings;
- proxy DLLs, Streamline/NGX files, ReShade layers/add-ons, mod loaders, overlays, launch options, and relevant environment variables;
- user configuration and save locations affected by the proposed change.

Do not infer feature support from filenames alone.

## 3. Research and classify

Use current upstream project documentation, release notes, issue trackers, and original mod pages. Label every claim:

- **local-tested**: reproduced on this machine and build;
- **upstream-supported**: documented by the author, not locally tested;
- **community-reported**: plausible but not authoritative;
- **inference**: explanation consistent with evidence but not proven;
- **unknown**: missing evidence.

Review high-churn experimental graphics tools after 30 days and ordinary mods after 90 days, or sooner after a game/driver/tool update.

For DLSS work, follow [Feature Decision](FEATURE-DECISION.md): identify the minimum path using real engine inputs, including a supported game-specific input integration when necessary. Compare implementations by input quality, supported features, stability and necessary dependencies; OptiScaler is not mandatory. Review every useful missing feature and the smallest addition needed beyond the previous stage. Separately research the game's ReShade/RenoDX visual profile and its compatibility with the selected DLSS path.

## 4. Offer numbered paths

Unless an exact path was already selected, provide three to six choices. Use this compact shape:

| # | Goal and stack | Benefit | Main conflict/risk | Difficulty | Confidence | Rollback |
|---|---|---|---|---|---|---|
| 1 | Recommended path | | | | | |

Include **stock/no change** when experiments carry meaningful risk. Distinguish a reversible test from a permanent default.

For graphics installs, show the minimum baseline, useful feature extensions with only their additional dependencies, and the separate ReShade/RenoDX visual stage. Explain any tradeoff between fewer components and more supported features. Identify required helper processes separately from in-process add-ons/runtime files. Apply the saved preferences without asking the user to select the same defaults again; numbered choices resolve materially different game-specific paths.

## 5. Snapshot at the last safe moment

Immediately before mutation:

1. Stop the game, launcher, store client if its config must change, helpers, and shader compilers.
2. Resolve and validate exact absolute target paths.
3. Save a current-state snapshot and preserve the known-good baseline separately.
4. Inventory relative paths, size, SHA-256, file version, source/version, and whether each file was stock, added, or replaced.
5. Save configuration, launch options, layer manifests, environment/profile overrides, and user settings that the game may rewrite.
6. Write a restore procedure and validate that its source files exist before mutation.

Steam verification is not a complete backup: it does not restore every user setting, global layer registration, or launch option.

## 6. Install in fault-isolating stages

Use dependency order, omitting stages the current baseline already supplies:

1. Stock baseline.
2. Required translation layer or mod loader.
3. Required host and game-specific input integration, if native inputs are insufficient.
4. Minimum supported DLSS/input path, with one owner per feature.
5. Additional useful features, reusing existing capabilities and adding only missing dependencies one at a time.
6. ReShade plus the compatible game-specific RenoDX visual profile; reuse the supported host and resolve overlapping shader/HDR work.
7. Combined-stack validation, tuning and optional overlays.

Run a checkpoint after every stage. If a checkpoint fails, roll that stage back before substituting another implementation.

Include the user's [default graphics controls](GRAPHICS-CONTROLS.md) in each requested graphics add-on installation, regardless of the chosen tool. Configure supported actions, record unavailable controls and their reasons, and document how the selected values are saved. The current F7 two-value default is in `preferences/GENERAL.md`; an older example's hard-coded cycle does not override it.

## 7. Validate the real feature

Static validation checks ownership, versions, hashes, configuration, and duplicate hooks. Runtime validation should include:

- the correct process and API loaded;
- feature creation and repeated evaluation/delivery;
- a moving gameplay scene, not only a static menu;
- HUD/UI stability and correct motion-vector direction/scale;
- native HDR plus black/white levels and no double tonemapping;
- base FPS, displayed FPS, frame pacing, latency, VRAM, and system RAM;
- resolution or swapchain recreation, alt-tab, loading, and clean shutdown.

For FG/MFG, report base rendered FPS separately from generated display FPS. For a neural pass, prove which buffers it receives and whether those are engine-native or estimated.

Verify each consumer's actual input source and any fallback. Separate captured/converted engine resources from reconstructed/estimated resources. After adding the visual stage, recheck the DLSS features, input color space, UI and presentation. Record each requested feature as verified, configured but untested, failed, or unavailable with its concrete blocker; a shorter installed component list is not sufficient evidence of success.

## 8. Long-task fault handling

- Preserve logs before another run overwrites them.
- At the first crash, capture timestamps, last successful frame, effective resolution, VRAM/RAM, Event Viewer/WER evidence, and all component logs.
- Reproduce only when safe and useful. Do not repeatedly launch a known-crashing state without changing one hypothesis.
- Prefer the smallest diagnostic change: resolution, one add-on, one overlay, one provider, or one model.
- If the game becomes unplayable, prioritize restoration over further diagnosis.
- A caught plug-in exception and a game-process crash are different outcomes; document which occurred.

## 9. Finish and preserve learning

Update the game's history, preferences, catalog, recommendations, and evidence. Promote reusable findings to `docs/`. Record a clear paused/resume boundary when work stops. Never create a reminder unless explicitly requested.

## Rating vocabulary

- Recommendation: **Core**, **Strong**, **Optional**, **Experimental**, **Avoid**.
- Confidence: **High** (direct current evidence), **Medium** (good upstream or partial evidence), **Low** (untested/community/inference).
- Difficulty: **1** copy/config only; **2** loader plus dependencies; **3** multiple hooks/testing; **4** bridge/profile work; **5** development/debugging.
- Stability: **Stable**, **Conditional**, **Partial**, **Failed**, **Untested**.
