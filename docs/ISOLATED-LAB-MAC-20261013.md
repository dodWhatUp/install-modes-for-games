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
