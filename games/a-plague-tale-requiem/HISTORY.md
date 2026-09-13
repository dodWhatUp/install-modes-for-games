# A Plague Tale: Requiem History

## 2026-09-13 — F7 two-value controls installed

- User requested replacing every installed NR resolution cycle with F7 toggling only 25% and 100%, and live DLSS SR selection beside NR where possible.
- Same game builds, rendering APIs, RTX 5070 Ti/616.56 and existing hook owners as the preceding inventory; live desktop 3840×2160 at 150 Hz. No game or helper was running; Steam was shut down gracefully before mutation.
- Current-state snapshot: private `f7-controls-20260913/before-f7-20260913-141908`, with before/after file hashes, root hook/executable version/hash inventory, INIs, CET configuration, UserSettings, per-app Steam state, launch configuration, NVIDIA DRS and graphics environment. Prior stock/known-good snapshots remain separate.
- Full rebuilds used MSVC 14.44.35207 / Windows SDK 10.0.26100.0. Both preserve all 946 named exports/ordinals. [Follow-up source patches](../../examples/optiscaler-dlssnr/f7-two-scale/README.md) preserve the exact code changes without binaries.
- New proxy `298D93C3D648330E279B614FC4B822FE38D87EC33516EFED90537664E9E9A090`, stamp `e237f89+f7-25-100`; ScaleCycleKey explicitly 0x76 instead of the former auto/F9 default. F8 placement and saved NR scale 1.0 remain. Only DLL and INI changed.
- The compact panel explicitly reports live native SR unavailable for this game. Current local source confirms ratio overrides only affect resolution queries. Upstream research found no verified Requiem engine-level hotkey adapter; no settings-file reload claim or memory patch installed.
- Verification: target hashes matched after installation, protected native files unchanged; restore dry-run passed before and after mutation. No new game launch or live keyboard test. Earlier runtime evidence is historical, not proof for this revision.
- Rollback: close games/Steam/helpers; run the snapshot's `Restore-F7.ps1 -Game Requiem`. It validates targets/backups, preserves the current files and restores only this revision's changes. Run it before older rollback scripts because those expect the previous hashes. No rollback executed.
- Next boundary: verify F7 key release, notification, actual 25%/100% model sizes, recreation and Save Settings reload in a repeatable scene. Requiem's earlier 25% title-scene success belongs to the prior build. Native SR remains controllable through the game menu; an external live shortcut needs a verified engine integration. No reminder or automatic resume scheduled.

## State recorded before the F7 revision

- Installed: OptiScaler-DLSSNR v0.7.7 with local compact, model-resolution and placement controls, as `dxgi.dll`.
- Baseline: stock animated title scene rendered; no gameplay or campaign save was started by the agent.
- Snapshot: private `requiem-before-optiscaler-20260913-131853`, preserving stock files, per-app Steam state, external settings, NVIDIA DRS and hashes.
- Resume boundary: finish the first-run privacy choice manually, then verify gameplay motion/HUD, native FG, display HDR and alt-tab/resolution recreation. Title-scene shutdown passed; no reminder scheduled.

## 2026-09-13 — Install NR and requested controls

- Goal: install OptiScaler with the community DLSS 5 extension; Delete full menu, F12 compact window, F11 NR preset hints, F10 toggle; investigate F9 working resolution, F8 placement, and F7 native upscaling modes.
- Inventory: Steam build 11415435; game 1.6.0.0; `APlagueTaleRequiem_x64.exe`, x64 D3D12; RTX 5070 Ti 16 GB/616.56; 4K display. Clean game root with native DLSS 2.4.12, FG 3.1.1 and Streamline 1.5.4. No ReShade/OptiScaler proxy or anti-cheat found. NVIDIA and Steam overlays present.
- Upstream review: OptiScaler compatibility list includes Requiem DLSS inputs. v0.7.7 supports pre/post-SR and working resolution. Native temporal inputs make Feeder unnecessary.
- Provenance: the reused extracted package's INI had been edited, so its checksum check failed before installation. A fresh extraction of the hash-verified original release ZIP passed all 63 internal checksums. No mismatching file was installed as an upstream default.
- Custom controls: reused the available local source build based on `e237f895623742b761f9e5f00067cb3dc62619f4`. Proxy SHA-256 `4400E00C58451AAC69554600AEFB178089C4D9D67C6BCF9C8BFEA8FE961557BE`; all 946 names/ordinals matched the release. Exact source delta preserved under the game's examples.
- NVIDIA model: original signed RTX 50 310.8, hash `E16BCF15E16E13F527491CDF7845B2FE6521A738D8F7C9C721866A8496E1FC8E`. Open-source forwarder hash `DE80593C5404C0909526B6F3D4C966CCFDF26CAC8286FBE088EA9883EAFCB21D`.
- Mutation: after the stock run and Steam exited, created/verified a just-in-time snapshot and added 65 manifest-owned files. No existing file was overwritten. Game process filter is exact; native FG retained with internal OptiScaler FG off; NR one-pass FP8/pre-SR/scale 1.0; capture, residual and finished-picture modes off.
- Runtime evidence: proxy loaded, DLSS backend creation succeeded, model creation and readiness followed submitted work, composition and repeated GPU timing were logged. Game supplied 1920×1080 color/depth/MV inputs to 4K output. Effective DLSS version logged as 310.9 while original on-disk file stayed 2.4.12.
- F9 evidence: 100%→75%→50%→25%→100% rebuilt model sizes 1920×1080, 1440×810, 960×540, 480×270, and 1920×1080. Each reduced scale reached readiness and composition without a process crash.
- F8 evidence: at 50%, toggling after SR rebuilt against 3840×2160 output with a 1920×1080 model. Returning before SR rebuilt at 960×540. This is actual placement/resolution evidence, not only overlay state.
- Other controls: F10 visibly disabled NR with a matching skipped-dispatch log and enabled it again; F11 completed 0→1→2→3→0 with model readiness. Delete opened the full menu, F12 switched to the compact window and closed it. Mouse Save Settings wrote the INI at 13:26:14.
- Persistence: saved defaults are NR on, before SR, scale 1.0, one pass, preset 0, style 0 and intensity 1.0. The serializer writes default-valued keys as `auto`; the exact custom source defaults confirm Delete/F8–F12 and disabled internal FG remain effective. Explicit DLSS backend, external FG, process filter and disabled spoofing were retained.
- Final verification: graceful Alt+F4 released the feature, detached and unloaded OptiScaler at 13:26:38. Game process exited. All 22 original root files and 64 immutable installed files still matched their snapshot hashes. Post-save INI hash is `6DFCCF8D473448EA5D388D2DE8DC5A10E61CC5A31F4F33222C02A7935FB1DF47`; final raw log and INI preserved privately.
- F7 conclusion: no verified live native SR quality switch was found. Existing OptiScaler ratio overrides affect resolution-query replies, not the engine's render targets by themselves. No fake mode-switch key, memory patch, or macro installed.
- First-run boundary: stock EULA accepted; the telemetry choice was left to the user because the computer-use skill forbids acting on privacy permission prompts. Installation and title-scene NR tests proceeded independently.
- Limitations: animated title scene only; no claim of campaign/HUD/FG/HDR/long-run validation. Model preset-hint visual effects are undocumented.
- Rollback: not performed. Private `Restore-Requiem.ps1` checks exact added-file identities, preserves the current mod state, and removes only owned additions; native files and settings stay intact. Syntax and `-WhatIf` passed.

## 2026-09-14 — Library comparison review

Added [categorized comparisons](COMPARISONS.md) covering manager/foundations, performance, graphics/DLSS, QoL/UI, animation, AI, abilities/mechanics and actual content extensions. No game files changed or new gameplay tests were performed by this review. Earlier local evidence remains stronger than generic recommendations; historical control mappings and unresolved validation boundaries are preserved. See the [14-game guide](../../docs/INSTALLED-GAMES-MOD-GUIDE.md) for scope and installed-library checks.
