# Bayonetta

Status: **working**.

Supporting records:

- [History](bayonetta/HISTORY.md)
- [Preferences](bayonetta/PREFERENCES.md)
- [Mod catalog](bayonetta/MOD-CATALOG.md)
- [Curated recommendations](bayonetta/RECOMMENDATIONS.md)

Bayonetta is a 32-bit Direct3D 9 game. NVIDIA NGX and the RenoDX DLSS5 add-on are 64-bit, so they cannot run directly inside the game. The successful design translated D3D9 to D3D11 and moved NGX work to a separate 64-bit helper.

## Tested environment

- Windows 11
- NVIDIA GeForce RTX 5070 Ti, driver 616.56
- 3840×2160 output
- ReShade 6.8.0 x86 in the game and x64 in the helper
- dgVoodoo2 D3D9-to-D3D11 translation
- 32-bit DLSS5-Feeder plus 64-bit helper
- RenoDX DLSS5 add-on in the helper
- LumeniteFX Kernel motion-vector provider

## Working directory layout

Obtain every binary from the projects listed in [Sources](../docs/SOURCES.md).

```text
Bayonetta\
├─ Bayonetta.exe
├─ d3d9.dll                   # dgVoodoo2 x86 D3D9 wrapper
├─ dgVoodoo.conf
├─ dxgi.dll                   # ReShade x86 full add-on build
├─ dlss5-feed.addon32
├─ dlss5-feed.cfg
├─ ReShade.ini
├─ ReShadePreset.ini
├─ reshade-shaders\
│  ├─ Shaders\
│  │  ├─ DLSS5_Feed.fx
│  │  └─ LumeniteFX files
│  └─ Textures\
└─ host64\
   ├─ dlss5-feed-host64.exe
   ├─ dxgi.dll                # ReShade x64 full add-on build
   ├─ renodx-dlss5.addon64
   ├─ nvngx_dlssnr.dll
   ├─ nvngx_dlss.dll
   └─ ReShade.ini
```

Do not put the 64-bit RenoDX add-on in the 32-bit game process.

## Installation workflow

1. Back up the Bayonetta folder and its `system_data` settings/save file.
2. Install dgVoodoo2's x86 `d3d9.dll` beside `Bayonetta.exe`.
3. Set adequate virtual VRAM in `dgVoodoo.conf`. The tested profile used 4096 MB and 3840×2160 output. Start lower if the game or display cannot sustain that mode.
4. Leave the dgVoodoo watermark on for the first launch. It proves the translation layer loaded; disable it after verification.
5. Install the 32-bit ReShade full add-on build for the translated D3D10/11/12 path. The resulting `dxgi.dll` is x86.
6. Install the 32-bit Feeder add-on and shader in the game folder.
7. Create `host64` and add the 64-bit helper, x64 ReShade, RenoDX DLSS5 add-on, and trusted NGX runtimes.
8. Install LumeniteFX and set `DLSS5_MV_PROVIDER=3` in the game ReShade preprocessor definitions.
9. Enable `Lumenite_Kernel` before `DLSS5_Feed` in the preset.
10. Start with 100% work resolution and automatic HDR/depth detection using [the example files](../examples/bayonetta/).

## Positive evidence

The successful run reported:

- x86 ReShade loaded into `Bayonetta.exe` and created a D3D11 device through dgVoodoo2;
- both required effects compiled;
- Lumenite Kernel, motion vectors, and depth were found;
- the 64-bit host connected to the 32-bit game;
- NGX initialized successfully;
- a 3840×2160 DLAA feature became ready;
- frames 1, 2, 3, 1800, and 3600 were delivered and evaluated;
- RenoDX created feature 18 and repeatedly reported successful inline neural evaluations;
- the game and helper shut down cleanly.

See [the sanitized evidence](../evidence/BAYONETTA.txt).

## Settings that mattered

- `DLSS5_MV_PROVIDER=3`
- effect order: Lumenite Kernel, then DLSS5 Feed
- `EnableHooks=2` in the helper's RenoDX settings (NGX hooks only)
- 100% work resolution
- no MSAA/SSAA
- correct x86/x64 separation

## What failed and why

### Native D3D9 without translation

Modern ReShade effects and the D3D11/shared-texture feeder path were unavailable. dgVoodoo2 created the D3D11 device the chain needed.

### Missing motion-vector shaders

The feeder log initially reported its technique, motion vectors, and depth as missing. After shader compilation and the correct effect order, all three appeared. If they stay missing, neural output cannot be temporally valid.

### 67% work-resolution experiment

The reduced-work-resolution test produced black captures and was not accepted as working. The proven run used 100%. Feeder's current upstream documentation also describes its path as DLAA/full-resolution rather than a performance upscaler.

### Impossible FPS values

One capture showed `9999 FPS`. That was an overlay/present measurement error, not a performance result. The logs, not that counter, prove operation.

## Rollback

Use Feeder/FeedKit's own uninstall manifest when available. Otherwise remove only the exact files added by the layout above, restore any `.bak` files, and restore the original `system_data`. Keep an untouched copy before experimenting because Bayonetta may restore settings from more than one Documents/Steam Cloud location.
