# A Plague Tale: Requiem Mod Catalog

**Current controls revision, 2026-09-13:** [F7 two-scale customization](../../examples/optiscaler-dlssnr/f7-two-scale/README.md) installed on the same consumer fork. F7 toggles NR 25%/100%. Native live SR remains unavailable in this installed chain. Old F9/F7 descriptions below record the preceding package/review. No additional graphics consumer was installed.

Last reviewed: 2026-09-13. Focused on the requested graphics installation; this is not a comprehensive mod survey.

| Mod/tool | Category | Purpose | Requirements | Conflicts/risks | Local state | Confidence |
|---|---|---|---|---|---|---|
| [OptiScaler-DLSSNR v0.7.7](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/releases/tag/v0.7.7) plus local controls | Graphics | NR before/after native SR, resolution controls and compact UI | Native D3D12 temporal input, correct signed RTX 50 model, complete package | Model rebuild latency, VRAM cost, potential temporal artifacts; no second NR/FG owner | Installed; title-scene neural and recreation evidence | High for observed title behavior; untested in gameplay |
| [Native OptiScaler compatibility](https://github.com/optiscaler/OptiScaler/wiki/Compatibility-List) | Upscaling framework | Supports Requiem DLSS inputs | DLSS enabled in game | Compatibility listing does not validate this NR fork | Used as upstream prerequisite evidence | Medium upstream |
| Native DLSS SR/FG and Reflex | Graphics/performance | Original engine integration | Compatible NVIDIA GPU | FG delivery must be checked separately from NR | Original files retained | High file integrity; FG activity unknown |

## Other categories

- Framework/bug-fix/performance replacements: none added beyond the requested stack.
- QoL/movement, UI outside the custom overlay, gameplay, cosmetics/audio: not investigated in this installation task.
- Expansion-scale or total-conversion status: not researched; no claim of availability or absence.

## Compatibility groups

OptiScaler alone owns `dxgi.dll` and NR. Native game components retain FG. ReShade, RenoDX and Feeder are absent. No campaign data modification is part of this installation; private snapshots contain only local recovery data and are not publishable.

## 2026-09-14 — Library comparison review

Added [categorized comparisons](COMPARISONS.md) covering manager/foundations, performance, graphics/DLSS, QoL/UI, animation, AI, abilities/mechanics and actual content extensions. No game files changed or new gameplay tests were performed by this review. Earlier local evidence remains stronger than generic recommendations; historical control mappings and unresolved validation boundaries are preserved. See the [14-game guide](../../docs/INSTALLED-GAMES-MOD-GUIDE.md) for scope and installed-library checks.
