# Game Tools Keybinds 0.2.0-preview.1 — merged component

This data-driven keybinding component is integrated into the existing Unified Game
Tools owner. The keybind merge was reviewed at `0.25.0-preview.2`; the current additive host
candidate is `0.26.0-preview.1`. There is no
second Hub, approval store, journal, game-ID namespace or installer.

Start with [`README.md`](README.md). Use `scripts/Game-Keybinds.py` for local CLI
operations and `scripts/GameToolWorkbenchLaunch.pyw` only through the extracted
preview launchers. Core/CLI require Python 3.10+; the local panel also requires Tk.
No runtime is installed automatically.

Adding a game with an already-supported text grammar should add one reviewed
`game-packs/<category>/<game>/` data folder with `pack.json`, evidence and sanitized
fixtures. A new grammar requires one explicitly registered trusted adapter. Data
packs cannot load code, run commands or approve/import/activate themselves.

The component reuses the host's process guard, immutable plans, retained original
bytes, approval mailbox and journal. Mod recipes and keybind packs remain separate
registries even when they share a `game_id`. A keybind-only game does not receive a
fabricated mod recipe. A change in capability shape requires reopening the Workbench;
a recipe-only revision refreshes the scoped service while retaining old immutable
jobs and requests.

Ten built-in text routes and their fixtures are format evidence, not ten supported
games. The 17 game folders are research drafts. There were no native Windows,
installed-client, real-config, gameplay or physical-device acceptance runs in this
delivery. See the current validation and limitations files linked from `README.md`.
