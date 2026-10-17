# Monthly compatibility review — 2026-09-15

**Installation held.** The game and store processes were closed at review time. The outstanding limit is compatibility and the user's newer control requirements, not process availability. No game or NVIDIA profile file was changed and no game was launched.

## Current and available versions

| Component | Installed | Reviewed update | Result |
|---|---|---|---|
| Custom OptiScaler NR | v0.7.7 personal-slots build, hash `A6B69CCAD9F2176B6255365BDD651395459BEC7BF9F26A066DD82BB0B2A2A270` | v0.8.3 stable / v0.8.4 prerelease | v0.8.4 downloaded and custom source port staged; not compiled or installed |
| NVIDIA DLSS SR/RR/FG | 310.1 | 310.9.1 | Existing candidate still current; signatures rechecked |
| Native Streamline | 2.7.1 | 2.14.1 | Existing candidate still current; game integration remains unverified |
| NVIDIA NR runtime | Signed 310.8 | No replacement supplied by the fork | Preserve current runtime |

[OptiScaler NR v0.8.4](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/releases/tag/v0.8.4), source `8802b2b470db0462fa1ed03a125e793a7c06d735`, adds a model/placement-switch VRAM lifetime fix and an optional pass-count unlock. The standard ZIP SHA-256 matched the published digest: `8789912859882E66B3F3A1AA768DB947DA779DFD65225DF69EA919052E73A2E4`. All 55 files listed in its internal checksum manifest matched. No multipass option was enabled. Upstream's lifetime reproduction and builds do not establish full Cyberpunk-session stability.

NVIDIA still lists [DLSS 310.9.1](https://github.com/NVIDIA/DLSS/releases/tag/v310.9.1), with RR model F, and [Streamline 2.14.1](https://github.com/NVIDIA-RTX/Streamline/releases/tag/v2.14.1) as latest. The eleven NVIDIA candidate DLL signatures are Valid; the existing SDK ZIP still matches `92C4D954631A1710DA86CA3FA8D5034F2B9503838C95FC4AE977AE149319781B`. Pin SR L and retain the latest verified compatible FG model when an update is finally installed; do not replace a game-specific Streamline set blindly.

## Control audit

The custom source patch applies cleanly to v0.8.4. The private staged header/Lua captions were updated to **F9** to match the already installed native-quality binding. F6 belongs to Quick Load; F5 remains Quick Save. No installed binding changed.

The current prepared adapter failed four isolated tests against the newer [Dynamic SR requirements](../../../docs/DYNAMIC-DLSS-SR.md):

1. With native FG disabled, a dynamic request still enables target mode.
2. After a manual fixed 80% request, enabling dynamic mode and then disabling it does not restore that manual request.
3. Disabling FG through the adapter leaves dynamic mode enabled.
4. Turning FG off externally also leaves dynamic mode enabled.

These are reproducible failures in the prepared adapter, not observations of a newly installed game build. Persistent manual override and native controller qualification also remain unverified. Earlier passing tests cover the earlier specification and are not acceptance evidence for these newer requirements.

## Resume boundary

The private `cyberpunk-monthly-20260915` folder contains the verified upstream ZIP, detached v0.8.4 source port, policy audit, NVIDIA signature/driver readbacks and installed inventory. The earlier built v0.8.3 package remains separate. Its installer now refuses `-Apply` while its `INSTALL-HOLD.json` is present.

Before clearing that hold, implement and test FG eligibility/transitions, save/restore manual SR and persistence, preserve F9 and the NR slots, and build the selected source revision. Keep Dynamic SR unavailable/off until a real engine controller and the enabled FG path are verified. Validate manual controls and actual DLSS input dimensions, then the NR/FG combination and any Streamline replacement in a user-initiated session. The monthly task must not launch the game itself. Take a fresh current-state snapshot immediately before any later installation.

No rollback is needed for this review because installed files were not mutated. The existing known-good and current-state backups remain intact. Staging the release does not authorize running its stock installer over the custom host.
