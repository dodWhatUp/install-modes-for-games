# Cyberpunk 2077 — Preferences

Monthly maintenance reconciliation, 2026-10-14: the existing task retains its monthly schedule and compatible-update authorization for the selected NVIDIA runtime path. Follow the October rebuild and subsequent actual settings; do not reinstall the removed OptiScaler/NR or FrameWarp stack, run obsolete controllers or apply the held September candidate. ReShade owns `dxgi.dll`, CET/Ultra+ owns F12, ReShade uses Delete and native DLSS uses F9. DLSS 310.9.1 and later saved RR/Ultra+ Auto settings were observed during this audit; they were not installed by it. Preserve these choices and archived NR slots. No automatic beta enrollment, unrelated mod/driver upgrade, benchmark or game launch is implied. See the [latest audit](HISTORY.md).

Current work scope, confirmed 2026-10-11: prioritize connecting/learning measurement tools and preparing management/import/user controls. Benchmarking, game launches and capture activation remain deferred. Existing programs provide complex metrics. See [tool connections](../../docs/GAME-TOOL-CONNECTIONS.md); no new lows or latency results are claimed.

## Latest request and live baseline — 2026-10-11 (stack baseline 2026-10-10)

- User explicitly requested removal of the prior mods and fresh ReShade, Cyberpunk RenoDX HDR and Ultra+ according to the supplied research text, then authorized the proposed installation and requested the in-game shortcuts. This supersedes the FrameWarp installation and earlier neural/modular profiles.
- Current stack: ReShade 6.8.0 full add-on as sole `dxgi.dll`, RenoDX nightly-20261009 HDR add-on, Ultra+ X rc7 with only required foundations. Keep native DLSS/Streamline and native FG as the only FG owner; leave OptiScaler/NR and FrameWarp absent. The existing GraphicsHotkeys CET adapter is retained for the requested native controls.
- Restrained Ultra+ profile: Advanced/PT21/Fast, Vanilla streaming, NRD with DLSS while RR is off; auto quality/auto confirm/graphics-menu overrides off. Native PT is seeded true before startup to avoid the observed RR/Clean transition; preserve the original PT-off recovery settings. No extended LOD/fog/Virtual Photography or additional cosmetic ReShade effects. The user subsequently authorized runtime, resource, 1% low and latency tests. Built-in benchmarks completed; differing PT workloads prevent an isolated Ultra+ cost/benefit claim. Loaded-save and per-frame checks remain pending in [runtime evidence](RUNTIME-VALIDATION.md).
- Follow-up, 2026-10-11: after the user reported very low performance, restored the saved Ultra+ config and native PT flags to the measured PT21/Fast/Vanilla profile. Pre-change RT+ / Low / PT-off settings are preserved in private snapshot `before-benchmarked-ultraplus-restore-20261011-025455`. Static verification only; no new launch or benchmark. The prior run's effective fixed-x2 versus Dynamic MFG mode remains unknown, so its game-reported FPS is not a verified current-performance result.
- Current mapping, statically read back 2026-10-11: **F12** CET/Ultra+, **Delete** ReShade/RenoDX, **F9** native DLSS quality, **F5** Quick Save, **F6** Quick Load. The installed RenoDX add-on is present and was not replaced. OptiScaler/NR is absent; Home is reserved for its full menu if installed later. F7/F10/F11 NR controls remain unavailable; the experimental F12 OptiScaler candidate conflicts with Ultra+ and must not be combined until that collision is resolved. Recover the game's saved Quick Load override as well as CET bindings during reinstalls.
- Preserve saves, all other native UserSettings and the distinct known-good/current-state snapshots. Dynamic SR stays off until its FG/engine/manual-override requirements are verified. No device mapper or Steam Input layout change is implied by these direct keyboard graphics controls.
- RHI may retain Cyberpunk ReShade/RenoDX records, but must not own the removed OptiScaler package or replace protected native/shared files. Old Vortex packages are disabled; new framework/Ultra+ copies use a private manual deployment manifest. Do not resume obsolete switch scripts or updates automatically.
- Current GPU driver is 617.42; earlier driver values below are historical. See [current guide](CLEAN-REBUILD.md) for the RR-denoiser compatibility limit and recovery boundary.

## Historical request and baseline — 2026-10-07

- Install the best available compatible FrameWarp for Cyberpunk **in addition to** its native features. Installed XPAR 1.8.5 with only its required ReShade 6.8.0 host; preserve native DLSS SR/RR/FG and Reflex. No OptiScaler/NR revival or native runtime replacement is implied.
- The October 10 clean rebuild supersedes the earlier FrameWarp/XPAR install. Its historical Delete/XPAR panel binding is no longer active; the current ReShade Delete and CET/Ultra+ F12 controls are listed above.
- Current ReShade already uses Delete. If a future separately approved OptiScaler profile is installed, its full menu uses Home; this preference does not revive the removed stack.
- Keep the experiment reversible independently, preserving current settings and known-good recovery points. See [FrameWarp guide](FRAMEWARP.md).

**Historical NR mapping, 2026-09-14:** the user moved native Quick Load to F6; Quick Save remains F5. Native DLSS quality cycling moved from F6 to the now-free F9 through the existing GraphicsHotkeys CET adapter. F11 recalls personal NR settings slots 0–3, with Save Settings storing the selected slot. F7 toggles NR 25%/100% only. F8/Page Up/Page Down are unbound; user prefers NVIDIA statistics. Slot numbers are independent of the model hints inside them. Preserve this Cyberpunk-specific exception during upgrades.

Last confirmed: 2026-10-10. Older sections below are historical or conditional on a future explicitly selected neural profile.

## Current modular-install direction — 2026-09-20

- The user explicitly selected RHI and Ultra+, delegated selection of a recommended manager and compatible performance/graphics/QoL additions, and requested continuous installation with gameplay tests left to the user at the end. This authorizes the selected foundations, ReShade, the Cyberpunk RenoDX visual profile and focused QoL pair; the earlier ask-before restriction below is superseded for this specific installation.
- Preserve a checkpoint after each installation as well as the just-in-time before state. Record downloaded/added/replaced files, versions and hashes. Change or remove only the relevant component, preserving unrelated components and later personal settings; do not require reverse-order whole-stack restoration.
- Use Vortex for ordinary game packages and the separate two-file graphics controller for ReShade/RenoDX. Keep mutable settings persistent and snapshot them separately. Respect actual shared dependencies when removing a framework.
- Protect the custom OptiScaler host, native NVIDIA runtime set, existing GraphicsHotkeys and personal NR slots from automatic manager replacement. This request does not resume the held unified-host/Dynamic SR update.
- Ultra+ first-launch profile is Advanced, PT21/Fast, Vanilla denoiser/streaming, automatic quality and automatic menu confirmation off. This intentionally introduces the requested PT tuning layer; runtime quality/performance remain unverified. Keep the saved native DLSS/FG choices and all existing shortcut exceptions.

## Latest requested direction — 2026-09-14

- The prepared Dynamic DLSS SR candidate uses F12 for its OptiScaler panel and is still uninstalled. Installed CET/Ultra+ now owns F12, so do not combine the candidate with the current stack until a collision-free panel key is chosen. The selected experimental target remains **30 rendered FPS before frame generation**, with adjustable target and 50–100% bounds; this is not Dynamic MFG.
- User explicitly selected a common OptiScaler/ReShade control interface for SR, RR, MFG/Dynamic MFG and NR. Extend the existing OptiScaler installation first. This supersedes the earlier requirement that native MFG controls remain outside OptiScaler, while preserving one underlying FG implementation.
- Use latest compatible NVIDIA runtimes and documented RR/FG models; explicitly select SR model L. Preserve personal NR slots and the established keyboard mapping.
- Apply SR resolution and NR changes during gameplay, with no restart/save reload for those settings; show effective dimensions and verify actual engine changes. DLL installation and changes to the FG backend still require a closed game.
- Monthly automatic update checks are authorized through the `Monthly Cyberpunk graphics updates` task. Preserve local controls and snapshots; do not interrupt active games. No daily or per-launch update check was requested.

## Always prefer

- Preserve Cyberpunk's native DLSS SR, Ray Reconstruction, Streamline, Reflex, and RTX 50 MFG files.
- Keep exactly one FG/MFG implementation. OptiScaler may control Cyberpunk's native Streamline settings; do not add a second generated-frame output.
- Verify the RTX 50 neural runtime by both SHA-256 and a valid NVIDIA signature.
- Keep the first neural test to one FP8 pass, pre-SR, with captures and secondary experiments off.
- Preserve the executable directory and `UserSettings.json` before updates or proxy changes.
- Use Delete full menu, F12 compact NR window, F11 personal slots, F10 neural on/off, F7 NR 25%/100% and F9 native DLSS quality. Reserve F6 for the user's Quick Load and F5 for Quick Save. Keep F8/Page Up/Page Down unbound. This describes the older NR candidate only; its CET overlay formerly used grave/tilde. The installed CET/Ultra+ mapping is now F12, and the F12 OptiScaler candidate is not co-installable until its menu collision is resolved.
- Save each NR slot explicitly and visibly report its number. Do not force direct native game-settings writes. F11 stores user-selected NR settings; native DLSS/FG remains separate.

## Prefer when compatible

- High image quality at 4K with native DLSS temporal inputs.
- Native/official named controls before numeric preset forcing.
- `dxgi.dll` for this clean install because it was absent and does not use Cyberpunk's problematic `d3d12.dll` proxy route.

## Ask before

- Enabling multipass, finished-picture placement, residual-across-RR, residual FG, hybrid precision, or OptiScaler-owned FG.
- Adding further CET-dependent mods, RED4ext, redscript, ReShade, RenoDX, or another proxy/overlay. The specific CET 1.37.1 + GraphicsHotkeys adapter for F7 was approved and installed on 2026-09-13; its runtime combination remains untested.
- Turning the global RT/path-tracing stack on as part of neural validation; test it as a separate setting group.

## Avoid

- DLSS5-Feeder or the RenoDX DLSS5 add-on alongside this OptiScaler neural consumer.
- Replacing or renaming `nvngx_dlssd.dll` as a neural runtime.
- Rapid NR/model-scale toggling while native FG is active until the reported Cyberpunk device-removal path is resolved.
- Trusting a DLL because its filename or version string says 310.8 when its hash/signature does not validate.

## Hardware/build constraints

- Recorded game/build: Cyberpunk 2077 2.31, Steam build 20383525.
- Recorded GPU/driver: RTX 5070 Ti 16 GB, 616.56.
- Original NVIDIA-signed DLSS-NR 310.8 is the RTX 50 runtime. Other RTX generations require their documented compatibility runtime and are outside this profile.
