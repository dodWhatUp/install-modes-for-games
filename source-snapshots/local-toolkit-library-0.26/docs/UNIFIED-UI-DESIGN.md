# Unified GameTools interface design and feedback

## 2026-10-13 — optional Focus UI and previous-work audit

**Hub 0.22.0-preview.1 source preview**, derived from exact 0.21.0 bytes.
[Audit, design decisions and next boundaries](FOCUS-UI-REVIEW.md) and
[data-only audit](WORKSTREAM-AUDIT-2026-10-13.json) distinguish research, source,
publication, installation and actual use. Focus adds an alternative shell and
Mods/AI panels with independent density/zoom, while Original remains available.
Existing services, approval rules, GT-001–060 and all native AHK files are retained.
Two preview launchers share isolated preview data, not production settings.
No Windows deployment, game, benchmark, recording, new AI connection, Global
adoption or retry of blocked Git/remote effects occurred.


## Native Multi Image Canvas — 2026-10-12, Hub 0.20.2

The MIC tab is a connection/setup editor for the separate Multi Image Canvas
application, not a replacement canvas engine. `StudioMicEditor` shares the
existing native presentation boundary and six-file installation. The existing
shortcut widget, Save, manual toggle, Mark hidden, website, full setup guide
and Local-overlay alternative are retained, with a Classic layout fallback.

Modern groups the task into matching the overlay shortcut and checking visibility
before connecting a Picture slot. Process/bridge status, dirty shortcut state,
the toggle-desynchronization warning and the reliable Local alternative stay
visible. Only the detailed canvas/Hold instructions use Show/Hide. A direct
Picture-buttons route changes the tab without saving, sending input or changing
the current overlay. Manual toggle/Mark hidden/Save are still explicit actions;
an editor navigation is not permission to invoke them.

At 850 logical pixels, four action buttons reflow into two rows. The readable
minimum is 700 pixels; the existing Hub viewport supplies scrolling beneath
it. Expanding the guide increases the declared minimum height, not operational
settings. Classic and Modern use the same draft widget. Layout/disclosure state
is session-only; no settings/profile/appearance migration is introduced. Other
native forms and the advanced Picture editor remain separate design stages.

Native Hotkey letter text depends on the active keyboard layout. MIC's owned
widget VK is used to read ASCII physical-letter identities on explicit Save
and for dirty comparison; modifier order/case are normalized for comparison
only. The keyboard layout and saved shortcut are never changed by reflow.
One deferred native repaint after Tab3 visibility settles prevents a blank
newly revealed dropdown; it cannot reflow or enqueue itself.

219 inert native MIC checks cover four widths, guide visibility versus enablement,
draft/layout/navigation retention, locale-safe shortcut reading, existing UI IDs,
actual marker positions, declared minima and unchanged fixture INI/runtime data.
Picture Buttons' 62-check native suite remains a separate regression. External
MIC Hold behavior, physical devices, games, all-DPI coverage and resource tests
are not established by this desktop-only change.

The shared move helper does not assign ordinary field height to a dropdown:
its height controls the whole popup, so fixed 28-pixel sizing can hide the
choices. Preserve native popup sizing in both reflow and Classic restoration;
test the actual dropped-control rectangle, not only programmatic selection.
See [AutoHotkey's dropdown sizing contract](https://github.com/AutoHotkey/AutoHotkeyDocs/blob/v2/docs/lib/GuiControls.htm#L309).

MIC's two mutually exclusive layout choices use visible Modern/Classic radio
buttons. This avoids a transient popup and exposes active selection directly.
The embedded desktop-control route did not reliably expose the dropdown popup
even after its height contract passed; that observation is not proof of a
universal native-popup failure. Other existing dropdowns retain their controls
and corrected native popup sizing; broad embedded-focus acceptance is separate.

## Native Picture Buttons — 2026-10-12, Hub 0.19.2

Apply the shared Modern contract to the first native editor, retaining the exact
operational controls/callbacks and a Classic fallback. `StudioPictureEditor` in
the existing Picture module owns only layout, disclosure and draft status;
legacy INI, advanced sidecar, native profile, HUD, MIC and overlay owners remain
unchanged. The primary editor reflows to narrower rows at 850 logical pixels,
with 700-pixel readable minimum width and scrollable Hub presentation. Resizing
does not reset column widths. Owner-bound minimum-size properties carry display
dimensions only; they are not a key/text or arbitrary-command transport.

Keep essential actions and saved/unsaved state visible. Show display settings
reveals placement/opacity/offset controls without changing their enabled values;
Timed duration and the chosen Local/MIC source receive contextual visibility.
Layout/disclosure are session-only; they neither overwrite saved Hub appearance
preferences nor migrate user data. Moving to another row with unsaved edits needs
confirmation, with cancellation restoring the original row and draft.

Native feedback markers track reflow and target visibility. Classic, MIC/HUD/
status/Game Input tabs, advanced library/variants/context and runtime overlays
remain available. Their separate internal forms are future editor stages, not
completed by this first primary-editor slice. Tests use prepared private fixture
INIs with input hooks, MIC shortcuts and Game Input activation disabled. Linux
portable UI evidence cannot establish native AHK behavior; bounded requested
Windows desktop tests are recorded separately from games/DPI/device acceptance.

Shared layout ownership: Modern page labels declare that their page owns
wrapping, so generic Appearance wrapping must not attach a competing resize
callback. Reapplying an identical wrap width is a no-op; font measurement reuses
one retained font. A seeded Modern preference must pass bounded visible-startup
and advancing-timer acceptance, not only withdrawn-root theme switching. See
the [installed receipt and remaining live-visual limit](GAME-TOOL-CONNECTIONS.md#2026-10-12--native-picture-buttons-redesign-installed).

## Modern task workspace — 2026-10-12, Hub 0.18.0

The user explicitly requested deeper design research and a new interface built
around the existing capabilities. Modern is a new presentation surface, not a
new automation engine or a destructive replacement of the native Studio.
Professional, Compact and Classic remain selectable, using the same editors.

### Shared design contract

- Start from the user's task, not a list of software products. Home has four
  task groups with eight direct routes; Results, Controls, Diagnostics and
  Library expose the twelve existing feature workspaces. Route selection never
  invokes an operation. Do not label mock readiness as measured/live readiness.
- Use one contextual page title and a short safety scope. Put longer route
  explanations behind Show details. Keep the top-level category visibly active;
  Home must remain reachable when the rail collapses.
- Preserve the editable find/select control. Typing filters choices; Enter
  commits one unambiguous route; Escape clears without changing the editor.
  Search while editing must not hide or recreate unsaved contents. Ctrl+K is
  local to the Hub and cannot steal focus from a modal/native Studio editor.
- Use semantic color tokens in `GameToolModernUI.py`: pale workspace, white
  work surfaces, navy navigation, teal actionable text, dark primary text and
  readable muted detail. Text contrast pairs have automated 4.5:1 minimum
  checks; this is not a blanket accessibility certification.
- Use a small type hierarchy (page title, card title, normal text, contextual
  label) and spacing groups, not arbitrary per-widget colors or dense text
  bands. Do not shrink fonts to fit a small window. Cards reflow to one column
  based on available width and font measurement, with owned scrolling.
- Collapse the navigation rail at narrow widths without overwriting the user's
  preference. Preserve the draggable divider, explicit Show/Hide control,
  native table heading dragging, fit menus and existing focus/scroll ownership.
- Keep feedback on the component itself. Modern uses stable `UI-007` role and
  route suffixes, including text and task sections. Copying an ID never invokes
  the underlying task. Retired search cards must not leak feedback widgets.
- Home/category navigation cannot forward hidden Tools launch/capture/import
  shortcuts. All existing operational actions remain owned by their editors;
  no feature is silently enabled by navigation or a style change.
- Keep versioned source separate from user data. A session-only Modern preview
  does not save over the existing layout. Explicit Interface selection saves
  the chosen mode while retaining each earlier layout's view and unknown fields.

### Research basis and deliberate choices

Microsoft's [adaptive navigation guidance](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/navigationview)
supports consistent categories and collapsing navigation to preserve content
space. This implementation adapts those principles in the existing Tk stack;
it is not WinUI and does not inherit WinUI's accessibility behavior automatically.
NN/g's [progressive disclosure guidance](https://www.nngroup.com/articles/progressive-disclosure/)
supports showing common choices first while keeping secondary detail available.
Microsoft's [form guidance](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/forms)
informs grouping and responsive layout for subsequent individual editor work.
These sources were refreshed on 2026-10-12. The particular four categories,
palette and task cards are design decisions for this user's toolkit, not
universal requirements or claims made by those sources.

### Coverage and next boundary

Implemented: the new task home/category navigation, search results, contextual
heading/disclosure, responsive cards, shared visual tokens and existing Python
control/table styling. Shared action bars with more than four commands show two
primary commands and More actions in Modern; secondary items invoke the original
buttons and mirror their disabled states. Other layouts restore all buttons.
Existing AHK forms, Picture Buttons/MIC/HUD and overlays
stay reachable through the preserved Studio; their internals have not all been
redesigned from scratch. Future editor work should use the shared contract above
and retain an old-editor fallback until feature-equivalence tests pass.

Portable visible snapshots and withdrawn widget/fixture tests establish only
their declared UI scope. They do not prove physical input, every Windows DPI,
native AHK reflow, game menus or benchmark acceptance. Live games, performance
tests and recording remain deferred. See the dated connections record for
actual installation/preservation evidence, not an inferred completion claim.

## Purpose and boundaries

Make a complex toolkit understandable without removing power, old features or
user data. These are selectable design candidates, not a claim that one layout
is universally better. The user will compare them and choose what to retain.
Keep games, benchmarks and recording stopped during desktop acceptance.

## Three layouts, one application

| Layout | Presentation | Intended comparison |
|---|---|---|
| Professional | Goal-first grouped sidebar when space permits; current task and safety scope above the workspace; stronger hierarchy and spacious action controls | Research-informed task-oriented workspace |
| Compact | Feature search as the primary navigation; navigation optional; denser controls and minimal lower breadcrumb | User-preference-led, less navigation chrome |
| Classic | Original Notebook tabs and native Windows theme; searchable original-page list remains available when tabs overflow | Familiar earlier interaction, with the new feedback and scrolling fixes |

All three reuse the same existing panel and native AHK engine instances. Changing
layout is not a Save, reload, profile activation or feature enablement command.
Do not recreate panels on a layout switch. Retain unsaved fields, selected page,
search and each layout's visibility choices. Appearance choices are stored in
`ui-preferences.json` under the existing version-independent Hub data directory;
operational profiles, settings, reports and image assets remain separate.
Unknown/future preference schemas and observed concurrent edits are retained,
not overwritten. An unsupported view can still be used for the current session.

## Recovered preferences and their limits

The saved MATAM HTML design comparison (2026-10-06, fetched 2026-10-12) favors
local expansion, preserving reading position and independently selectable views.
The saved requirements collection's REQ-027 through REQ-033 distinguishes topic,
information type and depth; it preserves parallel integrated/separate views and
visible critical qualifications. Some entries are contextual preferences or
implementation proposals, not universal mandates. The earlier app-specific
design conversation has not been comprehensively recovered in this review.

Sources: [MATAM original formula/design comparison](https://drive.google.com/file/d/1-NiR5hXTOKMmU9c6TIjtqTDi9VmHAgQ8/view),
[requirements and learning-design collection](https://drive.google.com/file/d/1esgmVZkZL2QUH7jPXPEsfO_MZx8RFfzn/view).
These private knowledge references were read, not modified or republished.
Use the [shared design foundation](../../../docs/UI-AND-CONTENT-DESIGN.md) as an optional
starting point, consistent with the user's 2026-10-12 clarification. Compactness
must not hide important states, shrink text excessively or remove useful choices.

## Research-informed decisions

Adapt the surrounding layout by resizing, reflowing and repositioning elements;
collapse a space-consuming sidebar without losing its routes. These are adapted
principles, not use of WinUI/XAML in this Tk/AHK application.
[Microsoft responsive design](https://learn.microsoft.com/en-us/windows/apps/design/layout/responsive-design).

Give secondary detail a clearly labeled entry point and keep frequently needed
controls visible. The classic research is dated 2006; it informs a candidate,
not a new empirical usability study of this toolkit.
[Nielsen Norman Group: Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/).

Use layout weights and shared widget styles rather than fixed root dimensions
and duplicated panels. [TkDocs: grid](https://tkdocs.com/tutorial/grid.html),
[TkDocs: styles](https://tkdocs.com/tutorial/styles.html).
Normal text/form work should avoid two-axis scrolling where possible; broad
data tables and legacy native forms may require a horizontal fallback. This is
design guidance, not a native-app WCAG compliance certification.
[W3C: understanding reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).

## Stable feature numbers: UI-006

The top-row **? Identify UI** opens a contextual display menu, not a separate
component list. Choose **Show all components**, one type-only preset, or
**Choose types…** to combine Controls, Text & status, Tables & images and Sections.
**Hide all markers** leaves every original feature enabled/disabled as before.
The button and status show the active display state. Filters are session-only
and identification is Off on restart; existing view/profile JSON is not migrated.

Floating **?** markers stay on actual components, including authored explanation,
status and labels, tables/images and named sections. Hover a Hub marker for its
public name/ID; click to copy and open a local confirmation with a selectable,
read-only ID and **Copy ID** retry. Native Studio uses the same confirmation
pattern. Clipboard failure is explicitly reported rather than counted as a
copy; it never invokes the underlying control. Text markers get a temporary
gutter in the Hub or sit beside native text; hiding restores original padding.

Permanent feature numbers such as `UI-103` (Studio image/preview) and `UI-202`
(saved-report import) remain valid. Component suffixes, e.g.
`UI-103.action-preview-current-edits`, use declared fields/action names, never
screen coordinates or automatic widget ordinals. Preserve these roles across
refactors or provide an explicit alias; never repurpose retired identifiers.
The optional old searchable index remains a compatibility helper in source,
but is not the top button's action or required identification workflow.

Markers have their own copy-only callbacks. They do not intercept normal clicks,
activate Save/preview/launch/input, read field contents or copy program source.
Normal controls still work outside the small marker area, even in identification
mode. Copying replaces the clipboard only after the explicit marker click;
paste the ID with your comments or screenshot yourself. There is no screenshot
capture, network transmission or automatic chat message.

Coverage includes main Hub actions, authored labels/status, declared fields/tables, owned import and
session child dialogs, native Studio Picture/MIC/HUD/Status/Game Input controls
and Advanced Picture Buttons. Generic unlabelled controls are not assigned
guessed value-based IDs; section IDs remain available. Unknown/private-bearing
text or undeclared data views use a public area-level ID, not a generated ID
containing their contents. Table cells/rows are identified as their table, not
copied as separate private-content IDs. Declared roles remain the precise stable
integration path. This is not instrumentation of other
apps, mapper software, game overlays or every future control. New panels must
register their public roles with the shared presentation service.

Hub/native synchronization carries only an owner-bound Boolean display flag
and a validated four-bit type filter (0–15, encoded 16–31) on the existing
viewport. A missing filter keeps backward-compatible all-type display; an
invalid mask is rejected/ignored. It is not an arbitrary input/command transport.
Native badges must explicitly raise their own sibling z-order: visibility
alone can paint a marker while leaving the original action as the click target.
Validate the actual copied confirmation, not only marker screenshots.
Raised native badges also require sibling paint clipping; otherwise lower
controls can repaint over them despite correct hit-testing. Apply
`WS_CLIPSIBLINGS` only to the owned targets/badges, not other applications.
[Microsoft: child-window update regions](https://learn.microsoft.com/en-us/windows/win32/gdi/child-window-update-region).

## Scrolling, keyboard and native ownership

### Responsive workspace continuation — source Hub 0.16.0

The sidebar and content share a native horizontal Panedwindow. Drag its divider
to set a preferred width (150–520 logical pixels); double-click the divider or
use **View → Reset sidebar width** to restore 256. **View → Narrow sidebar**
sets 170. A visible **Show sidebar / Hide sidebar** button stays beside search.
At very small widths the sidebar temporarily collapses; explicitly choosing
Show still works. Automatic shrinking/collapse does not overwrite the preferred
width or saved visibility, select a different route, discard edits or enable a
feature. The sidebar width is an optional additive schema-1 presentation field;
older view files without it remain valid. Each interface mode keeps its width.

Hover a navigation row for its full authored name and scope in a floating hint.
Filtering, selecting, hiding or leaving the row removes the hint. It contains
public route descriptions, not private profile fields or copied record data.
The search label moves above its field when space is limited. The initial window
fits the screen reported by Tk, has a lower bounded minimum and includes a
bottom-right resize grip; normal Windows title-bar maximization remains available.
This is not acceptance of every monitor/DPI configuration or work-area boundary.

Shared heading-table controls fit initial column proportions to the viewport.
Drag a heading divider normally to enter manual-width mode; later resizing and
layout switches leave that manual choice alone. Double-click a divider to fit
that column to existing text. Right-click a heading, or focus the table and press
Shift+F10, for **Fit this column to text**, **Fit columns to window**, or
**Restore original widths**. Text fitting is bounded to 200 displayed root rows
and 512 characters per cell, with widths capped at 800; no measurement is saved
or copied. Row selection, sort callbacks and source values are untouched. These
table widths currently persist for the session, not across app restarts.

Catalog field groups reflow using the shared ResponsiveGrid instead of four
fixed columns. Its Browse and comparison-preparation pages have owned scrolling;
preparation actions and Comparison actions wrap without replacing callbacks.
The legacy native AHK forms still keep their original internal geometry inside
the scrollable Hub viewport. Their individual fields are not yet a responsive
rewrite, and native ListView columns are not governed by the Tk table service.

The installed 0.16.0 update also includes the 0.15.0 marker type/filter and
copy-confirmation corrections above. The guarded updater was applied after
verified normal shutdown; 134 protected user files and saved view preferences
remain unchanged. Nineteen visible portable Tk fixture checks passed in the
isolated Linux guest using exact installed modules. Some narrow labels/headings
still clip; hover text/state assertions do not establish readable popup pixels.
Windows/native AHK viewport, physical keyboard, heading-menu and marker-copy
visual acceptance remain pending. Do not equate guest/hidden fixtures with a
restarted production app or universal monitor/DPI coverage. See the
[installed acceptance boundary](GAME-TOOL-CONNECTIONS.md#2026-10-12--responsive-update-installed-after-normal-shutdown).

Search remains reachable when the sidebar automatically collapses. Ctrl+K and
original Ctrl+1 through Ctrl+8 navigation retain their existing context guards;
do not steal shortcuts from a native AHK control, text editor or modal dialog.
Tool/update action rows wrap rather than deleting less-used commands. Original
Hub pages gain bounded scrolling and tables retain horizontal access.

Shared scrolling accumulates small wheel deltas, honors larger deltas and keeps
list/text/value controls' own wheel behavior. Keyboard focus can reveal an
off-screen form control. Embedded Studio retains its native control geometry,
settings and hotkey ownership: scrollbars and a bounded wheel-delta relay make
its legacy form reachable without pretending the form itself has been fully
rewritten. Relay only the owned embedded GUI's display scrolling; never add
arbitrary input, executable commands or cross-window automation to that bridge.

## Acceptance and preservation protocol

1. Make a just-in-time source and installed data checkpoint; hash originals and
   copies. Preserve last known-good and current checkpoints separately.
2. Exercise all available layouts with the same page instances and unsaved entries.
   Check narrow/wide geometry, readable labels, navigation, visible scope, scroll
   ownership, modal/text guards and feedback selection/copy.
3. Verify view JSON round trips and future/invalid/drift cases; preserve unknown
   extension fields. Run existing regression suites as well as new UI tests.
4. Export the curated source bundle, inspect every entry, then use the existing
   guarded in-place update transaction. Never uninstall/reset to change layout.
5. Test the actual installed desktop UI. Distinguish withdrawn-widget fixtures,
   visible UI observations and still-deferred games/hardware acceptance.
6. Recheck original Studio/MIC/native profiles/settings/assets against hashes.
   A new presentation preference file is intentional; no existing file is reset.
7. Record verified results and limitations separately. Roll back only authored
   code through Updates, preserving user data and the private recovery copies.

Future candidates: reflow individual native AHK forms, improve modern contextual
help and add per-control IDs where feedback requires finer targeting. These are
not claimed completed by the initial shell redesign.
