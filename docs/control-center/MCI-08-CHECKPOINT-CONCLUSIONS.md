# MCI-08 — bounded seed checkpoint source proof

## Local handover preparation — 2026-10-21

Continuation from `0969584` adds exact-plan local quiescence through the existing
checkpoint/access/Journal owners. It verifies the published v2 graph and current
selected saved files under the existing locks, then invokes local stop. Evidence
and all authority stores must remain off the data volume. The operation writes no
data-volume bytes and creates no drive lease/owner registry. Inspection remains
local while access is stopped or the data volume is absent. Missing/cancelled
receipts, unknown locks, changed local revisions and replaced stop markers never
become a release claim or automatic replay.

All receipts retain `physical_transfer_ready: false`,
`all_writers_released: false` and pending native unmount. This is the local
preparation portion of the original drive-handover check. Actual external writer
shutdown, native OS release, physical movement and destination acceptance are
still separate. An actual forced test-child exit after local stop preserved stop,
all three stale cooperative locks and inspectable pending evidence. A fresh
receive test verified complete receipt-pending payloads into another new
operation while preserving the original attempt and journal unchanged.

A retained one-host native Windows fixture passed full/delta publication,
inactive byte and functional readback, local preparation and stop inspection
using real principal and volume observations. It used local OS-session test
authorization; no protected prompt, eject, move or other physical host was tested.
See [stage verification](MCI-08-HANDOVER-VALIDATION.json).

The selected stage checks have **127 distinct passes and two environment skips**
across 129 Python cases, including 26 new handover/acceptance-preparation cases.
The 69 source-export contracts passed. An initial negative-test setup omitted its
required project ID; that fixture was corrected and the case passed on recheck.
The validation record keeps that correction and targeted case accounting explicit;
earlier/intermediate runs are not added again. Windows symlink privilege and the
optional `jsonschema` dependency remain the two skips; no dependency was installed.

The [native acceptance packet](MCI-08-NATIVE-ACCEPTANCE.md) prepares explicit
Windows success/Cancel on A and B, fresh local grants, physical release/return
and unexpected-removal recovery. Source-pinned private launchers and inert B
request templates are retained outside Git. The Windows harness now defaults to
non-writing preflight; `--run-interactive` is required for its two human prompts.
An available verifier is not an interactive pass.

One reproduced limitation is now explicit: a stopped registry older than the
existing 300-second freshness window cannot resume or heartbeat through current
authorization. Tests confirm refusal without timestamp renewal or stop removal.
Production stale-device reauthorization is an access-owner follow-up, not a
bypass added to checkpoint handover.

**Acceptance stays 47/108; MCI-08 0/6; MCI-13 5/6. Next environment: Codex** for
the prepared native/physical checks. Return to ChatGPT Pro if evidence requires
changing the accepted authority, ancestry, stale-device reauthorization or
recovery contracts. This stage installs and merges nothing.

## Continuation candidate — 2026-10-21

The reviewed PR #31 seed at `cc5d8f2841f562f611cec4864c9b3f9ec490af18`
is extended through the same checkpoint, UserData, Journal, vault, policy, access
and CLI owners. The earlier dated proof below remains historical evidence.
Current verification belongs to
[the continuation machine record](MCI-08-CONTINUATION-VALIDATION.json).

Windows verification: **271 passed, eight environment skips, no failures/errors**.
Ten focused Linux cases passed, including those eight gaps; two cases overlap
Windows passes. There are 279 distinct Python case identities across the selected
environments. The 69 existing source-export contracts also passed. Repeated and
intermediate runs are not added to these counts.

Independent audit reproduced three defects: Windows path/handle `ctime`
observations could falsely reject unchanged streamed files; an accepted plan
could omit its exact revision vector; reconstruction inspection could accept an
unrelated or cancelled audit as completed evidence. Fixes keep path and handle
change checks separately, require all three exact revisions, and bind successful
audit intent, owner, result and terminal event. Inspection also enforces logical
workspace/project scope before reading payloads and refuses unlisted restored
content. Torn publication evidence is explicit uncertainty, never success.

The additive v2 format implements bounded single-parent full/delta packages,
explicit expected ancestry and complete selected-state closure. Full and delta
representations share checkpoint identity but have distinct package identities.
The eight-node ancestry bound, existing 512-file/16 MiB-file/64 MiB-checkpoint
bounds and 1 MiB streaming buffer are deliberate proof limits. Ancestor bytes
are also bounded by the selected graph; this is not a production throughput or
peak-memory claim. V1 seed hashes have a golden compatibility fixture.

Locally staged carriers receive fresh destination-local read/write checks and
new operation receipts identifying received, verified and unadopted state on the
target replica. Missing/wrong/unlisted/duplicate parents, corrupted objects,
changed sources, expired access and stop refuse. Repeated operation IDs never
overwrite prior evidence. Locator order does not select ancestry or a winner.
No network transport or sender-authentication claim is supplied by a checksum.

Restoration remains an inactive new copy. Selected recovery preserves the
interrupted directory and later work. Granular rollback restores selected bytes
from the exact direct parent into another new inactive copy; it does not rewind
active files. Both bind current before-images and label subset receipts and
inspection as `whole_checkpoint: false`. Imported scripts/instructions do not
execute, and receipt recovery never appends or repairs an old journal.

The synthetic A→B→A harness uses independent local policy/access/binding stores
and distinct replicas. It separately verifies returned hashes and a known benign
relative-reference/arithmetic oracle. Only manifest/object bytes cross its
authored carrier. No native identity, binding, grant or credential is copied.
The retained evidence excludes authorization stores. It is not two physical
computers, protected Windows presence, a moved drive or native chat acceptance.

A separate one-host fixture also passed with the actual Windows principal and
`windows-volume-guid` observer on a verified non-system NTFS volume, without
identity/volume mocks. Five benign files across all four classes passed full /
delta publication, exact-parent verification, byte readback and inactive
relative-reference/arithmetic restoration. Fixture authorization stayed on the
system volume outside the vault/data volume and was left stopped. This uses the
existing local OS-session test mode, not protected Windows presence acceptance;
no physical release/unmount, other computer or production project was tested.

The policy coupling repair is separately versioned under the existing policy
owner: effective configuration, queue/view mutation and store CAS remain
distinct. Explicit upgrade changes the digest, requiring fresh access pin and
device acknowledgement. Legacy queues are preserved and require explicit
restaging. Legacy hash meanings and exact central-rule acknowledgements are not
silently changed. The same renderer exposes history capacity and freshness
limits; no epoch reset or expiry bypass is implemented.

The existing build reader rechecks its aggregate source vector and derives
relevant shared-owner gate summaries from the task manifest. Original MCI/GT
IDs, dependency arrays and acceptance checklists stay unchanged. Hash-bound
example files now retain LF bytes on Windows checkouts.

**Acceptance remains 47/108; MCI-08 0/6; MCI-13 5/6.** Source/synthetic tests do
not automatically accept an original product criterion. Physical release and
surprise-removal recovery, real destination binding and protected Windows
success/Cancel, active adoption, conflict reconciliation, native chat/context,
network/cloud/remote operation and whole-program release remain independent.

**Next environment: Codex.** Continue source review and the existing platform /
physical acceptance gates when their actual capabilities and human actions are
available. Return to ChatGPT Pro if those observations require a material change
to the accepted authority, ancestry or recovery contracts; no architecture
decision blocks the implemented bounded source workflow.

## Original seed proof — 2026-10-20

Date: 2026-10-20. Baseline: `9683b32ca6260b060f4727937f26e6a4a96d50de`.
Candidate: `agent/shared-workspace-pro-followup-20261020-00e82af0`.
Status: **source/synthetic proof passed; not installed or adopted into main**.

## What was implemented

The existing managed-workspace CLI now exposes a non-writing seed preview,
exact-digest publication, read-only attempt inspection, a separate inactive
reconstruction preview/commit, and reconstruction inspection. It does not
bootstrap authorization or install a runtime.

The new checkpoint format adapter composes the existing VaultRegistry,
PolicyStore, AccessStore, Journal and cooperative locks. UserData supplies two
additive bounded streaming primitives; the legacy private archive body, format,
limits and readers are unchanged. There is no second credential store, registry,
approval queue, renderer or transport service.

Logical checkpoint identity is separate from package representation and local
operation identity. The initial directory-object representation contains only
explicitly selected saved files. It declares missing unsaved/unselected coverage,
not application-consistent snapshots. Parents, deltas and tombstones are rejected.
Known instruction-discovery filenames and the existing sensitive path/classes are
outside this first proof. This is not a general secret scanner.

## Effects and recovery

Preview reads granted selected sources and pins binding/access/policy revisions;
it creates no lock, journal, directory, cache or persistent record. Publication
requires current per-class source read and output write grants plus transfer
policy. Reconstruction additionally requires adoption/write policy for the
logical content classes and the managed output class. Inspection rechecks each
included class's read permission before reading payloads.

Operations use the existing access -> policy -> binding lock order. Stop,
expiry, scope and exact revisions are rechecked at streaming boundaries. No
heartbeat or enrollment is automatically renewed. Operation IDs bind deterministic
new destinations (`checkpoint-ID`, `reconstruction-ID`) within selected results;
repeated attempts are inspection-only, never overwritten or replayed.

Publication writes its marker only after payload verification and a source
recheck. The existing Journal records intent, result and terminal evidence.
Missing terminal evidence is `PUBLISHED_RECEIPT_PENDING`, not false success or
permission to reconstruct. Inspection does not repair journals or remove locks.
Actual forced child-process exits leave stale cooperative locks for inspection;
only the test's own temporary fixture cleanup removes those test directories.

Reconstruction writes a new inactive directory. It verifies final destination
bytes and a benign relative-data-reference oracle without running imported code.
Missing/partial files remain `RECONSTRUCTION_INCOMPLETE`; receipt loss after bytes
complete remains `RECONSTRUCTED_RECEIPT_PENDING`. Existing destinations and later
external edits are preserved. No active binding/head, index, context, instruction,
profile or chat is activated. External programs outside the manager are not
claimed controlled; actual use needs an appropriately inactive destination.

Files are flushed/fsynced. This proves the named process-interruption protocol,
not power-loss durability, physical detach or transactional external applications.

## Verification

[Machine record](MCI-08-CHECKPOINT-VALIDATION.json): **43 new checkpoint tests
passed**. **169 existing regressions passed; two environment-dependent cases
were skipped**. Total: **212 passed, two skipped, no failures/errors**, counting
only the final distinct cases. Earlier runs are not added again.

The suites cover preview purity; explicit coverage; byte/path/type/size limits;
source/configuration drift; scope and per-class permissions; duplicate attempts;
corruption; stop/expiry including a mid-file stop; publication/reconstruction
receipt loss; injected resource failures; two actual test-child process exits;
new-copy functional data reading; portable metadata privacy; and all six existing
CLI entry modes through explicit synthetic fixtures.

A separately retained harness run published/reopened/reconstructed five benign
files across all four managed content classes. It checked a relative reference
and arithmetic result, retained only synthetic payload/evidence, stopped fixture
access and exported no local grants/bindings. Receipt and source hashes are in
the machine record. Actual code ran on macOS Python 3.9.6, but identity and volume
observations were explicitly mocked. No native macOS account/volume adapter was
added, and no native Windows GUI or second computer was tested.

The skipped cases are the existing optional jsonschema check (dependency absent)
and an existing child-process principal test that requires supported Linux/Windows
identity. These are not passing native/platform evidence. The new child tests
supply their own explicit synthetic identity. No dependency was installed.

## Earlier review finding reproduced, not silently repaired

The previously static MCI-12 queue-coupling finding was reproduced against unchanged
`policy.py`: stage A, stage B, then request A's notice; a queue-only change is
reported as policy drift. This raises its evidence from static analysis to a
reproduced fixture. A versioned separation of policy configuration, queue state
and acknowledgements remains a separate change; no security hash or existing
acknowledgement was reinterpreted in this source candidate.

## Stable acceptance and next boundary

Program acceptance remains **47/108**. MCI-13 remains **5/6**. None of the six
whole original MCI-08 criteria closes automatically: seed+delta, full rollback,
package ordering/parents, drive handover and A-to-B-to-A still need their complete
evidence. This is partial source evidence for GT-063/064/076/080, not their broad
acceptance. The master task manifest and task trackers were not changed.

Next source work is full/delta packaging and remaining MCI-08 recovery semantics
on this tested seed contract, after source-candidate review. Human Windows
success/cancel and independent destination acceptance remain separate gates.
Real moved-drive/network/cloud/native-chat/remote-operation release claims are
still unavailable. No production data, installation, native configuration,
credentials, services, schedules, task systems or paid model trials changed.
