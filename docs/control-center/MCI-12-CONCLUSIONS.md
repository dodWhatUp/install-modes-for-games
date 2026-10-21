# MCI-12 conclusions — 2026-10-20

Result: 6/6 original checklist items accepted for policy configuration, restrictive decisions and reference staging.

Rules scope account, workspace, project, source device, destination device, capability and content class. A-to-B and B-to-A configure independently. Transfer, file adoption, index refresh and context exposure are separate booleans. Manual, checkpoint, reconnect, interval and debounced triggers calculate eligibility only; they create no scheduler or transport.

Effective decisions intersect matching destination rules and exactly acknowledged central proposals. Local hard exclusions and unsupported content classes deny all effects. Peer content cannot grant authority. Central proposal edits invalidate the earlier acknowledgement. Every result cites matched/ignored rules, policy revision, restrictions and uncertainty.

Context levels are none, notice, summary, task_packet and selected_details. Active or unobserved turn boundaries keep references staged. A reported new-turn/on-request boundary can release a reference notice only under the unchanged policy. Native model-context delivery is not connected; no active Codex chat is modified. Actual platform turn integration belongs to continuity and transport consumers.

Edits remain previews until the exact digest is accepted. Preparation and commit both check the base revision; an edit cannot silently rebase an older body onto a newer state. Granular rollback creates a new revision of one rule, preserving other directional settings and writer history. Presentation visibility has no enablement effect.

Evidence: 17 policy tests passed in the isolated Linux guest, including schema, scope/direction isolation, controls, all context levels, triggers/clocks, local exclusion, acknowledgement drift, peer data, cancellation, staged references and granular rollback. The final native CLI integration also required current policy acknowledgement and enabled adoption before placement.

Decision: accept the original policy-source criteria. This is a policy/eligibility implementation, not an active synchronizer, automatic context injector or remote executor. Those effects keep their separate source owners and acceptance gates.
# Versioned queue/configuration correction — 2026-10-21 source candidate

The PR #31 continuation reproduces the legacy two-reference invalidation, then
adds an explicit `effective-config-v2` policy revision scheme. Rules, exclusions,
exact central acknowledgements and unknown future configuration fields remain
in the effective digest. Queue and presentation mutation remain in LocalState's
full-body CAS/audit revision without invalidating unrelated v2 notices.

`propose_revision_upgrade` is a non-writing exact proposal. Acceptance preserves
legacy queued rows and old hash meanings; the access owner refuses managed
effects until an administrator pins the new revision and the device explicitly
acknowledges it. Old rows require an exact `restage_context` proposal and commit.
Central acknowledgements continue to reference their exact unchanged rules.
No existing store is automatically migrated. Notices still require a reported
supported boundary and deliver no model context. Real rule/ack/exclusion changes
still invalidate references. The existing CLI and schema expose the new scheme.

See [current checkpoint continuation evidence](MCI-08-CONTINUATION-VALIDATION.json).
This is source-candidate correction, not deployment or new acceptance. MCI-12's
existing 6/6 scope and the program's 47/108 accepted checks are unchanged.
