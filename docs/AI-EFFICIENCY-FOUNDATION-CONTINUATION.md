# Continuation checkpoint — read-only planning 0.27.0-preview.1

## Current durable base

- AI Efficiency Foundation 0.26 was independently reviewed and merged into canonical `main` through PR #7, followed by its adoption record.
- This slice starts from exact main commit `108cb332b874583776c7a9cb1a19ce67c8cc96e5` on `task/ai-plan-readonly-slice2-20261014`.
- The existing proposal mailbox, approval controller, jobs, journal, game-support and keybind owners remain unchanged.

## Current candidate

- Opaque private game-instance identities are implemented; paths are selected and retained only through an explicit local operator route.
- UMM is the first accepted read adapter. It reads reviewed executable/loader markers, `Info.json` and declared assembly presence without loading code or writing the game.
- Deterministic goal-plan DAGs and ownership/conflict graphs are implemented as read-only previews.
- Four new tools are limited to the modern multi-game MCP surface. The legacy tool list and payload shapes remain unchanged.
- Synthetic UMM and selected regression tests have passed. Final package, native Windows and any real-folder read require separate receipts before publication claims.

## Next safe stages

1. Finish exporter/package wiring, static checks and the selected/full regression gate.
2. Perform native Windows acceptance against a copied candidate and synthetic UMM fixture; return the VM to its prior state.
3. Optionally perform one separately authorized real-folder **read-only** acceptance. Absence of that pass remains visible and does not block synthetic source publication.
4. Publish only a reviewed task branch and draft PR; do not merge automatically.
5. Keep install, upgrade, disable, rollback, manager writes and arbitrary discovery behind a later transaction gate.

## Do not infer

A registered instance is not installation health. UMM manifest presence is not enabled state, load order, runtime compatibility or gameplay acceptance. A goal plan is not a durable job, proposal, approval or execution. Task-branch publication is not main adoption or production installation.
