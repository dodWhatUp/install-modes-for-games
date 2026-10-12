---
name: isolated-lab
description: Use the prepared isolated guest for compatible software-development tests needing browser or native-app interaction while the user keeps using the Mac. Also use for isolatedLab setup and recovery. Plain file edits and headless CLI work do not require a VM.
---

# Isolated development lab

Run [scripts/resolve_lab.py](scripts/resolve_lab.py) to resolve this Mac's local binding. Read the resolved source's `README.md` and machine-local `private/acceptance.json` when present. Historical Windows/Linux acceptance does not accept this Mac. Run the supported `python3 <source>/mac_lab.py preflight` bridge; named MCP tools are usable only when they actually target this enrolled local guest. The existing ChatGPT connector is read-only and belongs to its separate reference installation.

For an accepted Linux development workflow, read [references/linux-bridge.md](references/linux-bridge.md) for the local command/API route. Reuse the resolved bridge and its observed request/session identities; the fixture runner is a protocol example, not a substitute for testing the user's own application.

For compatible development tasks needing browser or native UI, select the guest before opening a host browser or interacting with a host app. Preserve the selected project's source master. Transfer only selected files, build/run in an owned guest workspace, inspect DOM/accessibility state, use current snapshot/session/app identity for actions, read back, retrieve selected outputs to new destinations and clean up the owned sessions. Headless file/CLI tasks can stay in their selected environment. Explicit host configuration or hardware work retains its requested host scope.

The Mac source is a candidate until local guest acceptance passes. Missing binding, installation, transport or guest permissions require the relevant setup; they never permit a host mouse, keyboard, focus or display fallback. Inspect actual capabilities independently for Arm Linux, Windows Arm and native macOS guests. Do not infer Windows/macOS readiness from Linux. Request unavoidable account/OS-consent steps precisely; do not buy an edition or bypass consent.

Reserve the exact VM for the workflow. Another owner's reservation, an unknown admitted request or a stale observation stops the affected action. Inspect the same request and effects before any retry; mutations are never automatically replayed. A timeout does not prove nothing changed. Keep secrets and private receipts outside Git/Drive source packets. Never read transport keys, passwords, account profiles or product keys into chat.

Use headless lifecycle and temporary sleep protection. Avoid Coherence, shared clipboard, drag-and-drop, broad Home sharing and automatic device assignment. This migration uses structured text observations without screen/video capture. The current candidate exposes only its prepared Linux bridge; Windows and native macOS adapters require their own implementation and tests. Read the source README for the acceptance and recovery gates.
