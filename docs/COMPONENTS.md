# Components and Compatibility

Apply the [minimum-dependency and real-input workflow](FEATURE-DECISION.md) before selecting products. An integration supplies inputs, a consumer processes them, and a visual profile changes presentation; one component may fill several roles. Reuse those capabilities and add only missing prerequisites. Count running helper programs separately from required DLLs, add-ons and presets.

## The feature layers

| Component | Job | Needs game-provided temporal inputs? | Typical injection |
|---|---|---|---|
| DLSS Super Resolution / DLAA | Reconstructs or antialiases the rendered frame | Yes | Native game integration or an upscaler bridge |
| DLSS Frame Generation / MFG | Generates additional presentation frames | Yes, plus correct UI and pacing data | Native Streamline, NVIDIA override, or a supported OptiScaler path |
| DLSS Ray Reconstruction | Replaces denoisers for ray-traced effects | Yes, including ray data | Native game support or a carefully tested bridge |
| DLSS neural rendering (“DLSS 5”) | Applies NVIDIA's neural-rendering model | Depth, motion vectors, color, and an NGX contract | Native integration, OptiScaler interception, or RenoDX hooked through Feeder |

Do not rename `nvngx_dlssnr.dll` to `nvngx_dlssd.dll`. Neural Rendering and Ray Reconstruction are different features; a large NR model DLL misnamed as RR breaks the RR path.

## OptiScaler

OptiScaler intercepts temporal-upscaler inputs from games that already implement DLSS2+, FSR2+, or XeSS. It can replace the selected upscaler and, in supported DX12 cases, manage frame-generation paths.

Best fit: modern D3D11/D3D12 Unreal games with native temporal-upscaler support.

OptiScaler is not the default requirement for every installation. Prefer native settings when sufficient; compare exact forks with other compatible consumers when extending features. Its [current upstream documentation](https://github.com/optiscaler/OptiScaler) distinguishes APIs and incomplete input integrations, including some Unreal XeSS paths without depth. Do not transfer mainline capabilities to an older/custom neural fork without checking it.

Important rules:

- Install beside the real rendering executable.
- Let the setup script choose a proxy name; `dxgi.dll` is common for DX12 but not universal.
- Start with the default INI and change only one setting at a time.
- Keep native frame generation and OptiScaler frame generation from controlling the same swapchain simultaneously.
- Read the current compatibility entry in the OptiScaler wiki before changing per-game hotfixes.

## ReShade

ReShade provides the graphics-API hook, effect runtime, depth access, and add-on API used by RenoDX and DLSS5-Feeder. Add-ons require the full add-on build.

The bitness must match the process. A 32-bit game needs 32-bit ReShade even on 64-bit Windows.

ReShade can host an adapter that captures engine buffers or an effect that estimates motion. The host name does not establish input provenance. Reuse one compatible host for required add-ons and the requested visual profile. [Documented shared-host arrangements](https://github.com/optiscaler/OptiScaler/wiki/Luma-Unreal-Engine-Luma-UE) can avoid an additional loader, but must match the actual game and build.

## RenoDX

RenoDX is a framework for shader replacement, HDR work, resource upgrades, overlays, and other game-specific graphics changes. Its generic DLSS5 add-on hooks NGX calls; it does not by itself invent the DLSS inputs for a game that has no DLSS.

That distinction explains why DLSS5-Feeder exists.

For the user's separate visual stage, check the [RenoDX game list](https://github.com/clshortfuse/renodx/wiki/Mods) and exact profile requirements. A RenoDX HDR/color mod is distinct from a RenoDX-derived neural consumer. Investigate sharing ReShade with the selected DLSS implementation, resolving shader, tonemap, resource-format and swapchain overlap. A preset alone does not create engine motion vectors or a DLSS integration. See [combined validation](FEATURE-DECISION.md#reshade-and-renodx-alongside-dlss).

## Game-specific input integrations

Before synthesizing missing inputs, look for a supported game/engine mod that exposes them. [Luma](https://github.com/Filoppi/Luma-Framework) uses ReShade and includes DLSS integrations for particular games. Other adapters, including RenoDX-based implementations, require the same per-game evidence. Establish the integration alone, then add a separate consumer only for missing features. Do not assume that a DLAA integration also supplies lower-resolution SR, RR, FG/MFG or neural rendering.

## DLSS5-Feeder

Feeder builds a DLAA-like NGX contract from a ReShade color frame, depth, and estimated motion vectors. RenoDX can hook that evaluate and insert the neural pass.

Use Feeder only when the game does not already provide a suitable DLSS path, or when upstream explicitly documents the scenario. **Refreshed 2026-09-13:** [current upstream](https://github.com/jlrouzies-fr/DLSS5-Feeder#alternative-optiscaler-dlss-nr) supports Dagherbou's OptiScaler DLSS-NR as the sole neural consumer, with ReShade as `dxgi.dll` and OptiScaler as an imported `winmm.dll`/`version.dll`. Ordinary OptiScaler remains incompatible. The exact v0.2.0 + Feeder 1.16.0-beta.1 chain passed an isolated local helper test; Arkham Knight gameplay remains unverified.

Current upstream also documents Vulkan support and permits Smooth Motion on D3D11/D3D12 after specific fixes; Vulkan plus Smooth Motion remains incompatible. These newer statements do not validate or migrate the older pinned DOOM/Bayonetta experiments. Keep their historical failures and version requirements intact. ShortFuse's newer standalone `renodx-dlss` is distinct from Krish's `renodx-dlss5`: the former replaces Feeder and must not be layered over it.

## Motion vectors and depth

Temporal neural processing needs correct motion vectors and depth. In these tests, LumeniteFX Kernel exposed motion vectors through the community `texMotionVectors` convention, selected with:

```ini
PreprocessorDefinitions=DLSS5_MV_PROVIDER=3
```

The effect order matters:

```text
motion-vector provider → DLSS5_Feed → later post-processing → present
```

Wrong sign, scale, reversed depth, or a HUD mixed into scene inputs causes smearing, halos, flicker, or black output even when feature creation succeeds.

Enable one provider technique, not every effect distributed with that provider. Unless a game-specific adapter captures engine buffers, these shared motion vectors are estimated and are not equivalent to dense engine motion vectors for camera plus dynamic objects.

## dgVoodoo2

dgVoodoo2 translated Bayonetta's 32-bit D3D9 output to D3D11. That made a modern ReShade effect chain possible. It is a translation layer, not DLSS. The verified chain was:

```text
Bayonetta D3D9
  → dgVoodoo2 D3D11
  → 32-bit ReShade + Feeder
  → shared textures/fence
  → 64-bit helper with ReShade + RenoDX + NGX
  → processed frame returned to the game
```

## NVIDIA App overrides

For games that already support native DLSS, use NVIDIA App per-game overrides before experimenting with undocumented profile flags. Official overrides expose newer Super Resolution models and supported MFG modes without manually replacing game DLLs.

Do not apply both an NVIDIA App MFG override and an independent injector-driven MFG override unless the injector explicitly requires that setup.
