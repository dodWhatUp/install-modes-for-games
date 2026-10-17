# Codex independent test lab

For another chat/computer, use `source/docs/ISOLATED-LAB-PORTABILITY.md` and `$isolated-lab`. Release 0.4.0 adds verified setup, local skill binding and guarded source recovery; guest helper 0.3.0 is unchanged. The acceptance below is reference-machine history. Inspect `private/acceptance.json` and current status for this selected computer before claiming readiness.

This file is installed at the private lab root. The accompanying source is in `source/examples/isolated-lab`; the full plan is in `source/docs/ISOLATED-DEVELOPMENT-LAB.md`.

**Linux is accepted for the tested slice. Windows and accelerated operation remain blocked.** Use `Lab.ps1 -Action status` for current runtime state. This lab is a trusted app-development environment, not a malware sandbox.

From this directory:

```powershell
.\Lab.ps1 -Action status
.\Lab.ps1 -Action start -Guest linux
.\Lab.ps1 -Action wait-ready -Guest linux -Timeout 180
.\Lab.ps1 -Action run -Guest linux -Script .\source\examples\isolated-lab\linux-smoke.sh
.\Lab.ps1 -Action run -Guest linux -Script .\source\examples\isolated-lab\linux-gui-smoke.sh
.\Lab.ps1 -Action fetch -Guest linux -Name linux-gui.png
.\Lab.ps1 -Action stop -Guest linux
```

All input in the GUI test goes to a virtual X display inside the Linux VM. The screenshot is fetched from the guest artifacts directory. No VM viewer is necessary. Software-emulated cold boot can take about a minute; use `wait-ready` before dispatch.

The 0.3.0 guest helper adds structured system/process/file data, browser DOM/accessibility actions and native Linux AT-SPI controls in a private guest D-Bus/Xvfb session. Read `source/docs/ISOLATED-LAB-GUEST-TOOLS.md` and `source/examples/isolated-lab/VALIDATION.json` for acceptance and limits. The local MCP bridge exposes lifecycle, inspection and action tools; it initializes without starting a VM. Codex's actual MCP client discovered all five tools and the local isolated-lab skill. The standalone `guest_tools.py` route works from shell tools before a chat's MCP refresh. Session tokens expire at shutdown; no personal host browser profile is imported.

Acceptance: 21 guard fixtures, the earlier 35 structured guest/browser checks and 25 new native checks passed. The 30-minute mixed build/browser/native workload passed 73 cycles and 742 requests with no errors. A newly restored 0.3.0 checkpoint passed 10 cold source/browser/native checks and was cleanly stopped. Both-guest real-work acceptance, Windows GUI and acceleration remain pending. Another chat prevented the user's simultaneous-work observation; no focus-isolation claim is inferred from this unattended workload.

The original accepted Linux disk and private stopped-disk checkpoint are preserved. The private config currently selects a separately restored disk that was boot-tested. The checkpoint depends on the retained base image and private guest key/config; the authored-source ZIP excludes those. Relocating a backing image needs a separately reviewed offline rebase; a source bundle is not a full guest backup.

Next physical step: enable **SVM Mode** in ASUS BIOS/UEFI, **Advanced → CPU Configuration**, save and return to Windows. Then reinspect firmware and run the prepared minimal installer with normal administrator consent. Legitimate Windows media/licensing must be resolved before provisioning; see `source/docs/ISOLATED-LAB-WINDOWS-SETUP.md`. No host driver, BIOS change, reboot or AI API subscription has been applied. The requested one-time Codex reminder only follows up about the pending user-work check; it does not start a VM or take host input.

Use the source installer in its default preflight mode to inspect readiness. Its `-Install` flag is the explicit install action and remains blocked while SVM is disabled. Keep credential files and VM/install logs private. Jobs and services do not automatically resume after this chat ends.
