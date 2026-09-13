# Default controls for graphics add-on installations

Follow the current [general preferences](../preferences/GENERAL.md). The latest 2026-09-13 request changes NR model resolution to **F7: 25% ↔ 100% only**. Earlier F9 cycles are historical.

| Key | Meaning |
|---|---|
| Delete | Full graphics add-on controls |
| F12 | Compact NR controls, with native SR controls beside them where supported |
| F11 | Personal NR settings slots 0–3; Save Settings saves the selected slot |
| F10 | NR on/off |
| F8 | Unbound by user request |
| F7 | NR model dimensions 25%/100% only |
| F6 | Live native DLSS quality where an engine adapter exists |
| Page Up / Page Down | Unbound; use NVIDIA statistics instead |

F7 is explicitly user-selected. F6 is the collision-avoiding implementation choice for separate SR because Cyberpunk already uses F9 for Quick Load. Preserve native game bindings unless a conflict must be resolved and documented. Do not bind the same action in two components.

During a requested installation or controls update:

1. Identify the owner for NR scale, placement and native SR. A changed NR model size is not a changed game render resolution. Percentages describe each image dimension: 25% × 25% is 6.25% of the NR pixels.
2. Configure existing runtime settings, or extend the exact compatible source build. Changing an INI key cannot replace a hard-coded multi-step cycle. Preserve focus/key-release handling, notifications and a cooldown for model recreation.
3. Leave F8/Page Up/Page Down unbound. Bind F6 only where the game adapter applies a real native quality setting. OptiScaler resolution-query overrides alone do not force engine render-target recreation.
4. Put the native SR control beside NR settings when a supported adapter can receive a request. Display unsupported status otherwise. Do not install Cyberpunk's CET adapter into other games.
5. Snapshot files and external settings immediately before mutation, preserve known-good baselines, and install with the game/launcher/helpers stopped. Record new hashes and the first rollback step.
6. Save NR selections through OptiScaler **Save Settings** into the selected personal settings slot. Keep model hints separate from slot numbers. Validate independent slots and restart persistence; do not claim ordinary upstream Save Settings already supplies this behavior. Native settings remain under game ownership. ReShade preset saving does not save another add-on's state.
7. Report compilation, helper evaluation, input testing and gameplay evidence separately. Runtime validation checks actual dimensions, recreation, UI/motion, FG interaction and persistence.

Cyberpunk now has a [personal-settings-slot revision](../examples/optiscaler-dlssnr/personal-slots/README.md) over the earlier [F7 patches](../examples/optiscaler-dlssnr/f7-two-scale/README.md). The other games retain their preceding installed controls until a requested migration. Each game retains its own consumer; no DLL is universal.
