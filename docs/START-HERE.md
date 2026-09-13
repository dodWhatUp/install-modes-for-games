# Start Here: Choose the Correct Injection Path

There is no universal “copy these DLLs into every game” install. First identify four facts:

1. Which executable actually renders the game?
2. Is it 32-bit or 64-bit?
3. Does it use D3D9, D3D11, D3D12, OpenGL, or Vulkan?
4. Does it already expose DLSS, FSR2+, or XeSS inputs?

Then check whether a supported game-specific integration can expose any missing engine inputs. Follow [Feature Decision](FEATURE-DECISION.md): minimum working baseline first, compatible feature extensions next, then a separate ReShade/RenoDX visual stage. OptiScaler is a candidate rather than a universal requirement.

## Decision table

| Game type | Recommended first path | Avoid |
|---|---|---|
| Game already supports the desired feature | In-game setting or supported official per-game override | Adding an interceptor without a missing capability to supply |
| D3D11/D3D12 game with usable temporal inputs but missing desired output | One compatible bridge/interceptor plus required runtimes | Assuming an upscaler name proves complete inputs; adding Feeder to duplicate them |
| Game without usable native temporal inputs | Research a supported game/engine integration such as a game-specific Luma or equivalent adapter; add only its required host/consumer | Jumping directly to optical-flow Feeder because the game has no DLSS menu |
| No practical real-input integration found | Explicit synthetic/hybrid experiment using the minimum currently documented provider/consumer chain | Calling estimated vectors engine-native; assuming compatibility across forks |
| 32-bit game needing a 64-bit consumer | Documented matching 32-bit host and required 64-bit helper, only when necessary | Loading 64-bit add-ons in a 32-bit process; removing an essential helper to reduce program count |
| D3D9 game | Check game-specific support, then a documented translation path if required; match process bitness | Assuming all D3D9 games are 32-bit or translation creates temporal inputs |
| Vulkan game | Native/game-specific path first; verify the exact bridge/add-on API support and loading method | Inferring Vulkan support from a proxy filename or applying another version's compatibility result |
| Unreal Engine game | Install beside `ProjectName-Win64-Shipping.exe` or the actual executable under `Binaries\Win64` | Installing only beside the small launcher executable in the game root |
| Game has a compatible RenoDX visual profile | Add it as a separate stage, reusing one supported ReShade host; validate alongside DLSS | Duplicate hosts/consumers, overlapping shader replacements or double tonemapping |

## Identify the real executable

For Unreal Engine games, the common location is:

```text
<Game>\<Project>\Binaries\Win64\<Project>-Win64-Shipping.exe
```

Hogwarts Legacy is unusual in that the observed running executable was `Phoenix\Binaries\Win64\HogwartsLegacy.exe`. OptiScaler worked only when its proxy and support folder were beside that executable.

For games with a launcher, inspect logs carefully. An overlay loading into the launcher proves only that the launcher was injected. DOOM: The Dark Ages needed process isolation because the system-wide Vulkan ReShade layer saw both `idTechLauncher.exe` and `DOOMTheDarkAges.exe`.

## Build the stack gradually

Before building it, search the game's history and present the user with numbered alternatives using [the option template](../templates/OPTION-MENU.md). Include stock/no-change when the experimental path has meaningful risk.

Use dependency order and verify each changed stage; omit components already provided by the baseline:

1. Stock game and stock settings.
2. Translation layer, only if required (for example, dgVoodoo2 for D3D9).
3. Required host and engine-input adapter, if native inputs are insufficient.
4. Minimum DLSS path and its necessary runtimes.
5. Useful compatible extensions: reuse existing capabilities, then add only missing dependencies.
6. ReShade and the supported game-specific RenoDX visual profile, sharing a compatible host/load chain.
7. Combined-stack checks, tuning and optional overlays.

If step 4 fails, remove it before trying a different step 4. Keeping abandoned proxy DLLs is the most common cause of confusing startup crashes.

## What counts as success

- OptiScaler: the log names the correct game, proxy mode, selected upscaler, and successful feature creation/evaluation.
- ReShade: the log names the correct executable and API, registers the intended add-on, and compiles the required effects.
- DLSS5-Feeder: the log reports `feature ready` and increasing `frame N delivered` values.
- RenoDX DLSS5: its ReShade log reports feature 18 creation and successful inline evaluations.
- D3D9 translation: the temporary dgVoodoo watermark appears, then the game continues correctly after the watermark is disabled.

An FPS counter, overlay, DLL load, or changed color alone does not prove that the intended neural feature is active.

After the run, update both the game-specific history and any reusable general lesson. See the [Operating Standard](OPERATING-STANDARD.md).
