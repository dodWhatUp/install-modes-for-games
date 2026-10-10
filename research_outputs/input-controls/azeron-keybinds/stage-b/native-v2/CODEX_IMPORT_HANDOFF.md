# Current Codex handoff — R6 Azeron candidates and overlay prototype

This entry now points to R6. The earlier R5 instructions are preserved in
[the pre-R6 revision](https://github.com/dodWhatUp/install-modes-for-games/blob/52b844176e0da69f418cb382657c239f31e1febd/research_outputs/input-controls/azeron-keybinds/stage-b/native-v2/CODEX_IMPORT_HANDOFF.md).
Do not repeat R5 import from that historical handoff blindly.

## Read first, retrieve existing files yourself

Read [R6 README](r6/README.md), [DESIGN](r6/DESIGN_R6.json),
[QA](r6/QA_R6_PUBLIC.json) and [delivery locators/hashes](r6/PUBLICATION_MANIFEST.json).
Use the authenticated Google Drive connector to obtain the exact chosen R6
family from the existing private Azeron archive. No user re-upload is needed.
The complete package includes research, source recovery, nine candidate native
files, and a keys-only HTML prototype. Never restore the delivery ZIP as an
application backup. Never make the private files public for convenience.

## Current facts and limits

- R6 COMPACT has 4 layers; R6 SPARSE has 5, with nine additional source-derived
  finger cells disabled. Both retain 78 logical outputs including WASD.
- Native #19 is reserved and unassigned in every layer. It is omitted from the
  overlay. No external hotkey or raw-input integration is configured by R6;
  a disabled key does not itself emit a keyboard trigger.
- MENUS replaces LETTERS. The joystick still functions but is not drawn.
  All 29 other digital controls remain in the prototype, including #36/#37.
- BASIC #2 holds NUMBERS, #1 holds MENUS, #36 holds TOOLS. SPARSE additionally
  uses thumb #28 to hold NAV, returning on release. No nested held layers.
- R6 native structure and links were checked offline, but R6 has not been
  imported or hardware/game-tested. Preserve the known Alt/Space, thumb versus
  movement, ordinary-letter chord and cross-bank exceptions in the README.
- Draft PR4 separately reports R5 already loaded into the native software store
  and #1/#2/#36 transitions observed outside games. Preserve R5 and all later
  changes. Import profiles chooser acceptance and general gameplay were not
  verified by that report; do not transfer its results to R6.

## Scope of any later authorized execution

The current chat requested research, downloadable candidate files and an HTML
prototype, not an automatic live installation or new images. Execute device
changes only when the user opens/continues the installation task with authority.
Then use the actual Windows gaming computer, supported native/text routes,
read the live SOFTWARE list, and take a fresh private backup before mutation.
Do not touch onboard slots, firmware, games, Steam Input, reWASD, unrelated
sessions, graphics shortcuts or the external overlay application.

Choose one family for the first test. If no family was selected, read the
recorded user choice; if it is genuinely absent, ask one concise choice rather
than silently installing both. Extract the chosen ZIP and import individual
JSONs additively through a supported route. Check for existing same-name/ID
candidates first. Never overwrite original or R5 profiles, never replace the
whole store with the old backup, and never repeat an import with uncertain effects.

Inspect the resulting names, IDs and all layer targets; importer ID remapping
is unknown. Make only narrow reversible corrections to broken links after a
verified read. With games closed and appropriate user participation, test entry,
hold and release return, ordinary keys, duplicate-modifier key-up handling and
thumb/movement conflicts. A physical hand test cannot be replaced by JSON fields
or injected simulated keys. No screenshots/video or global keylogging.

If an operation is denied, blocked or leaves unknown effects, stop that affected
route and inspect state before any retry. Do not bypass prior browser/import-
handler access denials. Continue independently safe preparation only. Distinguish
native store loading from the Import profiles dialog's acceptance.

## Future game-action images

The user postponed images. First review the HTML prototype, then reconcile
actual or explicitly scoped source game bindings. One fixed device layout can
have many game label sets. Changing the game changes displayed labels only;
it must not rewrite outputs or switch profiles. Support keys, actions, and
keys-plus-actions from the same validated records.

Use GAME_READINESS_R6.json: requested 23 scopes are not verified key tables.
Keep title/edition, keyboard scheme, character, gameplay context and mods
separate. Unsupported labels stay unknown. Earlier AI posters are rejected
as mapping evidence and cannot seed a new overlay.

## Completion evidence and owner route

Keep live exports/recovery files private in the existing Drive folder; keep
sanitized results in this canonical repo after current-head/writer checks.
Record what was checked in files, loaded in app, physically exercised, and
verified in games separately. Do not merge unrelated PRs or adopt draft
AGENTS preferences. Save a concise next boundary without claiming whole-project
sync, deployment or background continuation.
