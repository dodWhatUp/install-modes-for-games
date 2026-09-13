# Personal neural-rendering settings slots

Cyberpunk-specific installation on 2026-09-13, built over the existing wilsjo2 v0.7.7 F7 customization. This is a local source change, not an upstream release or a universal DLL.

## Controls and saving

- F11 recalls settings slots **0 → 1 → 2 → 3**.
- Open **F12**, choose **My NR settings**, edit the NR settings, then press **Save Settings**. Save each slot separately. The full Delete menu saves the same selected slot.
- All four slots initially share the current configuration. They become different only after the user saves different settings in them. Unsaved changes are marked; switching recalls the target slot's saved settings.
- **Model preset** remains an independent model hint inside each slot. The former F11 model-hint cycle did not provide per-number personal settings.
- F7 retains **25% ↔ 100% only**. F10 toggles NR, F12 controls the compact menu, Delete controls the full menu.
- F8, Page Up and Page Down are unbound (`-1`); the OptiScaler FPS overlay starts off. Manual placement controls remain available.
- F6 remains Cyberpunk's separate native DLSS control, with [corrected CET notifications](../../cyberpunk-2077/GraphicsHotkeys/README.md).

## Implementation

`PersonalProfiles.h` snapshots 64 NR settings and optional overrides for passes 4–30. It includes model/style, NR scale, intensity, skin/environment controls, white-point settings, placement and pass settings. Hotkeys, native DLSS quality/FG, probe/runtime-loader switches, automatic capture and temporary Hold frame are outside the slots.

The sidecar `DlssNrProfiles.json` stores the four slots and last saved selection. Save Settings also writes the normal OptiScaler INI. JSON saves use a temporary file and atomic Windows replacement; failed saves produce a warning. An unreadable profile file is preserved rather than overwritten. Every slot is validated in full before application. There is a one-second slot-switch cooldown; the existing NR recreation path handles changed model parameters. Startup reads slot metadata without applying new graphics settings.

The included patch applies after the prior F7 revision on commit `e237f895623742b761f9e5f00067cb3dc62619f4`. Add the included header at `OptiScaler/dlssnr/PersonalProfiles.h`. Binaries and private game profiles are excluded from this repository.

## Validation and rollback

The complete x64 proxy links successfully; all 946 exported names/ordinals match the installed predecessor. Standalone C++ tests cover independent slots, all-setting serialization, inherited-option reset, cooldown, restart metadata without startup mutation, invalid data rejection before any mutation, and corrupt-file preservation. CET Lua tests cover the existing native-mode/bridge guards and drawing notifications only in onDraw.

Initial installed proxy SHA-256: `A6B69CCAD9F2176B6255365BDD651395459BEC7BF9F26A066DD82BB0B2A2A270`.

Private snapshot `cyberpunk-personal-controls-20260913-232201` contains the preceding DLL/INI/adapter, logs, native-file hashes, user/Steam/NVIDIA configuration, source files and pre-test saves. Its `Restore-PersonalControls.ps1` defaults to validation only; with games and Steam closed, `-Apply` preserves current controls and restores the preceding three files. It preserves personal-slot JSON and leaves NVIDIA's overlay enabled. Use this before the older F7 rollback chain. See the game history for the final runtime boundary.
