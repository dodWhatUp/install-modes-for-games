# MCI-05: human device, synchronization, change and chat overview

Outcome: implemented an in-memory view of selected device reports, transfer lifecycle declarations, gaps/conflicts, activity goals/outcomes/blockers, changed artifacts and continuation boundaries. Existing journal input goes through GameToolJournal's hash-chain validator and projects only event metadata, not private payloads or commands.

Decision: recent reports are not live connections; receiving bytes is not adoption or context refresh. Unknown operations and incomplete transition history stay visibly partial. Chat summaries are source-owned selected records, not an automatic native-chat reader.

Full referenced UTF-8 content is read only after an explicit selected-reference request and local authorization, with exact hash and bounded-root checks. No-store views write no index/cache; detail is cleared when leaving the tab, switching context, forgetting detail or clearing the view. Upstream retention remains with its original owner.

Validation covers stale/unknown devices, event gaps, summary-only projection, full-content denial before authorization, changed detail refusal, validated journal reuse and no-store UI clearing. No actual two-device transport, native-chat adapter or always-on monitor is claimed.

Next: connect real transport receipts after MCI-08/10 and actual supported chat summaries after MCI-15. Keep unsupported/missing content visible.
