# Contributing a Game Test

Add a game only after testing from a clean or restorable baseline.

1. Create a game folder and copy the [game-guide](templates/GAME-GUIDE.md), [history](templates/GAME-HISTORY.md), [catalog](templates/MOD-CATALOG.md), and [preference](templates/PREFERENCE-PROFILE.md) templates as needed.
2. Record the game build, executable, bitness, graphics API, GPU, driver, display mode, and every installed component version.
3. Record a stock-file inventory before installation. Use `scripts/Get-ModFileReport.ps1` for hashes and file versions.
4. Change one layer at a time.
5. Attach short, sanitized log evidence. Remove usernames, absolute paths, account IDs, save data, and machine names.
6. Use one of these result labels: `working`, `partial`, `failed`, or `untested`.
7. Never commit game binaries, NVIDIA DLLs, installers, archives, crash dumps, or copyrighted shader packs.

Keep a broad catalog separate from curated recommendations. Every catalog entry needs an original source, category, requirements/conflicts, update/review date, local test state, and confidence. Explicitly state when no expansion-scale project was found rather than stretching the definition.

A visual difference alone is not enough. A working upscaler, frame generator, or neural pass should also have positive runtime evidence in its own log.
