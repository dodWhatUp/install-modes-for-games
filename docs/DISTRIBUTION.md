# Repository and Drive export

The maintained source is [dodWhatUp/install-modes-for-games](https://github.com/dodWhatUp/install-modes-for-games). Start with the [installed-games guide](INSTALLED-GAMES-MOD-GUIDE.md). Google Drive holds a dated information export; it is not an automatic synchronization service.

The [14 September 2026 Google Drive folder](https://drive.google.com/drive/folders/1uQuBbrDS0bSVibb-1kj2arZfjVfnrFLy) is the connected export destination. Its existing private access is unchanged; a repository link does not grant access. Download the HTML to browse it locally, or the ZIP for the full documentation and examples.

The export contains a browsable `Mod-Guide.html`, Markdown guides, small authored examples, templates, sanitized evidence excerpts and a SHA-256 manifest. Download mods from the original author links. Game files, mod archives/binaries, saves, personal paths, credentials and private rollback snapshots are excluded.

Run `python scripts/Export-ModGuide.py --output <private-output-folder>` from the repository, with Python's `Markdown` package installed. The script checks allowed file types and common private-path/credential patterns before creating the files. Review the resulting inventory before upload; an automated scan is not a substitute for content review.

For the shared game-tool work, use `scripts/Export-GameTools.ps1 -OutputDirectory <new-private-output-directory>`. It exports an explicit authored-source inventory, the knowledge index, operating procedures, catalog/planner, Hub foundation and input integration. `scripts/Export-GameInput.ps1` produces the smaller input-only package. These mechanical exporters do not launch tools or upload files. Their public-source inventories exclude personal settings/native profiles and private recovery files; review the inventory and validation boundaries before distribution.

Configuration/source examples document previous installations and may require private snapshot files or runtime-specific builds. They are not universal installers. In particular, `Restore-UnifiedControls.ps1` requires an explicit `-GameDirectory` pointing at the actual Cyberpunk `bin/x64` folder plus the matching private snapshot; it cannot restore anything from this public repository alone.

Read [Skyrim's history](../games/skyrim-special-edition/HISTORY.md) for installation status. A candidate in a comparison table is not evidence that its archive has been downloaded, installed or tested.

The separate [PureDark private archive index](PUREDARK-ARCHIVE-2026-10-07.md) records the 7 October 2026 paid-release backup. Its linked Drive folder keeps private archives under existing permissions; Git contains only sanitized metadata and hashes.

## 2026-10-10 — Agent game-input module archive

Historical checkpoint: the following links describe the original preview.1 package, not the later installed preview.3 host integration. Preserve its evidence boundary and use the current [knowledge index](GAME-TOOLS-KNOWLEDGE-INDEX.md) and [integration record](../examples/game-input/OVERLAY-STUDIO-INTEGRATION.md) for the superseding state.

The [GameInputModule source/documentation ZIP](https://drive.google.com/file/d/1xCE9ycIyf0m6IYUfrXng57bSbxq5PQnJ/view) contains 11 authored source/guide/validation/export files plus a SHA-256 manifest. Final archive: 32,568 bytes; SHA-256 `5A13FE47492DD3C079BDFF175F0F8B1F77E2146CF70DA775EEE57E02EBB76671`. Final Drive download readback matched the local archive byte-for-byte after formatting-only EOF cleanup and a repeated 36-test pass. Folder listing confirmed existing private/not-shared access; no permissions were widened. The prior package revision remains recoverable through Drive revision history/local checkpoints.

Separate readable files: [workflow/evidence guide](https://drive.google.com/file/d/1jWV9wtKL8hFhuZO2lKxtWgOVEZfQ0o-M/view) and [ready-to-copy message for the larger AHK chat](https://drive.google.com/file/d/1VvBbmVdEZvHEpZGXLFgZYEKb_dyCWZCr/view). The message has not been sent. The larger AHK source remains unchanged; actual host integration is pending.

The archive preserves exact v0.3.1 live-tested baseline bytes and v0.5-preview.1 integration source. The new preview passed native syntax and 36 no-input tests, not GUI/lifecycle/game acceptance. Text/Enter/Escape/holds and MFG/FrameWarp remain pending/deferred; do not transfer baseline runtime proof to the refactor. See [agent game input](AGENT-GAME-INPUT.md).

Use `scripts/Export-GameInput.ps1 -OutputDirectory <new-private-output-directory>` for a focused source bundle. It refuses an existing/output-in-repository directory, scans private-path/credential candidates, checks baseline hash and verifies every archived source hash. The general guide exporter now also permits authored `.ahk` text; it still excludes interpreter/game/mod binaries, saves, private recovery data and credentials. Git preserves the baseline without line-ending normalization. This dated bundle is a checkpoint, not automatic synchronization or a second code master.

## 2026-10-11 — Private recovery and linked knowledge

The [private GameTools recovery checkpoint](https://drive.google.com/file/d/1BNk-LCA2gIaTd-t7D4vIB6QuL13e4hxR/view) contains ten copied recovery/source-index files plus a manifest: the installed Studio2 integration, pre-integration source, Studio settings and referenced F7 picture, the Hub registry, a bounded chat-source index and restore instructions. Final archive: 420,978 bytes; SHA-256 `2E0D20DF898B6448CC50BC4DB1455B32C4D1DE351B9B7554675512938F4E26A0`. Source/copy/archive checks and a downloaded Drive readback matched. Drive metadata confirmed existing private owner-only access; no sharing changes were made.

This is not a complete chat export, full-system backup or tested restore. Previously archived native profiles, Studio3 and earlier overlay/MIC sources are linked by role rather than silently replaced. Their metadata was checked; their archive bytes were not re-downloaded this session. Some related chat reads were rate-limited. The [knowledge index](GAME-TOOLS-KNOWLEDGE-INDEX.md) records coverage, masters, derivatives, conflicts and unfinished acceptance. Close and reconcile newer state before restoring; the old host checkpoint retains its historical loader defect.

## 2026-10-11 — Earlier authored source and knowledge checkpoint r3

The [GameTools source/knowledge checkpoint r3](https://drive.google.com/file/d/1OKtbD2__enE61Ui3YjWsPGI_DRI9XC6l/view) contains 47 curated authored files plus `MANIFEST.json`: current GameInputModule preview.3 and Studio2 integration, exact historical v0.3.1 baseline, Hub 0.2.0, catalog 0.1.1, source/tests, knowledge/operating/overhead procedures and templates. Final archive: 181,669 bytes; SHA-256 `27AFD54D28636B89BD24F3D0E0EF931AE22DC70BD58CCDBCE4B5CDA4EBBAE69E`. All source and manifest ZIP entries were size/hash-verified; downloaded Drive bytes matched. Metadata confirmed the existing private folder and owner-only/not-shared access; no permissions were changed.

Catalog 35 pure tests and existing Hub 22 contracts passed. Focused exporters passed 38 synthetic contracts in both Windows PowerShell 5.1 and PowerShell 7, including portable ZIP paths, version/ledger consistency, privacy/output guards and stale-source refusal. A concurrent source edit was correctly refused before output creation. No live AHK/game/provider acceptance, recording or benchmark was performed for this checkpoint; no measured CPU/GPU/RAM/VRAM costs are supplied.

This bundle is an immutable source/knowledge snapshot, not a complete restore or automatic synchronization. The manifest records exact packaged hashes and unbundled canonical references rather than claiming identity with a later Git commit. This distribution receipt and the index's final archive link were added after packaging; use the maintained repository for the latest receipt. Personal settings/assets/native exports require the separate private recovery packages. The [first interim source archive](https://drive.google.com/file/d/1JR8Hy3Iyms7zGPgZB3X948H9-DuwWe4M/view) remains a superseded private checkpoint; use r3 for the corrected public-source locators and source-ownership handoff. No older checkpoint was deleted or overwritten.

## 2026-10-11 — Current source/knowledge checkpoint r4

Use the [final GameTools source/knowledge checkpoint r4](https://drive.google.com/file/d/1TYp7eEQMXugertEkDJ2711dRHHujnJB8/view). It supersedes r3 by correcting the remaining draft-only architecture link and adding a qualified pointer to the separately published R6 design/prototype; existing R5/live profiles are not replaced. The same 47-file scope, exclusions, component versions and pending runtime boundary apply. Final archive: 182,864 bytes; SHA-256 `551B3842B259C836E1DA3F8249970E5580908E406C30196B3502B90120A91A21`. All ZIP entries and downloaded Drive readback matched; folder/owner-only/not-shared metadata was verified without permission changes. Reference checks found zero missing local targets; 19 intentionally unbundled references are declared in the manifest.

The r4 receipt/final link postdate its immutable packaged documentation; this maintained page is the current receipt. Earlier checkpoints remain preserved. Catalog/Hub pure checks and the two-engine export tests are not game input, automated installation, recorded crash recovery or measured overhead acceptance. No game was launched, save loaded, graphics changed or benchmark/capture started.
