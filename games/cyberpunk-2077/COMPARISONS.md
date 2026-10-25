# Cyberpunk 2077 — categorized comparisons

## Native inputs, NR implementations and memory — researched 2026-10-18

**Decision:** retain wilsjo2 DLSS NR as the first controlled Cyberpunk candidate, not a proven stability winner. ShortFuse on the game's native DLSS hook is a legitimate real-input alternative. F5 has useful native-game optimizations as well as its non-DLSS fallback; the earlier description of it only as a missing-input solution was incomplete. No matched Cyberpunk/RTX5090 study reviewed here establishes a RAM, VRAM, latency, quality or long-session stability winner.

This is source/documentation research, not local game acceptance. The installation/recovery task remains deferred. Its latest observed state—OptiScaler and native SR/RR/FG files removed by the user's RHI variant switch—is recorded in [history](HISTORY.md). No binaries, game settings, driver profiles or runtime tests were changed for this research.

### What counts as real input

Both middleware and ReShade add-ons can intercept the game's upscaler/NGX calls. Wilsjo2 v0.8.91's [DX12 adapter](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/blob/v0.8.91/OptiScaler/dlssnr/DlssNr_Pipeline_Dx12.cpp) reads color, depth, motion, regions, motion scales, reset and exposure metadata from NGX parameters. RenoDX has a public [D3D11/D3D12 NGX hook utility](https://github.com/clshortfuse/renodx/blob/6d563066956190c8b9a2c7a907398bfac3629a3c/src/utils/dlss/nvngx.hpp). Its existence establishes framework capability, not a complete audit of separately distributed ShortFuse binaries.

[Feeder's integration documentation](https://github.com/jlrouzies-fr/DLSS5-Feeder#before-you-install-four-things) explicitly describes ShortFuse consuming calls made by native-DLSS games. A ReShade host therefore does not imply estimated input. Conversely, an OptiScaler DLL does not imply every route has engine motion. Identify the actual route and every guide's origin.

[NVIDIA's research description](https://research.nvidia.com/labs/adlr/DLSS5/) identifies rendered color, engine motion and carried state/artistic controls for NR. Do not claim that either mod gets unrestricted engine access, meshes/material semantics or every RR guide. Extra SR metadata available to an adapter need not be a direct NR-model input.

| Route | Input provenance | Important qualification |
|---|---|---|
| OptiScaler NR on native DLSS/compatible temporal upscaler | Captured game upscaler color/depth/motion, with conversion as required | Resource regions, motion scale, state and frame ordering must remain coherent |
| RenoDX ShortFuse/native DLSS5 hook | Game NGX/upscaler resources on a working native hook | Exact binary/hook mode must be established; Present/Auto labels alone prove nothing |
| F5 Optical F5Low without a game upscaler call | Captured final color, heuristically selected game depth where available, image-estimated motion | Mixed inputs, not engine-native motion |
| Generic ReShade Feeder | Selected depth plus the selected motion provider and synthetic contract | Optical-flow providers estimate motion; game-specific real-vector adapters need separate proof |
| Game-specific RenoDX HDR mod | Game shader/color processing | It is not the neural consumer and does not itself supply every temporal input |

F5 v0.1.32's [optical-flow code](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/motion/OpticalFlow_Dx12.h) estimates displacement from images. Its [depth finder](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/native/DepthFinderCore.h) observes graphics-API activity and selects/copies depth resources using heuristics. Calling the producer “native” does not make estimated motion engine-generated. Cyberpunk has native DLSS inputs, so start on that route rather than manufacturing replacements.

### Features and evidence

| Candidate | Useful capability | Evidence limit / judgment |
|---|---|---|
| wilsjo2 v0.8.91 | Native temporal input route, placement/scale/pass controls, HDR codec, upscaler middleware, optional spatial compression | Source is inspectable; short game tests and synthetic regressions do not certify all combinations. First baseline with experimental extras off |
| ShortFuse DLSS Tool | ReShade-hosted native NGX interception; works alongside a separate game HDR add-on when the exact chain is compatible | Potentially avoids a broader upscaler replacement layer when native DLSS already works. Lower overhead is an inference to test, not measured here; full release-binary/source correspondence was unavailable |
| F5 v0.1.32 | Native input path plus optional estimated-input route, internal-network reuse, frame-detail reuse, model/pass controls and broader FG work | More feature choices, not established superior stability. Release tests list several games but do not establish the complete Cyberpunk combination |
| An0sTheGreat's RenoDX-derived DLSS 5 Super Anus v1.1.2.31 | Additional scaling/history/reconstruction/resource-pool controls, separate transfer/color strength and multipass edge protection | Independent community build, not endorsed by RenoDX. [Public source and author documentation](https://github.com/An0sTheGreat/DLSS-5-Super-Anus-Manual) exist, but this is not a locally accepted replacement or a measured improvement over OptiScaler |

F5's [v0.1.32 notes](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/releases/tag/v0.1.32) add 310.9-model support to bottleneck reuse and per-pass model presets. This is more than non-DLSS compatibility. Its [guide](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/INSTALL-DLSSNR.md) describes alternate-frame detail reuse and the opposing flicker/ghosting tradeoff. Its [kernel reuse implementation](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/dlssnr/DlssNrVitReuse.h) is a different optimization: selected internal network work is reused under runtime-specific guards. Neither should be conflated with ordinary every-frame NR at identical quality.

### Stability, performance and memory

Wilsjo2 [v0.8.4](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/releases/tag/v0.8.4) fixed inactive command recordings retaining replaced models. A standalone reproduction changed from 3,663 MiB retained after twelve replacements to about 51 MiB after cleanup. This is a specific regression result, not total game VRAM consumption. Its [lifetime record](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/blob/v0.8.91/docs/NR-GPU-RETIREMENT.md) documents additional retirement/concurrency failures and fixes; the [review](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/blob/v0.8.91/docs/NR-UPSTREAM-REVIEW.md) explicitly limits long-session acceptance.

Wilsjo2's [v0.8.9 spatial benchmark](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/releases/tag/v0.8.9) reports 10.6–12.3% lower pack/model/unpack GPU time for one layout on RTX5090. It excludes host codec/composition and game rendering; it is not a whole-game FPS gain or a comparison against ShortFuse.

The RenoDX-derived community fork describes bounded working pools and [fence-based recycling](https://github.com/An0sTheGreat/DLSS-5-Super-Anus-Manual/blob/main/docs/DAWNWALKER_RESOURCE_POOL_1.md). A larger deliberate cache can reduce allocation churn while increasing steady VRAM. Its [Cyberpunk history investigation](https://github.com/An0sTheGreat/DLSS-5-Super-Anus-Manual/blob/main/docs/CYBERPUNK_HISTORY_COMPARISON_1.md) separates a fixed transition defect from unresolved temporal variation. Neither record establishes superiority over OptiScaler.

Published [ShortFuse 0.55/TLOU2 failure](https://github.com/clshortfuse/renodx/issues/666) and [DLSS5/Cyberpunk motion-scale investigation](https://github.com/clshortfuse/renodx/issues/642) illustrate that successful NGX evaluation or real motion resources do not guarantee valid presentation/temporal output. These are dated, build-specific primary reports, not failure rates or proof that current releases retain those defects.

System RAM/commit, game-local VRAM residency/budget, whole-adapter VRAM and manager-process memory are different scopes. No matched system-RAM series was found. Healthy behavior requires bounded memory in a stable workload, safe retirement after changes, stable pacing and no pressure-related deterioration; low allocation alone is not a health score. Managers do not perform NR themselves, and fewer installation files do not establish lower runtime cost.

### Continued review: separately identified ReShade implementations

The follow-up continues research only. ShortFuse's `renodx-dlss.addon64`, the Generic `renodx-dlss5.addon64` line, and independent derivatives are distinct consumers. RHI distribution labels and mirrors do not establish original authorship, exact source equivalence or runtime acceptance. Do not merge their features, tests or failure reports into one "RenoDX version." The Generic source-copy lead could not be inspected through the available web route; no complete source-to-release audit is claimed.

An additional independent ReShade project, [matiasLombo/neural-upstream](https://github.com/matiasLombo/neural-upstream/blob/c06c07b27c3c5af0d916c3d9545434735d624bdf/README.md), was reviewed at HEAD `c06c07b27c3c5af0d916c3d9545434735d624bdf`. Its author documents intercepting native D3D12 NGX evaluation, running NR on the game's render-resolution color, then returning the result to native DLSS. Exposure-aware color conversion and motion/depth-based effect reuse are documented. This is a separate ReShade implementation, not an identified RenoDX fork or a Cyberpunk-tested replacement.

Its [findings](https://github.com/matiasLombo/neural-upstream/blob/c06c07b27c3c5af0d916c3d9545434735d624bdf/FINDINGS.md) record tests on RTX4070Ti in GTA V Enhanced and Bright Memory: Infinite, residual cadence-related flicker, a rare black flash, multi-evaluate/descriptor-lifetime fixes and frame-pacing difficulties with skipped NR frames under MFG. They also document earlier profiling mistakes. Those primary reports support the existence of the native-input route and its limits; they do not establish a Cyberpunk/RTX5090 performance or stability ranking. Some forwarded model controls have unconfirmed effects, so overlay controls alone are not verified features.

The inspected An0sTheGreat derivative similarly exposes genuine native-DLSS routes and bounded caches, while its [Cyberpunk history investigation](https://github.com/An0sTheGreat/DLSS-5-Super-Anus-Manual/blob/main/docs/CYBERPUNK_HISTORY_COMPARISON_1.md) explicitly leaves shimmer unresolved. F5 v0.1.32's per-pass main/small-model selection requires the 310.9 model generation; it must not be credited to the previously observed 310.8.0 setup. Less frequent evaluation, lower NR dimensions and a smaller model are different workloads, not automatically equivalent-quality implementation improvements.

### RHI / F5 FG routes and Auto semantics — 2026-10-18

Read-only review for the user's four screenshots: RHI 2.8.7's pinned component dialog source versus F5 v0.1.32, revision `9f8350810e1544befe18472a11367f6c9509db4c`. Hashed public source excerpts are retained privately. No game/manager/driver setting changed, no game launched and Home remained `0x24`. This is source/configuration evidence, not runtime acceptance.

The dialog combines separate decisions: fork/version, API-specific SR backend, FG input contract, FG output implementation, runtime deployment and latency. FG Input identifies the calls/resources to intercept, not an NR model. DLSS SR alone does not imply native DLSS FG; FSR2/3 upscaling alone does not imply FSR3 FG. FSR1/NIS do not provide the same temporal contract. A supported game-specific adapter may expose actual engine resources even when no upscaler option is visible.

| Existing integration / goal | Candidate route |
|---|---|
| Native DLSS FG works; add only SR/NR/HDR | Preserve native FG. F5's startup-only `[FrameGen] External=true` explicitly leaves Streamline/Reflex/FG to the game; it is not exposed in this RHI dialog. Consider and validate on resumption, not applied here |
| Intentionally intercept/replace Streamline DLSS FG | DLSSG via Streamline input and an explicit supported output; prefer its game HUD-less/timing data over upscaler-only capture |
| Native FSR3.1 or FSR3.0 FG, intentionally replacing it | Matching FSR FG input API, not the newest label; SR output remains a separate choice |
| Compatible temporal upscaler, no native FG | For an intentional FG addition, OptiFG/Upscaler input plus explicit supported output and validated HUD handling |
| Spatial scaling only / no compatible calls | Seek an engine-input adapter first. Optical F5Low is an optional mixed/estimated path: NR only, or a virtual upscaler feeding OptiFG for NR + FG. It is not native lower-resolution DLSS SR |

The [F5 parser/defaults](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/Config.cpp) resolve ordinary FG Input/Output auto to NoFG, not a best-backend search. [Startup](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/dllmain.cpp) disables an input without output, except the special Nvngx replacement/ForceXeLL routes. Nvngx FG uses its replacement path and ignores normal FG Output; it is not the preferred native-RTX5090 route.

RHI's Auto (false) FG label is incomplete for F5. The [follow-game rule](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/framegen/FGFollowGameRule.h) follows the game's on/off and requested frame count when the active input is Streamline DLSSG 2+ and Enabled is unset/auto. Explicit values or External mode override it; output limits/checks remain. True alone does not select/create an input/output. RHI also displays explicit false with the same label as auto.

A version-specific manager mismatch: RHI offers FG Input XeFG and writes `xefg`; F5 v0.1.32's input parser recognizes no such value, while its output parser does support XeFG. Do not recommend that input entry for this fork. This is a static parser finding, not a measured game failure.

The normal D3D12 [SR backend selector](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/inputs/NVNGX_DLSS_Dx12.cpp) starts with XeSS, selects DLSS if NGX initializes and the GPU is capable, then FFX if FSR4 support is reported; an explicit Dx12Upscaler wins. Failure paths can fall back to FSR2.1.2. This is capability/loading logic, not automatic benchmarking or newest-DLL selection. DX11/Vulkan defaults differ. Optical F5Low's [virtual backend](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/native/VirtualUpscalerDriver.cpp) instead defaults to FFX. Its image pass is normally skipped: a full-size unjittered synthetic call supplies FG, and NR can run in place. Do not generalize the normal RTX/DLSS Auto rule to this fallback.

[ForceReflex](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/hooks/Streamline_Hooks.cpp) 0 follows the game, 1 forces off and 2 forces on (the inspected Streamline hook requests low latency with Boost). It cannot create missing markers or motion/depth. Keep game markers for native Reflex. F5's [separate latency rules](https://github.com/janblade/OptiScaler-F5-DLSSNR-Multipass/blob/v0.1.32/OptiScaler/native/NativeLowLatencyRule.h) make Auto become Game in the Optical F5Low virtual-upscaler mode: games without Reflex calls do not automatically gain OptiScaler's own calls there. Explicit OptiScaler low-latency input is separate from ForceReflex=2.

For Cyberpunk/RTX5090, preserve native DLSS/RR/FG/Reflex alongside one NR consumer and RenoDX HDR. Explicit DX12/DLSS is clearer than Auto for the intended SR choice. Keep Force Reflex Auto and native markers; no replacement FG/Enabler is needed merely for NR. Any later FG replacement needs explicit input/output/dependencies and HDR/swapchain validation. The inspected XeFG checks reject scRGB/exclusive fullscreen unless overridden; this review neither recommends bypassing them nor changes any setting.

### Recommendation and future comparison boundary

Keep the user's selected wilsjo2 path as the initial candidate for Cyberpunk; choose a known pinned release and one NR pass, use real game inputs, keep optional reuse/spatial/multipass experiments off initially, preserve native SR/RR/FG and the same RenoDX HDR mod. ShortFuse's verified native hook is a valid alternative if it works better in this game. F5 is a meaningful optional performance candidate, not automatically a less capable or more stable one.

A future comparison must match the NVIDIA model/runtime, actual model dimensions, placement, pass count, quality/effect strength, native PT/RR/SR and fixed/effectively verified FG mode. First compare ordinary every-frame NR; evaluate reuse/small models/compression separately with quality changes labeled. Record rendered frame time, delivered NR output/artifacts, private commit/working set, process VRAM budget/residency where available, and steady-state plus recreation/loading behavior. NR overlay elapsed GPU timings are not necessarily incremental frame cost. On 2026-10-18 the user added the actual wilsjo2/F5/ShortFuse comparison to [the saved task](HISTORY.md#matched-wilsjo2--f5--shortfuse-comparison--deferred), to execute only when resumed. Use existing measurement tools; this does not authorize a new benchmark program or start the experiments now.

Research scope: public source excerpts, release notes and primary issue/test reports checked on 2026-10-18. Wilsjo2 v0.8.91 and F5 v0.1.32 were inspected separately from moving main branches. ShortFuse 26.1003.2350 and DLSS5 8.5.0-rc10 were found in RHI's distribution mirror; mirror labels do not certify provenance or source equivalence. Public-source/API availability limited full matching of those binaries. No new game launch, collection or visual/runtime acceptance. The 2026-09 comparison below remains historical.

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
