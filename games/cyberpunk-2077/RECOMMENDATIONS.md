# Cyberpunk 2077 — Curated Recommendations

**Audit correction, 2026-10-14:** installed DLSS is now 310.9.1 with Streamline 2.7.1; the older 310.1 version limitation below describes the original rebuild. Saved RR/Ultra+ Auto/RR Clean settings also differ from that receipt. Preserve them pending a separately authorized runtime check; meeting a version minimum does not establish combination stability. No game or settings change was made by monthly maintenance. Continue to leave the removed NR/FrameWarp consumers absent. See [current observations](HISTORY.md).

## Current recommendation — 2026-10-10

- **First playthrough:** preserve native DLSS/Reflex/FG as the recovery foundation and the selected Cyberpunk RenoDX HDR profile. The restrained Ultra+ stack completed its built-in benchmark; RenoDX exposure delivery and CET controls were observed. Loaded-save behavior, frame pacing and longer stability remain pending. Keep automatic quality/DRS and unrelated gameplay mods off during this comparison. Different PT workloads do not isolate Ultra+'s performance cost. See [current guide](CLEAN-REBUILD.md) and [runtime evidence](RUNTIME-VALIDATION.md).
- **Later play:** compare the selected Advanced/PT21/Fast/Vanilla-streaming profile against native rendering on the same route. Tune native DLSS and native FG separately, monitoring actual rendered FPS and stable VRAM rather than promising a fixed memory saving. ReShade/CET controls are Delete and F12; F9 cycles native DLSS, F6 Quick Load and F5 Quick Save. The F12 configuration was read back 2026-10-11; gameplay input remains untested.
- **Post-game / experimental:** Ultra+ X rc7 remains a release candidate. More expensive PT/streaming modes, a newer coherent native runtime set or NR/FrameWarp require separate input/ownership and stability review. The user-selected rebuild removes NR/FrameWarp; do not resume them automatically. Native 310.1 cannot support Ultra+ RR Clean/Sharp: select Vanilla denoiser if enabling RR with this set.

The supplied text's native HDR10 PQ + game-specific RenoDX + restrained Ultra+ daily path was selected. Its old F6/F9 recommendation is superseded by the user's saved F9 DLSS/F6 Quick Load preference, recovered during this install. RHI's known Cyberpunk uninstall/shared-folder failures mean the custom stack uses explicit manual ownership, with only safe Cyberpunk tracking reconciled. No cosmetic shader pack, second FG owner or NR pass is installed.

## Historical recommendation — 2026-10-07

- **First playthrough:** keep native DLSS/Reflex as the reliable fallback; don't call the new warping experiment gameplay-proven.
- **Later play:** retain native x2 FG initially and compare XPAR on/off in the same scene before changing graphics quality or adding other visual mods.
- **Post-game / experimental:** the user-selected FrameWarp/XPAR 1.8.5 is installed with its required ReShade host. Use XPAR engine, Auto latency, native DLSS inputs and the existing borderless mode. No Latewarp alongside FG or second FG owner; no full >4x delivery claim. Follow [validation/rollback](FRAMEWARP.md). Leave RenoDX/OptiScaler/NR absent for the initial test; the older held custom-host upgrade is not resumed.

Older recommendations below describe historical stacks and reviews, not today's clean ReShade/RenoDX/Ultra+ installation.

**2026-09-15 maintenance result:** preserve the existing installed setup until the [prepared controls meet the newer FG/manual-restore requirements](../../examples/cyberpunk-2077/UnifiedControls/UPDATE-READINESS.md). NR v0.8.4's memory fix is relevant to future scale/placement testing, but its prerelease status and upstream tests do not establish Cyberpunk gameplay stability. Do not run the old fourteen-file installer or substitute an upstream stock DLL over the custom host. No game launch or automatic dynamic activation is part of monthly maintenance.

**Shortcut override, 2026-09-14:** use F9 for native DLSS quality; F6 is the user's Quick Load and F5 is Quick Save. Other graphics shortcuts remain as configured. Preserve this mapping during upgrades; live F9 validation is pending the next user-initiated launch.

**Experimental Dynamic SR candidate:** 30 real rendered FPS through native Cyberpunk DRS, prepared for an OptiScaler F12/CET panel. Start at 50–100% input bounds and preserve SR L. It remains **uninstalled**; CET/Ultra+ now owns F12, so resolve the menu collision first. Evaluate actual input dimensions, rendered FPS and pacing rather than total MFG FPS.

**2026-09-14 selected direction:** [Unified OptiScaler controls](../../examples/cyberpunk-2077/UnifiedControls/README.md), latest compatible runtimes, SR L and latest documented compatible RR/FG models; monthly updates. The v0.8.3 / Streamline 2.14.1 / DLSS 310.9.1 package is prepared but **not installed** while Batman/Steam are running. Treat it as experimental until actual SR buffer changes, NR recreation and native MFG delivery are tested. Streamline 2.14.1 adds Dynamic MFG support with V-Sync/frame limiters; older incompatibility guidance is superseded for that runtime. The older recommendations below describe the installed baseline, not the candidate.

**Controls update, 2026-09-13 evening:** F11 now recalls personal NR settings slots, F7 remains 25%/100%, and F8/Page Up/Page Down are unbound. Use NVIDIA statistics; for base versus displayed FPS use a tool that measures both, such as NVIDIA FrameView. The observed NVIDIA profile uses Dynamic MFG up to 6x, so a fixed division of displayed FPS is not a reliable base-FPS measurement. The F6 feedback repair and slot implementation pass isolated tests; actual F6 buffer recreation still needs verification. Restore the personal-slots revision before the older F7 rollback chain. Earlier control descriptions below are historical.


## 2026-09-20 — RHI + Ultra+ planning default

For future requested Cyberpunk graphics work, use **RHI** as the preferred compatible management/orchestration layer so ReShade/RenoDX/Luma/OptiScaler/DLSS/Streamline versions and updates are managed from one place when supported. Keep the underlying feature owners and input contracts explicit; RHI is not itself the renderer or neural consumer.

Whenever path tracing is in scope, include **Ultra+** as a separate PT/rendering-overhaul option alongside the native renderer. Do not bury it under ordinary presets. Evaluate it as its own rendering branch against the desired native RR/MFG, OptiScaler NR and any ReShade/RenoDX visual stage. RHI can surface the Ultra+ link, but that link is discovery rather than compatibility proof.

## First playthrough

**Core:** current Cyberpunk build, native DLSS Transformer, native Reflex, and native DLSS FG/MFG on RTX 50 when base rendered FPS and latency are acceptable.

**Experimental, not Core:** the installed OptiScaler-DLSSNR one-pass profile. Its files are validated, but visual quality, performance, and stability have not yet been proved in gameplay. Use a stable save/scene and avoid changing multiple graphics groups at once.

The requested custom controls are installed: Delete full menu, F12 compact NR window, F11 model preset hints, F10 NR toggle, F9 NR scale, F8 before/after SR, and F7 native DLSS quality via CET 1.37.1. Their compilation/placement and F7 mock tests are verified; interactive testing is pending. Keep the neural preset/scale stable during initial gameplay validation, then test each shortcut separately. The CET adapter is **Experimental/Conditional** here, not a proven compatibility recommendation: installation difficulty **2** (custom development **4**), no direct save edits, negligible intended script work between key presses, potentially significant GPU/VRAM changes when quality/placement is switched. Roll back through the F7–F9 snapshot first.

**Avoid:** gameplay overhauls or broad loader stacks during graphics validation. They add unrelated failure causes.

## After familiarity

**Strong:** tune Cyberpunk's native DLSS quality and x2/x3/x4 MFG using the same repeatable scene, reporting base and displayed FPS separately.

**Experimental:** compare one pre-SR neural pass with native FG off and on. If stable, test global RT/RR in a separate run. Keep HDR as another independent dimension because the captured profile used SDR.

**Optional:** add further CET/RED4ext/redscript-dependent QoL mods only after verifying current build support and preserving the clean graphics profile. CET is already present solely for the approved F7 adapter; this does not authorize a broad loader/mod stack.

## Post-game / experimental

**Experimental:** path tracing + native RR + one OptiScaler neural pass, with close inspection of shadows, reflections, faces, foliage, HUD, disocclusion, VRAM, and loading/alt-tab stability.

**Experimental:** finished-picture placement or reduced neural working scale as separate A/B tests after the basic path is proved. Do not combine them with multipass or residual modes in the first comparison.

**Avoid:** stacking OptiScaler neural rendering with RenoDX DLSS5, DLSS5-Feeder, a second FG owner, or an unexplained proxy rename.

## Graphics combinations

1. **Recommended current experiment:** native Cyberpunk DLSS SR/RR + native x2 FG/MFG + OptiScaler-DLSSNR 0.7.7 one FP8 pass before SR; OptiScaler FG disabled/external. Expected benefit: neural detail/material relighting using native temporal inputs. Main conflict: experimental NR/FG/RR stability and GPU cost. Difficulty **3**; confidence **Medium for installation, Low until gameplay validation**; rollback through the guarded snapshot manifest.
2. **Recommended stability baseline:** native Cyberpunk DLSS/RR/FG only. Expected benefit: officially integrated feature ownership and easiest support path. Main conflict: no DLSS 5 neural pass. Difficulty **1**; confidence **High**; rollback by disabling/removing the OptiScaler-owned files.
3. **Later visual experiment:** one finished-picture NR pass. Expected benefit: neural edit after lighting/effects and possible reduction of green noise. Main conflict: HUD/color changes and higher/ambiguous GPU timing. Difficulty **3–4**; confidence **Low**; rollback by setting `FinishedPicture=false` and restarting.
4. **Ultra+ PT overhaul branch:** current Ultra+ 9.3.7 as a separate renderer/PT experiment when PT is desired. Expected benefit: changes to the underlying PT/lighting/denoising/rendering path rather than a post-process preset. Main conflict: settings/loader overlap with the current NR/RR/ReShade stack; validate one layer at a time. Difficulty **3–4**; confidence **High for mod classification, Low until this exact combined profile is tested**; rollback with a clean Ultra+ removal plus the preserved graphics baseline.
5. **Avoid:** OptiScaler NR + RenoDX/Feeder or OptiScaler-owned FG + Cyberpunk native FG. Duplicate neural, proxy, or swapchain ownership makes failures ambiguous and can destabilize the game.

## 2026-09-14 — Library comparison review

Added [categorized comparisons](COMPARISONS.md) covering manager/foundations, performance, graphics/DLSS, QoL/UI, animation, AI, abilities/mechanics and actual content extensions. No game files changed or new gameplay tests were performed by this review. Earlier local evidence remains stronger than generic recommendations; historical control mappings and unresolved validation boundaries are preserved. See the [14-game guide](../../docs/INSTALLED-GAMES-MOD-GUIDE.md) for scope and installed-library checks.

## 2026-09-20 — Current modular selection

The user explicitly requested RHI, Ultra+, a recommended manager and selected graphics/performance/QoL mods, with a checkpoint after each installation and independent changes afterward. This authorizes the newly requested setup; it does not clear the separate [custom graphics-host update hold](../../examples/cyberpunk-2077/UnifiedControls/UPDATE-READINESS.md). The entries below record **verified file deployment**. No game was launched; runtime testing belongs to the user. Check [History](HISTORY.md) for evidence, and use the [modular setup guide](MODULAR-SETUP.md) for ownership, settings and rollback. RHI itself remains pending manual installation after automatic approval review blocked its execution; its .NET 8.0.31 Desktop Runtime dependency is installed.

### First playthrough

**Core, deployed:** preserve native story, balance and existing saves. Vortex 2.6.3 with Cyberpunk extension 0.13 manages the selected regular packages through hardlinks. RED4ext 1.30.0, redscript 0.5.31 and ArchiveXL 1.27.3 are deployed and hash verified for the selected dependencies; ArchiveXL supplies Ultra+'s supplementary `.xl` lighting removals. Keep existing custom graphics hooks protected and one owner per file. Manager difficulty 2; High upstream confidence, runtime combination untested.

**Strong, deployed:** Better Loot Markers 1.4.0 reuses existing CET and makes loot easier to identify; all 9 deployed files are hash verified. Real Vendor Names 2.1.0 adds recognizable shop names to the map through redscript; its script hash was verified at the Vortex extension-selected path. Neither intentionally edits saves or balance, and neither introduces hotkeys. Compatibility confidence is Medium until a gameplay session. Intended overhead is small but unmeasured. Toggle each Vortex package independently and Deploy; preserve generated settings and keep redscript while any dependent remains active.

**Requested, deployed:** Ultra+ 9.3.7 is the selected engine-tuning layer. Its persistent profile is verified: Advanced mode, PT21, Fast quality, Vanilla denoiser and streaming, automatic quality off, automatic menu confirmation/restoration off. It applies its rendering profile on first launch; these settings do not select native DLSS quality or FG. With the preserved DLSS 310.1 set, verify Vanilla again after switching RR off/on: Ultra+ can automatically select RR Clean, which requires 310.6+, and has no supported switch to suppress that transition. Do not silently upgrade the protected host or combine competing performance/PT packs. Difficulty 3; Medium upstream confidence, runtime result unknown. Snapshot and compare one preset at a time; gains and visual tradeoffs must be measured.

**Historical visual-stage record (2026-09-22):** ReShade 6.8.0 and the Cyberpunk RenoDX 0.2026.0916.2204 visual profile were enabled and hash verified through the existing OptiScaler plugin route. At that point ReShade used Home and CET/Ultra+ used grave/tilde (`VK_OEM_3`); the later cross-game and 2026-10-11 updates changed these to Delete and F12. The RenoDX disable/enable filesystem test preserved ReShade, Ultra+, NR and mutable settings. A later RHI OptiScaler install removed the shared CET `plugins` tree and RenoDX, then the verified host/CET/RenoDX state was restored on 2026-09-22 while preserving ReShade/Lilium settings. Do not let RHI install, update or uninstall OptiScaler for this Cyberpunk profile until its recursive shared-folder ownership is fixed. Disable RenoDX independently, and disable it before removing its ReShade host. Keep mutable configuration for later tests. Difficulty 3; combined runtime confidence Low until the user tests startup, image quality, HDR, motion and stability.

### After familiarity

**Optional:** Clear Skill Checks 1.1.1 is a focused addition if dialogue thresholds remain unclear. Its authoritative Nexus listing is reviewed, but no payload is staged. Native Settings UI should be added only for a selected mod that requires it. These do not justify broad gameplay frameworks or extra overlays by themselves.

**Optional, deferred:** Limited HUD 2.22.4 provides configurable HUD visibility, but must preserve Quick Load F6 and the user's unbound F8. Configure its controls deliberately before activation. It changes more HUD behavior than the selected QoL pair, so test it independently. Difficulty 2; Medium upstream confidence, local behavior untested; rollback its scripts/archive and settings snapshot.

### Post-game / experimental

**Experimental:** larger gameplay/AI/cyberware overhauls, additional neural passes, aggressive PT presets, and the full NR/PT/RR/HDR combination remain separate experiments. They are not part of the initial QoL pair. Preserve a separate save/profile when gameplay dependencies are introduced.

**Avoid:** automatic RHI/Vortex replacement of the custom OptiScaler binary or native NVIDIA set; two owners for a file or FG/neural feature; simultaneous competing performance packs; claiming a staged archive or successful overlay load proves performance or stability. File-level independent rollback works for disjoint components; shared dependencies and overlapping settings still require reconciliation.
