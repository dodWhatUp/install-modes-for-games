# Portable workspaces and collaboration across multiple computers

Current common implementation foundation: [one master build plan](INTEGRATED-SYSTEM-EXECUTION-PLAN.md#one-shared-foundation-then-specialized-adapters) and [machine-readable core/adapter map](INTEGRATED-SYSTEM-BUILD-MAP.json). Reuse the existing 18 tasks; retrieve one MCI build packet rather than duplicating the whole plan in each implementation prompt.

Prepared 2026-10-19, Asia/Jerusalem. Status: development plan, not an installed synchronization feature.

Provide one recognizable workspace across multiple computers, starting with two, with project files stored by default on a selected internal or external data drive. Support moving the drive, carrying a transfer file, using a network drive, direct networking and optional cloud exchange. Devices can work independently and concurrently with shared, split, replicated or hybrid storage. Each direction has separate controls for scope, frequency, adoption and influence on chat context.

Build this as an extension of the existing unified toolkit. Keep a reusable project-neutral core behind the toolkit's User data and AI workspaces. Consider a separate portable Codex launcher only after a feasibility gate proves it useful; it must call the same core. Existing adopted 0.27 source, the independent unadopted 0.26 library candidate, and their original owners remain separate.

The requested deliverable at this stage is the architecture, coverage and development sequence. Production storage defaults, Codex installations, network services and active chats are unchanged. Planning a later native-state experiment does not override the current rule against transplanting production Codex databases or credentials.

## Integrated execution and control-center dependencies

The [integrated execution plan](INTEGRATED-SYSTEM-EXECUTION-PLAN.md) expands this design into 60 integration points and 18 work packages with 108 implementation checks. The [work-package manifest](INTEGRATED-SYSTEM-WORK-PACKAGES.json) supplies the dependency graph; each [GT requirement](PORTABLE-WORKSPACE-REQUIREMENTS.json) maps back to its implementing packages. Both projects share resource identity, source provenance, revisions, policy decisions, receipts and context contracts. Their existing owners remain authoritative.

| Existing phase | Implementing work packages and cross-project links |
|---|---|
| R0 | MCI-01 inventory; MCI-15 native-session feasibility; MCI-17 conditional runtime decision; MCI-18 actual-host acceptance |
| R1 | MCI-02 shared contracts; MCI-07 non-system drive vault |
| R2 | MCI-08 checkpoints, move-drive handover and full/delta packages |
| R3 | MCI-09 independent parallel branches and N-device reconciliation |
| R4 | MCI-10 network/share, MCI-11 cloud/hybrid, MCI-12 policy, MCI-13 roles/enrollment and MCI-14 remote operations |
| R5 | MCI-15 honest continuity plus MCI-12 context/adoption controls |
| R6 | MCI-17 optional portable companion and MCI-18 acceptance |
| Shared human surface | MCI-03 architecture/instructions, MCI-04 static request checks, MCI-05 overview and MCI-06 local-source/Drive-link pilot |

The urgent control-center core can use fixture data before any synchronization service exists. Network and cloud adapters depend on merge, policy and authorization contracts; the local-source pilot depends on resource resolution and access rules. Received bytes, adopted workspace state and information supplied to a running chat are separate transitions. Policy must independently control transport, timing, adoption, context depth and remote actions. Native runtime/history failures do not block file exchange and clearly labeled continuation packets. MCI-16 model trials and MCI-17 runtime portability are optional acceptance tracks.


## Read the plan

- [What must be possible](#what-must-be-possible)
- [What is established about Codex](#what-is-established-about-codex)
- [Components and existing owners](#components-and-existing-owners)
- [Storage and default output locations](#storage-and-default-output-locations)
- [Four ways to move work](#four-ways-to-move-work)
- [Parallel work and conflicts](#parallel-work-and-conflicts)
- [Independent update controls](#independent-update-controls)
- [Chat continuity and native session identity](#chat-continuity-and-native-session-identity)
- [Development sequence](#development-sequence)
- [Acceptance and recovery](#acceptance-and-recovery)

The implementation backlog is [GT-061 through GT-096](PORTABLE-WORKSPACE-REQUIREMENTS.json). These extend GT-001, GT-006, GT-008, GT-009 and GT-055 through GT-059 without changing their historical status. The [policy example](../templates/WORKSPACE-SYNC-POLICY.example.json) is an inert design example, not configuration understood by the current application. The separately scoped [urgent control center and request preflight project](SYSTEM-CONTROL-CENTER-PLAN.md) owns the human-facing navigation and oversight work; [project priorities](SYSTEM-DEVELOPMENT-BACKLOG.json) preserve its urgent status.

## Multiple computers and storage topologies

Generalize device identity, branches and acknowledgement tracking to N devices. Each workspace declares its topology, replica membership and authoritative owner for each record class. A central account or selected management computer can administer linked projects, roles and policies; each device retains local hard exclusions and can revoke its own participation. Central administration does not grant access to another account or bypass local approval.

| Storage topology | Intended behavior | Required check |
|---|---|---|
| Shared storage | Several computers use one immutable object store and exchange area | Separate live working trees and runtime databases; concurrency-safe revision publication |
| Split storage | Different projects or content classes remain on their assigned computers or volumes | An availability catalog resolves the owner and fetches authorized content on demand |
| Replicated storage | Selected content has independent copies on several devices | Ancestry, conflicts, acknowledgements and offline reconciliation scale beyond a pair |
| Cloud exchange | An explicitly configured provider carries approved objects, manifests and receipts | Provider revisions, quotas, permissions, resumable transfer and local encryption policy |
| Hybrid storage | Combine local authoritative content, network/cache replicas and selected cloud recovery | Declare authority and cache freshness per class; no implicit last-writer-wins across providers |

Drive is the first existing cloud destination to investigate, not the only possible provider or an automatic upload destination. Git owns reviewed source; private originals, chat content and credentials have separate storage rules. Cloud placeholders and incomplete local downloads must not count as verified bytes. Add provider capability detection rather than assuming every cloud folder behaves as a local atomic filesystem.

For N-device operation, acknowledgements and tombstone retention are per enrolled replica. Retire a lost device explicitly, rotate its access, and preserve ancestry for late arrivals. Test A-to-B-to-C propagation, cycles, duplicate object delivery and simultaneous adoption; relaying content must not amplify a peer's permissions. Separate personal identities, account membership, device trust and project roles.

## Remote operation and central oversight

Add scoped remote capabilities behind the same operation and evidence contracts: inspect status, read selected information, prepare/transfer a checkpoint, open an accepted Codex project/session route, submit a named request, and later execute explicitly enabled supported actions. Remote desktop input and arbitrary shell access are separate capabilities, not prerequisites for file exchange.

Official Codex remote control and SSH project connections are reuse candidates. Existing-host control continues work on that host; host handoff changes execution location; a data transfer only changes available files. Availability, account pairing, destination policy, native-history mode and actual runtime acceptance must be checked separately. Do not represent a central dashboard as an implementation of unsupported Codex controls.

Each remote request carries operation ID, source and target identity, project scope, expected revision, capability name, expiry, cancellation state and result receipt. Revalidate on the target. An expired or disconnected request never executes simply because a device reconnects; uncertain effects require inspection, not blind retry. Local approval and an emergency stop stay available. Roles start with viewer, contributor and operator; administration of policy is distinct from permission to run an action.

The human overview shows device availability, expected versus observed policy, transfer/merge progress, last successful checkpoint, conflicts and a concise account of chat activity. Full conversation text and private file bytes are fetched only when requested and authorized. See the [control center project](SYSTEM-CONTROL-CENTER-PLAN.md) for source-bound architecture/trigger navigation, stable references and behavior preflight.

## What must be possible

| User workflow | Required outcome | Constraint that stays visible |
|---|---|---|
| Work on A, move its data drive to B | Recognize the same workspace, bind local tools and resume the selected project | A relinquishes that drive before B writes; B uses its own authentication |
| Keep different drives in A and B | Exchange selected changes using a full or incremental transfer file | Both versions and the last common checkpoint are retained |
| Use a network drive | Publish and retrieve verified checkpoints through one shared exchange location | Interrupted network access does not damage active local work |
| Connect A and B over a network | Transfer changes quickly, with independent direction and project policies | Receiving bytes and adopting them are separate operations |
| Work on both at the same time | Use separate working branches, chats and task scopes, then merge deliberately | One writable Codex session identity is never shared by two independent hosts |
| Continue the original Codex chat | Use a version-specific, verified native continuation route where available | A new chat with imported context must be labeled as a new chat |
| Adjust how computers influence one another | Set content, transfer cadence, adoption timing and context depth independently | No automatic remote instruction becomes permission to execute |

"One drive" means a common logical workspace identity and understandable revision history. Instant consistency during independent offline work is not a guarantee: divergent work must be preserved and reconciled. A physically moved drive alone cannot serve two disconnected computers simultaneously; parallel operation requires a local replica or a reachable exchange service.

## What is established about Codex

Evidence baseline is dated 2026-10-19 and must be refreshed after a Codex update.

| Capability | Evidence and status | Development consequence |
|---|---|---|
| Select another Codex state root | Official documentation describes `CODEX_HOME` for CLI, IDE, app-server and installers, including sessions and skills | Test supported components independently; this does not prove complete desktop portability |
| Choose SQLite state location | Official documentation describes `CODEX_SQLITE_HOME` and the overriding `sqlite_home` setting | Runtime state and portable project data need separate location rules |
| Choose standalone CLI install directory | Official documentation describes `CODEX_INSTALL_DIR` | A CLI on a data drive is a candidate; Windows app registration and another OS need separate tests |
| Resume a stored thread | Official app-server documentation exposes `thread/resume` using an existing thread ID | Discovery, history, identity and a successful subsequent turn must all be verified |
| Hand off to another host | Official documentation describes a connected destination and a matching saved Git project | Treat remote control, host handoff and offline SSD migration as different modes |
| Installed build's paginated restriction | Prior read-only inspection of desktop 26.1013.4894.0 and CLI 0.163.0-alpha.10.2 found an explicit cross-host handoff rejection for paginated chats | Seven local records were paginated at that inspection; this is not a count of all account chats or a universal impossibility claim |
| Full desktop program and original chats portable by SSD | No successful two-computer restoration was established | Keep this a feasibility gate; do not make the rest of the system depend on it |

The installed rejection reads: "Paginated chats cannot be continued on another host yet." This is a static code observation, not a failed migration test. It establishes a limitation of that handoff path, not that every future or custom native migration is impossible. Legacy handoff can create a new underlying conversation identity while retaining the visible conversation lineage; exact identity requires separate acceptance.

Official references: [state and installer variables](https://learn.chatgpt.com/docs/config-file/environment-variables), [native thread lifecycle](https://learn.chatgpt.com/docs/app-server), [remote access and handoff](https://learn.chatgpt.com/docs/remote-connections). These establish Codex interfaces; the replication design below is proposed application architecture.

## Components and existing owners

| Component | Responsibility | Existing owner to reuse |
|---|---|---|
| Workspace registry | Stable workspace, project, device and replica identities; local root bindings | `GameToolWorkspace` feature/navigation registry and existing private registry conventions |
| Snapshot and package service | Selection, manifest, hashes, staged copy, readback, receipt and new-copy restoration | `GameToolUserData`; retain its current private archive format and migration behavior |
| Revision and merge service | Parent revisions, branch ancestry, idempotency, conflicts and deletion records | New bounded service behind User data; Git where a project already uses Git |
| Transport adapters | Moved volume, package file, network share and authenticated peer connection | One package/receipt protocol, separate transport implementations |
| Policy service | Directional scope, timing, adoption, context exposure and local overrides | New policy model shared by all transports; existing local settings ownership |
| Evidence journal | Transfer and merge receipts, cancellation and recovery references | `GameToolJournal`; do not treat its local cooperative ownership as a distributed lock |
| Work coordination | References to existing tasks, resource ownership and branch assignments | `GameToolCoordinator`, `GameToolGameWorkspaces`, existing Workbench and approval owners |
| Codex adapter | Capability probe, project opening, supported session continuation and explicit context packets | Existing AI contract/tool boundary; preserve local consequential-action approval |
| Interface | One Workspace and sharing view, with contextual advanced controls | Existing compact design system and User data/AI workspaces |

The current User data exporter is a small selected-file recovery service, not a replication engine. Source inspection found limits of 512 files, 16 MiB per file and 64 MiB total, plus in-memory ZIP construction. Reuse its validation and preservation contracts; design a new versioned streaming format for larger project replicas rather than silently raising those limits or breaking old archives.

Keep this core useful for ordinary code, documents and assets. Game-specific profiles, collectors and automation remain adapters with their own owners. A future connection to a separately owned personal system exchanges versioned records; it does not replace that system's source or create a second task master.

## Storage and default output locations

The selected data volume needs no operating system. Each computer still needs a compatible operating system, supported Codex runtime, dependencies and local sign-in. Discover actual OS/architecture and filesystem capabilities on both machines before choosing executables or formats.

Proposed logical layout, relative to a user-selected vault root:

```text
WorkspaceVault/
  vault.json                 # vault identity and supported format versions
  projects/<project-id>/     # managed project roots, source, assets, outputs
  objects/                   # immutable content blobs addressed by digest
  revisions/                 # manifests, parent revisions and provenance
  continuation/              # selected context records and attachment indexes
  exchange/inbox/            # complete received packages awaiting inspection
  exchange/outbox/           # complete published packages
  recovery/                  # retained checkpoints and conflict versions
  runtime/<os-arch>/         # optional verified runtime payloads after gate R0
```

Local device bindings, tokens, account sessions, SSH private keys, OS credential stores, mutable application databases and local caches stay in a separate machine-owned location by default. A native-chat adapter must define its own supported export, quiescence, import and recovery contract; the generic file synchronizer never guesses that contract.

Bind the vault by its application vault ID plus locally verified volume/mount identity, not a drive letter alone. Store project paths relative to its root. Detect two attached copies carrying the same vault ID, renamed mounts, replacement drives and cloned media; require selecting the intended replica instead of choosing the first match. Resolve Windows drive paths, UNC paths, macOS/Linux mounts and WSL paths through per-device bindings.

Configure selected projects, generated artifacts, reports, downloads chosen for the project and continuation packets to use managed subfolders. Generated files must be discoverable even after a mount changes. Avoid changing global environment variables or creating broad filesystem junctions as the first implementation. Use scoped launcher environments and explicit project roots where supported.

Inventory each output class separately: project files, chat attachments, viewed/generated images, previews, scratch files, managed worktrees, logs, plugin data and external-program exports. Show whether each location is managed, host-local, explicitly excluded or unsupported. A project root cannot force every Codex tool or external program to honor a default directory. Report exceptions and verify actual writes with test artifacts before claiming coverage.

Validate filesystem behavior: case collisions, Unicode names, reserved names, path length, maximum file size, permissions, symlinks/reparse points and atomic rename support. Keep runtime databases on a supported local filesystem; exchange immutable files on a network share. Use encryption suitable for both actual operating systems, with fresh local unlock credentials and a documented recovery method. Measure throughput, free-space requirements and SSD wear before promising frequent large transfers.

## Four ways to move work

Every transport uses the same pipeline: select a checkpoint, stage immutable payloads, validate identity/schema/limits, verify digests, publish a complete manifest, inspect on the destination, adopt through the local policy, then acknowledge a revision. An acknowledgement of receipt is different from an acknowledgement of adoption. Received packages are data and never carry executable authorization.

| Transport | Normal operation | Failure and recovery contract |
|---|---|---|
| Move a drive | Checkpoint A, drain writes, release writer ownership and safely detach; B identifies the vault and binds its tools | Surprise removal stops owned writes; next attach checks the last committed manifest and incomplete staging before resuming |
| Transfer file | Create a full seed package or a delta against an identified parent; carry via any file-copy mechanism | Verify all entries; missing parents are reported; duplicates are idempotent; reordered packages are queued or refused without overwriting |
| Network drive | Publish immutable packages and manifests to per-device exchange folders; work from local active replicas | Disconnections, share permissions and stale listings never make incomplete files visible as committed revisions |
| Direct network | Pair the selected devices, authenticate transport, negotiate protocol/version and exchange missing objects | Reconnect resumes bounded transfers; revoked peers lose future access; offline edits stay local until a new exchange succeeds |

Start with one transport and preserve identical semantic results when others are added. Network clients use standard maintained authentication and transport libraries; do not implement custom cryptography. A network share can rely on verified platform identity/ACLs; peer networking must bind receipts to the paired device. An offline package from a trusted channel is not authenticated merely because its hashes match. Show integrity and sender authentication separately.

A new package manifest needs a package ID, workspace/project/replica IDs, parent revision IDs, producer and schema versions, content classes, relative paths, byte sizes, digests, deletion records, provenance, policy revision and any applicable writer generation. Local private source locators belong in a separate private receipt, not a public source release. Large binary objects need bounded streaming, resumable chunks and an allowlisted content policy. Do not copy build caches or reinstallable dependencies by default.

Publishing completion must survive interruption: stage on the destination filesystem, verify bytes, publish a commit marker only when complete, and keep recoverable pending state. Where atomic rename or durability is insufficient, refuse to label the package committed. A multi-file restore uses a transaction manifest and backups rather than claiming a whole-directory rename makes every external consumer transactional.

## Parallel work and conflicts

Each computer has its own active replica, branch, chat identities and local runtime databases. A shared workspace ID connects them. Existing Git repositories retain their origin, ancestry and branch rules. For non-Git projects, the revision service records equivalent parent relationships without inventing commits in someone else's repository. Worktrees that depend on another checkout must be materialized or rebound; copying their `.git` pointer is insufficient.

Code and text use a three-way merge from the last common revision. Apply clean non-overlapping changes only under an enabled adoption policy. For structured records, merge stable IDs and versioned fields through the format owner. Preserve unknown fields. Binary/native profiles, same-field edits, deletion versus edit and renamed-path ambiguity create visible conflicts with both original versions retained. Modification time alone never chooses a winner.

Deletion is a versioned tombstone, not immediate erasure on the other machine. Trash/retention, acknowledgement and restoration rules precede physical deletion. Retain missing-parent objects and conflict versions until the relevant replica acknowledges resolution or is explicitly retired; an offline device must not cause premature garbage collection.

Parallel branches do not require an exclusive global lock. Exclusive actions do: moving the active-drive role, publishing a shared branch head, applying a native profile or continuing one native Codex identity. Use monotonically increasing writer generations and destination-side rejection of stale generations. A timestamp-based lease alone does not prevent a partitioned old writer from returning. Existing local journals are not a distributed consensus service.

During a network partition, each side can continue its independent branch. It cannot claim exclusive ownership of the same protected resource without a trusted ownership authority or an explicit physical handover protocol. A forced takeover quarantines the old writer's later changes for review. External programs that bypass the manager are outside its enforcement; detect divergence before adoption instead of promising universal process control.

Reconciliation is explicit: compare parents, show changed items, choose clean merges or conflict resolutions, create a new revision, verify readback, and record adoption separately on each device. Recovery never replays tasks, approvals, shell commands, schedules or chat messages. Task summaries update existing task references; a remote 'complete' report remains evidence until its owner accepts it.

## Independent update controls

Policy key: workspace + project + source device + destination device + content class. Configure A to B separately from B to A. Named presets expand to visible controls; they do not silently override local choices.

| Control | Choices to support | Initial proposed default |
|---|---|---|
| Content scope | Selected projects, folders, records, assets, outputs, instructions, skills, continuation packets | Explicit selection; credentials and runtime databases excluded |
| Direction | A to B, B to A, both, receive only, send only | Disabled until a link is configured |
| Transfer trigger | Manual, safe detach, checkpoint, reconnect, debounced file change, interval | Manual |
| Transfer frequency | Independent interval/debounce, bandwidth and size limits per direction/class | No background transfer |
| Adoption | Notify only, inbox/stage, preview and merge, automatic clean eligible merges | Stage and preview |
| Adoption timing | Immediately for inactive files, next checkpoint, after turn completes, next project open, manual | Manual; active project adoption waits for a safe boundary |
| Context exposure | None, availability notice, short change summary, task packet, selected detailed sources | Availability notice |
| Context timing | On request, next turn, next chat/project open | On request |
| Settings depth | Per-project allowlist, portable preferences, independently selected skills/instructions | No remote policy/permission inheritance |
| Conflict behavior | Ask, retain both, leave staged, use an explicitly assigned owner | Retain both and leave staged |
| Deletion and retention | Preview tombstones, retention duration/size, replica acknowledgements | Retained; no automatic remote deletion |

Transfer frequency, file adoption and context visibility are independent. For example, a configured A-to-B link might transfer code at a 5-second debounce and let B adopt clean changes after its turn, while instruction changes are delivered as a daily digest requiring review. B-to-A might publish only a manually selected checkpoint. These are example settings, not promises of measured latency or newly active schedules.

Policy precedence is restrictive: local hard exclusions and security boundaries, destination project choices, directional/class choices, then a named preset. Peer content cannot broaden this policy, enable automation or grant permissions. Record an effective policy preview explaining why each item will transfer, stage, affect context or stay excluded. Changing context depth does not change the historical conversation or make an active model reread a file.

## Chat continuity and native session identity

Expose these distinct levels and their acceptance status:

| Level | Meaning | Identity and availability |
|---|---|---|
| C0 Files | Open project source and outputs on B | A separate chat can use the files |
| C1 Continuation packet | Supply goal, completed work, unresolved issues, source revisions, next step and chosen attachments | A new chat is labeled new, with links to the source conversation |
| C2 Existing-host access | Use another device to operate the chat on its original reachable host | The original host remains responsible for execution and storage |
| C3 Native handoff or migration | Resume supported native history on B after capability checks and exclusive handover | Preserve lineage; claim the exact original ID only if verified |
| C4 Portable runtime and native continuity | Launch the accepted platform runtime from the drive and complete C3 | Conditional product branch after clean-host acceptance |

The default system must work at C0/C1 while C3/C4 remain under investigation. A continuation packet contains selected, source-linked information with a scope and freshness revision. Keep raw private chat records and attachment bytes separate from sanitized project knowledge. Report missing assets, truncated projections and incomplete turns instead of filling gaps. Search/exposure happens through a bounded, project-scoped reader; do not inject all histories into every turn.

For C3, investigate documented exports/imports and handoff first. Any native-state experiment begins with synthetic chats and an isolated test profile. Inventory the exact history mode, IDs, native logs, database projections, attachment paths, worktree state, plugin dependencies and account binding; capture consistent state through a supported quiescence/backup method. Copying a live database while ignoring its WAL is not an acceptable snapshot procedure. Do not concatenate histories, edit production tables or force a legacy format to evade the installed restriction.

Acceptance must prove history discovery, pagination to the beginning, original and later attachments, working-directory rebinding, a successful subsequent turn, reopen after restart, and return transfer. Exact-ID preservation and lineage-preserving fork are separate results. Independent parallel work uses distinct native IDs linked to a shared logical work session. If both sides continued a copied identity, preserve both branches and resolve lineage; never merge the runtime databases blindly.

Keep authentication local. Test whether account binding permits the supported operation without copying tokens, browser profiles or an OS credential store. A local sign-in is not evidence that local histories automatically synchronize. Any new credentials or OpenAI-backed implementation later follows the credential skill; this plan introduces no API service.

## Portable Codex component decision

R0 decides among three outcomes. Record results separately for desktop app and CLI, actual OS/architecture, cold start, update, restart, paths, sign-in and native-history format.

1. **Desktop and native chats pass portable acceptance:** add an optional independently launchable companion using the shared engine, with platform-specific runtime folders and a stable entry point. Keep user data independent of runtime releases and preserve prior runtime versions for rollback.
2. **Only CLI portability passes:** label the CLI mode accurately; keep the installed desktop path and use the same workspace/transfer services. Do not present it as a portable desktop installation.
3. **Only project data and continuation pass:** keep everything in the existing toolkit's User data and AI workspaces. Codex remains separately installed and authenticated on each computer.

A separate system is therefore conditional, as requested. There is no reason to duplicate registry, merge, policy or transfer logic while native portability is unproven. Validate distribution/license requirements and use original verified installers or supported packages; do not redistribute an unpacked desktop installation based only on its presence on disk.

## Compact interface

Add a Workspace and sharing entry reachable from User data and AI. The main view shows the selected workspace/root, this device, peer device, transport, current revision, pending changes, conflicts and last verified adoption. A compact editable workspace selector combines choice and search; browsing the volume is an adjacent labeled utility action. Never auto-enroll a newly attached drive by name alone.

Main actions: Open project, Checkpoint, Compare, Send, Receive, Resolve, Prepare drive handover, and Resume work. Resume work displays the available C-level and chooses only an accepted route. The original chat ID/host or new-chat lineage remains visible. Network status and active automatic policies remain visible even when advanced controls are collapsed.

Show advanced scope, timing, direction, context and retention in named disclosures beside the selected link. Show an effective-policy preview before enabling automatic adoption. UI density/visibility is local presentation state, separate from operational policy. Preserve canceled edits, unsaved selections and previous values; support keyboard navigation, long roots, missing drives, narrow layouts and readable text scaling.

For later compatible GUI work, use the current local isolated-lab skill and its current connection/acceptance records. Windows remains unprovisioned/unaccepted for that lab unless a later local receipt establishes otherwise. Headless contract work requires no VM. Synthetic GUI tests do not prove hardware detach, native Codex migration or actual two-host networking.

## Development sequence

| Phase | Deliverable | Exit gate and dependency |
|---|---|---|
| R0 Capability and topology study | Two-device OS/storage matrix; actual output-location map; Codex CLI/desktop/native-session portability results; component decision | Select one honest capability level per host/version; unresolved native support never blocks C0/C1 |
| R1 Managed vault | Registry, relative paths/local bindings, selected default outputs, revision manifest and recovery preview | Reopen after mount changes; root bounds and ordinary outputs verified on synthetic projects |
| R2 Offline exchange MVP | Full and delta packages, move-drive handover, inbox/preview/new-copy adoption and receipt | Successful A-to-B-to-A cycle; interrupted transfer recovery, wrong parent refusal and duplicate import tests |
| R3 Independent parallel work | Per-device branches, three-way merge, binary/record conflicts, tombstones and ownership generations | Concurrent/offline changes preserved; protected resources reject a stale writer; no active chat files overwritten |
| R4 Network transports and policy | Network-share and paired direct-network adapters; directional class policies, throttling and reconnection | Same checkpoint results as R2; partition/revocation/cancellation tests and actual two-host acceptance |
| R5 Codex continuity adapter | C1 packets first; C2/C3 only as independently supported; scope/freshness and boundary-aware context refresh | Distinct new-chat versus native-ID result, history/attachment/restart/return-transfer evidence |
| R6 Optional portable companion | Stable double-click launcher, platform-specific runtime handling and reversible update | Only after R0 and the relevant R5 gates pass; cold-start and upgrade/rollback on both real computers |

Native-session feasibility starts in R0 and can proceed as a separate investigation while R1/R2 mature. Implementation dependencies: R1 before R2; R2 before R3; R2/R3 policy and conflict contracts before automatic R4 adoption; C1 can start after R2; C3 requires its own R0 result; R6 requires accepted runtime portability and whichever continuity level it advertises.

The first useful release is R1/R2: select the non-system drive, work in a managed project, create a verified checkpoint, move the drive or transfer a file, preview on the other computer and continue with files plus an honest C1 packet. This creates value before native chat portability is resolved. It is a planned release, not a claim that those functions were implemented here.

## Acceptance and recovery

Use authored fixtures first, then the accepted isolated GUI route, then scoped tests on both actual machines. Record exact source/runtime versions, hashes, protocol and filesystem versions, output roots, omissions, expected result, observed result and recovery evidence. A checksum proves byte identity; it does not prove a resumed chat or correct merge.

| Area | Required checks and pass condition |
|---|---|
| Data-drive defaults | Project source/assets/generated files/known attachments go to declared roots; unsupported host-local outputs are reported; no silent OS-drive fallback when the vault is absent |
| Identity and paths | Changed drive letter, different username/mount, duplicate vault clone, case/Unicode collisions, relative worktree pointers and missing source roots resolve safely or block visibly |
| Large files and bounds | Streaming/memory bounds, free space, quota, large binary, long path, malicious archive traversal, symlink/reparse escape and compression bombs are covered |
| Offline packages | Full seed, delta chain, missing parent, wrong workspace/device, duplicate package, reordering, corruption, source drift and incompatible future schema preserve current data |
| Parallel edits | Same-line and different-line edits, records with unknown fields, binary conflict, rename/delete/edit collision and both sides offline preserve every divergent version |
| Storage failures | Process crash, full disk, read-only mount, removal mid-write, unavailable network share and power-interruption simulation leave a recoverable committed prefix plus visible pending state |
| Network behavior | Initial pairing, sender identity, reconnect/resume, expired/revoked peer, bandwidth limit, partition and repeated delivery do not duplicate adoption or bypass scope |
| Policy isolation | A-to-B and B-to-A settings differ correctly; per-project/class timing, staging and context depth work independently; policy changes do not retroactively replay received actions |
| Live work | Unsaved editor files and active turns are held/staged; conflicting external writes trigger revalidation; imported instructions never restart a task or grant tool permissions |
| Native chats | Test legacy and paginated separately; same-ID versus fork explicitly recorded; history/tool outputs/attachments and a new turn survive restart and the return trip |
| Runtime portability | Actual desktop/CLI cold start, OS/architecture, dependencies, installer registration, update and rollback checked separately from data portability |
| Recovery | Restore selected prior revision into a new location; verify opens and project usability; native state remains under its adapter's exclusive ownership |
| Interface | Keyboard, narrow layouts, long names, empty/offline/error states, cancellation, view reset and hidden-controls versus active policy behavior checked |
| Preserved owners | Existing exports, journals, Workbench, profiles and source masters retain their current behavior; no duplication of tasks or automatic native-profile activation |

Rollback is granular. Pause the link; preserve received objects and receipts; restore a selected project revision through a reviewed new copy; restore only the changed local bindings/policy if needed. A runtime update restores its own prior version. Do not undo one project merge by replacing the entire Codex home, toolkit registry or native profile store. Retention and replica retirement need explicit handling before garbage collection.

## Planning completion and next development boundary

This design and the requirement ledger cover every requested transport, storage mode, parallel-work mode and independent influence control. The policy file is illustrative. Runtime code, protocol conformance tests, native-state migration and two-host acceptance remain planned.

Continue at R0/R1 using the adopted canonical product source, current local bindings and strongest current receipts. First build a read-only capability report and a synthetic managed-vault prototype; keep native-chat experiments separate. Refresh the installed Codex restriction and inspect the second computer before making a portable-runtime commitment. Native state, actual local roots and verification receipts stay outside Git and OneDrive.
