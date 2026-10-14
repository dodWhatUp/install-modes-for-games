# Mod acquisition, installation and maintenance

Version 0.1.0, 2026-10-13. Owner: `dodWhatUp/install-modes-for-games`.
This is an additive source module for Game Tool Hub, not an automatic app upgrade.

## The reusable workflow

The chat supplies a reviewed game recipe and selected items. The local module
prepares an ordered, hashed plan; obtains original archives where access permits;
checks the archives; stages files; and performs a separately approved manager
operation. Each operation returns structured JSON. Completed downloads are reused
only after their stored hash matches. Failed or interrupted transfers are not
silently resubmitted. No request text or recipe is executed as shell code.

One adapter is reused across games. A game's existing `games/<id>/` folder owns
its `MOD-WORKFLOW.json`, sources, compatibility and recommendations. Local jobs
are private execution receipts, not a second research catalog or task backlog.

## Provider support

| Provider | Implemented | Remaining user/access boundary |
|---|---|---|
| GitHub Releases | Exact repository/tag/asset; upstream SHA-256 when available; bounded transfer | Access, exact release availability and digest must match; no source fallback after denial |
| Author HTTPS | The UMM mirror linked by UMM's own README; limited redirects | Mutable mirror: manager version is not proven by the locally calculated hash |
| Nexus Mods | Personal-key metadata; exact file IDs; authorized download-link endpoint | A key is required. Free accounts need fresh website-issued NXM key/expiry or manual import; Premium can use the permitted API route |
| Other sites/archives | Explicit original-ZIP import and generic safe ZIP staging | No universal scraper, automatic login, CAPTCHA bypass or undocumented download route |

A site's familiarity is not permission to scrape or redistribute it. Nexus's
personal/testing API route does not register a public application. A finished
public-facing app must follow Nexus registration and API rules. Keys are read
from an optional local hidden prompt or `NEXUS_MODS_API_KEY`; they are not stored
in recipes, job receipts, source packages, Git or Drive. NXM links are ephemeral.
No global NXM handler is registered or taken away from Vortex/MO2.

Default limits: 128 MiB total transfer, 40 requests, 300 seconds, per-item limits,
12-second blocking I/O timeout, no automatic retry. HTTPS redirects remain in
provider allowlists and authenticated Nexus API requests do not redirect. The
deadline/cancellation is checked between bounded reads; an in-flight I/O may
finish after the requested cancellation. Rate-limit/access failures stop that
provider in the same job, including later invocations.

## Manager support

**Unity Mod Manager / Kingmaker:** the panel downloads/imports/stages; UMM's own
installer still bootstraps the loader. The optional `install-new` operation only
adds one previously absent `Mods/<Id>` directory after current-state checks.
It does not call an invented UMM command-line installer or edit activation settings.
UMM may enable a new mod by default on the next launch: review its menu before
continuing a valued save.

**Vortex, Mod Organizer 2 and RHI:** recognized routing choices, with generic ZIP
acquisition/staging and explicit native-manager handoff only. Their profile,
load-order, proxy and deployment formats are not overwritten. RHI remains the
separate graphics-orchestration candidate; it is not Kingmaker's gameplay loader.
An adapter for another manager should extend this module after its documented
interface and current owner are verified, not copy the whole download engine.

Operating-system, GPU and device driver installation is outside this module.

## Commands for a chat executor

Run from the package/repository root with an existing Python 3.10+ interpreter.
All examples containing paths are templates; use the actual chosen job paths.

```text
python scripts/Game-Mod-Ops.py catalog
python scripts/Game-Mod-Ops.py plan --mode real-time
python scripts/Game-Mod-Ops.py plan --mode turn-based --create-job
python scripts/Game-Mod-Ops.py plan --select kingmaker-tactics --create-job
python scripts/Game-Mod-Ops.py status --job "<job-folder>"
python scripts/Game-Mod-Ops.py acquire --job "<job-folder>" --allow-network
```

Selecting Tactics includes its UMM dependency automatically. `plan` alone writes
nothing; `--create-job` writes a new private job and does not use the network.
The default Windows data root is `%LOCALAPPDATA%\GameToolHub\mod-workflows`, separate
from existing Hub `tools.json`, overlay groups and native profiles. It can be
selected explicitly with `plan --data-dir` or the panel's `--data-dir` option.

For Nexus, inspect metadata and pin an actual file rather than guessing “latest”:

```text
python scripts/Game-Mod-Ops.py nexus-files --item buff-bot --ask-nexus-key
python scripts/Game-Mod-Ops.py plan --select buff-bot --file-pin buff-bot=<exact-file-id> --create-job
python scripts/Game-Mod-Ops.py acquire --job "<job-folder>" --allow-network --ask-nexus-key
```

For a free account, `--nxm-item buff-bot` additionally prompts locally for the fresh
website-issued NXM link. Never put keys/links in a chat, command argument, shared
settings or a public receipt. A file pin creates a new immutable plan; it does not
silently mutate the accepted game recipe. Record a reusable accepted file pin in
the existing recipe only after identity/compatibility review.

For manually downloaded ZIPs:

```text
python scripts/Game-Mod-Ops.py import-archive --job "<job-folder>" --item buff-bot --archive "<official-download.zip>" --confirm-official-source
python scripts/Game-Mod-Ops.py stage --job "<job-folder>" --item buff-bot
python scripts/Game-Mod-Ops.py inspect-game --game-dir "<Kingmaker-install-folder>"
```

`inspect-archive --archive ... --generic` supports a non-UMM ZIP. `.7z`/RAR and
multi-mod packs remain native-manager/manual handoffs in this version. Inspection
checks ZIP traversal, Windows filename aliases, collisions, links, metadata,
expansion limits and declared assembly presence. It never loads a DLL.

### Guarded new-mod deployment — advanced preview

```text
python scripts/Game-Mod-Ops.py install-new --job "<job-folder>" --item kingmaker-tactics --game-dir "<game-folder>" --user-data-dir "<Kingmaker-user-folder-containing-Saves>" --game-version 2.1.7 --umm-version 0.33.2 --approve-plan "<full-plan-sha256>"
python scripts/Game-Mod-Ops.py audit --job "<job-folder>" --item kingmaker-tactics
python scripts/Game-Mod-Ops.py rollback-new --job "<job-folder>" --item kingmaker-tactics --approve-plan "<full-plan-sha256>"
```

The version arguments are **operator-confirmed**, not independently detected.
Use the actual installed versions. A recipe without a verified UMM ID also needs
`--reviewed-umm-id` matching the inspected `Info.json`.

Deployment requires Windows process enumeration, the game/store/managers closed,
a matching plan, intact staged bytes, UMM loader presence, supported dependency
versions, no existing mod with that ID, and no unrecognized Mods entries. It copies
and readback-verifies a private recovery ZIP from the selected user-data folder
(up to 1 GiB/10,000 files, including `Saves/*.zks`) before adding files. It rechecks
processes and relevant state. Locks coordinate this module's cooperating callers;
they do not prevent another program starting or a noncooperating writer racing it.

Only new folders are supported. An existing mod, ambiguous partial installation,
changed game/loader, unavailable process inventory or changed recovery source
stops the operation. No automatic upgrade, existing-settings merge, whole-folder
restore, privilege escalation or process termination occurs.

Rollback is deliberately conservative: only this job's complete new-folder
installation, unchanged files/settings **and unchanged user-data state**, can be
moved outside `Mods` into retained recovery. New saves or generated settings block
this shortcut and require save-aware review. No save is automatically restored or
deleted. A changed file may be legitimate user work, not corruption.

## What a result means

`ACQUIRED` is not `STAGED_NOT_INSTALLED`; neither means
`FILES_INSTALLED_RUNTIME_UNVERIFIED`. A successful file audit is not a loaded mod,
correct spell behavior, stable save, working overlay or performance result.
Run actual Kingmaker/UMM acceptance only under a separate authorized test scope.

On timeout or interruption, inspect **the same job** and effects. Partial files
and intent receipts remain; never erase locks or make a new job merely to bypass
a stopped action. No scheduler or background listener is installed. Public exports
should contain source/recipes and sanitized summaries, never the jobs/recovery tree.

## Primary references

- [Nexus API acceptable-use policy](https://help.nexusmods.com/article/114-api-acceptable-use-policy).
- [Nexus official API client and authorization](https://github.com/Nexus-Mods/node-nexus-api).
- [Nexus download-URL parameters](https://github.com/Nexus-Mods/node-nexus-api/blob/master/docs/classes/_nexus_.nexus.md).
- [UMM author download links](https://github.com/newman55/unity-mod-manager).
- [UMM Info.json and assembly requirements](https://github.com/newman55/unity-mod-manager/wiki/How-to-create-a-mod-for-unity-game).
- [UMM actual Mods directory loading](https://github.com/newman55/unity-mod-manager/blob/master/UnityModManager/ModManager.cs).
- [Kingmaker Tactics v1.0.1 release and install instructions](https://github.com/Gh05d/kingmaker-tactics/releases/tag/v1.0.1).

Sources were reviewed for this preview; no live account, website download, Windows
process or gameplay acceptance is implied by the citations.
