# isolatedLab Mac candidate 0.1.0

This is a prepared source candidate, not an accepted Mac environment. The current Mac has no installed Parallels Desktop or `prlctl`. Administrator installation and existing-subscription sign-in are required before edition and real CLI behavior can be measured. No guest was started and no host input or capture API was used.

The canonical owner is `dodWhatUp/install-modes-for-games`. This directory adds the Mac transport layer; `upstream/` preserves exact Linux guest source from the verified base 0.5.0 package. Its `PROVENANCE.json` lists hashes. The current standalone Drive records remain authoritative for subsequent Windows human acceptance. That report does not accept this Mac. The older snapshots inside the immutable ZIP remain historical.

## Present source and evidence

| Capability | Current state |
|---|---|
| Mac preflight, finite commands/output, own process-group cleanup | Offline tests on this Mac |
| HMAC envelope, correlation, duplicate-ID rejection and retained receipts | Offline tests; guest roundtrip pending |
| Atomic selected file publication, Unicode, traversal/symlink and overwrite rejection | Offline tests including concurrent publication |
| Exact VM UUID plus bundle path, workflow reservation, headless lifecycle | Source candidate; actual Parallels acceptance pending |
| Parallels Tools and loopback authenticated SSH command paths | Prepared; each needs installed guest transport probes |
| Browser DOM and Linux native accessibility | Verified reusable source; Arm guest dependencies and actual readbacks pending |
| Browser current-snapshot guard and other-owner rejection | Offline tests |
| Windows Arm helper adaptation and macOS Accessibility adapter | Not implemented in this candidate |
| Resource configuration, sleep lease, stopped backup/restore | Sleep lifecycle lease prepared; limits and restore acceptance pending |
| Local skill/default discovery | Recorded separately in `VALIDATION.json` |
| Cold login, build/UI actions, crash/lock/lost-helper recovery, mixed interval, fresh development chat | Not run on a Mac guest |

## Reproduce the safe preparation

Run `python3 -m unittest -v test_mac_lab.py` from this directory. Run `python3 mac_lab.py preflight`; it does not start or configure a VM. Only the host Python standard library is needed. Guest dependencies are separate and must never be installed by running guest scripts on the Mac.

Install the signed Parallels application and sign in with the existing subscription through normal OS/account prompts. Inspect version, edition and the actual help/JSON output. CLI management is documented for Pro/Business/Enterprise; a subscription alone does not establish this entitlement. Do not start a paid trial, purchase an upgrade or infer readiness from help text. Capture sanitized capability results and retain raw configuration/license output privately.

This Mac has 16 GiB RAM and about 14 GiB internal free space. An attached ExFAT SSD has about 292 GB free and is a possible VM-storage target; verify suitability, stable mount and bundle I/O before provisioning. Keep keys/config/receipts on private internal storage. Do not delete existing files or reformat the disk. Start with one fresh Arm Linux guest, 2 vCPUs/4 GiB guest RAM and a host memory reserve, then separately provision Windows Arm and macOS only when their application tests require them. Confirm the actual installed backend's resource settings and isolation controls, rather than assuming flags.

Inspect all existing VMs and owners. Disable Coherence, shared clipboard, drag-and-drop, broad Home/profile sharing, and automatic USB/camera assignment for the new owned guest. Verify the resulting configuration. Do not alter another VM. Capture the exact installed JSON field names for UUID/home/state in the local enrollment; the candidate rejects unknown mappings rather than guessing a VM by its display name.

## Enrollment and transport gates

The local lab root is resolved by the installed skill. Its `private/` directory must be mode 700. `config.json`, the fresh 32-byte `transport.key`, pinned SSH known-hosts and the fresh SSH private key stay mode 600 outside Git and Drive. No credentials/settings from the Windows reference computer are imported.

The future enrollment record uses `schema:1`, `backend:parallels`, an exact `vm_uuid`, canonical `bundle_path`, `guest_os:linux`, `guest_arch:arm64`, `observed_json_fields:{uuid,home,state}`, `transport:tools` or `ssh`, and measured readiness fields. `lifecycle_accepted` and `transport_accepted` are false until independent local acceptance; do not flip these to skip the tests. An acceptance-mode enrollment/probe runner still needs to be completed after actual installed CLI behavior is available. Thus the candidate does not yet provision or accept a VM autonomously.

Deploy `contracts.py`, `guest_bridge.py`, and the preserved `upstream/guest_agent.py`, `desktop_agent.py`, `desktop_demo.py` directly into `/home/lab/agent/` in the newly enrolled guest. The guest requires a private `~/.local/state/isolatedlab-mac/enrollment.json` identifying the same UUID/OS/architecture and the newly generated transport key. Bootstrap only through the measured owned Tools/SSH path. The `install-linux-guest.sh` script installs through signed Ubuntu repositories and the exact inherited Playwright version; record resolved package versions. Do not invoke the preserved x86-only `prepare_guest_browser.py` on Arm. Any download or installation failure stops that stage; inspect its effects before a retry.

Parallels Tools invokes Linux commands through a shell. Only a fixed guest bridge command and URL-safe encoded authenticated JSON are used; task data never becomes shell command text. The SSH path is loopback-only, key authenticated, host-key pinned, noninteractive and has forwarding disabled. Restrict the guest SSH account/key to the bridge when that transport is required. Test argument/Unicode behavior, exact exit codes, returned identity, interruptions and invalid envelopes independently. No network-facing MCP server or expansion of the existing read-only ChatGPT connector is installed.

## Owned operation and recovery

After measured enrollment, reserve with `python3 mac_lab.py reserve --owner <chat-id>`. Use the returned browser/desktop session and native app identity; browser mutations require the current snapshot digest. Native mutations preserve the base adapter's current-tree/process guards. `push` selects one project-relative file up to 64 KiB; `pull` retrieves one selected result and refuses an existing destination. Project masters stay in the chosen project. CLI `--project` is the explicitly selected project or result root.

Requests are admitted once on both sides and retain private request/transport/response receipts. After an ambiguous timeout, inspect `request.status` with a new ID referencing the original ID, then observe sessions/processes before recovery. A missing response does not permit mutation replay. An abandoned reservation never expires into permission to steal another owner. The current candidate requires manual reconciliation of ambiguous admission; it has no force-recovery switch.

Close only sessions created by the reserved workflow and release only after no guest session or unknown admitted request remains. The `release` command first releases the empty guest workflow, then stops the VM normally, and removes the host reservation only after stopped-state readback. Any ambiguous shutdown retains that reservation and its receipts for inspection. Normal orchestration still requires runtime acceptance before use.

Before helper upgrades, prepare a stopped checkpoint preserving bundle/config/firmware, external disk dependencies and matching source. Verify all bytes before restore to a new disconnected copy with a fresh local identity. Preserve the original and test command/native readiness and normal stop. No backup/restore implementation or acceptance is claimed by this candidate.

## Acceptance still required

Complete provisioning/probe/recovery orchestration and independently accept Linux, Windows Arm and native macOS. Test cold start/login, realistic selected source/build/results, DOM/native mutation and readback, Unicode/invalid inputs, stale/path/identity rejection, deadlines/child cleanup, app crash, locked session and helper loss, exact session cleanup, shutdown and stopped checkpoint restore. Run no screen/video capture under this task's active instruction.

Only when the user is ready, announce the start of a measured 5–10 minute mixed workload while they use the Mac. Record the separate mouse/keyboard/focus/display report afterward. Then create the authorized fresh Codex chat with a realistic development request that does not mention isolatedLab and verify routing, build, retrieval and cleanup. Discovery, candidate publication and default installation do not prove either test.
