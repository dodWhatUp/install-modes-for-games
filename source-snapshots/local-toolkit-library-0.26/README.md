# Game Tools Keybinds 0.2.0-preview.1

An **extensible native-keybinding source module** for the existing Unified Game
Tools owner, `dodWhatUp/install-modes-for-games`. This is an additive evolution of
0.1, not a replacement Hub, an installer/update ZIP, or installed game support.

## What changes when adding another game?

For supported text semantics: add **one data-pack folder**, not changes to core.
Its `pack.json` declares exact native fields, shared key encodings, scoped discovery
rules, runtime contexts, alternate input variants, file precedence, presets,
writer processes and evidence. Add sanitized before/expected fixtures and notes.
For a genuinely different text grammar, explicitly register one reviewed adapter
module using the SDK; all existing staging, backups, approval and recovery remain.
Data packs cannot load that code, run commands or approve their own installation.

Start with `00_START_HERE.html` for a compact Hebrew guide,
`docs/EXTENSION_GUIDE.md` for the developer workflow, and
`KEYBIND_INTEGRATION_HANDOFF.md` for the current Workbench integration.

## Runnable entry points

Use the existing compatible Python 3.10+ runtime. No new dependencies are required
for core/CLI. Tk is needed for the local panel; no runtime is installed by this module.

```text
python scripts/Game-Keybinds.py adapters
python scripts/Game-Keybinds.py pack-check --pack game-packs/format-examples/sample-json
python scripts/Game-Keybinds.py pack-scaffold --out MY_NEW_GAME --game my-game --title "My game" --adapter json
python scripts/Game-Keybinds.py learn-diff --before before.json --after after.json --adapter json
python scripts/Game-Keybinds.py --data-dir SELECTED_EXISTING_HOST_DATA gui
```

`Open-Keybinds.cmd` reuses `GAME_TOOLS_PYTHON` and optional
`GAME_TOOL_HUB_DATA_DIR`; it does not install Python or bypass blocked policy.
Choose a separate preview data root for experiments. Never copy production data
into the preview automatically. A local file picker or reviewed instance request
chooses active files; filename, timestamp and store metadata are only candidates.

## Capabilities and boundaries

Ten built-in text routes: JSON, JSONC (comments/trailing comma), INI,
INI sparse scalar overrides, existing Unreal key records, existing Unreal chord
records, XML attributes, quoted CFG binds, quoted KeyValues1, and key:value lines.
These are **format routes, not ten confirmed game integrations**.

The 17 retained game research drafts are not ready native recipes. Their location
notes are preserved separately. Zero newly certified real-game adapters, zero native
Windows/in-game tests, zero live configuration/device modifications in this delivery.
The ten format examples and SDK example are fictional fixtures, not replacement
files for any real game. Do not install them into real game directories.

Scoped plans guard hashes of all related declared files, including read-only
defaults. A reviewed scalar-override model resolves actual owners, not a universal
engine input stack. Unreal +/-/!/dot list merging, arbitrary includes, binary/save
layouts, registry mutations and auto-selecting input/profile modes are not implemented.
Unknown roles/encodings/conflicts remain typed blockers. No OCR, game launch,
recording, arbitrary shell commands, automatic retries, network updater or AI approval.

## Existing backend and host

Use one `game_keybind_ops.core.Service` under the existing host data root. The
original `GameToolJournal`, `GameToolAutomation` approvals, process guard, immutable
plans, before/after copies and exact/selective rollback are reused. Optional
`GameToolKeybindWorkspaces` composes with the **0.23.0-preview.1** Workbench;
keybind-only games do not require a fake mod recipe. See the handoff before mounting.
The host archive and all source payloads used for testing remain unchanged.

Read `validation/final/VALIDATION.json` for actual test counts and exclusions.
`validation/previous-0.1/` retains dated original evidence, not current acceptance.
