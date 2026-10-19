# System control center: read-only source preview

Start with [stage conclusions](../../docs/control-center/MCI-01-CONCLUSIONS.md), the [reuse inventory](../../docs/control-center/MCI-01-INVENTORY.json), and the [P0 implementation report](../../docs/control-center/P0-IMPLEMENTATION.md).

Double-click scripts/GameToolSystemControl.pyw with an existing Python/Tk runtime, or run `python -B scripts/GameToolSystemControl.py gui`. The current-project button explicitly reads a fixed small source selection; the initial authored example contains invented devices/events/chat summaries. A selected JSON context binds relative sources to its own directory, or use `--root` for an explicitly chosen project root. No Codex installation, authentication or configuration change is needed.

The existing Hub adds System control through its optional Mods/AI integration. The standalone source preview uses the same panel/services. Opening a source preview is separate from installation or update of the existing toolkit.

CLI modes: explore, preflight, overview, journal and gui. `--context`, `--root`, `--scope` and `--query` select evidence; `--draft` is checked locally and never submitted. `journal --journal PATH` reads only the explicitly selected journal through its existing validator. A context file is bounded to the existing reader's 128 KiB; selected source files are at most 128 KiB, 32 sources and 2 MiB combined. In-memory JSON additionally has depth/value/schema bounds.

Keep personal context files, journals, drafts, native chats and local bindings outside Git/OneDrive. The application writes no cache, local task master, native chat store, schedule or service. Loaded-state claims in selected contexts are reports, not authenticated platform state. No network, cloud, remote action or model API is connected here. Future transports and source owners retain their independent acceptance gates.
