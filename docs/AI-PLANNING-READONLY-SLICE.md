# Read-only planning and UMM instance slice — 0.27.0-preview.1

**Source status:** tested product commit `cd444009d063b27894bf8e399d517670b30ebc47`

**Acceptance:** bounded synthetic Windows/UMM and external stdio PASS; real-folder and production acceptance remain separate.

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
Candidate R4 then passed the separate [Windows, source-package and external
stdio acceptance](AI-PLANNING-READONLY-WINDOWS-ACCEPTANCE-2026-10-14.md): 715
payloads matched, 13 Windows suites ran 370 tests, exported packaging passed
without skips, and the synthetic UMM directory remained byte-identical. A real
registered game folder, specific product UI and production transactions remain
unaccepted.

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
