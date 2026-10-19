# System control center and request preflight

Date: 2026-10-19, Asia/Jerusalem. Priority: **P0 urgent development task**, requested by the user. Status: planned and ready for the first read-only development slice; no control service, model evaluator or migration is installed by this record. Project ID: `system-control-center`. Urgent task: [GitHub issue 12](https://github.com/dodWhatUp/install-modes-for-games/issues/12). Requirement owner: [GT-086 through GT-096](PORTABLE-WORKSPACE-REQUIREMENTS.json); related infrastructure: [portable workspace plan](PORTABLE-WORKSPACE-PLAN.md).

Build a program a person can use to understand and supervise the existing system: its architecture, source owners, instructions, triggers, permissions, devices, synchronization, changes and chat activity. Add a request preflight tool that explains what the current system supplies automatically, what a proposed request adds, what may activate, and the smallest clear wording that retains the user's intent. Keep these as two connected views in one application, backed by the existing owners.

The initial interface should work from explicit local/source snapshots without a paid model call. Later optional model-assisted interpretation or controlled behavioral evaluation needs its own credential, cost, runtime and test setup. The program remains useful when exact model behavior or hidden platform state is unavailable.

## Integrated execution and portable-workspace dependencies

The [integrated execution plan](INTEGRATED-SYSTEM-EXECUTION-PLAN.md) is the combined dependency and integration map: 60 integration points, 18 work packages and 108 checks. Use its [machine-readable packages](INTEGRATED-SYSTEM-WORK-PACKAGES.json) and the GT-to-package mapping in the [requirement ledger](PORTABLE-WORKSPACE-REQUIREMENTS.json). This makes control-center views consumers of the same source, resource, policy and receipt contracts as portable workspaces. It does not create a competing task master or import another project's implementation.

| Control-center slice | Work packages and required integration |
|---|---|
| U0 inventory | MCI-01 source/capability inventory and MCI-02 shared contracts |
| U1 human explorer | MCI-03 architecture, instruction and trigger navigation with exact source provenance |
| U2 overview | MCI-05 human device/sync/change/chat overview consuming MCI-08 receipts; MCI-12 exposes effective policy |
| U3 local source | MCI-06 local-source and Drive-link pilot, with MCI-02 resolution and MCI-13 access control |
| U4 request checks | MCI-04 static preflight consuming MCI-03 applicability, MCI-12 policy and current capability evidence |
| U5 optional evaluation | MCI-16 controlled model trials; separate credential, budget and isolated-tool acceptance |
| U6 central control | MCI-13 enrollment/roles, MCI-14 scoped operations through accepted MCI-10 transport, and MCI-18 integrated acceptance |

First deliver MCI-01 through MCI-04; MCI-05 can proceed from stable contract fixtures. U2/U4 may show known rules before policy editing exists, while edits and actions stay unavailable until their capability passes. U3 is a selected reversible pilot: keep historical Drive object links, source ownership and provider-specific semantics. U5 and remote operations do not delay a useful read-only architecture and preflight tool. GitHub tracks implementation acceptance; TickTick provides a private execution view using the same MCI identifiers. Neither task registration nor planning publication proves a running synchronizer, native-chat migration or model-prediction accuracy.


## Main user journeys

| User question | Useful answer |
|---|---|
| What changed while the computers worked? | A chronological overview of received, staged, merged, conflicted and applied changes with owners and revisions |
| What happened in these chats? | Goal, broad outcome, current blocker, changed artifacts and next boundary; selected source content on demand |
| Which rules apply here, and why? | A navigable instruction/source map with applicability, precedence evidence, freshness and overrides |
| What activates this behavior? | Trigger conditions, explicit invocation, automatic selection, confirmation/execution boundary, dependencies and recent observed examples |
| Can I keep the information on my computer? | Source availability, stable reference mapping, authorized access route, replicas and link-preservation status |
| Is this request enough? | Necessary details missing, defaults already supplied, ambiguous wording and a minimal-intent-preserving alternative |
| What would the model probably do? | Deterministic policy facts, conditional route estimates, observed evaluation results and clearly unknown behavior |
| Can I control another computer? | Available paired-host capabilities and target-side permission/health checks, separate from mere connectivity |

## One navigable control surface

Offer five views with a shared project/device/source selector: Overview, Architecture and rules, Activity, Sources and links, and Request check. Start with overview cards and a compact searchable list; reveal source detail, graph edges and advanced policy only when needed. Keep human readable text available alongside stable IDs. Preserve keyboard access, text scaling, narrow-window behavior and long source names.

Overview shows active devices/accounts, queued transfers, conflicts, recent changes and next decisions. Architecture and rules shows a dependency graph plus an equivalent accessible list: owner, service, instruction, skill, trigger, tool, data source, task and permission boundary. Activity shows relevant sync events, deployments, approvals and concise chat summaries, with filters for project/device/time/type. Sources and links shows ownership, availability, replicas, exact revision and access route. Request check compares the draft request with the effective observable context and recent evaluation evidence.

A central management computer or account can propose policy and inspect authorized status across devices. A workspace/project/device role model constrains what it can see or operate. Local exclusions and target approval survive central administration. Display requested, accepted and actually observed policy separately; a toggle in the control center is not proof that an offline device applied it.

## Reuse before building

The source survey distinguishes implemented code, documented interfaces, owner-reported work and missing functionality. It does not claim new runtime acceptance.

| Existing owner | Reusable part | Current evidence and missing part |
|---|---|---|
| Canonical toolkit `GameToolUserData.py` | Versioned selected-file packages, source drift checks, original bytes and new-copy restore | Local source inspected; not a multi-device replication or cloud engine |
| `GameToolJournal.py` and `GameToolCoordinator.py` | Operation evidence, bounded reads, local cooperative ownership and prefix recovery | Existing source/contracts; not distributed locking or remote execution |
| `GameToolAIKnowledge.py` | Manifest-verified bounded knowledge search/fetch and opaque revision-bound references | Source inspected; useful reader foundation, not an entire architecture scanner |
| `GameToolAIFoundation.py` and AI contracts | Continuation/change/status summaries, explicit evidence states and existing handles | Source inspected; no action replay, network daemon or universal chat reader |
| `GameToolAutomation.py` and Workbench owners | Existing requests, local approvals and named product operations | Reuse the task/approval master; do not build a competing queue |
| Separately owned personal system | Topic-first progressive retrieval, original source ownership and reversible handoff preparation | Readme/current-state/execution-plan source records read on 2026-10-19; bounded documentation evidence, not a fresh source/runtime audit or owner repin |
| Codex host features | Supported remote control, SSH projects and thread APIs | Official interfaces; exact product availability and paginated-history limitations remain capability-gated |

The personal-system source remains [Attempt2 at its existing branch](https://github.com/dodWhatUp/attempt-2-unified-personal-system/tree/codex/rebuild-stage3-20260920). Observed source blobs: `README.md` at `1139a8aef96e66b4d443288674ff6d7c995c427d`, `CURRENT_STATE.md` at `25b4cd73dc742daf0564749a65e1f5b757d1a5ff`, `integration/REBUILD_EXECUTION_PLAN.md` at `33038210565a84db18febf6d7f34429a549b5fe2`, and `AGENTS.md` at `fe080de394a8c3f5fdc13919037ce8a554a9b2e9`. Its documented local tests and pending integration statuses remain attributed to that owner. This project does not restart completed Pro intake or adopt Global/Sync/Research/Coding owners. Reference its existing readers and continuation protocols through a reviewed adapter.

## Architecture and instruction inventory

Register only selected roots, repositories and accessible account resources. Each record needs stable ID, kind, owner, exact locator/revision/hash, scope, applicable client/version, declared trigger, priority/precedence evidence, dependencies, allowed effects, freshness, and provenance. Keep original text with its owner and show bounded excerpts on demand. Do not turn a historical chat instruction into an active rule.

Distinguish configuration declared on disk, sources actually loaded into a session where observable, and behavior observed in a completed run. Inventory AGENTS files and overrides, selected skills and their invocation rules, MCP/tool capabilities, permissions, opted-in automations, memory/context files, project defaults, current user constraints and source-specific integration rules. Inaccessible platform instructions or memory remain unknown; never fabricate a comprehensive hidden prompt.

Represent trigger types explicitly: direct user invocation, file/path applicability, declared schedule, tool event, UI action and model-selected skill. A model-selected skill description is a selection cue, not a deterministic string-match rule. Record false-positive/false-negative examples and confidence. Precedence adapters must use actual client/runtime semantics and applicable instruction levels; a nearby project file cannot override higher-priority platform rules. A central policy cannot silently weaken destination restrictions.

The graph explains relationships such as reads, overrides, depends on, writes, asks approval, prepares and executes. The same rule can be active in one project and irrelevant in another. Show conflicts, duplicated defaults, stale sources and coverage gaps beside the relevant node. Follow a graph edge to its exact source, current version and observed evidence. Offer comparisons between device A, device B and a proposed configuration without activating it.

## Make the computer an information source

Separate content authority from its storage location. A logical resource ID maps to an owner, an exact revision, an authorized access route and optional verified replicas. The owner may be a local computer, a network share, Drive, Git or another connected source. Local private paths are device bindings, not public identifiers or universal cloud-chat links.

Three access modes need separate acceptance:

1. A local Codex/toolkit adapter reads selected files directly through existing bounded tools.
2. A paired remote device accesses an authorized host while that host is available.
3. A cloud chat uses an approved connector/MCP or deliberately published data gateway. Do not assume a local filesystem path or local-only stdio service can be reached by the cloud.

Keep on-demand content and small indexes separate. The central overview may retain authorized summaries and metadata while detailed documents, chat content and attachments stay at the owning host. Apply no-store and retention choices to summaries, indexes, embeddings and caches as well as original bytes. If the host is offline, show unavailable/stale or use an explicitly approved replica; do not silently substitute an old copy as current.

## Preserve existing links during a source change

Existing `drive.google.com` URLs identify Drive objects. They cannot be made to point directly to a local file merely by moving bytes or configuring this application. Keep old Drive objects and IDs while introducing a durable logical reference resolver for new links. A bridge/index file can direct a person to the resolver, but does not make every historical attachment, embedded link or third-party client follow it automatically.

Migration sequence: inventory inbound references and owners; assign stable IDs; map current Drive IDs/Git locators to those IDs; copy a selected pilot set without deleting originals; verify bytes and native document semantics; connect the host adapter; validate resolution from each required client; then choose ongoing mirroring or selected cutover. Keep a reversible mapping and fallback policy. Update references only in scopes the user owns and authorized for migration, with a diff and verification.

Native Google Docs/Sheets/Slides require special handling for export fidelity, comments, revisions, formulas and permissions; a binary copy does not reproduce provider semantics or a native URL. Deletion, access revocation, sharing changes, account changes and a missing host must each have explicit outcomes. Access-control equivalence must pass before a local source replaces a private cloud source. Current authorization is to plan and publish this design, not to move all Drive content or rewrite its existing links.

Later automation can maintain source indexes and approved replicas using scheduled or event-based jobs, health checks, bounded queues, conflict rules and receipts. A saved plan creates no schedule or always-on service. Enrollment, actual endpoints, authentication and retention need concrete acceptance before enabling that automation.

## Request preflight and behavior explanation

Input: the proposed request, intended outcome, selected project/device/account, observable active instructions, available tools, source revisions and relevant remembered preferences with provenance. Let the user exclude history and compare a fresh-session view. Baseline model knowledge and inaccessible account memory are not readable databases; mark them as unobserved influences.

Output should answer six questions briefly: what is already supplied, what this wording adds, what is ambiguous, which skills/tools or permissions may matter, which unnecessary wording can be removed, and what evidence supports the explanation. Suggest a rewrite only when it improves clarity or resolves an evidenced conflict. Preserve intent, exclusions, required detail, deliverables and permission boundaries; token count alone is not the quality objective. The user can keep the original. Preflight never submits the request or alters system instructions automatically.

Use three visibly distinct evidence classes:

- **Verified policy fact:** a configured route, declared hard exclusion, applicable source or available capability with exact evidence.
- **Conditional behavior estimate:** a likely skill/tool choice or model interpretation with assumptions and uncertainty.
- **Observed behavior:** an actual controlled test for the named runtime/model/context revision, with result and repeat count.

There is no guarantee of an exact future response or complete knowledge of what a model learned. Do not invent deterministic trigger certainty, access hidden chain-of-thought, or label a plausible narrative as a traced execution. A preflight explanation is concise user-facing reasoning, source references and observable results.

Examples of checks: detect repeated defaults such as response language already supplied by the project; distinguish a request to inspect from a request to apply; flag an unintended expansion from files to credentials; preserve necessary game/project/version names; identify when saying 'use the browser' unnecessarily narrows a better supported route. Removing words is optional and must not silently remove meaning. A phrase that is harmless in one context may change routing in another.

## Controlled behavior evaluation

Begin with static policy checks and authored fixtures. The optional evaluation harness compares the minimal request, the user's original and carefully justified variants on the same frozen task/context/tool set. Include negative controls, ambiguous requests, repeated instructions, direct skill invocation, stale memory, source changes and conflicting lower-priority instructions. Test whether the requested behavior occurs, not just whether a keyword appears.

Separate baseline conditions: current project configuration; accessible platform/client defaults with project personalization disabled where supported; and a fresh session without prior conversation. 'Model alone' is not a valid experimental label if platform instructions and tools are still present. Record the actual available controls and remaining unknowns. Never disable production safety or change the user's real configuration to manufacture a baseline.

Pin runtime/model settings, instruction/source hashes, tools, fixture and evaluation version. Repeat stochastic cases and report counts with uncertainty. Score task correctness, necessary clarification, source use, unintended actions, tool/skill selection, scope preservation, latency and tokens where measured. Compare validation and held-out cases; avoid optimizing for fewer words while reducing correctness. Refresh after relevant model, skill, instruction, tool or account changes.

Model-assisted checks and trials may cost money or execute tools. Later implementation must use the OpenAI key/setup workflow for any API-backed component, explicit budgets and isolated tool fixtures. Default tests do not send real messages, change remote files or run production commands. Record only observable traces and allowed summaries. No success percentage is claimed until the corresponding evaluations run.

## Urgent delivery sequence

| Slice | Deliverable | Acceptance |
|---|---|---|
| U0 | Read-only source/owner and capability inventory; reuse map | Selected sources trace to exact revisions; unobserved state stays unknown |
| U1 | Human-readable architecture, instruction and trigger explorer | Search, source links, applicability, conflicts and accessible graph/list navigation work on fixtures |
| U2 | Device/sync/change/chat overview | Last-known versus live status distinct; summaries do not expose unrequested private content |
| U3 | Stable source resolver and local-source pilot | Pilot references resolve on required clients; original Drive URLs remain valid; offline fallback labeled |
| U4 | Static request preflight with minimal-rewrite comparison | Defaults, ambiguity and permission effects explained; original wording preserved unless accepted |
| U5 | Optional controlled model evaluation | Credential/cost gate and pinned contexts; repeated results, uncertainty and no production effects |
| U6 | Central policy and scoped remote actions | Target-side authorization, revocation, cancellation, offline behavior and result receipts accepted |

U0/U1/U4 are the urgent first development unit. U2 can reuse staged transfer receipts before a network synchronizer exists. U3 starts with a small selected pilot. U5/U6 are capability-gated extensions, not conditions for a useful read-only program. Keep the portable workspace and control-center projects distinct in the backlog but share registry, revisions, readers, evidence, policies and approvals.

Use the compact interface foundation and current isolated-lab acceptance for later compatible GUI work. Test long labels, keyboard navigation, search, missing sources, conflicting rules, no-results states, stale views, text scaling, cancellation and read-only operation. A source graph does not prove runtime execution; a screenshot does not prove multi-host acceptance.

## Completion and current next action

Plan-level completion: this project is recorded as urgent with stable requirements and a first development boundary. Implementation is not claimed. Preserve native Codex/session limitations, original source owners and current local authorization. Next: implement the bounded U0 inventory model and U1/U4 fixture-driven read-only prototype before introducing cloud cutover, automatic sync, paid evaluations or remote execution.

Official design references: [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [remote host features](https://learn.chatgpt.com/docs/remote-connections), [systematic skill evaluation](https://developers.openai.com/blog/eval-skills), and [instruction/context review](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra). These support source discovery, available interfaces and evaluation practice; the proposed control center and resolver are new project work.
