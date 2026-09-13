# F7 NR scale toggle and native SR controls

Local revision installed 2026-09-13. **F7 toggles only 25% and 100% of each NR working-image dimension.** It retains the saved starting scale; an intermediate slider value goes to 25% on the next tap. The existing full-menu scale slider remains available.

| Game | Consumer / build stamp | F7 | Separate live DLSS SR |
|---|---|---|---|
| Cyberpunk 2077 | wilsjo2 v0.7.7 / `e237f89+f7-25-100` | 25%/100% | F6 and a button beside NR settings in F12, through CET |
| A Plague Tale: Requiem | same v0.7.7 build | 25%/100% | No verified engine adapter; unavailable label in compact panel |
| Batman: Arkham Knight | Dagherbou v0.2.0 / `9737616+f7-25-100` | 25%/100% | Unavailable in its synthetic Feeder chain |

F6 avoids Cyberpunk's native F9 Quick Load. F8 retains actual pre/post-SR placement in v0.7.7; it remains unavailable in Batman. NR selections are saved through **Save Settings**. The hotkeys do not bundle preset/style/placement changes. 25% per dimension means 6.25% of the NR pixel count, not 25% of total game rendering work or a guaranteed FPS multiplier.

## Source prerequisites

- `v077-followup.patch` applies **after** [extended-controls-v077.patch](../extended-controls-v077.patch), on commit `e237f895623742b761f9e5f00067cb3dc62619f4`.
- `dagherbou-v020-followup.patch` applies **after** [f9-model-scale.patch](../dagherbou-v020-f9/f9-model-scale.patch), on commit `973761621353b99bee3dc7d4bb27b117fef2644f`.
- The patches include the locally generated `resource_build_commit.h` stamp; retain/generate the preceding stamp file before applying. Pinned dependencies and release build settings are unchanged. For extracted Windows sources, use `git apply --ignore-space-change <followup.patch>` to tolerate line-ending context. Both follow-up patches were applied to separate pre-change copies and compared with the final source after normalizing line endings.
- Config: `[DlssNr] ScaleCycleKey=0x76`; preserve the selected `WorkingScale`. Cyberpunk's [GraphicsHotkeys](../../cyberpunk-2077/GraphicsHotkeys/README.md) uses F6 (`117 << 48`).

The compact-panel bridge sends a short timestamped cycle request to the existing CET adapter. It validates and applies the native DLSS mode on the update event; status comes from native readback. The button is disabled when the heartbeat is absent, no game is loaded, or fixed DLSS is not selected. It does not implement an upscaler or a target-FPS controller.

## Verification

- Complete x64 builds passed with MSVC 14.44.35207 / Windows SDK 10.0.26100.0; all 946 exported names/ordinals match the preceding binaries.
- v0.7.7 SHA-256: `298D93C3D648330E279B614FC4B822FE38D87EC33516EFED90537664E9E9A090`.
- Dagherbou SHA-256: `F39E798B293A1F4BEBE10F0EED781C4B7AB4E6AFA6357030CF127314AA57517D`.
- Batman's exact DLL passed two separate 300/300-evaluation helper runs, with composition confirming 640×360 and 160×90 models for 100% and 25%. No error/critical lines. This does not test keyboard cycling.
- Cyberpunk Lua mocks passed cycle, cooldown, startup, overlay/player/upscaler/DRS guards, rejection/apply rollback and panel request/status tests, including stale/future/malformed requests.
- Both scale implementations passed 1,000 alternating transitions plus intermediate-value and NaN checks in a compiled test.
- Nine installed files verified; protected native files unchanged. Restore dry-runs passed before and after installation. No new in-game panel/keyboard test.

## Rollback

Private snapshot `f7-controls-20260913/before-f7-20260913-141908` contains `Restore-F7.ps1`. Close games, Steam and helpers; use `-Game Cyberpunk`, `-Game Requiem`, `-Game Batman`, or `-Game All`. It preserves the current files before restoring this revision. Use it **before** older profile/restore scripts, which expect previous hashes. Older staged payloads/manifests remain historical profiles.

Binaries, runtimes, raw logs and private snapshots are excluded from this repository.
