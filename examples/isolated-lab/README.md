# Isolated Windows and Linux lab

For other chats/computers, use the [portable setup and upgrade guide](../../docs/ISOLATED-LAB-PORTABILITY.md). Release 0.5.0 carries the tools, skill and workflow plus a [private ChatGPT web connection](../../docs/ISOLATED-LAB-WEB-CONNECTION.md); guest helper 0.3.0 remains unchanged. `Start-Here.ps1` inspects the host and installs a SHA256-verified source bundle. Runtime keys, local bindings and guest acceptance are regenerated on the destination. Web preparation/transport is locally tested; actual account/plugin activation remains pending.

Build and test ordinary applications inside separate guest operating systems while the host desktop stays available. Current implementation and acceptance are in [the plan](../../docs/ISOLATED-DEVELOPMENT-LAB.md).

The source is portable; guest disks, credentials, installers and raw evidence belong in a private lab directory outside the repository and OneDrive. There is no host keyboard/mouse automation in this controller.

Structured guest data, browser controls and native Linux AT-SPI actions are implemented in version 0.3.0: see [the guest-tool guide](../../docs/ISOLATED-LAB-GUEST-TOOLS.md). `guest_agent.py` runs inside Linux, `guest_tools.py` uses SSH, and `guest_mcp.py` exposes the guest tools to Codex. `desktop_agent.py` owns a private guest accessibility session. Runtime evidence is recorded separately from Windows capabilities, which remain pending. See [Windows setup](../../docs/ISOLATED-LAB-WINDOWS-SETUP.md) for the exact remaining gates.

## Common commands

Use Python 3.11 or later. A private `config.json` selects installed binaries, disks and ports; `config.example.json` describes it.

```powershell
python lab.py --config D:\CodexLab\private\config.json status
python lab.py --config D:\CodexLab\private\config.json start linux
python lab.py --config D:\CodexLab\private\config.json wait-ready linux --timeout 180
python lab.py --config D:\CodexLab\private\config.json run linux --script .\linux-smoke.sh --timeout 120
python lab.py --config D:\CodexLab\private\config.json screenshot linux
python lab.py --config D:\CodexLab\private\config.json stop linux
```

`start` is always headless and checks RAM/disk headroom. `wait-ready` has a finite deadline and does not restart the VM. Commands execute only in the named guest. `run` copies a selected script into the guest, runs it with a deadline and retains its result. Linux returns the guest process exit status; the unaccepted Windows route reports the Guest Control result. A timeout is a failure; it is not an automatic rerun. `stop` requests guest shutdown and reports if it remains running. `force-stop` is explicit and checks process/VM ownership. Screenshots and downloaded outputs are stored under `artifacts`, never automatically published. `fetch linux --name linux-gui.png` retrieves one file from the guest artifacts directory into a fresh host directory.

For Linux, SSH uses a lab-only key, loopback forwarding, a private known-hosts file, and finite connection/command deadlines. Lab invocations ignore user SSH configuration and explicitly disable agent forwarding, extra forwards and local commands. For Windows, VirtualBox Guest Control uses a lab-only password file and Guest Additions; desktop GUI tests must also verify the interactive guest session, since a service/background process is not an interactive desktop.

## Preparation and recovery

- `prepare_linux.py` creates a NoCloud seed and a new copy-on-write guest disk from a verified Ubuntu base image. It refuses to replace an existing disk.
- `prepare_windows.py --iso ...` creates an isolated Windows 11 VirtualBox VM and uses the official unattended installer. It requires enabled firmware virtualization, installed VirtualBox and explicitly selected legitimate Windows media. It refuses existing VM names/disks. Windows licensing/activation is a separate readiness gate.
- `lab.py checkpoint linux --name ...` copies a powered-off disk and its hash. `restore linux --checkpoint ...` restores into a new disk and updates the private configuration while preserving the current disk. Neither operation switches a running disk.
- `Install-VirtualBox.ps1` verifies the already-downloaded official installer before launching installation. It does not reboot, disable Windows security or install the optional Extension Pack.

Keep the original cloud image and SHA256 receipt. Recovery snapshots include disks and private VM configuration; source copies alone cannot restore installed guests. Use the private state manifest and README in the lab root to resume. No VM startup task, cloud service or AI API dependency is configured. A separately requested one-time Codex reminder only prompts the user for the pending simultaneous-work check; it does not operate the VM.

## Limits

Guest success does not prove host GPU/HDR/driver/game/physical-device behavior. NAT does not isolate a guest from all host/LAN services; treat this as a trusted development lab, not a malware sandbox. Loopback guest-control ports are accessible to local processes; never expose them to the LAN. Hardware acceleration, Windows installation, interactive Windows GUI tests and simultaneous-work acceptance remain pending until individually observed. See `VALIDATION.json` for the accepted Linux slice.
