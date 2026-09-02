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

## 4. Offer numbered paths

Unless an exact path was already selected, provide three to six choices. Use this compact shape:

| # | Goal and stack | Benefit | Main conflict/risk | Difficulty | Confidence |
|---|---|---|---|---|---|
| 1 | Recommended conservative path | | | | |

Include **stock/no change** when experiments carry meaningful risk. Distinguish a reversible test from a permanent default.

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

Typical order:

1. Stock baseline.
2. Required translation layer or mod loader.
3. One injection framework.
4. One feature bridge/add-on.
5. Input provider such as depth or motion vectors.
6. FG/MFG or neural processing.
7. Visual preset, tuning, and optional overlays.

Run a checkpoint after every stage. If a checkpoint fails, roll that stage back before substituting another implementation.

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
