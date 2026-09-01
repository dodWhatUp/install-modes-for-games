# DOOM: The Dark Ages

Status: **working technical RenoDX/DLSS neural-rendering integration at 2560×1440**.

The final test proved that the Vulkan bridge created NVIDIA neural-rendering feature 18, evaluated it repeatedly, and delivered more than 16,200 frames without a timeout, device loss, or feature-creation crash. The last long run was mostly a static/menu scene, so gameplay motion-vector quality still needs a moving-scene visual check before treating this as fully tuned.

See [the sanitized evidence](../evidence/DOOM-THE-DARK-AGES.txt) and [the tested configuration examples](../examples/doom-the-dark-ages/).

## Validated environment

- Test date: 2026-09-02
- Windows 11
- NVIDIA GeForce RTX 5070 Ti, 16 GB VRAM
- NVIDIA driver 616.56
- DOOM renderer: 64-bit Vulkan
- Separate launcher process: `idTechLauncher.exe`
- Stock game modules preserved: Streamline `2.11.1.0`, DLSS SR/RR/FG `310.6.0.0`
- Stable bridge output: 2560×1440 at 144 Hz

The game already provides native DLSS Super Resolution, Ray Reconstruction, and Frame Generation. This experiment adds a community neural-rendering pass; it does not replace the whole stock Streamline directory.

## Final working stack

```text
DOOM Vulkan frame
  → ReShade 6.8 full add-on Vulkan layer
  → root process gate (launcher isolation)
  → Lumenite Kernel motion vectors + DLSS5_Feed shader
  → DLSS5-Feeder 0.8.0-beta.4 Vulkan/D3D12 transport
  → private NVIDIA DLAA session using signed 310.8 SR runtime
  → RenoDX DLSS5 v4.55 hook + signed 310.8 NR runtime
  → neural result returned to Vulkan
```

The known-good pins matter. The successful test used RenoDX DLSS5 v4.55 with Feeder 0.8.0-beta.4. Do not assume a newer RenoDX build is compatible with this older Feeder release.

## Why OptiScaler was removed

The earlier OptiScaler DLSSNR package said its Vulkan neural path was not wired at that time. Its log could not distinguish experimental neural work from DOOM's native Vulkan NGX traffic, so the result was inconclusive.

OptiScaler was backed up and completely removed before installing RenoDX/Feeder. This also follows Feeder's incompatibility warning: do not combine this path with OptiScaler or NVIDIA Smooth Motion.

## Required layout

Names are important. Download binaries from their official projects; this repository does not redistribute them.

```text
DOOMTheDarkAges\
├─ doom-addon-gate.addon64
├─ ReShade.ini
├─ ReShadePreset.ini
├─ reshade-shaders\
│  ├─ Shaders\
│  │  ├─ DLSS5_Feed.fx
│  │  └─ LumeniteFX shader files
│  └─ Textures\
│     └─ LumeniteFX texture files
└─ doom-addons\
   ├─ renodx-dlss5.addon64
   ├─ dlss5-feed.addon64
   ├─ dlss5-feed.cfg
   ├─ nvngx_dlss.dll
   └─ nvngx_dlssnr.dll
```

`ReShade.ini` uses `AddonPath=.\`, so ReShade discovers only the root gate. The gate skips the launcher and loads the two exact `.addon64` filenames from `doom-addons` only inside `DOOMTheDarkAges.exe`. Keeping `nvngx_dlss.dll`, `nvngx_dlssnr.dll`, and `dlss5-feed.cfg` beside those add-ons satisfies their module-relative lookup behavior.

The first failed gate renamed the companions to `.dll`. Process isolation worked, but Feeder then could not find the exact adjacent name `renodx-dlss5.addon64`. Preserving the upstream filenames fixed discovery.

## Important configuration

The tested files are in [examples/doom-the-dark-ages](../examples/doom-the-dark-ages/).

### ReShade and RenoDX

- Install the official ReShade **full add-on** build as a Vulkan layer.
- Use `AddonPath=.\` for the root process gate.
- Run Lumenite Kernel before `DLSS5_Feed`.
- Set `DLSS5_MV_PROVIDER=3` for Lumenite Kernel.
- Use reversed depth: `RESHADE_DEPTH_INPUT_IS_REVERSED=1`.
- Use `EnableHooks=2` so RenoDX hooks NGX only.
- Enable neural uplift with `NeuralUplift=1`.
- Keep RenoDX's separate upscaling off with `NREnableUpscaling=0`; DOOM retains its native DLSS path.
- The stable test used neural preset/style `0`.

### Feeder

- `mode=2`
- `create_delay=120`
- `warmup_rebuild=0`
- `work_resolution=100`
- `mv_scale_x=1.000` and `mv_scale_y=1.000`
- `gpu_timeout_ms=2000`

The 120-frame delay lets RenoDX re-arm its hooks after ReShade's normal runtime transition. The older 180-frame warm-up rebuild was disabled because v4.55 did not need it. Work-resolution scaling below 100% was not validated on this Vulkan path.

### Launcher and Vulkan layer

The launcher initially displayed a misleading GPU-driver popup because it rejected the ReShade Vulkan layer. The final setup set `rgl_validateLayers 0` in the launcher configuration while leaving ReShade enabled for the game.

If that popup returns after an update, choose **No**. Choosing Yes can disable ReShade and therefore disable RenoDX.

The Vulkan manifest used a unique disable-environment key. A crucial lesson is that the Vulkan loader checks whether a disable variable exists, not whether its value is `1`: setting the variable to `0` can still disable the layer. The variable must be absent from Steam's child environment. Back up the global ReShade manifest before changing it.

## Resolution and VRAM

The 4K path could create the feature and deliver frames, but it was not stable on the 16 GB RTX 5070 Ti. After DOOM reached its final startup scene, total VRAM use reached about 15.4/16.3 GB. A normal ReShade/Vulkan runtime recreation then attempted a second 4K feature allocation and raised access violation `0xC0000005`. Feeder caught the exception, so DOOM kept rendering, but the neural pass stopped.

Timing changes cannot fix insufficient memory headroom. The stable solution was exclusive 2560×1440.

Borderless mode was not a solution on this 4K desktop: DOOM ignored the requested 1440p dimensions and created a near-4K/4K backbuffer. Exclusive mode produced the intended 2560×1440 allocation.

On the tested monitor, DOOM's filtered display list mapped:

- `r_mode 186` → 3840×2160 at 144 Hz
- `r_mode 156` → 2560×1440 at 144 Hz

These indices are monitor-specific. Select 2560×1440 in DOOM's video menu instead of copying `r_mode 156` blindly. DOOM may rewrite its local configuration on exit, so verify the effective backbuffer in `dlss5-feed.log` after every display change.

DOOM's high VRAM display is not itself proof of a leak; much of it is the game's texture-streaming budget/cache. The practical test is whether feature creation, runtime recreation, and sustained frame delivery succeed.

## Safe installation sequence

1. Close DOOM, `idTechLauncher.exe`, and Steam before changing loaded graphics files or Steam launch options.
2. Back up the game root, stock `streamline\production`, launcher configuration, ReShade Vulkan manifest, Steam app configuration, and saved graphics settings.
3. Remove the prior OptiScaler experiment without touching stock Streamline files.
4. Launch stock DOOM once and verify it still works.
5. Install ReShade 6.8 full add-on support for Vulkan from the official installer.
6. Obtain the pinned RenoDX, Feeder, Lumenite, and signed NVIDIA 310.8 files from their official sources.
7. Create the exact directory layout above.
8. Compile the optional x64 process gate from [doom-addon-gate.cpp](../examples/doom-the-dark-ages/doom-addon-gate.cpp) with the matching ReShade add-on headers, or prefer an upstream process-filtering feature if one becomes available.
9. Apply the tested ReShade, preset, and Feeder configuration.
10. Set DOOM to exclusive 2560×1440 and launch through Steam.
11. Verify the launcher was skipped, the game loaded both companions, the 1440p feature became ready, and RenoDX evaluated feature 18.

Do not install every layer at once on an unknown system. Launch-test after ReShade, after the gate, and after the two companions so a failure has one likely cause.

## Proof of a working run

The successful test recorded all of the following:

- Gate log for `idTechLauncher.exe`: companions skipped.
- Gate log for `DOOMTheDarkAges.exe`: both exact-name companions loaded.
- Feeder: `building: 2560x1440`.
- Feeder: `feature ready: 2560x1440 DLAA`.
- Feeder: frames 1, 2, 3, 1,800, and later checkpoints through at least 16,200 delivered.
- RenoDX: signed DLSSNR 310.8 runtime initialized.
- RenoDX: feature 18 created for 2560×1440 input/output.
- RenoDX: inline feature-18 evaluations succeeded.
- No Feeder timeout, device loss, or final feature-creation exception in the stability run.
- No OptiScaler payload remained in the game directory.

Early RenoDX lines saying it failed to find `NVSDK_NGX_D3D12_EvaluateFeature_C` were startup probes before the private runtime loaded. They were not fatal because later lines proved signed runtime initialization, feature creation, and successful evaluations.

`ReShade.log` belongs to the launcher in this shared directory; the game process may write `ReShade.log1`. Read the process gate logs before attributing one log to DOOM.

### Remaining quality check

The final long run's center motion-vector probe reported almost zero motion while the scene was static. That does not invalidate feature creation or delivery, but it also does not prove good temporal quality during gameplay. Test a moving combat scene and require non-zero, correctly directed motion vectors without smearing before calling the visual tuning complete.

Controls in the tested build:

- `F6`: toggle RenoDX neural rendering.
- `Home`: open ReShade.

## What failed and what it taught us

1. **OptiScaler Vulkan NR was inconclusive.** A loaded DLL and NGX messages were not enough to prove the experimental pass.
2. **Renaming add-ons broke discovery.** The gate must keep `renodx-dlss5.addon64` and `dlss5-feed.addon64` under their exact names.
3. **`SuperSampling.Available=0` was not a GPU verdict.** In the failed layout, discovery/runtime selection was wrong. Exact names plus the trusted 310.8 runtime produced a working private DLAA contract.
4. **A Vulkan disable variable set to zero is still present.** Remove it completely.
5. **The launcher popup was not an NVIDIA driver failure.** It was the launcher's Vulkan-layer validation.
6. **Borderless 1440p did not reduce allocation.** The game matched the 4K desktop backbuffer.
7. **The first 4K session working did not prove stability.** Runtime recreation exposed the lack of VRAM headroom.
8. **A longer create delay did not solve 4K.** Scheduling cannot create memory capacity.
9. **Static-menu depth or motion probes are limited evidence.** Validate during actual movement.

## Rollback

1. Close DOOM, its launcher, and Steam.
2. Remove the ReShade Vulkan registration for DOOM using ReShade's official setup tool.
3. Restore the backed-up global ReShade manifest and launcher configuration.
4. Remove only the gate, `doom-addons`, ReShade configuration, and shader files added by this experiment.
5. Restore the stock `streamline\production` snapshot and saved graphics settings.
6. Restore the prior Steam launch options.
7. Verify game files and launch stock DOOM once.

The local test machine also has a path-specific rollback script in its private backup. It is not published because it contains machine-specific paths and backup state.

## Official requirement context

Bethesda lists 16 GB VRAM for native 4K Ultra. That leaves little safety margin for an extra Vulkan/D3D12 bridge and neural feature allocation on a 16 GB card: [DOOM: The Dark Ages PC system requirements](https://help.bethesda.net/app/answers/detail/a_id/68551/).
