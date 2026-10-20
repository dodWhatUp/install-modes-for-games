# MCI-08 — bounded seed checkpoint source proof

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
