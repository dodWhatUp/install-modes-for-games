# Repository and Drive export

The maintained source is [dodWhatUp/install-modes-for-games](https://github.com/dodWhatUp/install-modes-for-games). Start with the [installed-games guide](INSTALLED-GAMES-MOD-GUIDE.md). Google Drive holds a dated information export; it is not an automatic synchronization service.

The [14 September 2026 Google Drive folder](https://drive.google.com/drive/folders/1uQuBbrDS0bSVibb-1kj2arZfjVfnrFLy) is the connected export destination. Its existing private access is unchanged; a repository link does not grant access. Download the HTML to browse it locally, or the ZIP for the full documentation and examples.

The export contains a browsable `Mod-Guide.html`, Markdown guides, small authored examples, templates, sanitized evidence excerpts and a SHA-256 manifest. Download mods from the original author links. Game files, mod archives/binaries, saves, personal paths, credentials and private rollback snapshots are excluded.

Run `python scripts/Export-ModGuide.py --output <private-output-folder>` from the repository, with Python's `Markdown` package installed. The script checks allowed file types and common private-path/credential patterns before creating the files. Review the resulting inventory before upload; an automated scan is not a substitute for content review.

Configuration/source examples document previous installations and may require private snapshot files or runtime-specific builds. They are not universal installers. In particular, `Restore-UnifiedControls.ps1` requires an explicit `-GameDirectory` pointing at the actual Cyberpunk `bin/x64` folder plus the matching private snapshot; it cannot restore anything from this public repository alone.

Read [Skyrim's history](../games/skyrim-special-edition/HISTORY.md) for installation status. A candidate in a comparison table is not evidence that its archive has been downloaded, installed or tested.
