# Choosing DLSS, Frame Generation, Neural Rendering, and HDR Paths

## Start with the feature contract

A newer DLL is a newer model, not a new game integration. The game or bridge still has to provide the required buffers, constants, timing, and presentation path.

| Desired result | Required foundation | Preferred order |
|---|---|---|
| Newer DLSS SR/DLAA model | Existing temporal upscaler integration with color, depth, motion vectors, jitter, exposure | In-game/NVIDIA override → supported DLL update → OptiScaler |
| FG/MFG | Existing FG integration or a supported frame-generation injector, plus depth, dense motion vectors, UI separation, pacing/Reflex and swapchain control | Native game/NVIDIA override → proven game-specific injector → driver Smooth Motion fallback |
| Ray Reconstruction | Ray-traced noisy inputs, depth, motion vectors, exposure and ray/reflection-specific data | Native game support → documented game-specific bridge; do not fake it by renaming DLLs |
| DLSS neural rendering | A compatible NGX evaluation and its neural model contract | Native/game-supported path → OptiScaler/bridge when real temporal inputs exist → Feeder experiment when the game has no contract |
| HDR upgrade/fix | Correct swapchain/resource formats and game-specific shader/tonemap knowledge | Native HDR fix or game-specific RenoDX/Luma profile → generic upgrade only when documented |

## Selection rules

1. Use native support and official overrides first. They retain the richest engine inputs and are easiest to roll back.
2. OptiScaler is a strong candidate when a D3D11/D3D12 game already exposes DLSS, FSR2+, or XeSS temporal inputs. It cannot reliably invent missing engine data.
3. A bridge is appropriate only for the API and game contract it documents. A DXGI proxy does not control a Vulkan renderer.
4. DLSS5-Feeder is for games without a usable DLSS call path and uses ReShade color/depth plus a motion-vector provider. Follow its current supported-API list; experimental forks or local Vulkan work must be documented separately.
5. RenoDX can replace shaders, upgrade resources/swapchains, expose HDR controls, and hook neural calls. Its generic add-on does not make every game profile-compatible.
6. Never run two FG owners, two neural consumers, Feeder plus OptiScaler, or Feeder plus NVIDIA Smooth Motion unless upstream documentation explicitly supports that exact combination.

## What receives “real” inputs?

Native DLSS components receive buffers tagged by the game/engine. NVIDIA's Streamline documentation requires dense motion vectors containing camera and moving-object motion; FG also benefits from HUD-less color/UI buffers. RR additionally consumes noisy ray-traced color and reflection-specific data.

A ReShade Feeder path is different. It sees the post-process frame, a ReShade-selected depth buffer, and the shared `texMotionVectors` texture written by the chosen provider. With optical-flow providers these vectors are **estimated from images**, not the game's native object motion. They can miss disoccluded or hidden surfaces, particles, transparency, and correct UI separation.

Enable exactly one compatible motion-vector provider technique **above** `DLSS5_Feed`. Enabling every Lumenite luminance or debug technique does not improve the contract and can add cost or alter the image. Use debug views only to validate depth/vector direction and then turn them off.

## Does an add-on disable the rest of DLSS?

Not automatically. A narrowly configured neural add-on can hook only its intended NGX feature while the game keeps native SR, RR, and FG. But all layers still share GPU memory, queues, swapchain recreation, color space, and hook order. The native features must therefore be verified after the add-on is installed; “separate feature” does not mean “zero interaction.”

For every combination, record ownership explicitly:

| Layer | Owner | Input source | Verified active? |
|---|---|---|---|
| SR/DLAA | | native/bridge/estimated | |
| RR | | native/bridge | |
| FG/MFG | | native/injector/driver | |
| Neural rendering | | native/OptiScaler/Feeder | |
| HDR/tonemap | | native/RenoDX/ReShade/driver | |
