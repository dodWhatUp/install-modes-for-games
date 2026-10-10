# Repository and Drive export

The maintained source is [dodWhatUp/install-modes-for-games](https://github.com/dodWhatUp/install-modes-for-games). Start with the [installed-games guide](INSTALLED-GAMES-MOD-GUIDE.md). Google Drive holds a dated information export; it is not an automatic synchronization service.

The [14 September 2026 Google Drive folder](https://drive.google.com/drive/folders/1uQuBbrDS0bSVibb-1kj2arZfjVfnrFLy) is the connected export destination. Its existing private access is unchanged; a repository link does not grant access. Download the HTML to browse it locally, or the ZIP for the full documentation and examples.

The export contains a browsable `Mod-Guide.html`, Markdown guides, small authored examples, templates, sanitized evidence excerpts and a SHA-256 manifest. Download mods from the original author links. Game files, mod archives/binaries, saves, personal paths, credentials and private rollback snapshots are excluded.

Run `python scripts/Export-ModGuide.py --output <private-output-folder>` from the repository, with Python's `Markdown` package installed. The script checks allowed file types and common private-path/credential patterns before creating the files. Review the resulting inventory before upload; an automated scan is not a substitute for content review.

Configuration/source examples document previous installations and may require private snapshot files or runtime-specific builds. They are not universal installers. In particular, `Restore-UnifiedControls.ps1` requires an explicit `-GameDirectory` pointing at the actual Cyberpunk `bin/x64` folder plus the matching private snapshot; it cannot restore anything from this public repository alone.

Read [Skyrim's history](../games/skyrim-special-edition/HISTORY.md) for installation status. A candidate in a comparison table is not evidence that its archive has been downloaded, installed or tested.

The separate [PureDark private archive index](PUREDARK-ARCHIVE-2026-10-07.md) records the 7 October 2026 paid-release backup. Its linked Drive folder keeps private archives under existing permissions; Git contains only sanitized metadata and hashes.

## 2026-10-10 — Agent game-input module archive

The [GameInputModule source/documentation ZIP](https://drive.google.com/file/d/1xCE9ycIyf0m6IYUfrXng57bSbxq5PQnJ/view) contains 11 authored source/guide/validation/export files plus a SHA-256 manifest. Final archive: 32,568 bytes; SHA-256 `5A13FE47492DD3C079BDFF175F0F8B1F77E2146CF70DA775EEE57E02EBB76671`. Final Drive download readback matched the local archive byte-for-byte after formatting-only EOF cleanup and a repeated 36-test pass. Folder listing confirmed existing private/not-shared access; no permissions were widened. The prior package revision remains recoverable through Drive revision history/local checkpoints.

Separate readable files: [workflow/evidence guide](https://drive.google.com/file/d/1jWV9wtKL8hFhuZO2lKxtWgOVEZfQ0o-M/view) and [ready-to-copy message for the larger AHK chat](https://drive.google.com/file/d/1VvBbmVdEZvHEpZGXLFgZYEKb_dyCWZCr/view). The message has not been sent. The larger AHK source remains unchanged; actual host integration is pending.

The archive preserves exact v0.3.1 live-tested baseline bytes and v0.5-preview.1 integration source. The new preview passed native syntax and 36 no-input tests, not GUI/lifecycle/game acceptance. Text/Enter/Escape/holds and MFG/FrameWarp remain pending/deferred; do not transfer baseline runtime proof to the refactor. See [agent game input](AGENT-GAME-INPUT.md).

Use `scripts/Export-GameInput.ps1 -OutputDirectory <new-private-output-directory>` for a focused source bundle. It refuses an existing/output-in-repository directory, scans private-path/credential candidates, checks baseline hash and verifies every archived source hash. The general guide exporter now also permits authored `.ahk` text; it still excludes interpreter/game/mod binaries, saves, private recovery data and credentials. Git preserves the baseline without line-ending normalization. This dated bundle is a checkpoint, not automatic synchronization or a second code master.
