# Skyrim Special Edition

Status: **Steam Skyrim 1.6.1170, SKSE64 2.2.6, Address Library v13 and PureDark AIO Build 19 Hotfix 1 are enabled after the user-authorized downgrade.** Agent-operated AHK v0.3.1 probes delivered mod-menu open/close, console-panel toggle, arrows and a one-digit/caret/Backspace test. Skyrim was then closed via the specifically approved Steam Stop path, not in-engine Quit. NVIDIA FG initialization previously failed `887A0004` and persisted None; input success does not fix it. MFG/FrameWarp, third-person visuals and performance remain **unverified and deferred**. Existing input profiles remain preserved. See [history](HISTORY.md) and [input workflow](../../docs/AGENT-GAME-INPUT.md).

**Graphics menu mapping:** ReShade uses Delete. PureDark uses F12 for its menu, numpad `*` for FG and numpad `+` for FrameWarp. F12 is physically confirmed and agent-confirmed only through the existing AHK F8 route; FG/FrameWarp bindings are statically verified only. Direct automated F12/Delete did not respond. No OptiScaler is installed; Home remains reserved for it. Keep Skyrim's Steam overlay Off to avoid the shared F12 screenshot path during further bounded tests.

**Helper boundary:** the [optional module](../../examples/game-input/README.md) is now v0.5-preview.1 with visible status, exact Skyrim/Cyberpunk targets and host-safe Start/Stop. Native syntax and 36 no-input tests pass; this refactor and its opt-in arbitrary text/Enter/Escape/hold extension have not passed live acceptance. The exact live-tested v0.3.1 baseline is preserved separately. No helper/game instance was started for packaging, and the larger AHK host has not been modified. Exit old helpers before any future authorized test.

## Observed environment

- Store: Steam; manually restored 1.6.1170 depot contents. The retained Steam manifest still reports the newer build 24914197 and is not the effective executable version.
- Relative executable: `SkyrimSE.exe`.
- Renderer: x64 / D3D11; runtime 1.6.1170.0.
- Hardware at 2026-10-10 validation: RTX 5070 Ti, 16 GB; driver 617.42 (previous test: 616.56).
- Profile: `02 - PureDark 1.6.1170`; launch through SKSE64 2.2.6 in MO2. Output 2560×1440, windowed borderless; DLSS Quality preset L, requested NVIDIA Dynamic MFG, FrameWarp First Person + Third Person; NR off. Latest effective FG is None after automatic startup fallback; inspect the backend on every launch.

## Decision and records

[Categorized comparisons](COMPARISONS.md) explain competing options, dependencies and content scope. [Catalog](MOD-CATALOG.md) is discovery; [recommendations](RECOMMENDATIONS.md) are the selected starting points. [History](HISTORY.md) records actual work and [preferences](PREFERENCES.md) preserve the user's intent.

## Installation and verification boundary

Use the runtime-matched foundation in the separate profile above. Preserve the existing ReShade 6.8 root hook. Do not let Steam verify/update the downgraded installation; a read-only manifest is not a guaranteed update lock. PureDark's earlier failure on 1.7.x remains historical, not the current runtime. Authentication is always user-operated; no credentials or license cache belong in this repository. Complete a temporary unsaved moving scene, third-person camera switching, independent FG/FrameWarp A/B tests, base-versus-displayed FPS and UI/pacing checks before calling the stack gameplay-verified. Initialization logs and menu counters are not sufficient proof. The current DLSS menu requires a restart for Quality changes; live SR control is unavailable in the observed UI.

## Rollback

The complete pre-downgrade 1.7.104 game directory and incompatible SKSE/Address Library mod folders were archived privately, not deleted. With Skyrim, MO2 and Steam closed, preserve the newer state, restore that root plus the matching old mod folders/profile/configuration and Steam metadata together. MO2 alone cannot reverse the game downgrade. See the exact snapshot identifiers in history.
