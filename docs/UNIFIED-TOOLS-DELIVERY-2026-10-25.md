# Unified Game Tools source checkpoint — 2026-10-25

The maintained app combines Mod Controls with the Azeron controls workflow,
runtime profiles, reWASD references and the optional New interface. The installed
line is 0.27.25 preview; source publication and backup do not reinstall it or
replace its version pointer, settings, profiles, maps, drafts or game files.

## Preserved behavior

- **Interface: Existing / New** selects two views in the same Hub. Existing is
  the default. All tools returns to the existing pages and their original owners.
  Switching views never applies a game or native profile.
- Mod Controls 2.2 retains typed settings, shared game identities and profiles,
  source links, component locations, Refresh files, manager preparation,
  floating options, recovery and local review/write ownership. Ranked local
  discovery remains a proposal until the user selects a location locally.
- The controls planner, keymap builder, Overlay appearance/alternate views,
  momentary layers, Hold behavior, map exchange and diagnostics retain their
  existing services. Runtime profiles and reWASD Save/Apply remain separate.
- Editable choice fields open from the text area while preserving the caret
  and filtering. Keyboard selection, Escape, stable IDs and explicit Add/Save
  remain separate from opening or typing. Ordinary text/fixed choices retain
  their purpose. APP LAUNCHER names and stable entry points remain supported.

## Source reconciliation

The checkpoint reconciles canonical main `e503cd6`, the controls-workflow lineage
at `823f8c7`, and the interface lineage at `b44c7d7`. Installed source payloads
supplied the later Mod Controls 2.2 and interface additions; their owners were
retained. The independent library 0.26 candidate remains unmerged. Original
private masters, exact archive inventories and recovery receipts stay private.

The optional Profiles page previously failed because its helper was missing
from the exact authored-module allowlist. The correction permits only that
reviewed helper and continues to refuse unknown modules.

The first editable-list build passed Linux checks but failed during actual
Windows preview construction: Windows Tk rejected the X11 `ISO_Left_Tab`
binding, leaving a partial window. Publication must include the platform-aware
correction and retain the actual Windows acceptance boundary; Linux checks
alone do not establish Windows startup success. The reviewed 0.1.2 source uses
Tab/Shift-Tab on every platform and adds ISO_Left_Tab only for X11. Its 16 guest
checks passed. The installed 0.1.1 copy was not replaced: the human stopped
Computer Use with Escape. Installing the correction and actual Windows startup,
typing/filtering and cancellation checks remain pending.

## Verification and recovery boundary

Reconciliation checks covered shared Mod Controls, interface packaging, preview
models/search, runtime profiles and reWASD services. Syntax, payload comparison,
privacy review and archive integrity are recorded separately from native UI and
physical game/device acceptance. The reconciled tree passed 64 focused headless
cases, 305 Python syntax checks and three platform-selection checks. PowerShell
script execution was blocked by destination policy; source syntax and four
extracted privacy-pattern checks passed without changing that policy. Native
Windows acceptance of the corrected dropdown remains pending. No game, graphics, input-mapping, native profile
or Overlay configuration action is part of publication.

The Drive checkpoint contains authored source, tests, examples and sanitized
documentation with a new per-file manifest. It excludes installed manifests
containing machine bindings, user configuration, native profiles, saves,
credentials, downloaded binaries and raw logs. It supports source reconstruction;
it is not a full machine/game backup or a tested native-profile restoration.

See [interface selection](UNIFIED-INTERFACE-VIEWS.md),
[editable lists](EDITABLE-CHOICE-LISTS.md), [Mod Controls](MULTI-GAME-MOD-CONTROLS.md),
[runtime profiles](GAME-PROFILES.md), [controls workflow](GAME-CONTROLS-WORKFLOW.md)
and [APP LAUNCHER contract](APP-LAUNCHERS.md).
