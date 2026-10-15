# Continuation checkpoint — MO2 read adapter 0.28.0-preview.1

## Current durable base

- AI Efficiency Foundation 0.26 and read-only planning 0.27 were independently reviewed and adopted through their existing PR and adoption records.
- The MO2 slice starts from exact canonical main `290bea7983ccca50073c5f45ce44337cacafc32a` on `task/mo2-read-adapter-reconcile-20261015`.
- The existing proposal mailbox, approval controller, jobs, journal, game-support, instance and keybind owners remain unchanged.

## Current task-branch candidate

- Tested product commit: `c0809f7ac99a776390e131859991105c2f4c88f4`; later acceptance documentation is separate.
- Unified Game Tools `0.28.0-preview.1`; Workspaces `0.2.2`; Instance Registry and Planning `0.2.0`; MO2 Read `0.2.0`; Unified Updater `0.2.1`.
- MO2 reuses the adopted `GameToolInstances` owner through an additive private schema-2 binding; UMM schema-1 records remain readable and unchanged.
- Local `register-mo2 --confirm` is the only path-bearing route. Modern and legacy MCP gain no registration or arbitrary-path argument.
- `game_tools_instance_inspect` reads exact registered MO2 declarations. MO2 comparison/conflict observation remains blocked by `ADAPTER_COMPARISON_PENDING` before private profile reads.
- R5 passed synthetic Windows, source-package and external stdio acceptance: 344 tests, 73 export contracts, 400 source files, 7/7 extracted-package checks and 29 MCP checks.
- Read [the exact MO2 contract](MO2-READ-ADAPTER.md), [validation record](MO2-READ-ADAPTER-VALIDATION.json) and [Windows acceptance](MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.md).

## Adopted 0.27 source boundary

- Exact runtime-tested product commit: `e454433e81e067b1f11267a3cac18081b60512f8`; later acceptance/documentation commit: `ab9c2cdf32dd9d361aa4273aca6e10a168e864d8`.
- PR #9 passed independent exact-head review and merged into canonical `main` as merge commit `ef38d94be4fb4847cbbeda5f8fe41455b267aeaa`; historical R8, R5 and R4 product commits remain preserved.
- Candidate R9: 715 payload files, aggregate SHA-256 `da3e7f3de4c106cc24ba0b7b3be01ea85898fede9aa348b90d6953f18595d9d1`.
- Windows gate: 13/13 suites, 388 tests, 381 passes and seven explicit environment/package skips; no timeout or automatic retry.
- Real source export: 394 files, ZIP SHA-256 `369a396b00f845a74fbaa7abfe8c004bf5a0d64becd24ea003cd575e79b6fc30`; exported packaging reran 7/7 with zero skips.
- External stdio: modern exposed the four read-only planning tools with exact read effects; legacy remained unchanged. Five synthetic game trees stayed byte-identical, one corrupt filename remained opaque, embedded credential/Windows/short POSIX paths were refused without echo, and filtered cross-game pagination stayed accurate across 34 checks.
- R1–R8 and the isolated R9 system-context copy remain preserved with their exact boundaries; none was overwritten or presented as the current-user R9 pass.

## Current capability boundary

- Opaque private game-instance identities are registered only through explicit local operator routes.
- Adopted UMM inspection remains unchanged. The 0.28 candidate additionally reads exact registered MO2 `modlist.txt`/`plugins.txt` declarations and bounded markers without manager API, VFS or code loading.
- Goal-plan DAGs remain deterministic read-only previews. MO2 inspection is available; MO2 planned-versus-installed comparison is not.
- The same four planning tools remain limited to the modern multi-game MCP surface. No new public tool name is added, and legacy payload shapes remain unchanged.
- No install, upgrade, disable, rollback, manager write, production profile or arbitrary discovery was added.

## Next safe stages

1. Commit the acceptance records separately from tested product commit `c0809f7ac99a776390e131859991105c2f4c88f4`.
2. Open a Draft PR and perform independent exact-head review before any merge.
3. Adopt only through a separate reviewed merge; do not treat publication as installation.
4. Optionally perform one separately authorized real-folder **read-only** acceptance; do not begin MO2 comparison or write transactions.

## Do not infer

A registered instance is not installation health. UMM manifests and MO2 declaration markers are not effective deployment, conflict winners, overwrite order, runtime compatibility or gameplay acceptance. A goal plan is not a durable job, proposal, approval or execution. A task-branch source candidate is not canonical adoption, production installation, client acceptance or permission to mutate a game or manager.
