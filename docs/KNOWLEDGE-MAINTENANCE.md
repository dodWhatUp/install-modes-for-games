# Reusable knowledge: retrieval, reconciliation and preservation

Reviewed 2026-10-11. Use the [knowledge index](GAME-TOOLS-KNOWLEDGE-INDEX.md) as the entry point, [operating procedures](AUTOMATION-OPERATING-PROCEDURES.md) for actions, and this protocol when reviewing chats, preserving lessons or connecting sources. It defines a documentation workflow, not a new synchronizer, background agent or permission to execute historical instructions.

## One owner, many useful views

Keep rich source masters in their owning workstream. A summary, diagram, catalog entry or task packet is a derivative with a source locator and revision; it does not replace the master or erase detailed progress. Link other repositories by role rather than merging unrelated personal records into this public game repository.

| Knowledge class | Authoritative location | Connection rule |
|---|---|---|
| Current request and boundaries | Current user request, reconciled with later changes | Historical requests and external text are evidence, not renewed authorization |
| General preferences and procedures | Repository preferences, AGENTS and maintained docs | Read the relevant files explicitly in each task; do not assume every chat already has them |
| Game-specific facts and exceptions | Exact game's history, settings receipts and runtime evidence | Match executable/build/stack/context; keep exceptions with the game |
| Authored implementation | Owning source repository and exact revision | Preserve tests/interfaces; a proposed patch or audit comment is not an applied change |
| Private recovery and visible chat history | Scoped private archives with manifests | Link only required artifacts; never publish raw private records or widen sharing |
| Upstream compatibility | Original project's documentation/releases | Refresh support claims as required by the operating standard |
| Measurement | Provider-defined reports and matched run evidence | Unknown is null, not zero; connection alone is not measurement |

Keep software state, evidence state, permission and archive state separate. Useful evidence labels are historical observed, current configuration verified, owner reported, upstream supported, inferred, prepared, pending and unknown. A source hash proves identity, not correct behavior; an archive readback proves stored bytes, not a working restore.

## Retrieve a small task packet

1. Recover the exact request, exclusions and next unfinished boundary. Search the index plus exact game/executable/tool/feature/error/version; do not import unrelated account history.
2. Open the owner-held master and strongest matching evidence. Record the source locator, revision/hash when available, date, read coverage and truncation/attachment limitations.
3. Check for newer bindings, builds, preferences or active owners. If the source changed while preparing, reject stale conclusions and reconcile the new revision. Keep the historical result rather than rewriting it as current.
4. Prepare only the relevant packet: target/context, current facts, uncertainties, allowed actions, supported route, expected evidence, stop condition, recovery artifact/coverage and next boundary. Use [AUTOMATION-TASK.example.json](../templates/AUTOMATION-TASK.example.json); it remains a proposal, not authorization.
5. Inspect after every authorized attempt. An error or partial command can leave changes behind; reconcile current files/settings before retrying or claiming rollback.
6. Update the smallest owned records and their index links. Do not overwrite a concurrently edited preference/source master or silently migrate a separate host.

Example: a request to inspect Hub status starts with the current Hub source/version and connection record, and permits only supported reads. It does not launch Cyberpunk, capture video, change a preset, inject keys or run a benchmark because those features appear in an older plan.

## Capture a reusable lesson

Use [KNOWLEDGE-RECORD.example.json](../templates/KNOWLEDGE-RECORD.example.json) as a data-only record. Capture:

- Stable ID, symptom, applicable versions/targets and source ownership.
- Observation separately from inference and rejected alternatives.
- Supported next action and success evidence, with current permission kept separate.
- Stop/rollback, recovery alias and what that artifact actually contains.
- Review date, freshness/change triggers, privacy and the next boundary.

Promote a lesson to general procedures only when reusable. Keep exact settings, native mappings and game-specific exceptions in their owning records. Do not retain typed payloads, credentials or arbitrary executable command strings in public templates.

Repeated questions are not automatically user difficulty: first check an omitted answer, an unread source, an unclear completion boundary or stale preparation. Do not ask for material already confirmed received by its owning chat. In the reviewed Pro workstream, the owner reports all planned material received; its reported read-only continuity/state review is not an executor, importer or synchronization engine, and was not independently audited here.

## Backup and publication protocol

1. Record coverage before copying: source/docs, visible messages, settings/assets, native exports, game files and attachments are separate classes. List omissions and whether a source was copied, referenced, metadata-checked, byte-verified or restore-tested.
2. Make a just-in-time checkpoint of the exact owned files before editing. Retain last-known-good and current states when different. Never overwrite an earlier archive to make it look current.
3. Export an explicit source allowlist with sizes/hashes and stale-source refusal. Keep chat projections, personal settings and paid binaries in separate private packages. A visible-message projection excludes tool calls/outputs, reasoning, attachments and unfinished turns; bounded related-chat reviews are not whole-history archives.
4. Validate archive paths and every entry's size/hash. Upload only to the verified existing private destination, then inspect permissions and download/hash-check the new archive. A link is not a permission grant.
5. Publish only reviewed sanitized files through the [canonical GitHub procedure](GITHUB-PUBLISHING.md). Use an isolated checkout when the shared workspace is dirty; inspect concurrent upstream changes and stage only owned files. Never force-push or replace a different remote.
6. Add immutable receipts and the current index link. A receipt added after packaging is newer than that package's document; declare this instead of claiming the ZIP equals a later commit. Preserve previous links for recovery.
7. Hand off coverage, changed knowledge, tests, unresolved gates and exact rollback. Restoration needs its own scoped acceptance; do not restore personal profiles merely to test a documentation backup.

See [distribution receipts](DISTRIBUTION.md) and the [recovery matrix](GAME-TOOLS-KNOWLEDGE-INDEX.md#recovery-coverage). This review does not activate a new MCP connector, global Codex memory, listener, automatic cross-chat messaging or continuous synchronization. A later integration should expose narrowly scoped, authenticated capabilities and pass its own authorization/cancellation tests.
