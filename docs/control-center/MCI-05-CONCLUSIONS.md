# MCI-05: human device, synchronization, change and chat overview

Result: all six original checklist items accepted for read-only selected evidence and content access. Device freshness, transfer receipt/verification/staging/adoption/context exposure, conflicts, activity goals/outcomes/blockers, changed artifacts and next boundaries remain distinct. Existing journal input uses GameToolJournal's hash-chain validator and omits private payloads.

Fixed an eager-read defect: architecture construction and ordinary source refresh now defer every resource body, including sources also referenced by a node. Verification is explicitly deferred until an authorized content request. Metadata refresh cannot promote a deferred body to a verified instruction.

Full content requires both a selected-resource request and local authorization, caller-selected root, exact locator and expected SHA-256. The existing bounded source reader owns link/reparse/identity checks. Routes support UTF-8 text (128 KiB), declared conversation projections (2 MiB with bounded message structure) and exact attachment bytes (16 MiB). Malformed, changed, missing, oversized, credential and native-state references are refused. Binary content stays in memory; no external application opens.

Conversation coverage is visible_messages, selected_messages or source_export. Message roles/text remain intact; native chat identity is explicitly not imported. Reading a projection does not resume the original native Codex chat. Real native continuity/source-specific adapters remain MCI-15; live transport and another computer remain unobserved.

No-store/session views write no index/cache. Detail references and bytes are released on filter, tab/context switch, failure, forget, clear and close; forensic memory erasure is not claimed. Durable HTML reports omit no_store/session_only summaries and every body. Upstream retention stays with its owner.

Evidence covers denial before IO, deferred body refresh, exact non-UTF-8 bytes, conversation content above the ordinary text limit, malformed/duplicate JSON, root/locator mismatch, drift/size/missing-content refusal and unchanged originals. Tk/browser filtering retains stale, unknown and partial labels. Windows/native screen-reader/human acceptance remains unverified.

Decision: accept the original P0 content/filtering criteria. Future adapters reuse these references and lifecycle contracts without implying live synchronization, automatic collection, native database migration or remote execution.
