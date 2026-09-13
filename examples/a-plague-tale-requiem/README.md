# Requiem compact NR controls

**Superseded controls, 2026-09-13:** the current installed F7 25%/100% builds and follow-up source patches are documented in [F7 two-scale controls](../optiscaler-dlssnr/f7-two-scale/README.md). Earlier cycle descriptions below are historical build evidence, not the current mapping.

The [INI delta](Controls.ini) requires the [source patch](compact-resolution-placement-v077.patch) on upstream [v0.7.7](https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass/releases/tag/v0.7.7), commit `e237f895623742b761f9e5f00067cb3dc62619f4`. It includes the earlier compact-menu implementation plus F9/F8 actions. Do not apply it on top of the older compact patch a second time.

The installed local x64 Release proxy has SHA-256 `4400E00C58451AAC69554600AEFB178089C4D9D67C6BCF9C8BFEA8FE961557BE`. All 946 export names and ordinals match the original release. Its local toolchain is MSVC 14.44.35207 / Windows SDK 10.0.26100.0. The binary and build staging are private; upstream GPL and dependency licenses apply.

The compact menu uses the same input capture and setting values as the full menu. Scale/intensity sliders commit on release. F9/F8 guard rapid repeats and recreate the model through the existing renderer path. F8 declines changes when Finished Picture or Deferred DLSS overrides ordinary placement.

F11 only cycles numeric model hints; it is not a saved whole-profile selector. Save Settings persists the combined current choices. F7 is deliberately absent because a generic INI override cannot ensure the game changes its rendering resolution live.

Save Settings serializes values equal to this custom build's defaults as `auto`. This is expected: Delete/F8–F12, scale 1.0, preset 0 and disabled internal FG retain their source-defined values. The example spells them out for review and initial installation.

See the [game record](../../games/A-PLAGUE-TALE-REQUIEM.md) for current runtime evidence and rollback. Do not copy this game-filtered INI to a different game.
