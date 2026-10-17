# Unified Game Tools — audit and Focus UI review

**2026-10-13 · Hub 0.22.0-preview.1 · source preview, not installed.**

## Recommendation

Use **Focus** as an optional task-oriented front end, while retaining **Original**.
Both must call the same services and preserve one set of operational records.
A different layout should not require a new installer, mod database, approval
engine, overlay owner or metric calculator. The present slice replaces the
navigation shell and Mods/AI presentation, not every native Studio form.

The two obvious package entries are `OPEN Focus UI.cmd` and `OPEN Original UI.cmd`.
They deliberately use the same separate preview data, leaving the installed
application and its settings untouched. Close one before opening the other.
Neither launcher performs installation or migration. Native Studio, Updates and
User data installation pages are not enabled by the isolated preview. The full
source is retained for later native integration through the existing updater.
Python 3.10+ with Tkinter must already exist; no runtime is downloaded.

## What the audit establishes

### A01 · Kingmaker spell help

**Research complete; feature gap remains.** Relevant mods, limitations and provider sources were recorded.

Remaining: No verified full spell-description simplifier, enemy weakness dashboard or spell recommendation engine was delivered.

Basis: Prior chat and game comparison record; this turn does not claim an exhaustive new mod search.

### A02 · Ordered download kit

**Delivered.** The 13-entry archive exists and passes ZIP CRC validation. It organizes official download links and a personal packaging helper.

Remaining: It is not a bundle of all mod binaries and is not a game installer.

Basis: validation/prior-artifacts.json; no new third-party downloads.

### A03 · Reusable mod engine

**Source tested.** The 0.1.0 package has recipes, plan/dependency checks, providers, imports, staging and a guarded new-folder UMM adapter. It is reused in 0.21.

Remaining: Live provider acceptance, UMM loader setup, existing-mod upgrades and other manager execution are not established.

Basis: game_mod_ops source; original 63+8 tests are included in later suite totals, not additional passes.

### A04 · Integration into newest app

**Source integrated.** 0.21.0 is based on the exact 0.20.2 source export. The earlier missing-source issue is resolved. All 181 prior payload hashes matched.

Remaining: An update installed on the gaming PC is not evidenced; historical installed baseline is 0.20.2.

Basis: 0.21 source manifest and reproduced 1,381 passes; continuation note.

### A05 · AI control and sharing

**Source tested; connection pending.** Named context/proposal methods, local approval, expiry, revision checks, no-replay handling and optional shared summaries exist.

Remaining: This chat is not automatically connected. AI cannot approve itself or install/rollback game files through this interface.

Basis: GameToolAutomation, panel and stdio adapter; original approval method is reused by Focus.

### A06 · Easy app launching

**Delivered; Windows unverified.** The game-specific launcher ZIP and global reusable generator exist. Global pref-global-041 is published on main.

Remaining: Actual Windows shortcuts, trust prompts, interpreter availability and macOS launch acceptance were not tested.

Basis: Global main 56d8b6d; 24 generator tests in source. Earlier 19/24 descriptions refer to revisions, not two cumulative suites.

### A07 · Proactive tool-building default

**Draft adoption pending.** The current explicit preference applies here. Its reusable skill and event are preserved in Global PR 20 and in the game continuation.

Remaining: PR 20 is still draft, open and unmerged. Global ACTIVE/MATRIX reconciliation and receiving-client adoption are not complete.

Basis: Fresh native GitHub read of PR20, head 12b17733.

### A08 · GitHub / Drive continuity

**Drive current; Git app source behind.** Seven prior archives were reopened and ZIP-checked; the existing owner folder and continuation were found.

Remaining: Game Git main is now d44f9cee due unrelated hardware work, but its Hub source still declares 0.2.0. The earlier blocked game-source publication was not retried.

Basis: Fresh native connector reads; later unrelated work must be preserved.

### A09 · Overlays and native input

**Existing implementation preserved.** Picture Buttons, MIC connection, overlay groups and native source remain with existing owners. All 15 original AHK files are unchanged by Focus.

Remaining: No new physical-device, native Studio, game, hold/release or all-DPI acceptance was performed. MIC remains a separate external app.

Basis: Source comparison against 0.21; earlier native receipts are historical, not re-tested here.

### A10 · Performance / benchmarks

**Existing preparation only.** Provider-defined saved-report imports, comparison and read-only tool interfaces remain.

Remaining: No new measurements, 1% lows, latency, VRAM results, benchmark runs or recording were produced.

Basis: Original 42 portable suites rerun; no capture or game launch.

### A11 · Focus alternative UI

**Implemented in source preview.** New shell, compact Mods/AI panels, independent 80–200% zoom and density, contextual detail, table filters/columns and original-view fallback.

Remaining: Native Windows rendering, screen-reader behavior, full-page DPI coverage and user acceptance remain. The native AHK editor has not been redesigned.

Basis: Focused widget, full-host and launcher tests plus non-capture geometry probes.

### A12 · One source, two opening files

**Prepared for review.** OPEN Focus UI.cmd and OPEN Original UI.cmd use the same packaged source and the same separate preview data directory. A local OS lease prevents simultaneous preview writers.

Remaining: These open a preview, not an installed update. Native Studio/Updates/User data pages require the existing verified Windows installation route and are not launched in this preview.

Basis: Launcher code and fixtures; no existing production data is copied or migrated.

## The design: fewer layers between intention and action

### What changed now

The Focus command strip combines a clearly labelled Find selector, navigation,
zoom and View controls. A short page title, consequential scope and scoped Stop
control replace repeated introductory bands. The game name remains visible.
The route rail uses short feature names grouped into Work, Evidence, and Tools &
setup. Typing in Find does not change pages or discard drafts; committing an
unambiguous result navigates through the original route system.

Mods starts with the chosen combat-mode preset, a small action row, the actual
mod table and a brief selected-item warning. Optional mod choices and raw
technical output are collapsible. Essential/Full column sets, per-column filters,
sorting, hiding and fitting operate only on the view: **visual sort is not install
order**. The primary label is **Prepare files**, while **Prepared ≠ installed**
stays visible. UMM still performs the installer step. Errors retain their exact
status rather than being replaced by a generic “finished” message.

AI requests keeps the exact selected request and its Approve / Reject / Stop
controls visible. Connection configuration and explicit context-sharing controls
can be expanded. The implementation reuses the original approval method, including
confirmation; the redesign does not grant the model approval or hidden execution.

**Compact / Comfortable density and 80–200% zoom are independent.** Density changes
spacing, not the amount of permission or available information. Zoom scales owned
Tk text/controls and tree rows; Ctrl+plus/minus/0 and Ctrl+wheel work within the
current app, not through a modal dialog or other application. Native embedded AHK
and external MIC windows are excluded and explicitly remain separate work.

Header controls reflow at narrow widths; navigation can auto-collapse without
changing the saved preference, and a manual request can show it again. Scroll
content fills available height instead of leaving unnecessary slack. Focus view
preferences have their own revision-checked file, separate from normal appearance,
mod selections, jobs, private reports and native mappings. Reset changes the view,
not working data. Original navigation can be restored in-session without destroying
editors; for the complete original panels use the Original launcher.

### Why this fits the user's demonstrated preferences

The current request and existing design protocol favor compact combined selection /
search, concise comparison rows, contextual controls, expandable detail, clear
state, preservation of choices and easy launching. Prior Picture Buttons requests
also favor shared configurations with specific overrides rather than copied
records. The correct interpretation is **less irrelevant information at once**, not
removing meaningful controls or making all text smaller. Essential warnings,
manual overrides, unsaved state, active work and explicit approvals must remain
visible. Icons are supplementary; short text labels remain for essential actions.

The current request explicitly permits separate executables/launchers. This is a
scoped exception to the general one-obvious-launcher rule, not a reason to create
two independent applications. These preferences are source-derived, not inferred
from private traits or from generic marketing material.

## Outside research, separate from user evidence

- **Microsoft compact sizing:** desktop mouse/keyboard productivity views benefit
  from reduced control spacing, while touch-oriented views need a roomier choice.
  Applied as Compact/Comfortable rather than an always-tiny interface.
- **JetBrains Appearance:** whole-interface zoom and compact mode are different
  controls. Applied here independently so readable larger text need not imply
  large decorative margins.
- **VS Code custom layout:** contextual panels, layout customization and reset
  provide ways to focus work while retaining capabilities. The cited page labels
  its specific new density switch experimental; we do not treat that experiment
  as a universal standard or copy its product behavior uncritically.
- **W3C Resize Text:** a useful target is usable text enlargement to 200% without
  losing content/function. This is a design/testing target, **not a WCAG compliance
  claim** for this Tk/native application. Screen-reader/UI Automation and actual
  Windows DPI acceptance were not performed.

These sources inform design choices; they do not prove that this application is
usable or fast. Geometry checks and automated contracts are not a user study.

## Lessons worth integrating

1. **Use a completion matrix, not one “done” flag.** Track source creation, tests,
   publication, installation, connection and task success independently. Several
   earlier “complete” statements described source delivery, not the user's ability
   to open or use it on Windows. Avoid aggregate green badges for partial tasks.
2. **Test the actual launch-to-page chain.** Full-host tests found a missing
   allowlist entry for the new authored Focus module after its panel tests passed.
   The module was registered explicitly; arbitrary module loading was not enabled.
   Existing shortcut extraction tests also exposed an added closure dependency;
   the handler now discovers the optional view through the existing root object.
   Original tests and guards were retained, not weakened.
3. **Preserve original evidence and count tests once.** Earlier 19/24 launcher
   counts and 707 native-editor checks belonged to other revisions/scopes. They
   must not be added to the current 1,381-case baseline. The baseline was rerun
   before modification, and the candidate was tested separately.
4. **Discover distributions per author/provider.** The early “everything requires
   Nexus” explanation was too broad: later work found an author-hosted GitHub
   release. Keep download provenance and sharing permissions per package, not as
   a blanket assumption. No third-party archive was redistributed here.
5. **Keep error, unknown and unverified meaningful.** A manifest match is not a
   security certification, module load is not game correctness, and a returned
   proposal is not performed work. The Focus view shows exact status and installer
   boundaries; private diagnostics remain expandable.
6. **Source discovery needs explicit version locators.** Drive's current source
   was newer than GitHub's application. The missing-source request is obsolete.
   Git's current head later advanced for unrelated hardware notes, not app source.
   Preserve both current source identity and consumer acceptance independently.
7. **Exports must include new dependencies.** The source exporter uses an explicit
   allowlist. Add new modules, tests and review records together, rather than
   relying on a passing local UI with a broken distributed package. The main
   design protocol referenced in guidance was not present in the 0.21 export;
   retain its canonical link and record the gap instead of inventing its bytes.
8. **Reusability is not unattended authority.** The proactive-tooling preference
   remains a draft Global adoption; current direct authorization still applies to
   this review. Helper creation never re-enables blocked writes or capture.

## Priority development plan (existing GT work, not a new task queue)

| Priority | Change | Expected benefit | Remaining acceptance |
|---|---|---|---|
| 1 | Native acceptance and release-aware launcher integration | User can actually open the current version reliably | Windows runtime, shortcuts, trust prompts, normal shutdown, updater and rollback |
| 2 | Reusable contextual inspector / progressive forms across all pages | Greater reduction in visible clutter beyond Mods and AI | Preserve each editor's draft/callbacks; shared native AHK designer remains separate |
| 3 | More useful mod lifecycle and compatibility readback | Fewer “prepared but not installed” surprises | Actual provider/UMM checks; new-folder install vs safe existing-mod upgrade |
| 4 | Workspace column/layout presets with scoped persistence | Fast switching between learning, compact work and diagnosis | Migrations, long names, resizing, all-column access, keyboard order |
| 5 | Current-client capability discovery and guided connection | AI knows what can really be done and where | Actual client round-trip, privacy preview, capability-scoped approval |
| 6 | Versioned recipe/provider adapters and bounded multi-step approvals | Less repetitive configuration without duplicate managers | Explicit budgets, expiry, cancellation/reconciliation; never self-approval |

A further independent front end is an option, not an obligation. A resizable
side inspector, split workspaces, pinned commands, compact list/cards per page,
light/dark/high-contrast themes, finer text-only zoom, and semantic group collapse
are useful later candidates. They must share the same service contracts. Do not
force native forms into an unsuitable old layout merely for visual consistency;
a separate front-end module can replace the presentation of one task at a time.
Do not trade the current goal for a large framework rewrite without demonstrated
benefit and a bounded scope. No claim of measured CPU/GPU/VRAM savings is made.

## Validation and what remains

See `FOCUS-UI-VALIDATION.json`, `FOCUS-UI-SOURCE-DELTA.json` and
`WORKSTREAM-AUDIT-2026-10-13.json`. The entire prior 42-suite portable set was rerun
on the original source and the edited candidate. New tests cover panel semantics,
full-host routing, protected display preferences, exact status, approvals, preview
manifest validation and the shared preview lease. No old AHK file or private
production setting was changed. Native PowerShell/AHK, Windows DPI/UIA,
actual provider download, AI-client and game tests are still unverified.

Existing blocked Git/remote effects remain stopped. This source candidate is
published through the existing private Drive delivery route; it is not Global
adoption, Git publication or an installed update. Current source/continuation
ownership stays with the game-tools project. No new scheduler or task queue.

## References

- design_owner: https://github.com/dodWhatUp/install-modes-for-games/blob/d44f9cee6782d1228d20610a08b404ee44a3aff8/docs/UI-AND-CONTENT-DESIGN.md
- global: https://github.com/dodWhatUp/global-chat-instructions/commit/56d8b6d72a2c7dbd91ad51fbe72f3326e7023a27
- draft: https://github.com/dodWhatUp/global-chat-instructions/pull/20
- continuation: https://drive.google.com/file/d/1sbAoFn3o2SYfOhphZccMn9S2VGbpPdVA/view
- microsoft: https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/compact-sizing
- jetbrains: https://www.jetbrains.com/help/idea/settings-appearance.html
- vscode: https://code.visualstudio.com/docs/configure/custom-layout
- w3c: https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html
