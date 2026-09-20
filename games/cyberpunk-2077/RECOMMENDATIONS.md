# Cyberpunk 2077 — Curated Recommendations

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
