# Contributing a Game Test

Add a game only after testing from a clean or restorable baseline.

1. Copy [the game-guide template](templates/GAME-GUIDE.md).
2. Record the game build, executable, bitness, graphics API, GPU, driver, display mode, and every installed component version.
3. Record a stock-file inventory before installation. Use `scripts/Get-ModFileReport.ps1` for hashes and file versions.
4. Change one layer at a time.
5. Attach short, sanitized log evidence. Remove usernames, absolute paths, account IDs, save data, and machine names.
6. Use one of these result labels: `working`, `partial`, `failed`, or `untested`.
7. Never commit game binaries, NVIDIA DLLs, installers, archives, crash dumps, or copyrighted shader packs.

A visual difference alone is not enough. A working upscaler, frame generator, or neural pass should also have positive runtime evidence in its own log.
