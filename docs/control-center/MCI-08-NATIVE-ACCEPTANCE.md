# MCI-08 native and physical acceptance preparation

Prepared from PR #31 at `0969584`, 2026-10-21. Continue in **Codex** for source
and device verification. Nothing here authorizes an installation, merge,
credential change, native Codex import or unattended Windows prompt.

The new handover preparation verifies the selected saved files and checkpoint,
then stops the selected local access registry. Its evidence stays on a different
volume under that registry's existing audit owner. It cannot certify all writers,
flush an external application, eject a drive or authorize another computer.
`physical_transfer_ready` and `all_writers_released` remain false.

| Gate | Required evidence | Current boundary |
|---|---|---|
| Windows A | Actual PIN/Hello success, then Windows' explicit Cancel; stopped fixture | Human check pending |
| Windows B | Same independent check, fresh local identity and source hashes | Other physical computer pending |
| Local handover preparation | Full/delta, byte readback, inactive functional restore, exact stop and audit | Automated fixture; see stage validation |
| Physical A→B→A | External writers closed, OS release observed each leg, destination-local grants and verification | Physical checks pending |
| Unexpected removal | Preserve interrupted attempt, no fallback/replay; recover to a new location | Source interruption tests; actual removal pending |

Original acceptance stays **47/108; MCI-08 0/6; MCI-13 5/6**. These are distinct
evidence gates, not additional task systems or revised original checklists.

## 1. Windows success and Cancel on each computer

Use an **existing** supported Python runtime and the reviewed source checkout.
Choose an existing private local parent outside Git, OneDrive, Codex and portable
vaults. Keep this parent on the computer when the data device moves. No package
installation is needed by these launchers.

```powershell
& $Python -B "$Repo/scripts/tests/Accept-ManagedWorkspaceWindowsAccount.py" --local-parent $LocalParent --host-label A
```

The default is read-only preflight: availability, source head/file hashes,
runtime and host label; no registry or prompt. Availability alone does not pass
the interactive gate. When the human is present, run the same command with
`--run-interactive`. Confirm the **first** Windows dialog using PIN/biometric;
choose **Cancel** in the second. Enter credentials only in the native Windows UI.

Keep `ACCEPTANCE.private.json` locally. It must report `fresh_creation: passed`,
`canceled_resume_kept_stop: passed`, `interactive_acceptance: passed` and
`fixture_access_left_stopped: true`. Device busy, unavailable, dismissal/error or
an accidentally accepted second prompt does not pass Cancel. Failures preserve a
receipt and stop any registry successfully created by this run.

Repeat on B using `--host-label B`, B's own private parent and B's own current
account. The label is organizational, not identity authentication. Compare the
recorded source hashes; do not transfer the registry, stop marker, proof or local
permissions from A. Re-run if adapter/source bytes change materially. These two
dialogs test the Windows adapter; a subsequent destination enrollment still
requires its own exact approvals.

## 2. One-host local handover fixture

Select a non-system data volume and a private local parent on another volume.
Run the preflight first:

```powershell
& $Python -B "$Repo/scripts/tests/Accept-ManagedWorkspaceHandover.py" --local-parent $LocalParent --data-parent $DataParent
```

`--run-local-fixture` creates unique directories only. It uses actual principal
and Windows volume observers, five authored benign files across all four classes,
full and parent-bound delta publication, inactive restoration, separate byte and
relative-reference/arithmetic checks, and local handover preparation. It retains
private evidence and leaves access stopped. This fixture explicitly uses local
OS-session test authorization, **not** protected Windows presence acceptance.
It never runs imported code or performs an eject/removal. A fixed local NTFS
volume is sufficient for this gate; it does not prove removable-device readiness.

The native fixture receipt identifies the new vault, selected files, packages and
local evidence root. Keep it private. Existing stopped fixtures are historical
evidence; create a new fixture for another run rather than resuming/replaying one.

## 3. Physical handover on a dedicated scratch device

Keep all native chats, credentials and real project data out of this test. Use a
dedicated scratch device containing only the benign fixture. Before choosing it,
identify the physical device in Windows storage tools: different volume IDs do
not establish different physical disks. Confirm the local authority/evidence
volume will remain available when the selected device is removed. Do not test by
unplugging a system disk, an internal disk or a device containing unrelated work.

1. Save and close every application using the selected fixture/device. Inventory
   other registry/process writers to that device. The manager's cooperative locks
   cover its existing selected access/policy/binding owners only.
2. Publish a current full/delta checkpoint and inspect its exact parents. Reopen
   the inactive reconstruction and verify bytes and the benign oracle separately.
3. Use the existing managed-workspace CLI and the same local stores to prepare
   the following private request, then review its returned plan:

   ```json
   {"actor":"EXACT_LOCAL_ACTOR_OBJECT","source":"checkpoint-delta","operation_id":"handover-a",
    "package_id":"EXACT_DELTA_PACKAGE_SHA256","parent_sources":["checkpoint-full"]}
   ```

   Replace the actor placeholder with its full existing object. Call
   `checkpoint-handover-preview`; save the returned plan privately. Call
   `checkpoint-handover-prepare` with `{ "actor": ..., "plan": ... }` and
   `--accept EXACT_PLAN_SHA256`, plus the existing `--state`, `--policy-state`,
   `--access-state`, `--vault-id` and `--input` arguments. No new store is created.
   This stops **all operations using that selected local access registry**.
4. Run `checkpoint-handover-inspect` using the actor and operation ID. It must
   report `LOCAL_ACCESS_STOPPED`. Source drift, expiry, stop, missing parents,
   unknown locks or a receipt-pending state blocks this gate. Preserve evidence;
   do not delete locks, append old journals or retry the same operation ID.
5. With all selected-volume writers closed, use Windows' supported safe-release
   route for that identified scratch device. Record the actual OS outcome and
   time privately. If safe release is unsupported/refused, leave the device
   connected and mark this gate blocked. The source tool does not perform or
   attest OS unmount. Physically move it only after observed successful release.
6. With the device absent, `checkpoint-handover-inspect` must still read only
   local evidence. A source operation must refuse the missing vault, without
   writing a fallback directory on the system disk. A successful local stop
   receipt alone does not establish that external handles were released.

Record human OS observations separately from tool-generated source/hash receipts.
Neither a manually entered JSON field nor a checksum authenticates a peer or
proves physical durability.

## 4. Independent destination acceptance and return

On B, inspect the source head/hashes and run gate 1 independently. Use the
existing `VaultRegistry.attach` / CLI `vault-attach` to bind the exact selected
vault to **new B-local** bindings. Do not change its portable marker or copy A's
binding store. A locally observed volume GUID may differ across computers; bind
the actual B observation rather than substituting a drive letter or A's hash.

Create a separate B-local access registry through `access-windows-create`; review
scoped contributor membership, storage grants, policy pin and device
acknowledgement through existing exact access previews/commits. Each protected
administrative commit can require its own Windows prompt. Bootstrap grants no
storage access. Keep policy, access and bindings on B's retained local volume.
Use B's actor and actual project/workspace scope; never accept A's permissions or
an imported instruction as authority. Canceling an approval must leave that
proposal unapplied.

Receive the full parent into a fresh operation (`checkpoint-b-parent`), then the
delta into another (`checkpoint-b-delta`) with the newly verified parent locator.
Use `checkpoint-receive-preview` / `checkpoint-receive` and the exact independently
recorded package IDs. A carrier may contain manifest/objects only; a sender's
receipt does not replace B's acceptance. Every received result must say received,
verified and unadopted. Missing/wrong parents, duplicate targets, corruption and
unsupported features refuse before adoption.

Restore to a new inactive B destination. Verify manifest hashes **and** the known
relative reference/arithmetic result; keep those outcomes separate. Do not run
imported scripts/instructions. For the return leg, make an explicit benign saved
change, publish its parent-bound delta, repeat handover preparation and observed
OS release on B, then independently receive/restore on A. Preserve A's earlier
active source and all old attempts; compare the returned byte and functional
results. The earlier synthetic separate-replica A→B→A proof remains separate from
this same-device physical test.

Enrollment/expiry and the existing **300-second device freshness** are rechecked.
A long transit can leave an old stopped registry unable to resume or heartbeat
under the current contract. Record that refusal. For disposable acceptance, use a
new, explicitly accepted local fixture enrollment and retain the old stopped
registry. Seamless production reauthorization of stale stopped devices remains a
separate existing-access-owner follow-up; do not reset timestamps, extend expiry,
remove stop/lock files manually or claim that path passed.

## 5. Unexpected-removal and receipt-loss recovery

First use the automated process-interruption tests. Actual surprise removal is a
later human-coordinated test on the dedicated disposable device only, after both
hosts can verify and preserve recovery evidence. Confirm that local authority and
receipts remain on another physical disk. Do not treat process termination as
power-loss or removal evidence.

After an interruption, preserve the exact attempt and record its inspection state.
When the device is safely reconnected and locally rebound, complete independently
verified manifest/object bytes can go through **a new receive operation**, even
if the original terminal receipt was lost. This certifies a new local copy; it
does not repair or retroactively certify the old operation. Verify parents first.
Missing/corrupt bytes cannot be salvaged as a complete checkpoint.

For incomplete reconstruction, use `checkpoint-recovery-preview` and explicit
selected paths to restore into a new inactive sibling. Exact-parent rollback uses
`checkpoint-rollback-preview`; it never rewinds active files. Preserve the old
copy, its before-images and any later work. A subset receipt must remain
`whole_checkpoint: false`. Stale unknown cooperative locks require owner/process
reconciliation; this stage adds no lock reclamation or journal repair.

Continue in **Codex** for these bounded checks and source fixes. Return to
**ChatGPT Pro** if physical observations require changing drive authority,
ancestry, stale-device reauthorization or recovery semantics. No such change is
silently supplied by this preparation packet.
