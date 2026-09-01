# Start Here: Choose the Correct Injection Path

There is no universal “copy these DLLs into every game” install. First identify four facts:

1. Which executable actually renders the game?
2. Is it 32-bit or 64-bit?
3. Does it use D3D9, D3D11, D3D12, OpenGL, or Vulkan?
4. Does it already expose DLSS, FSR2+, or XeSS inputs?

## Decision table

| Game type | Recommended first path | Avoid |
|---|---|---|
| D3D11/D3D12 game with native DLSS/FSR2/XeSS | OptiScaler, installed beside the real game executable | Adding DLSS5-Feeder just to duplicate inputs the game already provides |
| D3D11/D3D12 game without native DLSS | ReShade full add-on build + motion-vector provider + DLSS5-Feeder + RenoDX DLSS5 | Running OptiScaler, Feeder, and Smooth Motion together |
| 32-bit D3D11 game | 32-bit ReShade/Feeder in the game + 64-bit Feeder host containing RenoDX/NGX | Putting 64-bit add-ons directly into the 32-bit process |
| D3D9 game | dgVoodoo2 to D3D11, then the 32-bit path above | Expecting modern ReShade effects or NGX to run directly on D3D9 |
| Vulkan game | ReShade Vulkan layer + Feeder Vulkan transport, treated as experimental | Assuming a DXGI proxy such as `dxgi.dll` controls Vulkan |
| Unreal Engine game | Install beside `ProjectName-Win64-Shipping.exe` or the actual executable under `Binaries\Win64` | Installing only beside the small launcher executable in the game root |

## Identify the real executable

For Unreal Engine games, the common location is:

```text
<Game>\<Project>\Binaries\Win64\<Project>-Win64-Shipping.exe
```

Hogwarts Legacy is unusual in that the observed running executable was `Phoenix\Binaries\Win64\HogwartsLegacy.exe`. OptiScaler worked only when its proxy and support folder were beside that executable.

For games with a launcher, inspect logs carefully. An overlay loading into the launcher proves only that the launcher was injected. DOOM: The Dark Ages needed process isolation because the system-wide Vulkan ReShade layer saw both `idTechLauncher.exe` and `DOOMTheDarkAges.exe`.

## Build the stack gradually

Use this order and launch after each step:

1. Stock game and stock settings.
2. Translation layer, only if required (for example, dgVoodoo2 for D3D9).
3. One injection framework: OptiScaler or ReShade.
4. Add-on or upscaler replacement.
5. Motion-vector/depth provider.
6. Frame generation or neural rendering.
7. Optional tuning, presets, overlays, and dynamic resolution.

If step 4 fails, remove it before trying a different step 4. Keeping abandoned proxy DLLs is the most common cause of confusing startup crashes.

## What counts as success

- OptiScaler: the log names the correct game, proxy mode, selected upscaler, and successful feature creation/evaluation.
- ReShade: the log names the correct executable and API, registers the intended add-on, and compiles the required effects.
- DLSS5-Feeder: the log reports `feature ready` and increasing `frame N delivered` values.
- RenoDX DLSS5: its ReShade log reports feature 18 creation and successful inline evaluations.
- D3D9 translation: the temporary dgVoodoo watermark appears, then the game continues correctly after the watermark is disabled.

An FPS counter, overlay, DLL load, or changed color alone does not prove that the intended neural feature is active.
