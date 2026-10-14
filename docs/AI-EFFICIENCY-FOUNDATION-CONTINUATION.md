# Continuation checkpoint — read-only planning 0.27.0-preview.1

## Current durable base

- AI Efficiency Foundation 0.26 was independently reviewed and merged into canonical `main` through PR #7, followed by its adoption record.
- Slice 2 started from exact main commit `108cb332b874583776c7a9cb1a19ce67c8cc96e5` on `task/ai-plan-readonly-slice2-20261014`.
- The existing proposal mailbox, approval controller, jobs, journal, game-support and keybind owners remain unchanged.

## Accepted task-branch source

- Exact tested product commit: `cd444009d063b27894bf8e399d517670b30ebc47`.
- Candidate R4: 715 payload files, aggregate SHA-256 `c3259d56440dc817a7a54c633e5d3b1fba1f2ef7ac12bb787375822c4c69b420`.
- Windows gate: 13/13 suites, 370 tests, 363 passes and seven explicit environment/package skips; no timeout or automatic retry.
- Real source export: 394 files, ZIP SHA-256 `d843f59e4f148f01f26e29eaaa7895a27aa6bd1ec79403df44ccc82f475ef513`; exported packaging reran 7/7 with zero skips.
- External stdio: modern exposed the four read-only planning tools; legacy remained unchanged. One synthetic UMM fixture and its game tree stayed byte-identical.
- R1, R2 and R3 remain preserved reconciled candidates. None was overwritten or automatically retried.

## Current capability boundary

- Opaque private game-instance identities are registered only through an explicit local operator route.
- UMM is the first accepted read adapter. It reads reviewed executable/loader markers, `Info.json` and declared assembly presence without loading code or writing the game.
- Goal-plan DAGs and ownership/conflict graphs are deterministic read-only previews.
- Four new tools are limited to the modern multi-game MCP surface. The legacy tool list and payload shapes remain unchanged.
- No install, upgrade, disable, rollback, manager write, production profile or arbitrary discovery was added.

## Next safe stages

1. Publish this exact task branch and open a reviewed draft PR; do not merge automatically.
2. Optionally perform one separately authorized real-folder **read-only** acceptance. Its absence remains visible and does not invalidate the synthetic source acceptance.
3. After independent review, extend installed-state comparison only through another separately accepted read adapter or richer UMM evidence; do not begin transactions yet.
4. Keep install, upgrade, disable, rollback and shared-resource leases behind the later transaction state-machine gate.

## Do not infer

A registered instance is not installation health. UMM manifest presence is not enabled state, load order, runtime compatibility or gameplay acceptance. A goal plan is not a durable job, proposal, approval or execution. Task-branch publication is not `main` adoption or production installation.
