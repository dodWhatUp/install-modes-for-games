# isolatedLab Mac preparation — 2026-10-13

**Status: CANDIDATE; environment and runtime acceptance unfinished.**

Continue with the [Mac source README](../examples/isolated-lab-mac/README.md), [offline validation](../examples/isolated-lab-mac/VALIDATION.json), and [source manifest](../examples/isolated-lab-mac/MAC-SOURCE-MANIFEST.json). This is the canonical source-owner route for the Mac work. The existing standalone private Drive release records retain their Windows human-acceptance update; the immutable archived snapshots are older.

## Verified here

- The supplied handoff ZIP matched SHA-256 `c40b3f17df0cdf670c3056c56862876b6dac1876d1f3696bacab6b73e440c34d`. All 12 outer records, 58 base source files and 20 Windows source files matched their exact manifest sets, byte lengths and hashes before extraction. Traversal, collisions, non-files and links were rejected.
- The source-owner default branch and private distribution folder had no accepted Mac adapter. The canonical owner was reused in a separate linked task worktree; unrelated worktrees were preserved.
- The host is Arm macOS 26.6.2 with 16 GiB RAM. Parallels Desktop, its CLI, package receipts and running Parallels processes were absent from the checked local installation paths/state. A locally stored web installer was mounted read-only and verified with Parallels Developer ID team `4C6364ACXT`; it was not launched. Subscription edition remains unknown.
- Twenty-one offline contracts passed on this Mac: authenticated Unicode envelopes, tampering, deadlines including blocked input and children holding pipes, bounded output, path/symlink/FIFO rejection, hash checks, atomic publication with concurrent writers, no replacement, private-file modes, guest/owner/receipt identity, duplicate admission, stale browser observations, host-execution rejection and preservation of a reservation after ambiguous shutdown. Python compilation and guest shell syntax passed.
- Skill schema validation passed in a temporary dedicated PyYAML 6.0.3 environment. The initial system and bundled Python validators lacked PyYAML; those failures were retained and resolved without changing system Python.
- The local skill was installed and byte-verified in Codex's user discovery location. A real `skills/list` app-server response reported `isolated-lab`, `scope:user`, `enabled:true`; it started no AI turn or VM. The local command bridge's preflight returned the actual missing-installation blocker. The global instruction file preserved all prior bytes and the managed dispatcher, then appended the scoped default. Refreshed client instructions included that default.
- Fresh unbound transport/SSH identities were created privately on this computer. They are absent from the source packet and are not guest readiness. No reference-machine credentials, profiles, settings or product keys were imported.

No VM lifecycle or guest action was run. No screen/video capture or host input API was used. The existing read-only ChatGPT connection was not modified. Its reference-service status is not this Mac's status.

## Backend assessment

Parallels remains the first candidate because of the existing subscription. [Its official developer documentation](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility) places CLI management in Pro/Business/Enterprise. Installation is needed to determine the actual edition and measured tools. [The installation procedure](https://kb.parallels.com/en/130231) requires normal administrator/account steps; this session cannot authenticate them. No purchase, upgrade, trial or access expansion was made.

The Linux Tools execution path must account for [documented `bash -c` invocation](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility/manage-virtual-machines-from-cli/general-virtual-machine-management/execute-a-command-in-a-virtual-machine). The candidate passes only a fixed bridge and encoded authenticated JSON. SSH is a separately prepared loopback/key/host-key-pinned path, to be used only when its enrollment and execution probes pass.

About 14 GiB of internal space is available. An external ExFAT SSD has about 292 GB free and could hold newly owned VM bundles after backend/bundle I/O validation. It was not reformatted or modified. [Parallels system requirements](https://kb.parallels.com/en/124223) require additional space for guest systems; internal free space is insufficient for the requested multi-guest lab plus recovery copies.

Prefer fresh Arm Linux, then selected Windows Arm workloads. Do not transplant the x64 reference disk. Native macOS is a separate guest/Accessibility/SSH acceptance track: [documented macOS Arm constraints](https://kb.parallels.com/en/128867) and [provisioning](https://kb.parallels.com/en/125561) differ from Linux/Windows. No native macOS or Windows Arm adapter is implemented or accepted by this candidate.

## Exact continuation

The unavoidable next user action is to complete signed Parallels installation, approve its normal administrator prompt and sign in with the existing subscription. No administrator password or account credential should be pasted into chat.

Continue in the same local Codex chat/model/settings. After that action, inspect installed edition/version/help/VM ownership, validate the external storage candidate, complete enrollment/provisioning and the acceptance-mode probe runner, set measured resource/isolation controls, and accept an Arm Linux source/build/browser/native fixture. Extend Windows Arm and native macOS separately. Finish cold-login/timeout/crash/lock/lost-helper/cleanup/shutdown and stopped checkpoint restoration before advertising runtime readiness.

When the user is ready, announce and run the requested 5–10 minute mixed interval and record their separate interference report. Then create the already-authorized fresh development chat and test automatic routing/transfer/build/results/cleanup. Neither test was started while the guest was unavailable. No background continuation or scheduled wakeup exists.

Publication of this candidate is preservation of work, not activation or completion. Update the existing private Drive index with a candidate link, preserve prior release archives and standalone acceptance records, and publish a new accepted package only after the remaining evidence passes.
