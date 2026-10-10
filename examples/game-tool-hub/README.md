# Game Tool Hub — learning preview 0.1.0

Requested 2026-10-11: focus on connecting and learning existing measurement tools, user control and useful coordination. Benchmarking and recording remain deferred.

Open `Start-GameToolHub.ps1` with PowerShell. It uses installed Python/Tk, preferring the bundled Codex runtime. No packages, drivers or services are installed. The GUI starts in learning mode; optional auto refresh is off.

- **Tools:** installation/running status and actual executable versions, open an installed interface, register another installed interface, copy status without paths, save an immutable private connection snapshot.
- **Sensors:** read existing Afterburner names/units/values through `MAHMSharedMemory` using `FILE_MAP_READ`. No control mapping or new collector. Counters have no run association; desktop values do not validate game FPS/lows/latency.
- **Reports:** archive an explicitly chosen CSV/JSON/TXT/HML as original bytes with source program, definitions and SHA-256. No percentile, low or latency calculations. HML is currently opaque; a converter is not supplied.
- **How to use:** user controls, supported boundaries and next integration steps. Existing recording/hardware settings are read, not edited. Windows approvals remain manual.

Private data defaults to `%LOCALAPPDATA%/GameToolHub`. `tools.json` contains the user's registered executable paths. Registry changes preserve a previous copy. Imports use separate unique directories; changing source files are rejected with their partial evidence retained. No upload is automatic. Close the GUI to stop optional refresh; other tools stay open.

Agent interface, using the installed Python executable:

```text
python scripts/Game-Tool-Hub.py inspect
python scripts/Game-Tool-Hub.py snapshot --output <new-private-file.json>
python scripts/Game-Tool-Hub.py import-report --source <existing-report.csv> --provider <program-name> --definition <documented-method>
python scripts/tests/Test-GameToolHub.py
```

`--data-dir <private-directory>` goes before the command. Configure `GAME_TOOL_PRESENTMON` or the private registry to identify an existing console executable. PresentMon console is inventory-only in learning mode: opening it with no capture arguments can start ETW collection. The panel does not resume the older idle collector or stop it silently.

The read-only sensor adapter uses the installed author's `SDK/Include/MAHMSharedMemory.h` layout v2 prefix: validates signature, sizes/counts, bounded mapping, unavailable `FLT_MAX` and provider timestamp. It preserves original source IDs and flags. Samples are best effort rather than an atomic batch; no time-series file is created by auto refresh. This is an authored adapter, not a copied SDK binary/header.

Current evidence and next boundaries are in [tool connections](../../docs/GAME-TOOL-CONNECTIONS.md). Rollback: close only Game Tool Hub and remove its optional launcher/source after preserving private reports. No Afterburner/RTSS/game-profile restore is required for this helper alone.
