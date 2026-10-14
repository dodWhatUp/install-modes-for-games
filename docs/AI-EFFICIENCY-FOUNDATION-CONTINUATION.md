# Continuation checkpoint — read-only planning 0.27.0-preview.1

## Current durable base

- AI Efficiency Foundation 0.26 was independently reviewed and merged into canonical `main` through PR #7, followed by its adoption record.
- Slice 2 started from exact main commit `108cb332b874583776c7a9cb1a19ce67c8cc96e5` on `task/ai-plan-readonly-slice2-20261014`.
- The existing proposal mailbox, approval controller, jobs, journal, game-support and keybind owners remain unchanged.

## Accepted task-branch source

- Current tested product commit: `dbed124f40e3d336baf49e7598c16f2d1b57189d`; historical R5 `f37a6e4ed6321c2cae6c928bc889d0ab49dc9c39` and R4 `cd444009d063b27894bf8e399d517670b30ebc47` product commits remain preserved.
- Candidate R8: 715 payload files, aggregate SHA-256 `4dc1cbd371b3376b0b987300ec132ccfbd719675617a3c7a78880397c71f7c83`.
- Windows gate: 13/13 suites, 385 tests, 378 passes and seven explicit environment/package skips; no timeout or automatic retry.
- Real source export: 394 files, ZIP SHA-256 `4e5bcd4caae7752270a1b29101f873b85a9692dd04abd8b5e0419130cba252d2`; exported packaging reran 7/7 with zero skips.
- External stdio: modern exposed the four read-only planning tools with exact read effects; legacy remained unchanged. Three synthetic UMM trees stayed byte-identical, one corrupt filename remained opaque, and credential/path metadata was refused without echo across 32 checks.
- R1–R5 and the bounded R6 export refusal, R7 framing failure, host-invocation refusals and first R8 checker-count mismatch remain preserved with their exact boundaries; none was overwritten or presented as the R8 pass.

## Current capability boundary

- Opaque private game-instance identities are registered only through an explicit local operator route.
- UMM is the first accepted read adapter. It reads reviewed executable/loader markers, `Info.json` and declared assembly presence without loading code or writing the game.
- Goal-plan DAGs and ownership/conflict graphs are deterministic read-only previews.
- Four new tools are limited to the modern multi-game MCP surface. The legacy tool list and payload shapes remain unchanged.
- No install, upgrade, disable, rollback, manager write, production profile or arbitrary discovery was added.

## Next safe stages

1. Refresh draft PR #9 with the exact R8 product and later documentation commit; keep it draft and do not merge automatically.
2. Optionally perform one separately authorized real-folder **read-only** acceptance. Its absence remains visible and does not invalidate the synthetic source acceptance.
3. After independent review, extend installed-state comparison only through another separately accepted read adapter or richer UMM evidence; do not begin transactions yet.
4. Keep install, upgrade, disable, rollback and shared-resource leases behind the later transaction state-machine gate.

## Do not infer

A registered instance is not installation health. UMM manifest presence is not enabled state, load order, runtime compatibility or gameplay acceptance. A goal plan is not a durable job, proposal, approval or execution. Task-branch publication is not `main` adoption or production installation.
