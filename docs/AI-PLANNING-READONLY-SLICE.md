# Read-only planning and UMM instance slice — 0.27.0-preview.1

**Source status:** runtime-tested product commit `e454433e81e067b1f11267a3cac18081b60512f8`; acceptance/documentation commit `ab9c2cdf32dd9d361aa4273aca6e10a168e864d8`; adopted into canonical `main` through PR #9 as `ef38d94be4fb4847cbbeda5f8fe41455b267aeaa`. Historical R8, R5 and R4 product commits remain preserved.

**Acceptance:** bounded synthetic Windows/UMM and external stdio PASS; real-folder and production acceptance remain separate.

R9 is the current correction boundary. It preserves the same read-only
architecture while closing embedded short/punctuated absolute-path cases and
making filtered instance pagination depend only on matching records from one
bounded registry snapshot. Its 715-file candidate passed 388 Windows tests, 34
external stdio checks and an independent 394-file source-package readback. R8,
R5, R4 and the bounded R6/R7 attempts remain preserved in the dated acceptance
record; none establishes a real game or transaction.

## Purpose

This slice extends the adopted AI Efficiency Foundation with four modern,
multi-game read tools:

- `game_tools_instances`
- `game_tools_instance_inspect`
- `game_tools_plan_goal`
- `game_tools_conflicts`

The legacy MCP tool list is unchanged. No approval, execution, arbitrary path,
download, game launch, input, capture, background listener, or manager write was
added.

## Ownership

| Concern | Existing or new bounded owner |
|---|---|
| Game scope and current support/recipe revisions | `GameToolGameWorkspaces` |
| Private local installation identity | `GameToolInstances` |
| UMM marker and manifest read | existing `game_mod_ops.managers.inspect_game` |
| Immutable mod-plan preview | existing `GameToolAutomation` / recipe service |
| Goal DAG and declared ownership/conflict graph | `GameToolPlanning` |
| Keybind instances and effective native-field ownership | existing `GameToolKeybindIntegration` |
| Approval, job execution and receipts | existing local owners; not widened here |

Game-installation identity and keybind-instance identity remain separate schemas.
The planning graph may point to both owners, but it does not merge their records
or grant one owner authority over the other.

## Private instance registry

A local operator may register one exact game directory through
`Game-Instances.py register --confirm`. Registration:

1. resolves the current reviewed support definition;
2. accepts only the UMM adapter in this slice;
3. verifies the selected executable, loader markers and UMM manifest inventory;
4. rejects links, duplicate directory ownership and conflicting instance IDs;
5. writes one private metadata record under the existing Game Tools data root;
6. writes nothing to the game, manager, save, input profile or graphics stack.

Modern AI tools receive only an opaque `instance_id`, game/manager metadata and
revisions. They cannot register an instance or provide `path`, `game_dir`,
`root`, or `directory` arguments. Public results do not contain the private
filesystem path.

## UMM read adapter contract

The accepted adapter reads only:

- the explicitly registered executable marker;
- reviewed loader markers;
- `Mods/<folder>/Info.json`;
- the existence of the manifest-declared assembly inside the same mod folder.

It does not import or execute Python, DLLs, scripts or manager plugins. It does
not infer enabled state, load order, runtime compatibility or gameplay success.
A comparison means only **planned identity versus observed manifest identity**.
Unknown files, duplicate IDs, missing assemblies and manifest dependencies stay
visible as warnings or blockers.

Other existing folder inspectors are not silently promoted. A non-UMM
registration returns `ADAPTER_ACCEPTANCE_PENDING` until that adapter receives a
separate conformance and acceptance pass.

## Goal plan DAG

`game_tools_plan_goal` supports bounded goals:

- `prepare-game`
- `review-mods`
- `inspect-installed`
- `compare-intended-installed`
- `review-keybinds`

Each deterministic plan contains explicit nodes, owners, dependencies, read
sets, blockers and empty write sets. A plan is a preview only: it creates no job,
proposal or durable plan record and performs no inventory scan by itself.
Installed inspection remains a separate explicit read using a registered
instance ID.

## Ownership and conflict graph

`game_tools_conflicts` combines only declared evidence:

- recipe dependency edges;
- manager and mod-layout ownership;
- exact UMM manifest identities when configured;
- declared alternative conflicts;
- the separate keybind owner when available;
- optional observed UMM manifests from one explicitly named registered instance.

It never chooses an automatic winner. Equal or duplicate ownership becomes a
blocker. An unselected alternative remains a real graph node rather than a
phantom edge. Missing exact manifest identity remains advisory and prevents a
conclusive installed match.

The source-level test and boundary receipt is
[`AI-PLANNING-READONLY-VALIDATION.json`](AI-PLANNING-READONLY-VALIDATION.json).
Candidate R9 then passed the separate [Windows, source-package and external
stdio acceptance](AI-PLANNING-READONLY-WINDOWS-ACCEPTANCE-2026-10-14.md): 715
payloads matched the current product commit after Git clean filters, 13 Windows
suites ran 388 tests, exported packaging passed without skips, and five synthetic
game directories remained byte-identical while embedded private metadata was
refused without echo and filtered pagination stayed accurate. The earlier R8,
R5/R4 boundaries and bounded R6/R7 attempts are retained in that acceptance
record. A real
registered game folder, specific product UI and production transactions remain
unaccepted.

## Canonical source adoption

After independent exact-head review, PR #9 was merged with a merge commit so the
runtime-tested product boundary and the later acceptance/documentation boundary
remain separately identifiable. The merge commit is
`ef38d94be4fb4847cbbeda5f8fe41455b267aeaa`; its parents are the prior canonical
base `108cb332b874583776c7a9cb1a19ce67c8cc96e5` and reviewed head
`ab9c2cdf32dd9d361aa4273aca6e10a168e864d8`. This changes source publication state
only. It does not expand Windows/runtime acceptance, install production, inspect a
real game or manager, or authorize any write transaction.

## Result and safety boundaries

- Tool results use the existing typed AI result envelope.
- Goal plans additionally validate against
  `schemas/game-tools-goal-plan.schema.json`.
- `game_tools_status_batch` may inspect registered instance metadata but does
  not scan its folder.
- Unknown effects continue to prohibit automatic retry.
- Local registration metadata is not proof of installation health.
- UMM manifest observation is not runtime, gameplay or physical-device
  acceptance.
- Production installation, install/upgrade/disable/rollback transactions,
  manager writes and arbitrary discovery remain later gated work.
