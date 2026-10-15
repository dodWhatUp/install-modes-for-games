# Continuation checkpoint — read-only planning 0.27.0-preview.1

## Current durable base

- AI Efficiency Foundation 0.26 was independently reviewed and merged into canonical `main` through PR #7, followed by its adoption record.
- Slice 2 started from exact main commit `108cb332b874583776c7a9cb1a19ce67c8cc96e5` on `task/ai-plan-readonly-slice2-20261014`.
- The existing proposal mailbox, approval controller, jobs, journal, game-support and keybind owners remain unchanged.

## Canonical adopted source

- Exact runtime-tested product commit: `e454433e81e067b1f11267a3cac18081b60512f8`; later acceptance/documentation commit: `ab9c2cdf32dd9d361aa4273aca6e10a168e864d8`.
- PR #9 passed independent exact-head review and merged into canonical `main` as merge commit `ef38d94be4fb4847cbbeda5f8fe41455b267aeaa`; historical R8, R5 and R4 product commits remain preserved.
- Candidate R9: 715 payload files, aggregate SHA-256 `da3e7f3de4c106cc24ba0b7b3be01ea85898fede9aa348b90d6953f18595d9d1`.
- Windows gate: 13/13 suites, 388 tests, 381 passes and seven explicit environment/package skips; no timeout or automatic retry.
- Real source export: 394 files, ZIP SHA-256 `369a396b00f845a74fbaa7abfe8c004bf5a0d64becd24ea003cd575e79b6fc30`; exported packaging reran 7/7 with zero skips.
- External stdio: modern exposed the four read-only planning tools with exact read effects; legacy remained unchanged. Five synthetic game trees stayed byte-identical, one corrupt filename remained opaque, embedded credential/Windows/short POSIX paths were refused without echo, and filtered cross-game pagination stayed accurate across 34 checks.
- R1–R8 and the isolated R9 system-context copy remain preserved with their exact boundaries; none was overwritten or presented as the current-user R9 pass.

## Current capability boundary

- Opaque private game-instance identities are registered only through an explicit local operator route.
- UMM is the first accepted read adapter. It reads reviewed executable/loader markers, `Info.json` and declared assembly presence without loading code or writing the game.
- Goal-plan DAGs and ownership/conflict graphs are deterministic read-only previews.
- Four new tools are limited to the modern multi-game MCP surface. The legacy tool list and payload shapes remain unchanged.
- No install, upgrade, disable, rollback, manager write, production profile or arbitrary discovery was added.

## Next safe stages

1. Optionally perform one separately authorized real-folder **read-only** acceptance. Its absence remains visible and does not invalidate the synthetic source acceptance.
2. Continue the separately owned MO2 read-adapter work only after its own source and Windows acceptance; it was not part of PR #9.
3. Extend installed-state comparison only through a separately accepted adapter or richer UMM evidence; do not begin transactions yet.
4. Keep install, upgrade, disable, rollback and shared-resource leases behind the later transaction state-machine gate.

## Do not infer

A registered instance is not installation health. UMM manifest presence is not enabled state, load order, runtime compatibility or gameplay acceptance. A goal plan is not a durable job, proposal, approval or execution. Canonical `main` adoption is not production installation, product-client acceptance or permission to mutate a game or manager.
