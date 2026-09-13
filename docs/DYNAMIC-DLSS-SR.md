# Dynamic DLSS Super Resolution with a target frame rate

Reviewed 2026-09-14. The user selected **30 base rendered FPS** for Cyberpunk. A target/bounds control has been added to the prepared OptiScaler F12 + CET package; it is **not installed or gameplay-verified** while Batman/Steam are running. It delegates per-frame adjustment to Cyberpunk's native DRS. The earlier research below did not activate it.

## Current interceptor decision

| Route | What it actually supplies | Decision |
|---|---|---|
| Cyberpunk native DRS, controlled through the existing CET adapter and OptiScaler NR v0.8.3 F12 panel | Native target FPS and minimum/maximum engine render percentages; engine DLSS inputs remain native | Selected for this prepared package. Start at 30 FPS, 50–100%; keep SR model L. Verify real subrect dimensions under changing scene load before calling it working. |
| Standard OptiScaler / the inspected NR fork alone | DLSS interception and DRS min/max-query overrides; its documented FPS-target control is Dynamic MFG | No verified generic SR target-FPS controller. Existing engine DRS can operate through an interceptor, but the interceptor does not create engine DRS support. |
| DLSSTweaks | DLAA, model and per-quality scale overrides, dynamic-resolution compatibility offsets | No documented generic SR FPS-target loop in the inspected configuration. Do not add it alongside the existing interceptor for this feature. |
| DLSS Enabler | Upscaler routing and adaptive/dynamic frame-generation controls | Its documented FramerateLimit/FrameGenerationMode is about generated frames, not a native render-resolution FPS controller. |
| ReShade / game-specific engine integration | A suitable game add-on may expose real render-size controls | A ReShade preset alone cannot lower the engine's already-rendered workload. Investigate exact game support rather than assuming universal control. |

Sources checked: [OptiScaler configuration](https://github.com/optiscaler/OptiScaler/blob/master/OptiScaler.ini), [open SR target-FPS request](https://github.com/optiscaler/OptiScaler/discussions/584), [DLSSTweaks configuration](https://github.com/emoose/DLSSTweaks/blob/master/dlsstweaks.ini), [DLSS Enabler configuration](https://github.com/artur-graniszewski/DLSS-Enabler/blob/main/Dll%20version/nvngx.ini). The open request alone does not establish absence; the inspected configuration/source and lack of a demonstrated engine controller are the relevant limit.

The new [Cyberpunk control](../examples/cyberpunk-2077/UnifiedControls/README.md) sends one validated native-settings transaction. It does not estimate base FPS from generated FPS or repeatedly recreate DLSS quality modes in a Lua loop. Target and bounds are editable in F12; F6 exits DRS. The native target/bounds readback and real render-size observations are separate. At 4K, the selected 50–100% per-axis bounds request 1920×1080 through 3840×2160 input, subject to native/runtime limits. A 30-FPS target is not a guaranteed minimum when CPU, NR or other fixed costs dominate.

## Feasibility

DLSS SR can reconstruct a fixed output while the engine varies the input render dimensions. A target-FPS controller measures rendering time and asks the engine to change its workload within supported bounds. The engine must supply correctly sized color/depth/motion buffers, jitter and recreation behavior. Reducing the already-rendered NR working image is a separate operation.

NVIDIA publicly documented dynamic DLSS input dimensions on **1 September 2020**, explicitly conditioning it on engine dynamic-resolution support. This is an established integration feature. [NVIDIA announcement](https://developer.nvidia.com/blog/new-features-to-dlss-coming-to-nvidia-rtx-unreal-engine-4-branch/).

The current [DLSS programming guide](https://github.com/NVIDIA/DLSS/blob/main/doc/DLSS_Programming_Guide_Release.pdf) and [Streamline DLSS guide](https://github.com/NVIDIA-RTX/Streamline/blob/main/docs/ProgrammingGuideDLSS.md) document the engine/SDK contract. Query supported minimum and maximum input sizes; do not assume the NR 25% endpoint is supported as dynamic native SR input.

## This machine and the affected games

| Game | Current evidence | Conclusion |
|---|---|---|
| Cyberpunk 2077 2.31 | Local PC options and UserSettings contain DynamicResolutionScaling, DRS_TargetFPS (10–240), and min/max resolution controls (50–100%). Saved DRS is off, target 30, bounds 65/85%. CDPR documents DRS among upscaler settings. | Native DRS is the preferred route. Its combination with this NR/FG profile needs runtime verification; it was not enabled. |
| A Plague Tale: Requiem | Native DLSS contract exists. Current OptiScaler source supplies resolution-query overrides but no engine-level target-FPS controller. No verified live-SR hotkey adapter found in this targeted review. | Native menu quality changes remain available. Automated target-FPS scaling needs a game-specific engine integration; an INI edit does not establish this. |
| Batman: Arkham Knight | Luma build 649 + OptiScaler now tested with real engine inputs: 3840×2160 DLAA input/output; source sets dynamic_resolution=false. Native live SR adapter unavailable. | F7 changes only NR model dimensions; it does not lower the game's render resolution. No Quality/Balanced/Performance or target-FPS controller established. See the [updated history](../games/batman-arkham-knight/HISTORY.md). |
| Hogwarts Legacy (existing history) | Earlier Ultra Plus/Engine.ini profile recorded UE dynamic resolution targeting ~30 rendered FPS, with native MFG separate. | A game-specific route was already explored. This task did not change or revalidate it; it had no matching installed NR resolution-cycle shortcut. |

Cyberpunk's [official 2.1 notes, 4 December 2023](https://www.cyberpunk.net/en/news/49597/update-2-1-patch-notes) describe the reorganized upscaler settings and dynamic resolution depending on the upscaler. Current control bounds above come from the installed 2.31 configuration. The notes alone do not establish every DLSS/DRS/FG combination.

Use **base rendered FPS** for evaluating rendering workload, measuring generated display FPS separately. A CPU bottleneck may not improve when resolution falls. NR recreation and frame generation can add cost/stutter; begin future validation with a fixed NR scale and one FG owner. A numerical NR scale does not establish an achievable frame-rate target.

## Discussions and how substantive they are

| Date | Source | What it establishes |
|---|---|---|
| 2020-09-01 | [NVIDIA announcement](https://developer.nvidia.com/blog/new-features-to-dlss-coming-to-nvidia-rtx-unreal-engine-4-branch/) | Official support and engine requirements: strong evidence of an established feature. |
| 2023-09-28 | [NVIDIA developer-forum discussion](https://forums.developer.nvidia.com/t/dynamic-resolution-scaling-drs-with-dlss-scaling-factors-below-1-2/267840) | A developer reports testing DLSS 3.5 DRS bounds and asks about scales below 50%. Concrete SDK discussion; a historical participant result, not a universal current limitation or NVIDIA commitment. |
| 2025-07-09 | [OptiScaler discussion #584](https://github.com/optiscaler/OptiScaler/discussions/584) | Requests automatic resolution based on target FPS. Still unanswered, zero comments when reviewed. It is not evidence of an implementation or release schedule. |

The technology is established. Evidence for a universal target-FPS controller in the installed OptiScaler forks is weak: reviewed source exposes DRS min/max query overrides, while its FPS target control belongs to **Dynamic Multi Frame Generation**, a different feature. A generic bridge cannot by itself make an engine render different-sized buffers correctly.

Future activation should first select the target base FPS and bounds, preserve the stable profile, then verify changing render dimensions, frame times, motion/UI and recreation. No such experiment was scheduled or started here.
