# DLSS 5, Ultra+, HDR and VRAM — Cyberpunk decision review

Research date: 2026-10-10, Asia/Jerusalem. Status: researched recommendation; no game installation, settings change, gameplay benchmark or new automation was performed. Canonical owner: `dodWhatUp/install-modes-for-games`, `games/cyberpunk-2077/`. This report updates the decision evidence, not the recorded installed state.

## 1. Recommendation

For the documented RTX 5070 Ti 16 GB / 4K setup, my preferred everyday Cyberpunk direction is a restrained Ultra+ configuration, native DLSS features and the game-specific RenoDX HDR add-on. Keep DLSS 5 Neural Rendering (NR) as an optional visual mode. If its appearance is much more valuable to the user, keep one economical NR pass and reduce the other visual costs instead of maximizing both.

This recommendation assumes path tracing is desired. Turning path tracing on just to use Ultra+ can cost more than adding one NR pass to a raster/RT baseline. Neither Ultra+ nor NR is a universally cheaper substitute for the other. A native-only renderer plus HDR correction remains the lowest-complexity reference.

Ultra+ modifies engine rendering/lighting; NR enhances the rendered image. They can be combined, and Ultra+ documentation explicitly discusses DLSS5. No current matched Cyberpunk measurement establishes a universal FPS or VRAM winner. [S01, S02, S03]

| Option | Purpose and expected benefit | Main limitation | Difficulty / confidence | Reversible route |
|---|---|---|---|---|
| 1. Native rendering + native DLSS + RenoDX HDR | Budget reference; improve HDR while retaining existing renderer | Exact HDR/load-chain combination needs checking | 2–3 / high for role, untested locally | Restore the visual-stage snapshot |
| 2. Restrained Ultra+ + native DLSS + RenoDX HDR | Recommended PT direction; improve source lighting with bounded quality/streaming settings | Ultra+ can add memory and rendering cost; version-specific overlap | 3 / medium for recommendation, untested locally | Restore pre-Ultra+ files/settings |
| 3. Native rendering + one OptiScaler NR consumer + RenoDX HDR | Prefer when the neural appearance matters more than extra PT quality | NR compute, model memory and temporal/color artifacts | 3–4 / conditional | Disable NR through its master switch; guarded file rollback if needed |
| 4. Ultra+ + one NR consumer + RenoDX HDR | Most extensive combined visual experiment | All costs and interactions accumulate | 4 / untested combined profile | Remove the last added stage first |

Options describe proposed profiles, not already applied settings or new accepted preferences. Existing first-playthrough, later-play and experimental classifications remain in the Recommendations record.

## 2. Recovered personal baseline

The September game records establish a custom OptiScaler NR 0.7.7 personal-slots build and native temporal inputs. Creation/evaluation was observed; full interactive, visual and long-session validation remained incomplete. The prepared 0.8.3 / Streamline 2.14.1 / DLSS 310.9.1 package was not installed. RHI and Ultra+ were planning defaults, not verified installed components. These are historical records, not a live machine inventory. [L01, L02]

Preserve SR model L, the selected adjustable target of 30 rendered FPS before frame generation, and monthly update cadence. Dynamic MFG was recorded; displayed FPS cannot reliably be divided by a fixed multiplier. The current status of the earlier monthly automation was not checked and no new schedule was created. [L02]

| Saved control | Meaning to preserve |
|---|---|
| F12 / Delete | Compact or unified graphics controls / full menu |
| F11 | Personal NR slots 0–3; explicit Save Settings |
| F10 | NR master on/off |
| F7 | NR working dimensions 25% / 100% |
| F6 | Separate native DLSS SR quality control |
| F9 | Cyberpunk Quick Load |
| F8 / Page Up / Page Down | Unbound |

These selected mappings supersede older historical tables. The proposed common interface and some live native-resolution changes still need runtime validation. A generic upstream replacement does not necessarily contain these custom controls.

## 3. Performance and memory evidence

NR is independent of DLSS Super Resolution, Ray Reconstruction and frame generation. Disabling NR does not require abandoning those features. The neural pass consumes GPU work; lower working resolution or fewer passes may reduce its cost, but manager selection alone cannot do that. [S01, S06]

An original Tom's Hardware test dated 2026-09-02 measured Cyberpunk at 4K output, DLSS Performance (1080p input), maximum path tracing and RR, with no FG/MFG. RTX 5090 FE averaged 90.91 FPS without NR and 53.18 with it: about 42% lower. This was an early community injector; the precise build and NR preset were not identified. It is not a benchmark of this user's GPU, October backends, Ultra+ or their combination. No VRAM measurements were provided. [S04]

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| Ultra+ X RC7, uploaded 2026-10-09 | Actual downloadable release candidate; v9.3.10 remains offered | Either version's universal stability or memory superiority |
| RC7 changelog: 650 MiB reduction with High/Insane streaming | A specific memory improvement from preceding code/settings | Total Ultra+ overhead, savings versus stock, or savings on every preset |
| OptiScaler NR v0.8.4, 2026-09-15 | Fix for retained models after replacement/reconfiguration | A diagnosed leak on this user's PC |
| v0.8.4 standalone reproduction: 3,663 MiB retained after 12 replacements; roughly 51 MiB after corrected cleanup | A concrete resource-lifetime failure and fix in that reproduction | Cyberpunk's normal NR footprint or guaranteed user savings |

Sources: [S02, S03, S07]. The installed historical custom 0.7.7 and prepared 0.8.3 precede that memory-fix release. Prioritize reviewing/porting the fix into a compatible controlled update while preserving the custom interface. Do not blindly install an old release merely because it introduced one fix.

### Correction to earlier chat estimates

The earlier general ranges RenoDX HDR 20–200 MB, OptiScaler 10–100 MB and DLSS5 NR 0.3–0.8 GB were not established by controlled local measurement. Do not reuse them as guaranteed footprints or capacities for planning this setup. The historical 4.83 ms GPU interval / 4.74 ms model entry likewise is not an isolated current NR frame-time penalty. [L01]

Textures, LOD/streaming, render buffers, temporal history, NR models and selected modes all contribute to memory. Lowering the neural input reduces some work and resources, not every fixed allocation. At 4K DLSS Performance, pre-SR can process 1920×1080: one quarter of 4K pixels, not one quarter of total VRAM or four times the FPS. [S06]

Higher allocated memory by itself does not diagnose a leak. Compare the same scene/path after warm-up, sustained growth, shared GPU memory, stutters and crashes. A setting that causes no immediate problem can still leave insufficient headroom for a demanding area. Exact acceptable headroom remains unmeasured here.

## 4. Best installation and maintenance direction

RHI remains the preferred manager when its exact supported component matches the selected stack. Latest verified release is RHI 2.8.5, published 2026-10-05. It provides component management and original-DLL restoration; its documented Update All respects exclusions. This does not make every custom fork interchangeable. [S08, S09]

For this Cyberpunk installation, preserve the existing native-input OptiScaler approach and customized controls. A generic Feeder stack adds no demonstrated input advantage here. Ordinary OptiScaler and a DLSSNR-enabled fork are different packages. Keep one NR consumer and one native FG/MFG implementation. A compatible ReShade host and the Cyberpunk RenoDX HDR add-on are a distinct visual stage. [L01, S06, S10]

Proposed procedure for a later requested installation:

1. Read the current machine/build/files while no relevant game or update process is using them. Preserve the current and last-good snapshots, including custom slot settings and external driver settings.
2. Review a coherent NR update incorporating relevant fixes; port the saved controls and confirm the exact package. The earlier prepared package is not automatically the correct new candidate.
3. Use RHI for compatible standard components; exclude the custom OptiScaler deployment from generic replacement. Use one managed file arrangement, not a parallel manual copy.
4. Add the current Cyberpunk-specific RenoDX HDR add-on to one compatible full-add-on ReShade host. Resolve proxy loading through the selected package's documented chain. No universal DLL rename is safe for this existing installation.
5. Compare HDR and NR separately, then add a restrained Ultra+ profile if desired. Keep separate rollback for each stage.
6. Retain monthly update checks and controlled deployment of compatible releases. Do not silently promote release candidates or overwrite custom settings. No update schedule was changed by this review.

RHI also offers Feeder/ShortFuse neural routes and an optional NR Cost Scaler (documented default 75%). These are alternatives for suitable games, not reasons to replace this game's native-input custom path. No matched current test proves one manager or backend universally uses least VRAM. [S08]

For other games: use native NR if actually available; otherwise prefer a supported integration with real game inputs. Use a compatible ReShade-based route when it supplies the required data. The executable/API, input origin, HDR handling and version matter more than the tool's name.

## 5. Does DLSS 5 improve or fix HDR?

The user's observation is plausible. NVIDIA documents separate structure and tone controls: tone can change broad lighting/color, while structure changes finer material/light response. This can improve perceived contrast or highlight appearance. It does not establish correction of a game's transfer function, gamut, clipped source values or display calibration. An inferred highlight is not recovered original data. [S01]

There are also implementation fixes: a September Cyberpunk NR package explicitly listed an HDR-handling correction. Thus an improvement seen after installing “DLSS 5” may partly come from its injector or bundled visual stage. [S11]

First-hand reports are mixed. A Horizon Forbidden West user liked NR but still reported needing HDR fixes; commenters described both improved lighting and altered color. That supports reports of visible change, not a consensus or calibrated proof of HDR repair. [S12]

### Cyberpunk recommendation

Keep the game-specific RenoDX HDR add-on if HDR correction is wanted, with or without NR. Its author documents game shader and tone/LUT correction through the ReShade add-on API. Ordinary cosmetic ReShade effects are not required for that HDR add-on. Use the current upstream build, not an old Nexus binary chosen only by page popularity. [S10]

Ultra+ has historical RenoDX compatibility support and its own lighting/highlight adjustments. Its bright-light compression serves a source-lighting purpose; it is not evidence that the display-mapping stage is redundant. Verify the exact current combination rather than automatically disabling that compression. [S03]

| Control | Proposed starting decision |
|---|---|
| Windows HDR | On for HDR playback |
| HDR route | Native HDR with the compatible Cyberpunk RenoDX add-on; avoid stacking another SDR-to-HDR conversion |
| Peak brightness | Use the display's measured/calibrated peak; do not assume 1000 nits for every screen |
| Paper white / game brightness | Comfortable diffuse brightness, adjusted separately from peak highlights |
| Game HDR10 PQ Saturation with FG | Start at 0; Ultra+ history flags the saturation/FG interaction; use RenoDX for deliberate saturation adjustment |
| RenoDX tone mapper | Start from that selected build's defaults; older guides may describe different defaults |
| Extra ReShade effects | None for the initial HDR-only comparison; retain any effects genuinely required by a chosen NR route |

RHI's manual says enabling RTX HDR removes the active RenoDX mod and disabling RTX HDR does not reinstall it. Treat this as a switch of HDR approach. It is distinct from Windows HDR being enabled. [S09]

One NR consumer does not mean “never use ReShade.” OptiScaler NR plus RenoDX's game HDR add-on can be valid; OptiScaler NR plus a competing RenoDX NR consumer is a different, problematic arrangement. [S06]

## 6. Keep daily controls small

Use the saved compact menu and personal slots. Expose NR on/off, one-pass strength/working size, native SR quality, the adjustable base-FPS target and HDR brightness. Preserve full controls behind Delete. Keep undocumented model hints separate from saved slot numbers.

For an Ultra+ trial, begin in Simple Mode with a performance-oriented PT choice and conservative streaming/LOD. The author's v9 guide recommends PT21 for NVIDIA quality and PT20/Fast when more FPS is needed. Auto Quality is available, but do not run two competing automatic quality controllers without understanding what each changes. The existing 30-FPS dynamic-SR request remains separate from Dynamic MFG. [S05, L02]

For NR, start with one pass and no new multipass, finished-picture, hybrid or residual experiments. Existing pre-SR behavior should be retained only with its RR/FG limitations understood. Lower working dimensions before layering complex performance tricks, inspect moving detail and preserve settings. The documented “Apply the model” switch can hide the appearance while still doing GPU work; use the true NR master switch for performance comparisons. [S06]

## 7. Minimum remaining validation

No new on-device test was done. A later authorized test should use the same save, weather/route, resolution, SR preset, texture settings, frame-generation state and display settings. Compare native baseline, HDR stage, Ultra+ stage, NR stage and the intended combination without changing unrelated settings.

Measure base rendered FPS/frame time and displayed FPS separately; also record 1% lows, dedicated/shared GPU memory and process/system RAM. After a short repeatable comparison, use a longer repeated route to check growth. Restart between major model/placement configurations when establishing clean memory baselines. Do not rapidly recreate NR resources while FG is active on the historical affected build.

Inspect shadows, bright neon, skin, foliage, HUD, camera motion, loading/alt-tab and shutdown. A good-looking still or a loaded overlay is insufficient. No screen/video capture is required by this plan; respect the user's text-only inspection preference.

Remaining unknowns: current GPU/build/runtime inventory; whether later installations occurred; present NR/Ultra+/HDR versions; exact combined FPS and memory; cause of any user-observed RAM growth; status of the existing maintenance automation. None blocks the researched comparison. Installation requires a separate current-state check when requested.

## 8. Sources and provenance

Public sources were read on the research date. Author claims, original measurements, first-hand reports and recommendations are distinguished above. No proprietary DLLs, third-party binaries, raw private logs or personal filesystem paths are included.

| ID | Source | Role / qualification |
|---|---|---|
| S01 | [NVIDIA DLSS 5 launch/technical explanation](https://www.nvidia.com/en-us/geforce/news/dlss-5-3d-guided-neural-rendering/) | September 2026 vendor primary; NR role and tone/structure controls |
| S02 | [Ultra+ files](https://www.nexusmods.com/cyberpunk2077/mods/10490?tab=files) | RC7 and retained v9 download status |
| S03 | [Ultra+ change history](https://www.nexusmods.com/cyberpunk2077/mods/10490?tab=logs) | Version-specific memory/HDR/compatibility statements, not local tests |
| S04 | [Tom's Hardware original DLSS 5 benchmark](https://www.tomshardware.com/pc-components/gpus/we-explored-early-dlss-5-performance-with-community-mods-and-the-limits-of-the-12v-2x6-power-connector-may-hold-it-back-on-the-rtx-5090) | 2026-09-02; early injector; no FG/MFG or VRAM measurement |
| S05 | [Ultra+ Cyberpunk guide](https://theultraplace.com/games/cyberpunk2077/) | Author's v9-oriented controls/modes; not proof of exact v10 behavior |
| S06 | [OptiScaler NR setup guide](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/blob/main/INSTALL-DLSSNR.md) and [project](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass) | Experimental controls/contracts; the old forwarder checklist conflicts with later release history and should not be copied wholesale |
| S07 | [NR v0.8.4 memory fix](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/releases/tag/v0.8.4) | Standalone resource-lifetime reproduction; full-game validation not established |
| S08 | [RHI](https://github.com/RankFTW/RHI) and [RHI 2.8.5](https://github.com/RankFTW/RHI/releases/tag/RHI-2.8.5) | Manager capabilities and release status |
| S09 | [RHI 2.8.5 detailed manual](https://github.com/RankFTW/RHI/blob/RHI-2.8.5/docs/DETAILED_GUIDE.md) | Component management, exclusions, proxy coordination and HDR route switching; retrieved through GitHub connector |
| S10 | [ShortFuse's Cyberpunk RenoDX HDR mod](https://www.nexusmods.com/cyberpunk2077/mods/13912) and [current mod list](https://github.com/clshortfuse/renodx/wiki/Mods) | Primary shader/HDR purpose; Nexus binary is historical, current builds linked upstream |
| S11 | [Cyberpunk DLSS5 package/guide](https://www.nexusmods.com/cyberpunk2077/mods/33380) | September 1 package v4.7 HDR fix; not the preferred current installation checklist |
| S12 | [Horizon Forbidden West first-hand discussion](https://www.reddit.com/r/nvidia/comments/1w180ro/horizon_forbidden_west_dlss_5/) | User experiences, not calibrated evidence or Cyberpunk measurements |
| L01 | [Saved Cyberpunk history](https://github.com/dodWhatUp/install-modes-for-games/blob/8afe64c96b6fba7dff030ed0ab23cebf06b81392/games/cyberpunk-2077/HISTORY.md) | Historical installation, validation limits and prepared package |
| L02 | [Saved Cyberpunk preferences](https://github.com/dodWhatUp/install-modes-for-games/blob/8afe64c96b6fba7dff030ed0ab23cebf06b81392/games/cyberpunk-2077/PREFERENCES.md) | Saved hardware, controls, SR L, 30 base FPS and monthly cadence |

Guidance discovery: Global was read at `0150b1c42455a4167ec1095fbfb26a3731bbcf45`; research method at `57b12ccf2ac0aac21d40490c734164c22f39249f`; game owner at `8afe64c96b6fba7dff030ed0ab23cebf06b81392`. No consumer pin was installed or repinned. The game owner had no separate pending-correction queue in the inspected tree; this dated correction is linked from its existing History and Recommendations routes.
