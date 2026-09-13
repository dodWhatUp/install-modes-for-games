# F9 model-resolution control for Dagherbou v0.2.0

**Superseded controls, 2026-09-13:** the current installed F7 25%/100% builds and follow-up source patches are documented in [F7 two-scale controls](../f7-two-scale/README.md). Earlier cycle descriptions below are historical build evidence, not the current mapping.

Minimal source patch against [Dagherbou/OptiScaler_DLSSNR v0.2.0-dlssnr](https://github.com/Dagherbou/OptiScaler_DLSSNR/releases/tag/v0.2.0-dlssnr), commit `973761621353b99bee3dc7d4bb27b117fef2644f`. This is a local customization, not an upstream release.

Apply `f9-model-scale.patch` from that source tree's root. Build the original x64 Release target with its pinned dependencies. The local build uses MSVC 14.44.35207 and Windows SDK 10.0.26100.0; its generated resource stamp is `9737616+f9-scale`, dated 2026-09-13. The patch does not alter the renderer or proxy exports.

F9 cycles the existing `DlssNrWorkingScale`: 100% → 75% → 67% → 50% → 100%. Percentages describe each model-input dimension, not total pixel count, game render resolution, or DLSS SR quality. Existing non-cycle slider values choose the next smaller step; values below the last step wrap to 100%.

- Uses the same focus, key-release, and key-capture input path as the existing NR toggle.
- A 750 ms minimum interval limits rapid repeated resource rebuilds. Holding a key does not repeatedly cycle.
- Shows a 2.5-second model-resolution notification and logs the selected percentage.
- Keybind: `NR Model Resolution`; INI: `[DlssNr] ScaleCycleKey=0x78`.
- Starts with the configured `WorkingScale`; F9 changes it in memory. **Save Settings** persists the selection using the existing INI writer. ReShade preset saving does not save OptiScaler settings.
- F7 SR quality and F8 pre/post-SR are not implemented by this patch.

`nr-scale-cycle-test.cpp` contains 11 compile-time boundary assertions. To compile it after applying the patch, place it in a `tests` directory directly below the source root (its include is relative to that location). Game-specific validation and rollback evidence are recorded in [Batman history](../../../games/batman-arkham-knight/HISTORY.md).

No DLLs, dependencies, game files, or private paths are included here. Existing upstream licensing applies to context in the patch.
