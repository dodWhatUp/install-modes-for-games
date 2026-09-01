# Generic Unreal Engine 4/5 Guide

Status: **decision guide**. Per-game compatibility must still be tested.

Most modern Unreal PC games are 64-bit D3D12 and place the real executable below `Binaries\Win64`, but launchers and unusual packaging are common. Do not choose an injection path from the engine name alone.

## Find the real executable

Common locations:

```text
<Game>\<Project>\Binaries\Win64\<Project>-Win64-Shipping.exe
<Game>\<Project>\Binaries\Win64\<Game>.exe
```

Use Task Manager or a process-inspection tool while the game renders a 3D scene. The small executable in the game root may only start the shipping executable.

## Determine native feature support

Inspect the graphics menu and game files for:

- `nvngx_dlss.dll`: DLSS Super Resolution/DLAA
- `nvngx_dlssd.dll`: DLSS Ray Reconstruction
- `nvngx_dlssg.dll` and `sl.dlss_g.dll`: DLSS Frame Generation through Streamline
- AMD FSR2/3 or Intel XeSS plugins

Files alone do not guarantee that the current build enables a feature, but they identify likely integration paths.

## Path A: the game has DLSS/FSR2/XeSS

Use OptiScaler first.

1. Back up the shipping-executable directory and `%LOCALAPPDATA%\<Game>\Saved\Config`.
2. Extract OptiScaler beside the shipping executable.
3. Run the setup script and follow the current game-specific wiki entry.
4. Start with upscaler replacement only; keep OptiScaler frame generation disabled.
5. Verify the log detects the correct game, engine, API, native inputs, and GPU.
6. Enable native game frame generation separately if supported.
7. Only then test OptiScaler FG, model overrides, or neural rendering one at a time.

Do not copy Hogwarts-specific preset numbers or hotfixes to another Unreal title. Engine version, Streamline version, UI composition, swapchain behavior, and anti-tamper are all game-specific.

## Path B: the game has no DLSS contract

OptiScaler cannot invent all required temporal inputs in every game. For an offline game where ReShade depth works, use the current DLSS5-Feeder method:

1. Install ReShade's full add-on build beside the shipping executable.
2. Confirm ReShade attaches to D3D11 or D3D12 and selects the scene depth buffer.
3. Install Feeder, its effect, a supported motion-vector provider, RenoDX DLSS5, and trusted NGX runtimes according to upstream.
4. Enable the motion-vector technique before the Feeder technique.
5. Keep MSAA/SSAA off and start at 100% work resolution.
6. Require Feeder `feature ready`/`frame delivered` messages and RenoDX feature-18 evaluation messages.

Do not run Feeder with OptiScaler or NVIDIA Smooth Motion.

## UE5-specific considerations

- Lumen, Nanite, virtual shadow maps, and temporal super resolution make shader compilation and first-run stutter normal; do not confuse that with injector failure.
- Hardware ray tracing and Ray Reconstruction need different resources from Super Resolution. Replacing `nvngx_dlssd.dll` with an NR model is incorrect.
- Frame generation needs stable Reflex markers, UI composition, and swapchain handling. A game can support DLSS SR while remaining unsuitable for injected FG.
- Engine updates can replace plugin DLLs and invalidate old offsets or patches. Re-test after every game update.
- Mod managers may edit the same `Engine.ini` and `GameUserSettings.ini` files. Preserve comments and merge settings instead of overwriting complete files.

## Minimum verification checklist

- Correct shipping executable and API in the log
- Correct x64 build loaded
- Only one proxy DLL owns each hook name
- Native temporal inputs recognized, or Feeder resources recognized
- Feature created and evaluated repeatedly
- UI readable and motion stable
- Alt-tab, resolution change, menu transition, and shutdown tested
- Clean rollback verified

Copy [the game guide template](../templates/GAME-GUIDE.md) when documenting a new title.
