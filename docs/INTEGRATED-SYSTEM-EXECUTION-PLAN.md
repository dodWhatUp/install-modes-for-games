# Integrated development plan and implementation checklist

Date: 2026-10-19, Asia/Jerusalem. Status: planning integration completed; implementation remains planned. Parent tracker: [GitHub issue 12](https://github.com/dodWhatUp/install-modes-for-games/issues/12).

The portable workspace and the urgent human control center form one coordinated development program with shared contracts and separately deliverable capabilities. This plan integrates the original SSD/transfer workflow with multiple computers, storage topologies, cloud exchange, central policies, scoped remote operation, human architecture/trigger navigation, local information sources, stable links and request preflight.

## What was integrated and what needed completion

The preceding publication at `e174ba6fe6db0edc70725daf1d9255172ac97b01` already linked both plans and recorded all 36 requirements GT-061 through GT-096. It had two broad projects and one urgent GitHub issue. Its R0–R6 and U0–U6 sequences did not yet provide a single task dependency map, per-requirement execution coverage, shared event/record handoffs or TickTick task mirrors.

This continuation completes that planning integration through 18 stable work packages, 108 implementation checklist items, requirement-to-task coverage, cross-workstream dependencies, an explicit task ownership model and verified task publication. No software capability becomes implemented merely because its plan or task is complete.

The original [portable workspace design](PORTABLE-WORKSPACE-PLAN.md) retains storage and Codex continuity detail. The [control center design](SYSTEM-CONTROL-CENTER-PLAN.md) retains human navigation and request-evaluation detail. [Machine-readable work packages](INTEGRATED-SYSTEM-WORK-PACKAGES.json) own the checklist/task mapping. [Requirements](PORTABLE-WORKSPACE-REQUIREMENTS.json) retain the original stable GT IDs.

## Shared architecture and implementation handoffs

| Shared contract | Required fields or meaning | Producers and consumers |
|---|---|---|
| ResourceReference | Stable ID, owner, exact revision, content class, availability and private per-device bindings | Registry MCI-02; resolver MCI-06; vault MCI-07; all source readers |
| SourceInstructionRecord | Locator/hash, applicable client/scope, declared trigger, observed-load state, precedence evidence and freshness | Inventory MCI-01; explorer MCI-03; preflight MCI-04 |
| CapabilityRecord | Device/account/project scope, supported route, exact version, acceptance status and limitations | Inventory MCI-01; roles MCI-13; continuity MCI-15; companion MCI-17 |
| CheckpointManifest | Workspace/replica IDs, parents, content objects, tombstones, hashes, producer format and privacy | Vault/package MCI-07/08; merge MCI-09; transports MCI-10/11 |
| PolicyDecision | Source/destination, content/capability scope, rule revision, allowed effects, timing, context depth and explanation | Policy MCI-12; roles MCI-13; transports, resolver, remote operation and overview |
| OperationRequest and Receipt | Operation ID, source/target, expiry, expected revision, approval boundary, outcome, uncertainty and cancellation | Remote MCI-14 and existing named-operation owner; human overview MCI-05 |
| ActivitySummary | Goal, outcome, changed artifacts, blocker, source revision, evidence class, missing coverage and retention | Existing journal/continuation readers; overview MCI-05; authorized context readers |
| ContextPacket | Selected source references, scope, freshness, omissions, next boundary and permitted exposure level | Continuity MCI-15; policy MCI-12; request check MCI-04 |
| PreflightResult | Original intent, supplied defaults, ambiguities, conditional routes, minimal alternative and evidence | Preflight MCI-04; optional evaluation MCI-16; human review |
| WorkPackageReference | Stable MCI/GT IDs, task status owner, dependency IDs, acceptance, public issue and private task mirror | This plan/GitHub task tracking; TickTick execution view |

These are proposed versioned contracts. Reuse existing schemas and format owners where equivalent; design an additive adapter where they are not equivalent. Keep business logic in shared services. A renderer or transport must not invent a second registry, approval controller or operational task queue.

The operational sequence is **receive → verify → stage → adopt → index → expose selected context**. Each transition has its own receipt and policy. Receiving a file does not apply it, applying a file does not make a running model reread it, and exposing a summary does not authorize execution. The overview explains these distinctions. The request checker reads the selected observable context and policy snapshot; it never promises an exact future model response.

## Extended integration coverage

1. Preserve adopted source 0.27, independent source masters, current profiles and prior acceptance.
2. Keep durable data separate from program/runtime releases.
3. Default managed project files to a selected non-system internal or external drive.
4. Give workspaces, projects, devices, replicas, resources and tasks stable identities.
5. Rebind roots across drive letters, usernames, operating systems and mounts.
6. Detect duplicate vault clones and conflicting source identities.
7. Preserve credentials, local permissions and live runtime databases under their native owners.
8. Record actual managed output coverage and unsupported host-local outputs.
9. Create consistent, versioned checkpoints with parent ancestry.
10. Support explicit handover by moving the active data drive.
11. Support complete seed packages and incremental transfer files.
12. Use one manifest/receipt protocol across storage transports.
13. Support independent local replicas for concurrent work.
14. Merge text through common ancestry and structured records through their owner.
15. Preserve binary, rename, same-field and deletion conflicts.
16. Retain tombstones until replica acknowledgement and retention rules permit removal.
17. Extend acknowledgement, retirement and reconciliation to N devices.
18. Support shared, split, replicated, cloud and hybrid storage.
19. Exchange immutable data through network shares while active databases remain local.
20. Add authenticated resumable direct-network transfers.
21. Add opt-in provider adapters and verify cloud revisions, quotas and permissions.
22. Treat local/source authority, cache freshness and availability independently.
23. Separate transfer cadence, adoption timing, index refresh and context exposure.
24. Configure each source-to-destination direction and content class independently.
25. Preserve local hard exclusions when a central policy is proposed.
26. Explain effective policy by account, workspace, project, device and capability.
27. Separate viewer, contributor, operator and policy-administrator roles.
28. Handle pairing, revocation, expiry, missing hosts and stale writer generations.
29. Reuse existing local approvals and typed operation owners for remote actions.
30. Distinguish existing-host control, execution handoff, file transfer and remote desktop input.
31. Provide source-linked continuation packets when native chat transfer is unsupported.
32. Verify exact session identity separately from lineage-preserving forks or new chats.
33. Accept legacy/paginated history, attachments, later turns and restart/return transfer separately.
34. Keep a portable desktop/CLI companion conditional on actual host acceptance.
35. Show devices, changes, transfers, conflicts and adoption in a human-readable overview.
36. Summarize chat goals, outcomes, blockers and changed files by default.
37. Fetch detailed chat content and source bytes only when requested and authorized.
38. Apply no-store and retention policy to indexes and summaries as well as originals.
39. Navigate architecture, source owners, instructions, triggers and dependencies.
40. Distinguish declared rules, observed loading, actual behavior and inaccessible context.
41. Expose conflicts, duplicated defaults, stale references and coverage gaps.
42. Support selected local information sources through separately accepted client access routes.
43. Map stable logical resource IDs to Drive/Git identifiers and local bindings.
44. Preserve original Drive objects and URLs during a reversible pilot.
45. Verify native Google document semantics and access equivalence before any cutover.
46. Inspect a request before submission for ambiguity and unnecessary scope.
47. Identify defaults already supplied by observable project/session context.
48. Suggest minimal wording while preserving the user's intent and constraints.
49. Distinguish verified policy facts, conditional estimates and observed evaluations.
50. Compare original/minimal requests using frozen, repeated and held-out tests when enabled.
51. Pin model/runtime/context/tool versions and measure quality as well as cost where available.
52. Keep optional API evaluation behind credential, budget and isolation gates.
53. Offer keyboard-accessible compact views with cancellation, disclosure and visible active policy.
54. Verify actual multi-host behavior and granular restore independently from source or hash checks.
55. Keep implementation completion separate from registering tasks or publishing plans.
56. Track the urgent read-only core first, with later infrastructure dependencies explicit.
57. Link each work package to GT requirements, GitHub and a private TickTick execution view.
58. Preserve existing unrelated tasks and do not invent due dates, recurrence or automatic dispatch.
59. Keep old immutable Drive packages as historical snapshots and use Git's current plan as the updated development owner.
60. Record omissions, unsupported optional routes and the next evidence boundary before release.

## Execution order and work that can overlap

**Urgent core:** MCI-01 → MCI-02 → MCI-03 → MCI-04. MCI-05 can begin after MCI-02 using authored or existing receipts while network implementation is pending. These five tasks retain P0 priority.

**Storage lane:** MCI-07 → MCI-08 → MCI-09. MCI-10 and MCI-11 follow the merge, policy and authorization contracts, not merely a working file copy.

**Policy and trust lane:** MCI-12 and MCI-13 can develop after their declared source/registry dependencies. MCI-06 requires source identity, overview and authorization before an authorized local-source pilot. MCI-14 requires accepted networking, policy and destination permissions.

**Codex lane:** MCI-15 investigates continuation after capability/package/security prerequisites. MCI-17 is a separately gated optional portable-runtime branch. Their unsupported routes do not block files/context continuity.

**Behavior and release lane:** MCI-16 follows static preflight and is an optional model-assisted evaluation extension. MCI-18 qualifies the integrated base. It records MCI-16/17 results if enabled, or explicitly excluded/unsupported status; it must not claim an untested optional capability.

Parallel development means independent scoped work on owned modules. It does not authorize spawning chats, dispatching agents, starting network services or running remote operations from task text.

## Work package index

| ID | Priority | Work package | GitHub | Prerequisites |
|---|---|---|---|---|
| MCI-01 | P0 | [Inventory source owners, existing components and device capabilities](#mci-01) | [#13](https://github.com/dodWhatUp/install-modes-for-games/issues/13) | None |
| MCI-02 | P0 | [Define shared workspace, resource, revision and event contracts](#mci-02) | [#14](https://github.com/dodWhatUp/install-modes-for-games/issues/14) | MCI-01 |
| MCI-03 | P0 | [Build the human architecture, instruction and trigger explorer](#mci-03) | [#15](https://github.com/dodWhatUp/install-modes-for-games/issues/15) | MCI-01, MCI-02 |
| MCI-04 | P0 | [Build static request preflight and minimal wording comparison](#mci-04) | [#16](https://github.com/dodWhatUp/install-modes-for-games/issues/16) | MCI-02, MCI-03 |
| MCI-05 | P0 | [Build human device, synchronization, change and chat overview](#mci-05) | [#17](https://github.com/dodWhatUp/install-modes-for-games/issues/17) | MCI-02 |
| MCI-06 | P1 | [Pilot local information sources and preserve existing Drive links](#mci-06) | [#18](https://github.com/dodWhatUp/install-modes-for-games/issues/18) | MCI-02, MCI-05, MCI-13 |
| MCI-07 | P1 | [Implement managed storage on non-system internal or external drives](#mci-07) | [#19](https://github.com/dodWhatUp/install-modes-for-games/issues/19) | MCI-02 |
| MCI-08 | P1 | [Implement checkpoints, move-drive handover and full or delta packages](#mci-08) | [#20](https://github.com/dodWhatUp/install-modes-for-games/issues/20) | MCI-02, MCI-07 |
| MCI-09 | P1 | [Implement independent parallel branches and N-device conflict reconciliation](#mci-09) | [#21](https://github.com/dodWhatUp/install-modes-for-games/issues/21) | MCI-08 |
| MCI-10 | P1 | [Implement network-share and authenticated peer transfer adapters](#mci-10) | [#22](https://github.com/dodWhatUp/install-modes-for-games/issues/22) | MCI-09, MCI-12, MCI-13 |
| MCI-11 | P1 | [Implement opt-in cloud and hybrid storage adapters](#mci-11) | [#23](https://github.com/dodWhatUp/install-modes-for-games/issues/23) | MCI-09, MCI-12, MCI-13 |
| MCI-12 | P1 | [Implement independent directional scope, cadence, adoption and context policies](#mci-12) | [#24](https://github.com/dodWhatUp/install-modes-for-games/issues/24) | MCI-02, MCI-03 |
| MCI-13 | P1 | [Implement centralized roles, device enrollment and local authorization](#mci-13) | [#25](https://github.com/dodWhatUp/install-modes-for-games/issues/25) | MCI-02 |
| MCI-14 | P1 | [Implement scoped remote Codex and named-operation controls](#mci-14) | [#26](https://github.com/dodWhatUp/install-modes-for-games/issues/26) | MCI-10, MCI-12, MCI-13 |
| MCI-15 | P1 | [Implement honest Codex continuity and native-session feasibility](#mci-15) | [#27](https://github.com/dodWhatUp/install-modes-for-games/issues/27) | MCI-01, MCI-08, MCI-13 |
| MCI-16 | P2 | [Build optional controlled model behavior and prompt-quality evaluation](#mci-16) | [#28](https://github.com/dodWhatUp/install-modes-for-games/issues/28) | MCI-04 |
| MCI-17 | P2 | [Decide and implement the optional portable Codex companion](#mci-17) | [#29](https://github.com/dodWhatUp/install-modes-for-games/issues/29) | MCI-01, MCI-07, MCI-15 |
| MCI-18 | P1 | [Run integrated storage, control-center and recovery release acceptance](#mci-18) | [#30](https://github.com/dodWhatUp/install-modes-for-games/issues/30) | MCI-05, MCI-06, MCI-08, MCI-09, MCI-10, MCI-11, MCI-12, MCI-13, MCI-14, MCI-15 |

## Detailed implementation checklist

Each item below is planned and unchecked. Task registration and plan publication are separate from implementation evidence.

### MCI-01

Implementation tracker: [GitHub #13](https://github.com/dodWhatUp/install-modes-for-games/issues/13). Private TickTick mirror: registered under the same MCI ID.

**Inventory source owners, existing components and device capabilities** · P0 · Phases R0, U0.

Requirements: GT-079, GT-080, GT-093, GT-096. Dependencies: None.

- [ ] Record exact source owners, commits, versions and acceptance receipts for toolkit and personal-system components.
- [ ] Identify reusable registry, reader, journal, approval and handoff code without adopting an independent source master.
- [ ] Inventory each selected device OS, filesystem, runtime and reachable client; mark missing devices unknown.
- [ ] Classify every capability as implemented source, fixture-tested, installed, observed, planned or unsupported.
- [ ] Record current Codex history formats and runtime-portability constraints without copying credentials or production databases.
- [ ] Publish a source-bound capability matrix and the next smallest safe implementation slice.

### MCI-02

Implementation tracker: [GitHub #14](https://github.com/dodWhatUp/install-modes-for-games/issues/14). Private TickTick mirror: registered under the same MCI ID.

**Define shared workspace, resource, revision and event contracts** · P0 · Phases R1, U0.

Requirements: GT-062, GT-075, GT-079, GT-082. Dependencies: MCI-01.

- [ ] Define stable workspace, resource, device, replica, project and task-reference identities independently of paths.
- [ ] Specify versioned resource references, source records, checkpoint manifests, policy decisions and operation receipts.
- [ ] Map logical IDs to private local roots, source owners, revisions, authoritative locations and permitted replicas.
- [ ] Define one event progression from receipt through verification, staging, adoption, indexing and context exposure.
- [ ] Preserve unknown fields, existing native owners and old supported formats through explicit additive adapters.
- [ ] Validate schema, size bounds, stale revisions, duplicate IDs, clone detection and inaccessible-source behavior.

### MCI-03

Implementation tracker: [GitHub #15](https://github.com/dodWhatUp/install-modes-for-games/issues/15). Private TickTick mirror: registered under the same MCI ID.

**Build the human architecture, instruction and trigger explorer** · P0 · Phases U1.

Requirements: GT-078, GT-087. Dependencies: MCI-01, MCI-02.

- [ ] Inventory applicable AGENTS files, overrides, skills, declared triggers, tool capabilities and accessible preferences.
- [ ] Separate declared rules, sources actually loaded where observable, observed execution and inaccessible context.
- [ ] Resolve scope and precedence using the selected client version without weakening higher-priority instructions.
- [ ] Provide compact search, dependency graph and accessible list views with exact source and freshness links.
- [ ] Explain conflicts, repeated defaults, historical instructions and probabilistic skill-selection cues.
- [ ] Test keyboard navigation, long names, narrow layouts, missing sources, cancellation and stale-source refusal.

### MCI-04

Implementation tracker: [GitHub #16](https://github.com/dodWhatUp/install-modes-for-games/issues/16). Private TickTick mirror: registered under the same MCI ID.

**Build static request preflight and minimal wording comparison** · P0 · Phases U4.

Requirements: GT-071, GT-090, GT-092. Dependencies: MCI-02, MCI-03.

- [ ] Accept a draft request, intended outcome and selected observable project/device context without submitting it.
- [ ] Identify defaults already supplied, missing necessary details, ambiguity and unintended expansion of scope.
- [ ] Explain likely skills, tools, permissions and source needs as conditional estimates with citations.
- [ ] Compare original and minimal wording while retaining intent, exclusions, deliverables and action boundaries.
- [ ] Clearly distinguish verified policy facts, untested estimates and actual observed behavior; keep hidden model state unknown.
- [ ] Test positive, negative and ambiguous fixtures; preserve the original draft and require deliberate acceptance of a rewrite.

### MCI-05

Implementation tracker: [GitHub #17](https://github.com/dodWhatUp/install-modes-for-games/issues/17). Private TickTick mirror: registered under the same MCI ID.

**Build human device, synchronization, change and chat overview** · P0 · Phases U2.

Requirements: GT-086, GT-094. Dependencies: MCI-02.

- [ ] Project existing receipts and authored event fixtures into one human-readable activity timeline.
- [ ] Show device availability, last-known freshness, transfer, staging, conflict, adoption and next-decision states.
- [ ] Summarize chat goals, outcomes, blockers, changed artifacts and continuation boundaries with source provenance.
- [ ] Fetch full conversation content and attachment bytes only when specifically requested and authorized.
- [ ] Apply no-store, retention and access choices to summaries, indexes and caches as well as originals.
- [ ] Verify accessible filtering, missing content, stale devices, unknown operations and consistent status labels.

### MCI-06

Implementation tracker: [GitHub #18](https://github.com/dodWhatUp/install-modes-for-games/issues/18). Private TickTick mirror: registered under the same MCI ID.

**Pilot local information sources and preserve existing Drive links** · P1 · Phases U3.

Requirements: GT-088, GT-089, GT-094. Dependencies: MCI-02, MCI-05, MCI-13.

- [ ] Inventory selected resource owners and existing Drive/Git references before any pilot source change.
- [ ] Implement a stable logical-reference resolver with revision, availability and private local-binding information.
- [ ] Provide separately tested local, paired-host and approved cloud-client read routes; do not assume cloud access to local paths.
- [ ] Retain original Drive object IDs and URLs while verifying a small authorized local-source replica.
- [ ] Test access-control equivalence, native Google document semantics, offline fallback and missing attachments.
- [ ] Record a reversible pilot decision; automate selected indexing or mirroring only through an explicitly enabled adapter.

### MCI-07

Implementation tracker: [GitHub #19](https://github.com/dodWhatUp/install-modes-for-games/issues/19). Private TickTick mirror: registered under the same MCI ID.

**Implement managed storage on non-system internal or external drives** · P1 · Phases R1.

Requirements: GT-061, GT-062, GT-075, GT-078, GT-079. Dependencies: MCI-02.

- [ ] Enroll a selected vault and bind it by logical and volume identity rather than drive letter alone.
- [ ] Route managed project source, selected assets, outputs and continuation records into declared relative roots.
- [ ] Inventory unsupported host-local tool outputs and prevent silent OS-drive fallback when the vault is absent.
- [ ] Keep credentials, mutable runtime databases, local permissions and machine bindings under their existing owners.
- [ ] Test changed usernames, mounts, clone collisions, Unicode/case/path constraints and symlink escapes.
- [ ] Verify actual output placement and reopen behavior on synthetic projects while preserving existing native settings.

### MCI-08

Implementation tracker: [GitHub #20](https://github.com/dodWhatUp/install-modes-for-games/issues/20). Private TickTick mirror: registered under the same MCI ID.

**Implement checkpoints, move-drive handover and full or delta packages** · P1 · Phases R2.

Requirements: GT-063, GT-064, GT-076, GT-080. Dependencies: MCI-02, MCI-07.

- [ ] Create bounded streaming full-seed and parent-bound delta manifests with content hashes and provenance.
- [ ] Stage and verify complete payloads before publication; distinguish received, verified and adopted acknowledgements.
- [ ] Preview and restore into a new location with granular rollback and source-drift refusal.
- [ ] Handle missing parents, repeated packages, reordering, incompatible formats and untrusted archive paths.
- [ ] Checkpoint and release drive ownership before transfer; recover incomplete staging after unexpected removal.
- [ ] Complete a synthetic A-to-B-to-A round trip and record byte verification separately from functional restoration.

### MCI-09

Implementation tracker: [GitHub #21](https://github.com/dodWhatUp/install-modes-for-games/issues/21). Private TickTick mirror: registered under the same MCI ID.

**Implement independent parallel branches and N-device conflict reconciliation** · P1 · Phases R3.

Requirements: GT-067, GT-068, GT-077, GT-081. Dependencies: MCI-08.

- [ ] Give each enrolled device an independent working replica, branch, chat identity and explicit common ancestry.
- [ ] Merge text through three-way ancestry and structured records through stable format-owned identifiers.
- [ ] Retain both versions for binary, same-field, rename, deletion-versus-edit and external-writer conflicts.
- [ ] Use versioned tombstones, per-replica acknowledgements and deliberate device retirement before garbage collection.
- [ ] Fence exclusive operations by writer generation; a lease timeout alone must not authorize conflicting offline writers.
- [ ] Test A-B-C propagation, cycles, partitions, stale writers, late devices and lossless conflict recovery.

### MCI-10

Implementation tracker: [GitHub #22](https://github.com/dodWhatUp/install-modes-for-games/issues/22). Private TickTick mirror: registered under the same MCI ID.

**Implement network-share and authenticated peer transfer adapters** · P1 · Phases R4.

Requirements: GT-065, GT-066, GT-081, GT-082. Dependencies: MCI-09, MCI-12, MCI-13.

- [ ] Reuse one checkpoint and receipt protocol for network shares and direct peer networking.
- [ ] Keep active working trees and runtime databases local while exchanging immutable objects and manifests.
- [ ] Bind peer operations to authenticated device/project scopes using maintained transport libraries.
- [ ] Implement bounded resumable chunks, throttling, reconnect and visible queue state without automatic action replay.
- [ ] Test share disconnection, revoked peers, expired requests, partial files and duplicate network delivery.
- [ ] Verify two real hosts first and a third independent replica before advertising general multi-device support.

### MCI-11

Implementation tracker: [GitHub #23](https://github.com/dodWhatUp/install-modes-for-games/issues/23). Private TickTick mirror: registered under the same MCI ID.

**Implement opt-in cloud and hybrid storage adapters** · P1 · Phases R4.

Requirements: GT-075, GT-082, GT-083. Dependencies: MCI-09, MCI-12, MCI-13.

- [ ] Define shared, split, replicated, cloud and hybrid authority rules separately for each content class.
- [ ] Investigate the existing Drive route first while preserving original editable source owners and private recovery boundaries.
- [ ] Respect provider revisions, quotas, incomplete downloads, permissions and explicit transfer selection.
- [ ] Keep sender authentication distinct from integrity hashes and verify encryption/unlock compatibility where selected.
- [ ] Test cloud/local divergence, missing hosts, stale caches, account access changes and interrupted provider operations.
- [ ] Accept a small authorized provider pilot without automatic whole-account migration, upload or link rewriting.

### MCI-12

Implementation tracker: [GitHub #24](https://github.com/dodWhatUp/install-modes-for-games/issues/24). Private TickTick mirror: registered under the same MCI ID.

**Implement independent directional scope, cadence, adoption and context policies** · P1 · Phases R4, R5, U2.

Requirements: GT-069, GT-070, GT-071, GT-078, GT-085, GT-095. Dependencies: MCI-02, MCI-03.

- [ ] Define policy keys by account, workspace, project, source device, destination device, capability and content class.
- [ ] Configure A-to-B independently from B-to-A, including manual, checkpoint, reconnect, interval and debounced triggers.
- [ ] Separate data transfer, local file adoption, index refresh and model-context exposure into distinct controls.
- [ ] Support none, notice, summary, task packet and selected detailed-source context levels at supported turn boundaries.
- [ ] Show restrictive effective-policy decisions; local exclusions override broader central proposals and peer content.
- [ ] Test active-turn staging, canceled edits, hidden-controls versus enablement, policy revision drift and granular rollback.

### MCI-13

Implementation tracker: [GitHub #25](https://github.com/dodWhatUp/install-modes-for-games/issues/25). Private TickTick mirror: registered under the same MCI ID.

**Implement centralized roles, device enrollment and local authorization** · P1 · Phases R4, U6.

Requirements: GT-075, GT-077, GT-085, GT-095. Dependencies: MCI-02.

- [ ] Separate personal/account identities, enrolled devices, project membership and storage permissions.
- [ ] Define viewer, contributor, operator and policy-administrator capabilities without conflating them.
- [ ] Allow a selected central computer or account to propose policy while retaining destination-side hard exclusions.
- [ ] Keep secrets in local credential stores and require fresh supported sign-in rather than credential transplantation.
- [ ] Implement enrollment, revocation, expiry, policy acknowledgements and explicit device retirement.
- [ ] Test least-privilege reads/actions, offline devices, stale writer generations and an immediately usable local stop path.

### MCI-14

Implementation tracker: [GitHub #26](https://github.com/dodWhatUp/install-modes-for-games/issues/26). Private TickTick mirror: registered under the same MCI ID.

**Implement scoped remote Codex and named-operation controls** · P1 · Phases R4, U6.

Requirements: GT-084, GT-085, GT-095. Dependencies: MCI-10, MCI-12, MCI-13.

- [ ] Probe supported Codex remote-control, SSH-project and named application capabilities separately on each target.
- [ ] Define typed requests with operation ID, source/target identity, expected revision, expiry and result receipt.
- [ ] Revalidate capability, project scope and permission on the destination before a permitted action.
- [ ] Keep existing-host control, execution handoff, file transfer and remote desktop input visibly distinct.
- [ ] Provide cancellation, local approval and uncertain-effect inspection; reconnect must not replay expired work.
- [ ] Accept a bounded named operation on two actual hosts before advertising remote execution.

### MCI-15

Implementation tracker: [GitHub #27](https://github.com/dodWhatUp/install-modes-for-games/issues/27). Private TickTick mirror: registered under the same MCI ID.

**Implement honest Codex continuity and native-session feasibility** · P1 · Phases R0, R5.

Requirements: GT-072, GT-073, GT-075, GT-080. Dependencies: MCI-01, MCI-08, MCI-13.

- [ ] Offer files and source-linked continuation packets even when original native-session portability is unavailable.
- [ ] Label a new chat, original-host access, lineage-preserving fork and exact original-ID continuation separately.
- [ ] Inventory legacy/paginated formats, native logs, database projections, attachment paths and runtime dependencies in synthetic profiles.
- [ ] Use only a supported consistent-state snapshot/import route; do not concatenate histories or edit production databases.
- [ ] Verify pagination, attachments, directory rebinding, a subsequent turn, restart and return transfer for each advertised route.
- [ ] Maintain exclusive ownership of a native session identity and preserve divergent parallel chats as separate lineage.

### MCI-16

Implementation tracker: [GitHub #28](https://github.com/dodWhatUp/install-modes-for-games/issues/28). Private TickTick mirror: registered under the same MCI ID.

**Build optional controlled model behavior and prompt-quality evaluation** · P2 · Phases U5.

Requirements: GT-090, GT-091, GT-092. Dependencies: MCI-04.

- [ ] Compare original, minimal and justified prompt variants on frozen tasks with positive and negative controls.
- [ ] Distinguish current-project, fresh-session and accessible client-default baselines without claiming a model-alone condition.
- [ ] Pin runtime/model settings, instruction/source hashes, tool fixtures and evaluation version.
- [ ] Use the credential/setup workflow, explicit cost limits and isolated tools before any API-backed trials.
- [ ] Repeat stochastic cases and report correctness, scope, necessary clarification, tool choices, tokens and latency where measured.
- [ ] Retain uncertainty and held-out validation; never promise exact future responses or hidden-model-state inspection.

### MCI-17

Implementation tracker: [GitHub #29](https://github.com/dodWhatUp/install-modes-for-games/issues/29). Private TickTick mirror: registered under the same MCI ID.

**Decide and implement the optional portable Codex companion** · P2 · Phases R0, R6.

Requirements: GT-074, GT-075, GT-080. Dependencies: MCI-01, MCI-07, MCI-15.

- [ ] Test desktop app and standalone CLI portability separately for each actual OS and architecture.
- [ ] Verify cold start, dependencies, account sign-in, registration, update, restart and prior-version rollback.
- [ ] Decide among full accepted companion, accurately labeled portable CLI, or project-data-only integration.
- [ ] Reuse workspace, revision, policy and transfer owners rather than creating a duplicate application core.
- [ ] Keep user data independent of runtime releases and credentials local to the current computer.
- [ ] Publish only the capability level actually accepted, preserving the conditional project branch if unsupported.

### MCI-18

Implementation tracker: [GitHub #30](https://github.com/dodWhatUp/install-modes-for-games/issues/30). Private TickTick mirror: registered under the same MCI ID.

**Run integrated storage, control-center and recovery release acceptance** · P1 · Phases R0, R6, U6.

Requirements: GT-080, GT-086, GT-092, GT-096. Dependencies: MCI-05, MCI-06, MCI-08, MCI-09, MCI-10, MCI-11, MCI-12, MCI-13, MCI-14, MCI-15.

- [ ] Run schema/contract fixtures, accepted isolated GUI checks and scoped actual-host tests as distinct evidence classes.
- [ ] Exercise disk-full, surprise removal, process interruption, network partition, stale sources and corrupted packages.
- [ ] Verify end-to-end receipt-to-adoption-to-index-to-context flow with independent policy and readable human status.
- [ ] Verify selected local-source link preservation, permissions, no-store behavior and missing-asset disclosure.
- [ ] Restore a selected prior project revision into a new location and verify actual usability without whole-profile replacement.
- [ ] Record exact tested capabilities, unsupported optional routes, source versions, omissions and next boundaries before release.

## Requirement coverage and task mirrors

All 36 requirements GT-061 through GT-096 are covered by one or more work packages. The machine-readable requirement ledger carries the reverse mapping; existing requirement wording and acceptance remain intact.

GitHub issue #12 is the parent tracker for the integrated program. Child issues carry MCI IDs, prerequisites and acceptance checklists. TickTick uses the existing programming list for a private parent task and the same 18 work packages. Task descriptions link back to GitHub. Public Git data omits TickTick account, project and task identifiers; their exact IDs, URLs, etags and readback receipts stay in private local records. Read-back verified one TickTick parent, 18 matching checklist subtasks, all 108 unchecked items, priorities, links, and the absence of dates or recurrence.

GitHub is the status owner for these development work packages. TickTick is a human execution view with personal priority/scheduling choices. Registration creates no bidirectional synchronization service. Later status updates require an explicit reconciliation of matching MCI IDs, last observed revisions and actual implementation evidence; checking an item in one product does not silently complete it in the other. The existing toolkit's operational jobs, approvals and native chat tasks keep their separate owners.

Current authorization covers planning integration and task publication. No due dates, reminders, recurrence, model API calls, cloud migration, native-profile/database restore, remote execution or game activity is activated here.
