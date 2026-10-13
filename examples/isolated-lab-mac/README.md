# isolatedLab on Arm Mac — Lima candidate 0.2.0

This Mac now has a tested Arm Linux guest behind a local command bridge. It uses Lima 2.2.1 and Apple Virtualization.framework (VZ), independently of Parallels licensing. Browser tests use real DOM/accessibility semantics; native Linux app tests use a private D-Bus/AT-SPI/Xvfb session. No host input or screen/video capture is admitted.

The canonical editable source owner remains `dodWhatUp/install-modes-for-games`. `upstream/` preserves byte-identical Linux guest source from the verified base 0.5.0 packet. Its `PROVENANCE.json` records those inputs. Windows human acceptance on the reference computer does not accept this Mac or a Windows Arm guest. Distribution 0.2.0 extends the existing schema-1 bridge; the shared core version remains 0.1.0-candidate and the preserved guest worker is 0.3.0.

## Capability and evidence

| Capability | Current state |
|---|---|
| Arm Linux cold boot, normal shutdown, exact VM/file identity and resource readback | Passed on this Mac with Lima/VZ |
| Authenticated structured requests, retained receipts, duplicate IDs and owner/workspace guards | Offline tests plus actual pinned SSH/HMAC roundtrips |
| Selected source transfer, Unicode build/output and new-destination result retrieval | Actual Linux acceptance |
| Browser DOM and Linux native accessibility actions, stale observation rejection and cleanup | Actual Linux acceptance: 37 checks per workload |
| Five-minute mixed interval while the user used the Mac | Technical pass: 300.01 seconds, 11 workloads, 407 checks; separate human report recorded in local acceptance |
| Mac installer/default and Codex skill discovery | Installed and discovered; fresh normal chat implicitly selected the guest, transferred/built/tested its app, retrieved results and cleaned up: 35 checks |
| Stopped private encrypted checkpoint and restored bytes | See `VALIDATION.json` and the local acceptance record for final restore scope |
| Parallels | Installed during this task: 27.0.3; license was not valid at inspection; no Parallels VM was started or modified |
| Windows Arm and native macOS GUI adapters | Not implemented/accepted by this candidate; preserve separate guest/application acceptance |
| Native VZ live snapshots | Actual command returned `unimplemented`; stopped backup is the measured recovery route |
| Crash/helper-loss/unresponsive provider recovery | 26 operations passed; graphical Windows/macOS login-lock behavior remains separate |

## Fresh destination setup

Verify the independently supplied ZIP SHA-256 and its `SOURCE-MANIFEST.json` before extraction. Verify `MAC-SOURCE-MANIFEST.json` against source files before executing setup. Preserve any existing source, machine binding, skill/default, guest owner and checkpoints.

The host uses Python's standard library and the version-pinned official Lima Arm release. `prepare_lima.py` downloads the verified release into a private task-owned tools directory; no Homebrew or host administrator installation is needed. Its one known internal documentation symlink is validated and omitted. Archive hash or VM identity failure stops the affected stage. A partial job is retained; inspect its effects instead of repeating the command.

From a fresh private lab root, run `python3 prepare_lima.py --root <private-root>`. The default is `~/.local/share/isolatedlab`. A short private path is required by macOS's 104-character UNIX socket limit. Existing enrollment or a prior provisioning admission stops automatic preparation; this command does not replace an existing installation.

The runner creates one fresh Ubuntu 24.04 Arm minimal guest from the exact pinned official image, two vCPUs, 4 GiB RAM and a sparse 12 GiB guest disk. Plain mode disables host folder mounts, dynamic forwarding, container services, Rosetta and agent forwarding. Audio/video devices are disabled. Only localhost SSH transport is exposed. Keep sufficient host memory/storage for normal use, other VMs and recovery; start one owned guest at a time for acceptance. Do not import a Windows x64 disk, personal profiles or reference-machine configuration.

The guest dependency script installs signed Ubuntu packages, inherited Playwright 1.63.0 and its platform-selected Arm Chromium shell, system Python GI/AT-SPI/GTK, private D-Bus/Xvfb and xauth. It writes resolved apt/pip records inside the guest. Do not run any guest script on the Mac. Do not run the byte-preserved x64 browser fallback on Arm. Dependency/install failures stop that stage and retain its job result.

## Stable transport and identity

Lima's bootstrap SSH host key changed across a cold restart. Strict host-key checking correctly refused the old pin; a signed protocol diagnosis confirmed that the failed request was not admitted. The repair uses a separate persistent guest SSH service on port 2222, forwarded only to a selected localhost port. It accepts the newly generated bridge key only, forces the fixed bridge command, and disables passwords, root login, PTY, X11, agent/tunnel/TCP forwarding. Its persistent host key and signed VM identity passed subsequent cold roundtrips. The old failure/pin is retained privately; no host-key checking was disabled.

Lima's own SSH path is limited to fresh provisioning and explicit recovery diagnostics. Normal requests use the dedicated pinned service. Fresh local transport/SSH keys, host-key pins, enrolled bundle path, VZ identifier hash, exact Lima binary/config hashes and observed resource limits live in mode-600 private files under a mode-700 local directory. They stay out of Git/Drive. Configuration changes require an explicit observed re-enrollment; unknown JSON fields or changed identity never select a VM by display name.

Parallels remains a separately prepared backend when its actual edition and Tools/SSH capabilities satisfy the task. Its account/license output is private. A subscription alone does not prove CLI entitlement. Do not buy an upgrade, start a trial, change licensing or adopt a user-created VM merely to make a prepared recipe usable.

## Skill installation and routine use

Run `python3 install_local.py --root <private-root>` for a fresh skill/default installation. The source installer verifies hashes, preserves prior instruction bytes and the managed dispatcher, and records a private backup/readback receipt. It refuses existing skill/default/override conflicts. Use `--upgrade` only to update this owned installation after the prior source and installed skill match their hashes; later edits are preserved and cause a stop. Upgrades keep the prior immutable source and skill directory and leave global instruction text untouched.

The skill lives in Codex's discovered user skill location. Its resolver validates the installed manifest/files and resolves the machine binding without starting a VM. Use named MCP tools only if their actual binding targets this local enrolled guest. The existing read-only ChatGPT connection remains separate. The supported local fallback is `python3 <resolved-source>/mac_lab.py`.

Compatible browser/native GUI software development uses the guest by default. Plain file edits and headless CLI work can stay in the selected project/environment. Explicit host/hardware tasks preserve that scope. Missing readiness permits scoped setup, never an automatic host mouse/keyboard/focus/display fallback.

Reserve with `mac_lab.py reserve --owner <chat-id>`, start the stopped owned VM with `start`, and send schema-1 requests using `request --request <json> --owner <chat-id>`. `push --project <selected-project> --path <relative-file>` transfers one selected file up to 64 KiB; `pull` retrieves one selected result and refuses an existing target. Source masters remain in the chosen project. Guest workspaces are per-owner. Browser actions require the digest from the latest snapshot; native actions require current session/app/process/tree identity and exposed accessibility actions.

After cold start, observe the dedicated SSH banner with `prepare_lima.wait_ssh_banner(config["ssh_port"])` before sending the first request. Lima can report a running VM before its static forwarding path is ready. This bounded readiness observation sends no authenticated operation; an operation that fails afterward retains its original ID and receipts.

For a small local web server, use `desktop.launch` inside the workflow's private guest session; it shares that owned process group and is removed by `desktop.close`. No host port forwarding is needed for the guest's browser. Reuse the recorded API instead of launching an untracked daemon through a bounded build command.

Close owned browser/desktop sessions, then use `release`. The bridge checks empty sessions and unresolved admissions, normally shuts down the VM, verifies stopped state, and only then removes the host reservation. Unknown shutdown effects retain the reservation. Reservations never expire into permission to steal another chat's guest.

## Acceptance and recovery

Run `python3 -m unittest test_mac_lab.py test_lima_and_backup.py`; run `accept_linux.py --owner <owned-test-id>` for the measured source/build/DOM/native fixture. It retains failure reports and active-session identifiers; observation can be refreshed, but failed/unknown mutations are not replayed. After a timeout inspect `request.status` under a new ID referencing the original, then inspect the same processes/sessions before recovery. The current candidate deliberately has no force recovery command.

Run `mixed_linux.py` only after announcing the five-minute test and receiving user readiness. It holds temporary sleep protection for that process, repeats build/browser/native/readback/cleanup, and releases sleep protection afterward. Obtain the independent mouse, keyboard, focus and display report separately. Technical success does not replace that report.

The stopped backup command is `stopped_backup.py make --destination <new-private-backup-directory>`. It requires stopped VM state and no reservation while holding the operation lock. It captures selected bundle/disk/firmware/config, matching guest source and necessary private local recovery keys. The payload is compressed, encrypted with a fresh private key and authenticated with an independent HMAC; keys remain in private internal storage. No VM backup or key is uploaded with source.

Restore with `stopped_backup.py restore --backup <backup> --keyfile <private-key> --destination <new-staging-directory>`. Authentication and ciphertext hashes are verified before decryption; exact member names/sizes/hashes, no links/traversal/collisions, new destinations and sparse disk reconstruction are enforced. Byte restoration does not by itself accept a VM. Clone into a fresh owned VZ identity, preserve the original, rotate local enrollment/transport/SSH identities, then test cold boot, selected app/command/native readiness and normal stop. Record the actual tested restore scope.

`restore_lima.py` implements that fresh clone/enrollment route from authenticated staging. Its actual first attempt exposed forwarding readiness after the second boot; that failure is preserved. Observed service state, unchanged public host key and subsequent signed read probes resolved it before the selected 37-check runtime and normal shutdown passed. `recovery_linux.py` tests an owned process crash, identity-guarded provider loss/unresponsiveness, explicit state-loss readback, cleanup and fresh sessions. A private Xvfb session has no graphical login lock; this does not accept Windows/macOS login-lock behavior.

Windows Arm/native macOS require separate enrollment, dependencies, application compatibility, native accessibility/login permissions, failure recovery and local human acceptance. Parallels user-created VMs retain their owner until explicitly enrolled. No source publication, local default, old Windows report or Linux pass proves those tracks ready.
