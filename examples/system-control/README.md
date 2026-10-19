# System control center: read-only source application

Start with [P0 conclusions](../../docs/control-center/P0-IMPLEMENTATION.md), [stage reports](../../docs/control-center/STAGE-STATUS.json), [reuse inventory](../../docs/control-center/MCI-01-INVENTORY.json) and [validation](../../docs/control-center/P0-VALIDATION.json). Component version: 0.1.0-preview.2; adopted toolkit source remains 0.27.

Double-click scripts/GameToolSystemControl.pyw using an existing Python/Tk runtime, or run python -B scripts/GameToolSystemControl.py gui. The existing Hub's optional System control route uses the same panel/services. The initial example contains invented devices, events, chat summary, conversation and attachment references. Opening the source preview does not update/install Codex or the installed toolkit.

View current project inventories source owners. Select global guidance, add a skill folder or select a capability catalog explicitly to expand the view; skill folders are scanned one level only. A .system/plugin folder needs its own selection. Actual runtime load, account memory, tool permission and schedules remain unknown unless separately observed/reported. Missing sources and bounded omissions stay visible.

CLI modes: explore, preflight, overview, inventory, report, journal and gui. --context, --root, --scope and --query select evidence. Inventory requires --root; optionally add --global-root, repeated --skill-root, --catalog and project-relative --cwd. Private bindings come only from the caller; context JSON cannot supply root authority. Inventory output contains relative references; supply the explicit roots again to verify them. Report prints standalone HTML. UI Save accessible report creates a new file and refuses overwrite.

Capability catalogs use schema_version 1, kind GameToolsCapabilityCatalog, tools/automations arrays of name, description and optional trigger_terms. They describe selected declarations, do not execute commands and do not establish live account access. Keep real catalogs/roots private.

Preflight accepts the original draft, optional intended outcome and scope/device report. CLI uses --draft and --intended-outcome. The original stays separate; a suggested alternative needs deliberate acceptance with unchanged source/draft revision. No submission or exact-model prediction occurs.

Activity summaries do not fetch referenced bodies. Select a reference, authorize and choose Read selected detail. Text is at most 128 KiB; conversation projections at most 2 MiB with bounded messages and explicit visible_messages/selected_messages/source_export coverage; attachments at most 16 MiB. The invented examples demonstrate each route. Content requires exact source hash/root/locator; native databases, profiles, credentials, unsafe paths and linked sources are refused. Binary bytes remain in memory with an integrity receipt; no external application opens. Projections do not import native chat identity or resume original Codex chats.

Context/ordinary selected text is bounded to 128 KiB each, 32 selected sources and 2 MiB combined; JSON has depth/value/schema bounds. Journal mode requires --journal PATH and uses the existing validator. Detail is released on filter/tab/context change, forget, clear, close or failure. Durable reports omit no_store and session_only summaries and every full body. Upstream retention remains source-owned.

Keep personal contexts, journals, drafts, native exports, reports and bindings outside Git/OneDrive. No background service, task master, synchronization or native chat store is created. Transports, native continuity, remote effects and destination acceptance remain dependent work packages.
