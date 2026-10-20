# Shared build blueprint — conclusions

Date: 2026-10-20. Basis: `d94e1096e101bd7ba8395119a9a076eb5b888ab5`. This is a planning/projection extension, not a new synchronization service or additional accepted program checklist items.

## 1. Existing plan and reuse inventory

The [integrated plan](../INTEGRATED-SYSTEM-EXECUTION-PLAN.md) already contained the 18 MCI packages, 108 checks, 36 GT requirements, common contracts and dependency graph. The portable-workspace and control-center documents retained detailed use cases. Existing code owned bounded reading, schema validation, local revisions, journal/locks, vault routing, policy/access, Windows verification and the human renderer.

Decision: extend that master plan and its source owners. Do not create another program/task database, parallel synchronization engine, credential store or independent UI. GitHub remains the implementation tracker; TickTick remains the explicitly reconciled private view. Existing task IDs/checklist identities and accepted count 47/108 are preserved.

## 2. Common core and specialized systems

The master plan now explains seven common components: identity/references, guarded storage, revision/evidence, policy/trust, explicit lifecycle, source projections and task-scoped build context. Ten system groups describe the differences for storage/handover, replicas, transports, central controls, information sources, chat continuity, remote actions, human overview, preflight/evaluation and an optional companion. MCI-02 owns contracts; MCI-18 qualifies the integrated enabled system.

The [build map](../INTEGRATED-SYSTEM-BUILD-MAP.json) supplies inputs, outputs, invariants, source owners, adapter differences, failure cases and acceptance boundaries. It references the original task manifest for status and steps. Planned contract boundaries are explicitly distinguished from implemented APIs. Current Windows-account human acceptance remains pending; native Codex portability and remote authentication remain separate stages.

Decision: implement shared logic once and add thin adapters only where platform, provider, storage topology or content semantics differ. Keep live local state separate from immutable exchange objects. A common logical workspace is not one shared live database or instant consistency between disconnected writers.

## 3. Working human and AI reading prototype

The existing `GameToolSystemControl.py` now offers `build-plan`, `build-context` and `build-report` with an explicit source root. A selected `--task MCI-08` packet derives its checklist/prerequisites from the existing manifest, includes relevant core/adapter contracts and current source hashes, and omits unrelated task bodies and full code/chat content. The source graph records all three owners: build map, task manifest and master plan.

The existing report renderer adds a build-specific human introduction and plain-language receives/produces/specific-work sections, with machine records behind a second disclosure. The same search and keyboard/disclosure controls are reused. Nested evidence lists no longer become independent filter records. Filtering changes presentation only. No network call, model request, dispatch, operational configuration or persistent UI preference is created.

Decision: the person reads one overview and can inspect detail; an AI retrieves one relevant implementation packet and then the exact cited code. Neither view has authority to override applicable instructions, authorize a service or infer hidden model behavior.

## 4. Verification and efficiency evidence

Twelve new build-map tests passed. The final Windows regression set passed 79 cases with two existing environment skips. Eight final isolated Chromium checks passed for the new report: semantic region/record counts, human overview, filtering, Escape reset, keyboard disclosure, narrow layout, 200% text scaling and absence of external requests/page errors. Five existing report browser tests passed with the updated renderer. Final wide/narrow screenshots were retained privately; the wide render was inspected visually. Linux was stopped cleanly; host input and Windows GUI were not used. This is not a human usability study or second-computer acceptance.

For the current MCI-08 example, compact JSON is 9,829 UTF-8 bytes versus 27,054 bytes for the full build packet (36.33%). This demonstrates selective context size only. Actual model tokens, elapsed development time, quality and rework were not measured. No API evaluation or paid model call was made. Full content remains available on demand; required constraints and source references are retained.

Decision: use scoped retrieval to reduce repeated context, then measure real quality/cost only through the separately authorized evaluation stage. Do not claim a token-saving percentage from byte counts.

## 5. Next implementation boundary

MCI-08 checkpoint preview is the next eligible storage slice: explicit selected classes, parent revision, exclusions, object hashes and missing coverage; then one immutable synthetic checkpoint and reopen. This stage did not implement MCI-08 storage behavior or check off its items. MCI-13 still needs the human Windows success/cancel check and destination acceptance. Remote/network/cloud/native-chat capabilities follow their declared dependencies.

Codex installation/configuration/native state, Windows sign-in settings, credentials, installed toolkit, real project defaults and existing Drive objects/links remain unchanged. No background service, automatic tracker synchronization or future run is activated.
