# MCI-02: shared contracts and source boundaries

Outcome: implemented versioned context validation, source-bound stable IDs/revisions, dependency checks, checkpoint ancestry declarations, declared clone-conflict checks and the separate receive/verify/stage/adopt/index/context lifecycle.

The [schema](../../schemas/game-system-context.schema.json) defines shared resource, instruction, capability, checkpoint, policy, operation/receipt, activity, context, preflight and task-reference handoffs. Existing canonical JSON revision helpers are reused. Selected-root bindings stay local; path identity does not become a global resource identity.

Decision: accept additive unknown fields as inert data; refuse unsupported versions, duplicate JSON keys/IDs, cycles, missing references, nonfinite/deep/oversized data and stale selected sources. The existing bounded reader supplies filesystem identity and link checks. Native state/credential classes are outside this reader. All validators and lifecycle explanations have effect none; they do not implement future transfer or authorization enforcement.

Validation includes changed sources, inaccessible roots, traversal/symlink refusal, conflicting clone declarations, supported unknown-field preservation and wrong ancestry. Physical clone detection and real multi-device reconciliation remain future MCI-07/09 acceptance.

Next dependencies: MCI-03 source explorer, MCI-04 static preflight and MCI-05 evidence overview.

Compatibility finding: existing authored-source exports use uppercase SHA-256 text. The knowledge reader now accepts either hex case while preserving canonical lowercase revision output. A regression test exercises the original export spelling; no archived package was rewritten.
