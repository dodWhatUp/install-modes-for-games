# Skyrim Special Edition Mod Catalog

Last reviewed: 2026-10-07. Local build: 24914197. Candidates are **untested locally** unless [history](HISTORY.md) supplies direct evidence.

The [categorized comparison tables](COMPARISONS.md) are the catalog's detailed entries: author URLs, purpose, alternatives, dependencies, conflicts and content classification. They cover foundations/manager, performance, graphics/DLSS, QoL, configuration/UI, animation/movement, enemy behaviour, abilities/magic/tools, mechanics and added campaigns/content. Unknown support is marked as a gate, not a recommendation.

## Evidence and maintenance

- Confidence: Medium in author-documented purpose; Low in the exact installed-build combination until validated.
- Performance and VRAM impact: qualitative expectations only; no new measured gains.
- Review date is not the mod release date. Use each linked author's current files/changelog for the exact version before installation.
- Normal review interval: 90 days; experimental graphics: 30 days; relevant game updates trigger immediate review.

## Compatibility groups and expansion status

See the explicit conflicts and content table in [comparisons](COMPARISONS.md). A trainer, cosmetic pack, shader preset, new class or rebalance is not a new authored campaign. Save-dependent changes require restoring the old save and mod profile together.

The [recommendations](RECOMMENDATIONS.md) select combinations from this catalog; none authorizes a blanket installation.

## PureDark Skyrim Upscaler AIO

| Package | Purpose | Local status | Important boundaries |
|---|---|---|---|
| Build 19 Hotfix 1 | DLSS/FSR/XeSS upscaling, DLSS/FSR/XeSS FG, RTX 50 MFG, DLSS NR and PD FrameWarp | Official archive downloaded, hashed and privately archived; not deployed | Requires matching SKSE. Keep a single FG owner. First test without RTSS and with NVIDIA Smooth Motion off. Existing ReShade must be 6.8.0 full add-on support. Community Shaders upscaling/FG ownership must be resolved before adding it later |

PureDark describes PD FrameWarp as his own implementation that updates displayed camera rotation between rendered frames. It can run with or without FG and supports first-person or first- plus third-person modes. This is not evidence that NVIDIA Reflex 2 Frame Warp is directly injected into Skyrim. See [history](HISTORY.md) and the [private archive index](../../docs/PUREDARK-ARCHIVE-2026-10-07.md).
