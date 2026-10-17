# Windows setup history and current handoff

**Current reference status, October 12:** firmware virtualization and Windows provisioning completed; helper 0.7.6 passed selected guest build/UIA/CDP/transfer, timed work and a stopped checkpoint restore. The completed interval's human report passed with no interference; activation remains pending. Use [the current source/handoff](ISOLATED-LAB-HANDOFF-2026-10-12.md) and the bound lab's Windows guide for current commands. The local command bridge works without restarting Codex; Windows named MCP tools remain separate work.

The sections below preserve the initial prerequisite snapshot, when firmware virtualization was disabled and Windows was not provisioned. They are historical reference and conditional requirements for a new computer, not a request to redo this host's firmware/install steps.

## Required steps

1. **Enable SVM in firmware.** On the ASUS AMD board, open BIOS/UEFI, switch to Advanced mode, then **Advanced → CPU Configuration → SVM Mode → Enabled**. Save and return to Windows. This requires a physical restart and firmware interaction; it cannot be performed through the available shell tools while preserving current desktop work. [ASUS instructions](https://www.asus.com/au/support/faq/1045141/).
2. **Accept administrator installation.** The verified minimal VirtualBox installer is prepared in `D:/CodexLab`. After SVM is enabled, the agent can launch `Install-VirtualBox.ps1 -LabRoot D:/CodexLab -Install`; the user must accept Windows' administrator/UAC prompt. The agent cannot provide the user's administrator credentials. The installer avoids optional USB/bridged/host-only drivers, host shortcuts, manager startup and automatic restart. A requested reboot remains a separate user action.
3. **Choose legitimate Windows 11 media and guest licensing.** Use a separately licensed guest for ongoing work, or choose Microsoft's time-limited 90-day Enterprise evaluation for evaluation work. The host installation does not establish a guest license. The agent needs the chosen ISO path and edition/image index before unattended provisioning. [Windows 11 download](https://www.microsoft.com/en-us/software-download/windows11), [Enterprise evaluation](https://www.microsoft.com/en-us/evalcenter/evaluate-windows-11-enterprise).

After these gates pass, `prepare_windows.py` can create the selected guest headlessly with 8 GiB RAM, 4 virtual CPUs, a 64 GiB virtual disk, EFI/TPM 2.0 and NAT. Clipboard sharing, drag and drop, USB, audio and remote-desktop exposure remain disabled by the recipe. Matching Guest Additions provide guest command transport.

## Acceptance before automatic application work

The next agent boundary is provisioning and verification, not claiming Windows control already exists. Verify installation and licensing status, guest commands, cold boot and clean shutdown. Then establish a dedicated interactive guest session and accept a UI Automation provider using properties and exposed Invoke/Value patterns. A service or guest command session alone is insufficient proof of interactive application access. Test a locked or disconnected session, application hangs, bounded failures, recovery and simultaneous host work.

The user may need a guest's first login or legitimate activation step if the selected media requires it; report the observed step rather than inventing a universal manual setup requirement. No host keyboard/mouse fallback is permitted. Windows games, GPU passthrough, HDR and physical USB devices are outside this acceptance.

## Codex connection

`isolatedLab` is registered locally and Codex's actual MCP client discovered its five tools. If this chat has not loaded them, open **Settings → MCP servers → isolatedLab → Restart** after other active work can tolerate a refresh, then inspect `/mcp`. This is the documented MCP refresh, not a VM installation requirement. The local shell bridge remains usable beforehand. [OpenAI MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
