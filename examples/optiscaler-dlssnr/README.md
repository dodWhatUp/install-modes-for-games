# OptiScaler DLSS Neural Rendering controls

**Superseded controls, 2026-09-13:** the current installed F7 25%/100% builds and follow-up source patches are documented in [F7 two-scale controls](f7-two-scale/README.md). Earlier cycle descriptions below are historical build evidence, not the current mapping.

The table below records the **earlier v0.7.7 implementation**. The user's later cross-tool default uses F9 **100/75/67/50%**; see [current preferences](../../preferences/GENERAL.md) and the [installation procedure](../../docs/GRAPHICS-CONTROLS.md). This preserved patch/binary still uses 100/75/50/25%. Do not describe its existing behavior as the new default or rewrite its evidence without rebuilding and validating it. The [Batman patch](dagherbou-v020-f9/README.md) implements the newer cycle for Dagherbou v0.2.0.

| Key | Action |
|---|---|
| Delete | Full OptiScaler menu |
| F12 | Small DLSS Neural Rendering-only window |
| F11 | Cycle numeric model preset hints 0–3 |
| F10 | Neural Rendering on/off |
| F9 | Cycle NR working scale 100% → 75% → 50% → 25% → 100% |
| F8 | Switch NR before/after SR (combined RR+SR when active) |
| F7 | Native DLSS quality, only with a game-specific adapter; see Cyberpunk below |
| Page Up | FPS overlay on/off |
| Page Down | Change the visible FPS overlay's information mode |

[Compact-controls.ini](Compact-controls.ini) is a merge-only configuration delta. It is not a global Windows configuration and must not replace a game's complete INI.

[extended-controls-v077.patch](extended-controls-v077.patch) contains the complete custom UI/input implementation against [OptiScaler-DLSSNR v0.7.7](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/releases/tag/v0.7.7), commit `e237f895623742b761f9e5f00067cb3dc62619f4`. Apply it to that exact source tree, with matching submodules, before building. It includes the earlier compact controls plus F8/F9; do not apply it on top of the old patch. An unmodified upstream DLL cannot gain these actions from the INI alone. Upstream source and its license remain authoritative. [compact-controls-v077.patch](compact-controls-v077.patch) is preserved as the earlier F10–F12 revision, not the current installed build.

The current local x64 build used MSVC 14.44.35207 and Windows SDK 10.0.26100.0, stamp `e237f89+f7f9` / `20260913_extended_controls`. Its proxy SHA-256 is `4400E00C58451AAC69554600AEFB178089C4D9D67C6BCF9C8BFEA8FE961557BE`. The generated build-stamp headers, binary, and build script remain in private staging. The earlier compact-only proxy hash was `D563566B3B8BCF7CC895C805A64CDEA4F351CE31480ACB2B5A9A58FD0300AB0B`.

The compact window includes NR enable, numeric model preset, Style, Intensity, Working scale, Before Super Resolution, Passes, Save Settings, and Close. Opening either menu closes the other. Intensity and Working scale apply only after releasing the slider, avoiding model recreation on every drag frame. F8–F11 show status notifications; use Save Settings to persist OptiScaler session changes. The numeric preset hints have undocumented visual semantics and are distinct from native DLSS SR quality modes.

F9 scales each dimension of the NR model's working image, relative to its pre- or post-SR input; it does not change output resolution or DLSS quality. At a 1920×1080 NR input, 50% requests 960×540, not half the pixel count. F8 changes ordinary placement around SR, or the combined RR+SR evaluation when RR is active. It refuses to change placement while Finished Picture or Deferred DLSS is enabled. F8/F9 share a one-second debounce and use the fork's existing feature-recreation path. Avoid rapid changes, especially with native FG; debounce is not proof of stability.

Cyberpunk's separate [GraphicsHotkeys adapter](../cyberpunk-2077/GraphicsHotkeys/README.md) supplies F7 through CET 1.37.1. It cycles the game's DLAA/Quality/Balanced/Performance setting; Auto starts at Quality. It does not bundle those modes into F11 numeric NR model hints.

Page Down cycles Just FPS, Simple, Detailed, Detailed + Graph, Full, Full + Graph, and Reflex timings. Available metrics depend on the active backend and timing support; an overlay alone does not prove neural rendering or frame generation delivery.

Use current general preferences for future profiles; this example documents one exact implementation. Preserve each existing game's fork, proxy ownership, and known-good state before porting controls. The Cyberpunk build is not a universal drop-in replacement for a different custom OptiScaler build.

Validation: full rebuild/link succeeded; all 946 exported names and ordinals matched the previous proxy (which matched upstream); the saved source patch passed reverse-apply checking; Cyberpunk's installed keys and file hashes were checked. The F7 Lua mock tests passed, including rejection/apply rollback. Interactive in-game verification remains pending because another game was open and was not interrupted.
