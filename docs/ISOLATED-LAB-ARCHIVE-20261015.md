# isolatedLab Mac knowledge archive — 2026-10-15

**Current user decision: preserve the knowledge and reproducible source; remove this Mac's VM installations and heavy artifacts.** This supersedes the earlier local guest-first activation request. Removal is in progress until the final cleanup receipt is recorded below. Nothing in this archive authorizes installation, guest startup or automatic restoration.

## What to retain

The editable implementation remains in [the Mac source](../examples/isolated-lab-mac/README.md), with its exact `MAC-SOURCE-MANIFEST.json`, dependency records, tests and preserved upstream worker. The [dated Mac report](ISOLATED-LAB-MAC-20261013.md) preserves the actual acceptance and subsequent Parallels comparison. Source snapshot `548bde0273bbd1d0b78e5f4aae2ad78907de96ed` and comparison snapshot `0c89b5a10b4a33c42b4f6027072f56c083ca54c3` remain immutable historical references.

The private knowledge package includes the original task, a visible user/assistant message projection, the installed skill definition, the exact managed instruction block, the original pending Global request/audit, source/docs, selected acceptance summaries and a per-file SHA-256 manifest. It excludes reasoning, tool dumps, passwords, license/account exports, transport/SSH/backup keys, VM disks, installers, package caches and personal Windows profiles. The message projection is bounded to this chat as available before packaging; final cleanup receipts are newer and separate.

The existing private Drive folder is [isolatedLab source and continuation](https://drive.google.com/drive/folders/1SFxsgTctZoJqwzWuWhADNA14poM6f0in). Its current status, continuation and START-HERE records must point to this archive state. Old small immutable source packets remain useful; a VM image backup is not required for reconstruction.

## Consolidated ownership and retrieval

The user's follow-up explicitly requests Git and Drive preservation integrated with earlier knowledge, without duplicate masters. This guide consolidates the decisions, methods, failures and reconstruction route; the dated acceptance report retains detailed historical evidence. The implementation stays in its existing Git directory. No second repository, Drive folder, source master or replacement knowledge ZIP is created for this consolidation.

| Information | Maintained owner or existing retrieval record |
|---|---|
| Editable source, methods and reconstruction | This Git guide and `examples/isolated-lab-mac/`; source history and exact manifest remain intact. |
| One Drive entry point | [START-HERE](https://drive.google.com/file/d/1TxvlnQHmUAvduUv0OroIuVjhWXHZr6Eg/view), updated in place; contains the current artifact map and explicit historical labels. |
| Actual current cleanup state | [MAC-STATUS](https://drive.google.com/file/d/112-iQf_Ldd34KHWE48rknN4CtJ_1KPd5/view), updated in place; old acceptance is historical, not current readiness. |
| Precise unfinished boundary | [MAC-CONTINUATION](https://drive.google.com/file/d/1Btb2RYL6Ibw27F-YZTiwYlSZSKlrvb4e/view), updated in place; points to the same source/status and existing OS-auth job. |
| Immutable private knowledge snapshot | [The verified 2026-10-15 ZIP](https://drive.google.com/file/d/1EKvbgzW_lIhkou9juhHT_Q8SCilO2u4i/view); the hash and coverage below remain unchanged. It also preserves the earlier full status, continuation and index, so the live records can be concise. |

Older base/Windows/Mac source packets, hashes and standalone acceptance records are distinct version/evidence artifacts. They remain explicitly historical and are indexed once, not promoted as additional current installations or editable masters. The separate Windows reference machine's evidence is not this Mac's readiness or cleanup state. The original setup prompts are historical requests; opening one does not authorize installation or restore the removed default.

Git publication remains on the existing candidate task branch/draft PR6; this is not main-branch or fleet adoption. Current Drive records are derived delivery/continuation records. Their in-place updates and independent byte readbacks, rather than additional parallel documents, provide discoverability and continuity.

## User requirements and working method

- Keep normal Mac mouse, keyboard, focus and display use undisturbed. Use structured guest observations; no screen/video capture or automatic host-input fallback.
- Keep each selected project's source master in its original owner. Transfer only the selected files into an owned guest workspace; retrieve new outputs with exact hashes and refuse overwrites.
- Inspect the real host/guest architecture, version, entitlement, permissions and owner before acting. Linux acceptance does not accept Windows Arm or native macOS applications.
- Use reservations, exact VM/session/process identity, current DOM/accessibility snapshots and bounded commands. Preserve the same request and effects after a timeout; never replay an unknown mutation.
- Preserve original sources, failures, tested limits and later edits. Publishing code, installing a skill, observing a tool and accepting a real workflow are distinct events.
- Keep secrets and machine binding private. A future reconstruction creates fresh secrets and identities rather than importing old personal profiles.
- Complete feasible authorized work autonomously; request only a consequential unresolved choice or unavoidable account/OS consent. Do not purchase an edition or schedule continuation without authorization.

## What actually worked, and what did not

The accepted Linux implementation used Lima 2.2.1 with Apple VZ, pinned Ubuntu 24.04 Arm minimal, two vCPUs, 4 GiB RAM and a sparse 12 GiB disk. Plain mode disabled host mounts, clipboard/device/display integration, container services and agent forwarding. Browser checks used real Chromium DOM; native Linux checks used a private D-Bus/AT-SPI/Xvfb session through the enrolled SSH/HMAC bridge.

Historical evidence: 31 offline contracts; 37 selected build/browser/native checks; a 300.01-second mixed run with 407 technical checks and the separate user answer “No interference in any of the four”; two cold starts of fresh provisioning and restored copies; 26 recovery operations; and a fresh normal development chat that implicitly selected the guest and passed 35 browser checks. These are dated results, not a claim that a removed guest remains ready.

| Problem or boundary | Retained lesson |
|---|---|
| macOS UNIX socket path/name too long | Use a short private lab path and instance name. |
| Archive extraction and old host Python | Verify paths, types, exact entry sets/sizes/hashes before extraction; explicitly validate the known documentation symlink and omit it. Use the provided compatible extraction path and dedicated validation environment. |
| Bootstrap SSH host key changed after a cold start | Strict checking stopped transport. The accepted repair enrolled a separate persistent guest SSH service and verified signed cold roundtrips. Do not disable host-key verification. |
| Forwarding not ready immediately after a reported cold boot | Observe the dedicated SSH banner under a deadline before the first authenticated request. Inspect existing effects before any repair. |
| Missing output destination or wrong report shape | Preserve the failed report; inspect admitted requests and active sessions before correcting the bounded caller. |
| VZ native live snapshots returned `unimplemented` | Tested stopped encrypted checkpoints and fresh-identity restoration were the measured recovery route. Image restoration itself required new runtime acceptance. |
| Private Xvfb has no graphical OS login lock | Provider crash/unresponsiveness tests do not establish Windows/macOS login-lock recovery. |
| Parallels broad current-user probe returned `Invalid argument` | Retain the failure and reduce to narrow read-only observations. No mutation retry was involved. |
| Parallels Linux inventory discrepancy | The user clarified that only Windows was created; no live Linux-to-Linux comparison was performed or needed for the earlier default recommendation. |
| Parallels Control Center/menu difficulty | The documented route was the Parallels Dock icon → Control Center → `+`. Actual opening was not confirmed. The pending text-only menu query was stopped; no UI verification was claimed. |

Parallels 27.0.3 had matching Tools in Windows 11 Arm. Read-only system/current-user commands and UI Automation pattern observation worked, without invoking application actions. The local license reported a valid Pro trial through October 26, 2026; paid CLI entitlement was not established. Formal Windows enrollment, guarded actions, recovery and human acceptance were not completed. Snapshot creation/reversion, comparative performance and graphics were not tested. Existing personal sharing was not an isolated configuration. Native macOS adapters were not implemented or accepted.

## How to recreate later, if explicitly requested

1. Retrieve the preserved source/docs and independently verify the supplied ZIP hash plus every source-manifest path, size and hash. Check for newer owner guidance and actual destination compatibility. Do not execute an old personal binding.
2. On a compatible Arm Mac with sufficient storage/memory, read the source README and `RESOLVED-GUEST-DEPENDENCIES.txt`. The original known release archive SHA-256 was `9e9eacce88f37e185c346bad73aa6136f738d8cdf8c3bb23cd42b071824bc66e`; the Ubuntu image SHA-256 was `fbf6b15c50c474dc6dee5b3c74da212bb687a2625e877227828e6492d88dc151`. Inspect current availability/support rather than silently substituting another image.
3. From the verified source, use `python3 prepare_lima.py --root <short-new-private-root>`. Existing enrollment/admission stops replacement. The runner downloads pinned tools, provisions the guest and creates fresh local transport/SSH identities. Guest dependency scripts must run inside Linux, never on the Mac.
4. Run the meaningful offline contracts and selected Linux runtime acceptance; verify cold starts, source/result bytes, DOM/native stale guards, interruption recovery, empty owned sessions and normal shutdown. Repeat the announced user-present interval and independent four-part interference report before accepting normal-use compatibility.
5. Install/bind the skill and managed default only under a new explicit request after readiness is established. Preserve the current global instructions and prove actual tool discovery plus implicit normal-chat selection. Archiving this request does not reactivate it.
6. If Windows work is needed, install signed Parallels, sign in through normal user-owned account/OS consent, establish actual edition entitlement and prepare a fresh owned Arm guest. Implement/test the Windows adapter and isolation configuration separately. Do not treat the historical read probes or reference Windows x64 acceptance as this Mac's Windows acceptance.

An old Windows or Linux disk is unnecessary for this route. Rebuild applications and dependencies from preserved authored source. Personal accounts, product keys, guest data and old machine secrets were not included in the knowledge backup.

## Cleanup scope and remaining physical constraint

The authorized local targets are the observed Windows 11 Parallels bundle, Parallels Desktop and its identified support/download/shortcut files, the enrolled private Lima lab, owned fresh/restore test namespaces, the verified matching Lima image cache, and the installed guest-default skill/block. Unrelated projects, general tools and other product caches are outside this cleanup.

The old stopped encrypted Linux image backup was recorded on the external volume `ssd daniel`. That volume is not mounted at the current inspection. Its bytes cannot be removed or verified until it is connected. No background cleanup or future wake-up is scheduled. Old image/key material is not part of the new reconstruction package.

Parallels documents [app removal](https://kb.parallels.com/en/124255) and [separate VM deletion](https://kb.parallels.com/en/5029); removing the app alone does not remove its VM disk. Removal of root-owned app/support files may require the normal macOS administrator prompt. Subscription cancellation is separate and was not requested.

## Final cleanup receipt

Knowledge backup: [verified private ZIP](https://drive.google.com/file/d/1EKvbgzW_lIhkou9juhHT_Q8SCilO2u4i/view), 345554 bytes, 47 payload files plus manifest, 66 visible messages. SHA-256: `edbf23e69590d8de9cb78b8d57a2c5e8e8f768a04e864bbc88deb9222a6b5403`. Independent Drive byte equality, ZIP CRC, exact entries/sizes/hashes and file-only extraction/readback passed. Owner-only file permission metadata was verified. The immutable package captures source/guide checkpoint `29548f164f6a65e7fb39b00948feb9b6031483a2`; this receipt and the current Drive records are newer.

Completed locally: normal ACPI shutdown and exact deletion of the sole registered Windows 11 guest, with empty Parallels inventory and absent bundle readback; removal of the stopped enrolled Lima guest, restored disk staging, three owned fresh/restore namespaces, matching hash-verified Ubuntu download/conversion cache, Parallels Windows ISO/installer and user support/preferences/VM launchers. The exact managed global default block and matching installed skill/old bindings were removed while preserving all other global instruction bytes. Global default draft PR19 was closed without merging; its original candidate and audit remain preserved.

Observed free-space increase after these operations: approximately 53.1 GB (49.5 GiB). This is a before/after available-space observation; final accounting is in the machine-local receipt.

Still pending: normal administrator authorization for the root-owned Parallels app/system support removal. Three app CLI wrapper symlinks and a small root-owned log were additionally identified for bounded cleanup. The offline external encrypted image backup also remains physically undeleted until `ssd daniel` is connected. Subscription cancellation was not requested. No automatic reinstall or future wake-up was scheduled.
