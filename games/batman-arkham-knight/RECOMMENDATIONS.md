# Batman: Arkham Knight Recommendations

**Latest review, 2026-09-13 late evening:** the user selected maximum compatible DLSS features. The active ReShade + Luma 649 + OptiScaler v0.7.7 profile now passes short DLAA/NR gameplay and hotkey checks. Keep the stock fallback; the earlier Feeder profile remains disabled after startup crashes. See [current history](HISTORY.md).

**Selected experimental default:** real-input DLAA + one NR pass after SR, preset 0, 25% NR model dimensions. Approximately 45 FPS at 4K in the parked test scene versus 54 with NR off and 28 with full 4K NR. Confidence: medium for this exact tested scene, low for sustained traversal/combat. Difficulty 4 because exact DLL ownership and bridge settings matter. Rollback: private guarded Restore-LumaTrial.ps1 to the preserved disabled-hook baseline. [Controls](CONTROLS.md) lists tested shortcuts and unavailable actions.

Reviewed 2026-09-13.

## First playthrough

- **Core fallback:** stock profile, user-confirmed working after disabling the earlier injected stack.
- **Optional, user-selected experiment:** current Luma + OptiScaler profile, with the practical default above. Luma remains unfinished, so retain stock for visual or stability problems.
- **Optional:** direct MaxFPS edit after a snapshot if higher frame rates are requested. Difficulty 1; high confidence in the configuration mechanism, runtime validation pending. Restore the original line to roll back.
- **Avoid as an active default:** the preserved ReShade + Feeder + OptiScaler DLSS-NR profile, now associated with repeated startup crashes. Root cause remains unknown.

## Later play

- Extend checks to traversal/combat, alt-tab and resolution recreation before treating this profile as a sustained-play recommendation. Current evidence includes actual engine input, NGX creation/evaluation, NR composition and live recreation, beyond overlay loading.
- Additional graphics/performance mods need a separate compatibility review; none are automatically included.

## Post-game or experimental use

- **Experimental, installed:** [Luma Batman](https://github.com/Filoppi/Luma-Framework/wiki), as the real-input source for the single OptiScaler NR consumer. No RenoDX dependency. Current native-resolution DLAA does not provide Quality/Balanced/Performance or live F6 scaling.
- **Unavailable in the active path:** DLSS FG/MFG with Luma's FP16/scRGB output. NVIDIA's Streamline 2.14.1 guide excludes that presentation format; a separate supported-format conversion would require new validation. No FG files were installed. RR has no required ray-tracing integration.
- **Optional/untested:** Arkham Vision as a separate visual-preset experiment after the base neural chain works. Difficulty 3, low local confidence. Back up the current preset first and retain exactly one neural consumer.
- **Avoid:** re-enabling Feeder alongside Luma, duplicate RenoDX/OptiScaler NR consumers, competing swapchain/FG owners, blindly updating the custom binary, or interpreting NR scale as the game's render scale.

## 2026-09-14 — Library comparison review

Added [categorized comparisons](COMPARISONS.md) covering manager/foundations, performance, graphics/DLSS, QoL/UI, animation, AI, abilities/mechanics and actual content extensions. No game files changed or new gameplay tests were performed by this review. Earlier local evidence remains stronger than generic recommendations; historical control mappings and unresolved validation boundaries are preserved. See the [14-game guide](../../docs/INSTALLED-GAMES-MOD-GUIDE.md) for scope and installed-library checks.
