# isolatedLab on this Mac — 2026-10-13

**Status: selected Arm Linux runtime accepted locally; source distribution remains a candidate task branch.**

The [source README](../examples/isolated-lab-mac/README.md), [sanitized validation](../examples/isolated-lab-mac/VALIDATION.json), [exact source manifest](../examples/isolated-lab-mac/MAC-SOURCE-MANIFEST.json) and [resolved guest dependencies](../examples/isolated-lab-mac/RESOLVED-GUEST-DEPENDENCIES.txt) are the reusable implementation and setup routes. The canonical editable owner remains `dodWhatUp/install-modes-for-games`; private Drive distribution is derived. Earlier Windows reference acceptance and old immutable archives retain their own scope.

## Actual local evidence

The verified supplied ZIP matched `c40b3f17df0cdf670c3056c56862876b6dac1876d1f3696bacab6b73e440c34d`: exact sets, lengths and hashes passed for 12 outer records, 58 base files and 20 Windows files before extraction. No accepted Mac source was present in the checked owner/index. Preserved Linux worker files remain byte-identical to their verified upstream packet.

The host is Arm macOS 26.6.2, with 16 GiB RAM. The user authorized an alternative VM while handling Parallels account/installation separately. The selected backend is [Lima 2.2.1](https://github.com/lima-vm/lima/releases/tag/v2.2.1) with [Apple VZ](https://lima-vm.io/docs/config/vmtype/vz/), a fresh pinned Ubuntu 24.04 Arm minimal image, two vCPUs, 4 GiB RAM and a sparse 12 GiB disk. [Plain mode](https://lima-vm.io/docs/config/plain/) and measured configuration remove host mounts, device/display/audio integrations, container services and agent forwarding. Guest work uses loopback transport, headless Chromium DOM and private D-Bus/AT-SPI/Xvfb native accessibility.

| Test | Observed result |
|---|---|
| Offline contracts | 31 passed, including path/identity/resource/private-mode/authentication/admission/deadline/output/atomic-transfer guards and preserving later skill edits |
| Selected real source/build/UI fixture | 37 checks passed: Unicode, bounded build/deadline, non-overwrite/path guards, DOM/native actions and stale-state rejection, result hashes and exact cleanup |
| User-present mixed interval | 300.01 seconds, 11 workloads, 407 checks; temporary sleep protection released and guest normally stopped |
| Independent user interference report | Mouse: none. Keyboard: none. Focus: none. Display: none. Exact answer: “No interference in any of the four” |
| Fresh setup runner | Actual fresh private directory: pinned download, provision/enroll, two cold starts, stable signed probes, 37-check acceptance and normal stop passed |
| Stopped recovery | Encrypted checkpoint authenticated; all 20 selected files restored with exact hashes; fresh VZ/protocol/SSH identities, two cold starts, 37 UI/build checks and normal stop passed in a separate restored copy |
| Crash/helper recovery | 26 signed operations passed: process crash, exact provider PID/start-time/group guards, provider crash/unresponsiveness, explicit state loss, cleanup, fresh sessions and clean worker restart |
| Skill/default | Installed source verified; real Codex `skills/list` reports the user skill enabled; prior global instruction bytes/dispatcher preserved |
| Fresh ordinary development chat | Implicit selection, relevant source transfer, guest build, 35 real-browser checks, exact result retrieval, cleanup and stopped/reservation-released readback passed |

No host input or screen/video capture was used. No reference-machine private profile, credential, product key or complete Codex settings were imported. Private keys, request receipts, enrolled identifiers and heavy VM backup remain outside Git and Drive source packets.

## Failures and repairs retained

Lima's initial instance name exceeded macOS's UNIX socket limit before creation; a short name resolved that guard. Strict extraction rejected a known internal documentation symlink before extraction; its exact target was validated and that optional link omitted. System Python lacked the newer tar extraction filter and PyYAML; safe explicit regular-file extraction and a dedicated validator environment resolved those constraints.

A first fixture report failed on a missing new host destination; its partial evidence was inspected before correction. Lima bootstrap SSH changed its host key after cold boot; strict checking stopped transport and a signed diagnosis established that the request was not admitted. A separately enrolled persistent guest SSH service now passes pinned signed cold roundtrips. A restored copy's forwarding path initially reset before SSH authentication; observed service/key identity and a bounded non-authenticated readiness check resolved that race before a complete fresh restore run passed. A recovery report shape error was corrected only after active sessions/process effects were inspected and normally released. Failed receipts and original pins remain private.

Native VZ snapshot creation returned `unimplemented`, with no snapshot effect. Recovery uses the tested encrypted stopped checkpoint and fresh copy. A private Xvfb desktop has no graphical login lock. Provider unresponsiveness is tested; Windows/macOS login-lock behavior is a separate unaccepted capability.

## Backend boundaries and remaining scope

Parallels 27.0.3 was installed during this task. Its account/VM inventory is inspected privately; no user-created Parallels VM is adopted or modified. The earlier license inspection reported `not valid`; edition/CLI entitlement must be established from current installed state before enrollment. [Parallels CLI documentation](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility) scopes management to the relevant editions. Its Windows integration and Tools may help Windows-specific work; this Linux build/DOM/native protocol already works through Lima without occupying that subscription.

Windows Arm and native macOS adapters are not implemented/accepted here. Each requires its own application/compiler compatibility, local enrollment, permissions, recovery and human acceptance; Linux and historical Windows x64 results cannot establish them. [Parallels macOS Arm constraints](https://kb.parallels.com/en/128867) and [provisioning](https://kb.parallels.com/en/125561) remain relevant when native Mac application testing is actually needed.

The local guest-first development default is active under the user's direct request. The private Global preference record is pending its canonical lifecycle; neither candidate PR is merged and no fleet/source pin is changed. Preserve old immutable releases. New source/hash and standalone current status/continuation records belong in the existing private Drive folder/index, with exact readback verification.


<!-- BEGIN PARALLELS_REASSESSMENT_20261013 -->
## Parallels capability reassessment — 2026-10-13

Latest inspection: 2026-10-13T03:19:13+03:00. This section supersedes the earlier license/install snapshot only; it does not change the installed Lima source/binding or accept a Windows lab adapter.

Parallels Desktop 27.0.3 (58680) is signed in and its license is now valid. The active edition reported by `prlsrvctl info --license --json` is Pro, **marked as a trial**, expiring October 26, 2026 at the reported 23:59:59. The paid subscription edition has not been established from that local result. [Official CLI documentation](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility) scopes these management capabilities to Pro and Business/Enterprise; current trial availability should not be mistaken for permanent paid entitlement.

The registered Windows 11 guest is running, uses ARM64/Professional build 26300, and has matching Parallels Tools 27.0.3 installed. Selected read-only command probes succeeded through Tools without SSH, opening a host console or controlling input. Default execution reached Windows session 0; `--current-user` reached the logged-in session 2. Structured system/resource and browser-version readback succeeded. Windows UI Automation observation returned 95 elements, exposing 22 Invoke, 3 Value, 4 Toggle and 5 Selection patterns. Control names/text were not read and no action was invoked. This is actual guest command/accessibility access, **not full guarded application-action or isolatedLab acceptance**. The initial complex read error and missing-WSL read were retained before narrower observations resolved the useful capability questions.

Only Windows 11 appeared in repeated all-VM inventory and the observed default bundle directory. WSL enumeration in the current guest user's context reported that WSL is not installed. The user reported a ready Linux environment; its VM name/location is still required to complete a live Parallels Linux comparison. Do not infer that it is absent from every account or location.

| Need | Evidence and recommendation |
|---|---|
| General Linux builds, local web/browser tests and Linux native accessibility | Keep the measured Lima lab as the general default. Its owned transport, source/result hashes, reservations, interruption recovery, no-interference interval and implicit normal-chat routing already passed. No additional Linux control advantage has been demonstrated here. |
| Native Windows commands, libraries and applications | Parallels is a useful additional backend: Windows Arm and Tools commands/current-session UI Automation are actually accessible. An owned Windows adapter and app-specific acceptance are still required before automatic guest actions. The installed Lima lab remains Linux-only; upstream non-Linux Lima support is experimental. |
| VM snapshots, cloning and management | Parallels documents integrated [snapshot reversion](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility/manage-virtual-machines-from-cli/snapshot-management/reverting-to-a-snapshot) and exposes its management commands. Snapshot inventory was read successfully. Creation/restoration and lifecycle were not exercised on the user's already-running VM. Installed Lima/VZ 2.2.1 returned unimplemented for native snapshots; its stopped encrypted recovery was already tested. |
| More precise DOM/native control | This comes from Playwright/browser DOM and OS accessibility adapters. Parallels Tools simplifies transport/provisioning but does not automatically improve those application semantics. [Microsoft UI Automation](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview) supplies Windows' provider/control model. |
| Performance or graphics winner | Not measured. Windows currently has automatic 4-vCPU/~6-GiB allocation and a configured Parallels graphics adapter, while the accepted Lima fixture uses 2 vCPUs/4 GiB and headless private Linux sessions. Different guests/resources cannot establish a speed or overhead advantage. |

Windows currently has shared profile, clipboard, applications and cloud integration enabled. Existing settings and the running state were preserved. A future isolated Windows enrollment should use an explicitly owned configuration and the same selected-file/no-host-input contract; broad personal integration is not a reason to replace the existing default. No software, permissions, license, guest settings, lifecycle or global default was changed during this inspection. No screen/video capture or host input was used.

Conclusion: **keep Lima for compatible general development; use Parallels for Windows-specific work after scoped enrollment and acceptance.** Resolve the Linux VM location before claiming its live comparison complete. Both systems can coexist; there is no demonstrated benefit in migrating the accepted Linux lab merely to unify the hypervisor.
<!-- END PARALLELS_REASSESSMENT_20261013 -->
