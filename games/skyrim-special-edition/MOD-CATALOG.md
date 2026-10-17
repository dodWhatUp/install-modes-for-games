# Skyrim Special Edition Mod Catalog

Local status reconciled: 2026-10-10. Effective runtime: 1.6.1170.0 after the authorized downgrade; retained Steam metadata still reports build 24914197 and is not the executable version. Candidates are **untested locally** unless [history](HISTORY.md) supplies direct evidence.

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
| Build 19 Hotfix 1 | DLSS/FSR/XeSS upscaling, DLSS/FSR/XeSS FG, RTX 50 MFG, DLSS NR and PD FrameWarp | Enabled in the separate 1.6.1170 profile with SKSE64 2.2.6 and Address Library v13. Startup resource creation succeeds; feature UI is accessible after the user's authentication/loading step. Paid feature operation and third-person gameplay remain unverified. Earlier 1.7.104 failure remains historical | Authentication is user-operated. Keep a single FG owner. First functional test must use RTSS off and NVIDIA Smooth Motion off. Existing ReShade must remain 6.8.0 full add-on support. Current DLSS Quality selection requires restart. Community Shaders upscaling/FG ownership must be resolved before adding it later. Do not restore/update 1.7.x without a separate compatible plan |

PureDark describes PD FrameWarp as his own implementation that updates displayed camera rotation between rendered frames. It can run with or without FG and supports first-person or first- plus third-person modes. This is not evidence that NVIDIA Reflex 2 Frame Warp is directly injected into Skyrim. See [history](HISTORY.md) and the [private archive index](../../docs/PUREDARK-ARCHIVE-2026-10-07.md).

## Automated test input — experimental candidate, not a game mod

[reWASD Send Input](https://help.rewasd.com/mapping-features/send-input.html), reviewed/tested 2026-10-10, can remap software-generated keyboard events through its separate virtual input source. Introduced in 9.3; installed version is 9.5.0.11346. Applicable Lifetime Access and Send Input were already enabled locally; no purchase/trial/activation was needed. Original input is not muted, so duplicate input is possible, and short down/up timing can prevent recognition. The user-authorized isolated profile recognized F13 → J in Notepad, but properly bounded keyboard F12 and virtual Xbox 360 D-pad tests caused no verified Skyrim response. A connected-physical-controller warning limits the virtual-output conclusion; no physical controller was changed or disconnected. Confidence in Skyrim delivery: **Low / not verified**; difficulty **3/5**, stability **normal-app recognition only**, expected benefit **possible game-readable input, not an FPS improvement**, save risk **avoid progression saves during testing**. All 20 original native configs stayed byte-identical. Rollback is already applied: only the separate Send Input source is Off, with the new profile retained inactive. See [history](HISTORY.md).
