# Game Tool Hub — learning preview 0.2.0

Requested 2026-10-11: focus on connecting and learning existing measurement tools, user control and useful coordination. Benchmarking and recording remain deferred.

Open `Start-GameToolHub.ps1` with PowerShell. It uses installed Python/Tk, preferring the bundled Codex runtime. No packages, drivers or services are installed. The GUI starts in learning mode; optional auto refresh is off.

- **Tools:** installation/running status and executable file versions, open an installed interface, register another installed interface, copy status without paths, save an immutable private connection snapshot. File versions may differ from product versions (observed for NVIDIA App).
- **Sensors:** read existing Afterburner names/units/values through `MAHMSharedMemory` using `FILE_MAP_READ`. No control mapping or new collector. Counters have no run association; desktop values do not validate game FPS/lows/latency.
- **RTSS:** read existing `RTSSSharedMemoryV2` with read access only. Application/PID, provider interval/count, recording flags and RTSS-calculated average/1%/0.1% lows are preserved. Tenths of FPS become FPS by unit conversion only. Stale live counters remain unavailable; historical intervals and endpoint presence do not validate a game benchmark or measured latency.
- **Reports:** archive a chosen CSV/JSON/TXT/HML as original bytes with source program, definitions and SHA-256. PresentMon v2 CSV preview retains at most five original rows plus documented GPU/latency fields, endpoints and frame type where present. Blank/NA values stay intact. No percentile, low or latency calculations. HML and unrecognized formats remain opaque.
- **How to use:** user controls, supported boundaries and next integration steps. Existing recording/hardware settings are read, not edited. Windows approvals remain manual.

Private data defaults to `%LOCALAPPDATA%/GameToolHub`. `tools.json` contains the user's registered executable paths. Registry changes preserve a previous copy. Imports use separate unique directories; changing source files are rejected with their partial evidence retained. No upload is automatic. Close the GUI to stop optional refresh; other tools stay open.

Save snapshot creates a uniquely named connection JSON inside the private data directory. Add tool and Reports accept visible direct-path forms, with optional Browse buttons. Registration never launches the program and requires an interface-only confirmation. Known collectors remain blocked even if given a different name in the panel. NVIDIA App is an interface launch connection; the installed FrameView SDK is an inventory-only collector, not evidence of a standalone FrameView GUI or populated latency export.

Local shortcuts, active only while the Hub is focused:

| Shortcut | Action |
|---|---|
| Ctrl+1 / 2 / 3 / 4 / 5 | Tools / Sensors / RTSS / Reports / How to use |
| Ctrl+R | Refresh both readers and tool status |
| Ctrl+T | Toggle optional refresh on Sensors/RTSS; no time series saved |
| Ctrl+O | Open selected interface; collectors blocked |
| Ctrl+A | Show registration form (normal select-all retained in text fields) |
| Ctrl+C | Copy status without paths (normal text copy retained in text fields) |
| Ctrl+S | Save a new private snapshot |
| Ctrl+I | Import the visible report draft; incomplete drafts request missing fields |
| Ctrl+E | Open selected archived original in its associated application |
| Alt+F4 | Close only the Hub |

Windows shortcuts use virtual-key letters so a Hebrew/other active keyboard layout does not change the intended action. Modal dialogs retain input ownership.

Agent interface, using the installed Python executable:

```text
python scripts/Game-Tool-Hub.py inspect
python scripts/Game-Tool-Hub.py snapshot --output <new-private-file.json>
python scripts/Game-Tool-Hub.py import-report --source <existing-report.csv> --provider <program-name> --definition <documented-method>
python scripts/Game-Tool-Hub.py --form-file <private-draft.json>
python scripts/tests/Test-GameToolHub.py
```

`--data-dir <private-directory>` goes before the command. Configure `GAME_TOOL_PRESENTMON` or the private registry to identify an existing console executable. PresentMon console is inventory-only in learning mode: opening it with no capture arguments can start ETW collection. The panel does not resume the older idle collector or stop it silently.

Optional [`form-draft.example.json`](form-draft.example.json) is a bounded local startup draft for report path/provider/definitions and tool path/name. Copy it privately and supply actual paths. It only populates visible fields: no launch, import, registration, approval or capture is executed, and interface confirmation cannot be prefilled. It helps when supported Computer Use cannot enter text into Tk fields; agent commands remain the preferred non-UI route for imports/inspection. No runtime file watcher, input server or hidden click channel exists.

The read-only sensor adapter uses the installed author's `SDK/Include/MAHMSharedMemory.h` layout v2 prefix: validates signature, sizes/counts, bounded mapping, unavailable `FLT_MAX` and provider timestamp. It preserves original source IDs and flags. Samples are best effort rather than an atomic batch; no time-series file is created by auto refresh. This is an authored adapter, not a copied SDK binary/header.

The RTSS adapter follows the installed author's `RTSSSharedMemory.h` and `OverlayDataProviderInternal.cpp`: header offsets/strides, Windows packing 8, version/extent gates and documented FPS scaling. It writes no OSD, locks, statistics/capture flags or profiles. Latency instrumentation is endpoint availability only; supported programs must calculate latency. PresentMon definitions follow its [2.6.0 console documentation](https://github.com/GameTechDev/PresentMon/blob/v2.6.0/README-ConsoleApplication.md). Declared provider version remains separate from schema recognition.

Current evidence and next boundaries are in [tool connections](../../docs/GAME-TOOL-CONNECTIONS.md). Rollback: close only Game Tool Hub and remove its optional launcher/source after preserving private reports. No Afterburner/RTSS/game-profile restore is required for this helper alone.
