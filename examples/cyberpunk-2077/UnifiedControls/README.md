# Unified Cyberpunk graphics controls

Prepared 2026-09-14 for Cyberpunk 2077 2.31, RTX 5070 Ti and driver 616.56. Installation and gameplay verification must be checked against the latest game history; preparation alone is not a working-game claim.

Final prepared proxy SHA-256: `121D0D5D86A94D04A3DDC1C5C819BBF25554E8824982ECB0E130F1C74CEAA27F` (26,374,144 bytes). The final fourteen-file candidate was regenerated after the UI build. All fourteen installed originals still match the pre-installation validation snapshot; no game or driver mutation occurred. Installation is waiting for Batman/Steam to close.

The locally built host is based on [OptiScaler NR v0.8.3](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/releases/tag/v0.8.3), commit `47e134cb`, with the user's existing personal NR slots and keyboard controls ported to the newer source. F12 opens a common SR/RR/FG/NR panel. Delete retains the full upstream menu. The existing CET 1.37.1 loader handles the narrow native-settings requests; it does not generate frames.

## Controls

| Control | Effect | Verification boundary |
|---|---|---|
| F6 / Quality selector | Native DLAA, Quality, Balanced or Performance; Ultra Performance is additionally available in the selector | Game readback plus actual input/output dimensions |
| Dynamic DLSS / target FPS | Enable/apply the native engine DRS controller, initially **30 rendered FPS**, with adjustable 50–100% min/max input bounds | Verify changing input subrects and base FPS under scene load; setting readback is not proof of DRS performance |
| SR render-resolution slider | Requests equal native DRS bounds, 50–100%, when released | Experimental until effective engine dimensions are observed; not a resize of the NR image |
| RR checkbox | Changes Cyberpunk's RR setting | Enabling requires ray tracing already on; does not silently enable RT |
| FG checkbox | Changes native DLSS FG enable state | Requires the native DLSS FG backend already selected; backend changes require restart |
| MFG multiplier | Overrides native Streamline interpolation count within reported hardware/runtime support | No invented support for an unreported multiplier |
| Dynamic MFG / target | Uses the native Streamline dynamic mode when support is reported | Target 144 FPS initially; actual interpolation and presentation require gameplay verification |
| NR controls | Upstream model resolution, model parameters, skin/colour and placement settings | Expensive changes apply on slider release; GPU resource recreation can cause a hitch |
| F7 / F10 / F11 | NR 25%↔100%, NR enable, personal settings slots 0–3 | Save Settings stores the selected NR slot |

F8, Page Up and Page Down remain unbound. F9 remains Cyberpunk Quick Load. Slot JSON is preserved, including retired experimental values for rollback. New fields are migrated without applying a slot automatically at startup.

For Dynamic DLSS, adjust target/min/max and press **Enable / Apply Dynamic DLSS**. **Disable Dynamic DLSS** or F6/quality selection exits target mode; the fixed-scale slider is disabled while varying bounds are requested. Successful requests use native `DynamicResolutionScaling`, `DRS_TargetFPS`, `DRS_MinResolution` and `DRS_MaxResolution` settings. These are engine-owned settings, separate from NR slots and OptiScaler's Dynamic MFG target. Startup makes no native settings changes. SR model L remains the configured model at all input sizes.

Protocol 3 carries the native FPS target in its 18-field status packet. The adapter rejects stale/mismatched protocols, malformed targets and invalid ranges before writing any field. Bounds are changed in an order that respects the current min/max limits; immediate and delayed rejection restore the complete previous group. Dynamic resolution is delegated to the engine, not simulated by measuring generated FPS or continuously switching quality modes from Lua. The user selected 30 FPS, not a guaranteed floor: a CPU bottleneck or fixed NR cost can keep performance below target even at minimum resolution.

## Runtime and model plan

- NVIDIA production [Streamline 2.14.1](https://github.com/NVIDIA-RTX/Streamline/releases/tag/v2.14.1), published 2026-09-08, and its DLSS SR/RR/FG 310.9.1 libraries. The official ZIP SHA-256 is `92C4D954631A1710DA86CA3FA8D5034F2B9503838C95FC4AE977AE149319781B`. Only the relevant production files replace the corresponding existing game files as a coherent set; unrelated optional SDK features are not installed.
- SR preset **L** (`12`) in OptiScaler; RR preset **F** (`6`), the latest documented compatible RR model at this review. Model choice is not inferred from version numbers or NR hint numbers.
- Preserve the existing NVIDIA-signed NR 310.8 runtime. The current fork explicitly says to retain the installed NR runtime; its newer release does not supply a newer NVIDIA NR DLL. Other games' proprietary runtime files are not harvested.
- Keep native Cyberpunk FG as the only implementation. OptiScaler uses `FGInput=nofg`, `FGOutput=nofg`, `Enabled=false`, while its native Streamline hooks control the multiplier and dynamic target. v0.8.3 no longer implements the old `External` switch; the old INI entry is not proof of feature ownership in this version.
- The small NVIDIA DRS utility changes only Cyberpunk's driver profile: clear driver MFG mode/count/target overrides so they do not supersede the menu, delegate SR/RR model control to OptiScaler, and retain the documented FG B model. It snapshots eight exact settings and restores their values or inheritance. No global graphics profile is changed.

Streamline 2.14.1 adds Dynamic MFG support for V-Sync and frame limiters. Older NVIDIA launch guidance described those as incompatible; that historical restriction must not be repeated as universal current behavior.

## Files and checks

`init.lua` is the native adapter. `UnifiedControls.h` is the OptiScaler panel. `driver-profile.cpp` uses NVIDIA's public NVAPI DRS API. `Restore-UnifiedControls.ps1` runs from the private installation snapshot, defaults to validation only, and needs `-Apply` for restoration with games/Steam/compilers closed.

For rebuilding, use upstream commit `47e134cbcd9d3653d63f58a36d38281e827007ec` with its matching submodules, apply `optiscaler-v0.8.3-unified.patch`, and copy `PersonalProfiles.h` and `UnifiedControls.h` into `OptiScaler/dlssnr/`. Generate the normal resource headers with build stamp `47e134c+unified-controls` and date `20260914_unified`, then perform a full Release x64 build. The patch contains the integration changes; the two new headers are separate files. Do not use the initial private port helper as the final source patch. The final patch passed reverse-application checking against the built source.

`test-adapter.py` runs the native-settings adapter against a Lua mock using Python and Lupa. It is location-independent and does not read or write game settings. The personal-slot migration tests were also run in a separate C++ harness against the final header. Neither mock proves game-engine behavior.

The adapter validates complete requests before applying them, uses a session token/expiry/replay guard, permits one change at a time, verifies delayed readback and rolls back rejected changes. Notifications run only in CET's `onDraw`. Neither startup nor a stale request rewrites graphics settings. The actual engine-buffer change cannot be established by these isolated tests.

Static tests cover adapter prerequisites/rollback/protocol, NR slot migration and corrupt-file preservation, the declared proxy exports and explicit ordinals, and retained binaries' static Streamline imports. New Streamline removes 58 NGX exports from `sl.common.dll`; none are statically imported by the examined retained root binaries/replacement plugins. Dynamic lookup compatibility still needs a game launch. Fourteen incidental FSR library exports disappear from the newer OptiScaler build; all 854 names declared by the current proxy definition and its explicit ordinals are present.

No binary, game settings, save, private snapshot or raw log belongs in this repository. Private staged scripts perform a fresh snapshot immediately before installation. Rollback restores the prior DLLs, INI, CET adapter and the eight NVIDIA profile settings, while preserving NR slot JSON and saves. The previous personal-controls and clean snapshots remain separate.

Monthly maintenance is configured in the current Codex task on the 14th at 12:00 local time. It checks official/current releases and applies compatible verified updates only while games/store clients/compilers are closed, preserving custom controls and rollback. It stays quiet without an actionable change and never launches a game automatically.
