# Continuation checkpoint — read-only planning 0.27.0-preview.1

## Current durable base

- AI Efficiency Foundation 0.26 was independently reviewed and merged into canonical `main` through PR #7, followed by its adoption record.
- Slice 2 started from exact main commit `108cb332b874583776c7a9cb1a19ce67c8cc96e5` on `task/ai-plan-readonly-slice2-20261014`.
- The existing proposal mailbox, approval controller, jobs, journal, game-support and keybind owners remain unchanged.

## Accepted task-branch source

- Current tested product commit: `f37a6e4ed6321c2cae6c928bc889d0ab49dc9c39`; historical R4 product commit `cd444009d063b27894bf8e399d517670b30ebc47` remains preserved.
- Candidate R5: 715 payload files, aggregate SHA-256 `fbc07c7eed3319a9b778f76a11660609e8374107510e4f5b9493d9f079a77710`.
- Windows gate: 13/13 suites, 374 tests, 367 passes and seven explicit environment/package skips; no timeout or automatic retry.
- Real source export: 394 files, ZIP SHA-256 `e96ad5d012f03b1ee09a716b5e979d1385feaabb5d7bca7c30baa6ee81b6e3c9`; exported packaging reran 7/7 with zero skips.
- External stdio: modern exposed the four read-only planning tools with exact read effects; legacy remained unchanged. One synthetic UMM fixture and its game tree stayed byte-identical.
- R1–R4, the isolated mixed-copy attempt and the first line-ending readback remain preserved with their exact dated boundaries; none was overwritten or presented as the R5 pass.

## Current capability boundary

- Opaque private game-instance identities are registered only through an explicit local operator route.
- UMM is the first accepted read adapter. It reads reviewed executable/loader markers, `Info.json` and declared assembly presence without loading code or writing the game.
- Goal-plan DAGs and ownership/conflict graphs are deterministic read-only previews.
- Four new tools are limited to the modern multi-game MCP surface. The legacy tool list and payload shapes remain unchanged.
- No install, upgrade, disable, rollback, manager write, production profile or arbitrary discovery was added.

## Next safe stages

1. Refresh draft PR #9 with the exact R5 product and later documentation commits; keep it draft and do not merge automatically.
2. Optionally perform one separately authorized real-folder **read-only** acceptance. Its absence remains visible and does not invalidate the synthetic source acceptance.
3. After independent review, extend installed-state comparison only through another separately accepted read adapter or richer UMM evidence; do not begin transactions yet.
4. Keep install, upgrade, disable, rollback and shared-resource leases behind the later transaction state-machine gate.

## Do not infer

A registered instance is not installation health. UMM manifest presence is not enabled state, load order, runtime compatibility or gameplay acceptance. A goal plan is not a durable job, proposal, approval or execution. Task-branch publication is not `main` adoption or production installation.
