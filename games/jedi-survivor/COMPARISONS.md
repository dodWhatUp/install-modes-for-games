# STAR WARS Jedi: Survivor — categorized comparisons

Reviewed 2026-09-14; Steam build 15643690; real executable `SwGame/Binaries/Win64/JediSurvivor.exe` found. Mod packages below are untested locally.

| Category | Options / recommendation | Dependencies, conflicts and cost |
|---|---|---|
| Management / foundations | Author's install workflow for PAKs; [UE4SS](https://github.com/UE4SS-RE/RE-UE4SS) only for chosen logic mods | Place hooks beside the real executable, not EA installer/launcher. Match game signatures and package format |
| Performance + graphics | [Ultra Plus](https://www.nexusmods.com/starwarsjedisurvivor/mods/236) vs [May the Performance be with you](https://www.nexusmods.com/starwarsjedisurvivor/mods/7) | Ultra Plus is the preferred integrated visual/performance candidate; the other is an alternative. Overlapping engine settings: do not stack. Compare CPU traversal stutter separately from GPU load |
| Native DLSS | In-game DLSS SR and native FG first | Keep one FG owner; no replacement FG bridge needed merely because one exists. RR/MFG/NR were not verified for this local build |
| Best practical visual choice | Native high-quality settings, then one Ultra Plus profile if it improves measured scenes | Reduce only demonstrated bottlenecks; no promised stutter-free result, no blanket texture maximum on 16 GB |
| QoL / abilities / animation mechanics | [Blade Master](https://www.nexusmods.com/starwarsjedisurvivor/mods/380) vs [Stance swapping](https://www.nexusmods.com/starwarsjedisurvivor/mods/62) | Blade Master has broader stance/block-cancel features; stance swapping is narrower. Choose one stance owner. UE4SS 3.0.1 was the author's development version, not proof it matches every patch |
| Menus / configuration / UI | Native accessibility menus plus selected mod configuration | No universal MCM selected; keep stance keys separate from graphics hotkeys |
| Enemy behaviour | Native difficulty and replay modifiers | No verified independent AI overhaul selected; unlocking player stances does not improve enemy intelligence |
| Added mechanics | Blade Master is a systems change | Extra stances/cancels can disrupt balance and scripted encounters; prefer after familiarity |
| New content | Original campaign and native New Journey+ | No verified community campaign/total conversion found here; skins and stance changes are not expansion content |

## Recommended combinations

1. **First playthrough — Core:** current game, native DLSS/FG and original progression. Optional one performance mod only after stock comparison. Difficulty 1–2; Medium upstream confidence, no local benchmark.
2. **After familiarity — Strong candidate:** one proven performance profile plus Blade Master if its exact loader/build passes testing. Difficulty 3; gameplay changes meaningful.
3. **Replay — Optional:** broader stance/cancel options on a copied save; avoid combining all stance mods. Difficulty 3; compatibility conditional.

Rollback: preserve `Engine.ini`, game configuration, selected PAKs, UE4SS files/config and a save checkpoint. Restore the settings and file manifest together; a game verification alone leaves third-party additions. Test traversal, combat, stance UI, loading and clean exit separately from graphics changes.
