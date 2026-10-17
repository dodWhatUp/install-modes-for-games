# isolatedLab across chats and computers

Version 0.4.0 added source installation, local skill binding, pinned fresh-machine preparation and guarded source recovery. At the immutable 0.5.0 base release, [ChatGPT web connection](ISOLATED-LAB-WEB-CONNECTION.md) account activation was pending. The later approved connection and Windows 0.7.6 source/acceptance are indexed in [the current handoff](ISOLATED-LAB-HANDOFF-2026-10-12.md), including Windows/Mac setup messages and Parallels research. The Linux guest helper remains 0.3.0. Regenerate the machine-specific runtime; no Codex account-wide synchronization is assumed.

## The normal entry point

On a computer with the skill installed, request:

> Use $isolated-lab to build and test this application inside the appropriate guest. Inspect this computer's readiness first, install the selected project dependencies in the guest, verify the result and keep my host input available.

The skill has implicit invocation enabled for compatible browser/native-app tests and isolatedLab setup, transfer or upgrade. Explicit invocation is the reliable way to select it; implicit selection is a model decision, not a guarantee. New chats can discover the user skill. An already-running chat still needs its own actual MCP tool catalog checked; the CLI bridge is usable before refresh.

A running lab can receive a **skill-only** workflow update through `portable_setup.py bind-skill`: it verifies the package, backs up and replaces only owned skill files, and binds them to the existing lab. It leaves runtime source, sessions and VM lifecycle intact. The binding retains the source bundle/hash for future setup. Full source installation/upgrade holds the controller operation locks and requires stopped guests.

OpenAI documents [local skill scopes and explicit/implicit selection](https://learn.chatgpt.com/docs/build-skills), [skill/MCP responsibilities](https://developers.openai.com/plugins/concepts/skills), and [shared local MCP configuration and Restart](https://learn.chatgpt.com/docs/extend/mcp?surface=cli). Current official documentation uses `$HOME/.agents/skills`; this installed client also discovers its existing `$CODEX_HOME/skills` location. The installer retains an existing isolated-lab skill location or uses the documented modern user location when absent. A conflict between two copies stops installation for reconciliation. Account sign-in does not establish local runtime or connector readiness.

## On another computer

Transfer the source ZIP and its SHA256 through a channel you trust. The ZIP contains source, operating instructions, skill, dependency lock and application-profile template. It excludes keys, VM disks, machine bindings, Codex account/settings, licenses, binaries and private evidence. The maintained source belongs to this repository; do not publish a second repository merely to distribute this packet.

Ask the destination Codex:

> Use this isolatedLab source bundle and the supplied SHA256 to set up a private lab on this computer. Inspect the host, verify every archive entry, install and bind the user skill, prepare the supported guest and install its tools. Preserve existing Codex settings and project source. Run the target-machine acceptance checks, record any unavailable capabilities, and leave the guest stopped. Use the lab for compatible future interactive development tests. Do not import another computer's credentials or claim unsupported Windows/GPU behavior.

Current automated host support is **Windows x64**, with Python 3.11+ and Windows OpenSSH Client. A Linux guest does not mean a Linux/macOS host is supported. Codex can locate its own bundled Python through the workspace-dependencies tool. Missing runtimes, unsupported hosts or restricted filesystem access are concrete setup boundaries; preserve the package and report the prerequisite.

The supported sequence is:

1. Run `Start-Here.ps1 -Action preflight -LabRoot <selected-private-root>`. Keep the runtime outside OneDrive and Git. The user-selected path overrides defaults.
2. Run `Start-Here.ps1 -Action install -LabRoot <root> -Bundle <source.zip> -Sha256 <received-hash>`. Installation verifies all bytes before touching installed files, binds the skill to this root, backs up replaced source and leaves VMs stopped. For a first adoption of an inspected existing skill, use the Python entry point with `--adopt-existing`.
3. Run `prepare_portable_linux.py --lab-root <root>`. It downloads exact locked files over verified HTTPS, extracts portable QEMU/7-Zip privately, imports a pinned pure-Python ISO library, creates a new restricted SSH key and config, selects available loopback ports, and prepares a new disk/seed. It never replaces an existing runtime or starts a VM. An optional `--cache-dir` reuses selected downloaded files only after hash checks. A failed partial setup is retained for diagnosis; no blind replay.
4. For authorized provisioning, start Linux, wait for cloud-init readiness, deploy the helper with `guest_tools.py --deploy`, then run `install_guest_agent.sh` and `install_guest_desktop.sh` **inside that guest**. These install the pinned Playwright/browser provider and the native AT-SPI provider. Record resolved Ubuntu package versions: signed apt repositories are current, not a bit-identical OS lock.
5. Run the acceptance described below, stop cleanly, register only this MCP server through `configure_mcp.py`, and verify it through `accept_codex_client.py`. Registering MCP does not start the VM. Refresh the active client only through its supported MCP controls when needed.

The destination agent can perform this sequence using normal file/shell tools. Windows guest preparation additionally requires enabled firmware virtualization, administrator installation, legitimate media/licensing and interactive-session acceptance; follow the [current Windows add-on/handoff](ISOLATED-LAB-HANDOFF-2026-10-12.md). No setup script changes BIOS or restarts the host automatically. Selected Windows workspace UIA/CDP control is accepted on the reference machine through the local command bridge; every destination needs its own acceptance. Mac adaptation remains unaccepted.

## Acceptance belongs to the destination

`VALIDATION.json` contains reference-machine history. `private/acceptance.json` is the selected computer's record and starts with **NOT_TESTED_ON_THIS_HOST**. A source hash proves identity, not runtime behavior.

| Check | Required observation |
|---|---|
| Package and installation | Archive SHA256, every entry size/hash, installed source/skill readback, correct local binding |
| Fresh preparation | Correct QEMU version, pinned download hashes, local paths/ports, fresh key, no VM auto-start |
| Command/build | Real guest process exit status, selected compile/run output, bounded timeout and cleanup |
| Browser | DOM/ARIA readback, exact selected action, result, session close |
| Native application | Real AT-SPI tree/text/actions, exact result, stale-state rejection, frozen/provider-loss recovery |
| Restart/recovery | Cold boot, deployed source hashes, stopped checkpoint and a new-disk restore test |
| Codex client | `accept_mcp.py`, actual Codex client discovery, skill enabled, active chat catalog checked separately |
| Background work | `accept_background.py` for the selected duration plus an owner-observed simultaneous-work test |
| Cleanup | Task-owned sessions closed, guest stopped and its loopback listeners absent |

Use `test_lab.py` and `test_guest_tools.py` for guards, `accept_cold_guest.py` and `accept_desktop.py` for live guest behavior. The endurance harness is optional for ordinary short tasks but required before claiming long unattended acceptance on a new host. No finite test proves permanent freedom from hangs. Preserve failures, deadlines and precise unsupported cases.

Multiple chats can discover one lab, but a shared VM is not an accepted concurrent workflow scheduler. Individual operation locks do not reserve an entire chat's sessions. Inspect active owners; wait or prepare a separately accepted lab/guest. Never close another chat's sessions or fall back to host input. The fixed guest workspace requires coordinated ownership.

## Carrying an application and its settings

Use `project-profile.example.json` as a small data record for the chosen application's source revision, dependency lockfiles, guest setup script, startup argv, selected settings and acceptance. Carry those authored project files with their own hashes, excluding secrets and unrelated data. Install from the project's pinned manifests in the guest, restore selected settings, then inspect behavior. A profile is a recipe, not a command executor or fresh authorization. OS-specific programs may need a separately implemented adapter.

Use one selected bundle version and one explicitly selected guest OS. Keep advanced commands below this main sequence; do not multiply setup dialogs or silently change the selected path/version. This static guide uses hierarchy and linked procedures rather than simulated UI controls.

<details>
<summary>Version upgrades and conditional recovery</summary>

1. Read `release.json`, dependency-lock changes and current machine acceptance. Observe stopped guests. Take a stopped-disk checkpoint before guest software changes and retain the accepted baseline.
2. Build a new source-only package with `package_source.py --config <config> --archive-only`. The explicit source allowlist excludes private runtime. Keep the previous release immutable.
3. Run `portable_setup.py install ... --upgrade`. The installer refuses changed locally owned source/skill, occupied setup locks, unrecognized directories and running guests. It records every replaced/new file in `private/source-upgrades/<transaction>` with before/after hashes and original bytes. It preserves guest configuration, keys and disks. Reconcile local edits instead of overwriting them.
4. Deploy changed guest software only after its checkpoint and stopped old worker; rerun acceptance relevant to the change. A source-only skill change does not require reinstalling the OS or repeating endurance. A new dependency does require its own live acceptance.
5. For source recovery use `portable_setup.py rollback --lab-root <root> --transaction <recorded-directory>`. This restores only while current bytes still match that transaction's after hashes and backups match the before hashes. Later edits are preserved by refusal. It does not roll back a guest disk or MCP registration; those have separate records. An interrupted PREPARED transaction requires inspected reconciliation, not automatic rollback/replay.

`configure_mcp.py` changes only its owned server and preserves other Codex configuration semantics. It refuses a conflicting `isolatedLab` registration. If another Python runtime is selected during an upgrade, reconcile the registered command before replacing it. Never copy the whole config.toml from the old computer.

</details>

## Verification coverage

The 0.4.0 portability implementation is tested with temporary relocated installs, exact package readback, guarded upgrades and byte-verified rollback. Dependency download endpoints and the private extraction/preparation route are checked on the reference Windows host. A second physical computer is not available in this session, so destination OS/provider acceptance and model-driven implicit selection remain separately unverified. The reference Linux 0.3.0 acceptance is retained; the guest helper was not changed by this source/workflow release.
