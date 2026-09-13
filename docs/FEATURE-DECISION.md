# Choosing DLSS, Frame Generation, Neural Rendering, and HDR Paths

## Start with the feature contract

A newer DLL is a newer model, not a new game integration. The game or bridge still has to provide the required buffers, constants, timing, and presentation path.

**User default, 2026-09-14:** maximize useful compatible features using real game inputs, with the fewest necessary components. OptiScaler is not mandatory. Include ReShade and a compatible game-specific RenoDX visual profile as a separately tested stage of future requested graphics installations. This policy update does not change installed games or establish new runtime compatibility.

General upstream references reviewed 2026-09-14. Local results retain the dates and verification limits in each game's history.

| Desired result | Required foundation | Preferred order |
|---|---|---|
| Newer DLSS SR/DLAA model | Temporal integration with color, depth, motion vectors, jitter, exposure handling | In-game/NVIDIA override → supported runtime update → supported game integration or bridge as needed |
| FG/MFG | Existing FG integration or a supported frame-generation injector, plus depth, dense motion vectors, UI separation, pacing/Reflex and swapchain control | Native game/NVIDIA override → proven game-specific injector → driver Smooth Motion fallback |
| Ray Reconstruction | Ray-traced noisy inputs, depth, motion vectors, exposure and ray/reflection-specific data | Native game support → documented game-specific bridge; do not fake it by renaming DLLs |
| DLSS neural rendering | A compatible NGX evaluation and its neural model contract | Native/game-supported path → OptiScaler/bridge when real temporal inputs exist → Feeder experiment when the game has no contract |
| HDR upgrade/fix | Correct swapchain/resource formats and game-specific shader/tonemap knowledge | Native HDR fix or game-specific RenoDX/Luma profile → generic upgrade only when documented |

## Selection rules

1. Start with native support and official overrides where they provide the desired feature. Preserve working native SR/RR/FG when adding only a missing feature.
2. Identify the exact interceptor/enabler, fork, version, API and mode. [OptiScaler](https://github.com/optiscaler/OptiScaler) maps existing temporal-upscaler calls to selected backends. Its documentation notes that some Unreal XeSS inputs omit depth; an upscaler name alone does not prove a complete input contract.
3. If no accessible temporal contract exists, search for a supported game mod that captures engine buffers or implements the missing integration before choosing a feeder. [Luma](https://github.com/Filoppi/Luma-Framework) is one ReShade-based framework with game-specific DLSS support. Check equivalent RenoDX-based and other engine adapters; capabilities differ by game.
4. Use a bridge only for its documented API, resource format and consumer. A proxy filename or D3D12 code does not establish renderer support. Do not add another bridge when the chosen consumer already provides the required interoperability path.
5. Use estimated/synthetic inputs only after recording why no practical engine-input path is available. Verify a feeder's API, motion provider, consumer and versions together. Follow the dated exceptions in [Components](COMPONENTS.md); one fork's compatibility does not establish another's.
6. Keep one owner per SR/RR/FG/neural feature and proxy. A host loading another component is different from duplicate feature ownership. Never combine competing consumers, Feeder/OptiScaler or Feeder/Smooth Motion unless current upstream documentation supports that exact arrangement.

## Establish the minimum, then extend it

The minimum depends on what the game already supplies. Count additions to the working baseline, not DLL files in an archive.

| Starting point | Minimum candidate | Add only if needed |
|---|---|---|
| Desired feature already available natively | Game setting or supported per-game driver override; potentially no extra mod | Compatible model/runtime update or a missing feature extension |
| Usable temporal inputs, desired DLSS output missing | One compatible interceptor/bridge and required runtimes | A game-specific input fix, loader or adapter |
| No DLSS calls, but a supported mod exposes engine inputs | That integration plus its required host/runtime; e.g. ReShade + the game's Luma add-on | One consumer/interceptor for capabilities the integration lacks |
| Real-input baseline works, another feature is missing | Enable the existing owner's supported extension first | Only that feature's missing component and dependencies |
| No practical engine-input route found | A clearly identified synthetic/hybrid experiment | Required API/bitness helper; do not call it engine-native |
| Add ReShade/RenoDX visuals | Reuse a compatible host; add the exact game profile and required effects/settings | Host or loader only if absent and required |

Write a short dependency chain: **game/input source → required host/adapter → consumer → visual stage → presentation**. Mark existing components, each addition's purpose, and any new helper process. Retain essential runtimes, architecture helpers and supported package dependencies. Disable abandoned hooks through a reversible manifest instead of guessing which DLLs are unnecessary.

After the minimum baseline passes, check newer SR/DLAA models, actual SR quality modes, RR, FG/MFG, neural rendering and supported live/dynamic SR. Reuse existing capabilities, then add only the next missing prerequisite. Do not stop at a loaded interceptor or the first successful feature. Keep unsupported features off and record the exact missing input/format/API/hardware requirement, any supported remedy, and its cost.

| Feature | Already supplied by | Missing prerequisite | Smallest addition/setting | Conflict/overhead | Evidence and decision |
|---|---|---|---|---|---|
| SR/DLAA/models | | | | | |
| RR | | | | | |
| FG/MFG | | | | | |
| Neural rendering | | | | | |
| Live/dynamic SR | | | | | |
| ReShade + RenoDX visuals | | | | | |

Prefer the smaller stack when input quality, features and stability are comparable. Accept an essential extra component for real inputs or a useful feature. Count new processes separately from in-process loaders/add-ons and model/runtime files. Preserve performance/VRAM headroom and the user's [controls](GRAPHICS-CONTROLS.md). An NR working-size control is not engine SR.

## ReShade and RenoDX alongside DLSS

[RenoDX](https://github.com/clshortfuse/renodx) uses ReShade's add-on system for shader/resource/swapchain work. A game-specific HDR/color mod, a ReShade preset and a RenoDX-derived neural consumer have different roles. Check the [game list](https://github.com/clshortfuse/renodx/wiki/Mods), exact build and required settings; a listing does not prove interoperability.

1. Plan visuals independently and add them after validating the DLSS/input baseline. Prefer a maintained game profile, its required effects, and settings matching the display's SDR/HDR mode.
2. Reuse one compatible ReShade host and a documented load order. [OptiScaler's Luma UE guide](https://github.com/optiscaler/OptiScaler/wiki/Luma-Unreal-Engine-Luma-UE) documents shared hosting. This is evidence that it can work, not a universal installation recipe.
3. Resolve overlapping shader replacements, tonemapping, resource upgrades, NGX hooks and swapchain/FG control. A RenoDX visual mod need not be another neural consumer; a RenoDX neural add-on must not duplicate active OptiScaler NR. Check overlap with Luma or other visual mods too.
4. Preserve each feature's required processing order and color space. Keep aesthetic effects out of inputs that require unprocessed scene data; check UI separation and avoid unintended double tonemapping/HDR conversion.
5. Validate the DLSS stage, visuals, and combined output: motion, menus/HUD, highlights/blacks, latency, VRAM, recreation and shutdown. Investigate supported settings/load order before rejecting the combination. If it still conflicts, preserve the working baseline and document the limitation and closest supported alternative or separate reversible profiles.

The [Batman history](../games/batman-arkham-knight/HISTORY.md) records real inputs supplied through ReShade/Luma for OptiScaler DLAA/NR after a failed Feeder route. Its short gameplay result does not validate RenoDX co-installation or all DLSS features. Keep that game's limits and known-good profile intact.

## Historical compatibility exception

The 2026-09-13 review recorded [Feeder's documented Dagherbou OptiScaler DLSS-NR consumer](https://github.com/jlrouzies-fr/DLSS5-Feeder#alternative-optiscaler-dlss-nr) as an exception to the usual Feeder/OptiScaler conflict, with no competing neural add-on. ReShade owned `dxgi.dll`; OptiScaler used an imported alternate proxy. Ordinary OptiScaler was excluded. This synthetic finished-frame contract did not supply engine-native DLSS upscaling. See the [Arkham Knight record](../games/BATMAN-ARKHAM-KNIGHT.md) for exact versions, the helper-test result and the subsequent gameplay failure; it is not the current recommended Batman path.

## What receives “real” inputs?

Record each buffer/constant's origin for each consumer: **engine-native**, **captured/converted engine data**, **reconstructed**, **estimated**, **mixed**, or **unknown**. API conversion can preserve engine data but still needs correct timing, scale and interpretation. ReShade hosting does not imply synthetic inputs; access to depth alone does not prove a complete temporal contract. A preset cannot expose missing motion/jitter/UI/ray inputs without implementation code.

Trace the active inputs through creation, repeated evaluation and presentation. Identify automatic optical-flow/finished-frame fallbacks and disable them where supported during engine-input validation; otherwise label the result mixed/unknown. NVIDIA's [DLSS guide](https://github.com/NVIDIA-RTX/Streamline/blob/main/docs/ProgrammingGuideDLSS.md) also requires the engine to use the intended render size: a quality label alone does not prove lower-resolution SR.

Native DLSS components receive buffers tagged by the game/engine. NVIDIA's Streamline documentation requires dense motion vectors containing camera and moving-object motion; FG also benefits from HUD-less color/UI buffers. RR additionally consumes noisy ray-traced color and reflection-specific data.

A ReShade Feeder path is different. It sees the post-process frame, a ReShade-selected depth buffer, and the shared `texMotionVectors` texture written by the chosen provider. With optical-flow providers these vectors are **estimated from images**, not the game's native object motion. They can miss disoccluded or hidden surfaces, particles, transparency, and correct UI separation.

Enable exactly one compatible motion-vector provider technique **above** `DLSS5_Feed`. Enabling every Lumenite luminance or debug technique does not improve the contract and can add cost or alter the image. Use debug views only to validate depth/vector direction and then turn them off.

## Does an add-on disable the rest of DLSS?

Not automatically. A narrowly configured neural add-on can hook only its intended NGX feature while the game keeps native SR, RR, and FG. But all layers still share GPU memory, queues, swapchain recreation, color space, and hook order. The native features must therefore be verified after the add-on is installed; “separate feature” does not mean “zero interaction.”

For every combination, record ownership explicitly:

| Layer | Owner | Input source | Verified active? |
|---|---|---|---|
| SR/DLAA | | origin of color/depth/motion/jitter/exposure | |
| RR | | origin of noisy ray data and other required guides | |
| FG/MFG | | origin of frames/depth/motion/UI and timing | |
| Neural rendering | | origin of each required model input; fallback state | |
| HDR/tonemap | | input/output format and color space; shader stage | |
| Input adapter/bridge | | captured, converted, reconstructed, estimated or mixed | |
| Proxy/ReShade host/presentation | | documented load order and swapchain owner | |
