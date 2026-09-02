# Components and Compatibility

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

Important rules:

- Install beside the real rendering executable.
- Let the setup script choose a proxy name; `dxgi.dll` is common for DX12 but not universal.
- Start with the default INI and change only one setting at a time.
- Keep native frame generation and OptiScaler frame generation from controlling the same swapchain simultaneously.
- Read the current compatibility entry in the OptiScaler wiki before changing per-game hotfixes.

## ReShade

ReShade provides the graphics-API hook, effect runtime, depth access, and add-on API used by RenoDX and DLSS5-Feeder. Add-ons require the full add-on build.

The bitness must match the process. A 32-bit game needs 32-bit ReShade even on 64-bit Windows.

## RenoDX

RenoDX is a framework for shader replacement, HDR work, resource upgrades, overlays, and other game-specific graphics changes. Its generic DLSS5 add-on hooks NGX calls; it does not by itself invent the DLSS inputs for a game that has no DLSS.

That distinction explains why DLSS5-Feeder exists.

## DLSS5-Feeder

Feeder builds a DLAA-like NGX contract from a ReShade color frame, depth, and estimated motion vectors. RenoDX can hook that evaluate and insert the neural pass.

Use Feeder only when the game does not already provide a suitable DLSS path, or when the upstream project explicitly documents the scenario. The current upstream warning says it is not compatible with NVIDIA Smooth Motion or OptiScaler. Its current main documentation lists D3D11/D3D12 and wrapped D3D9 paths, not Vulkan. The locally preserved DOOM Vulkan build/path is therefore historical experimental evidence, not a generic supported install recipe.

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
