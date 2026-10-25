# Responsive page headings

The compact top area keeps the editable finder, navigation and View menu in
one row. The duplicate app heading and persistent setup toolbars are collapsed;
Layout, Interface, Identify UI, All tools and Show APP LAUNCHER reuse their
existing owners through View. Show expanded app controls reveals the original
controls. New interface keeps a small View row so switching back remains
reachable. The scope banner remains visible with reduced padding. This changes
presentation only and does not rewrite view preferences on startup.

For 0.27.27-preview.1, 27 GUI regressions passed, plus an integration fixture
using the unchanged InterfaceViews 1.0.1 owner. The fixture posts the Interface
cascade and switches Existing/New/Existing while retaining both drafts and the
selected route. Native Windows confirmed the compact rendering and retained
View entries. Full native menu interaction remains a separate acceptance check;
host input was left to the user when a game became foreground. All 44 protected
game/native/Overlay files remained byte-identical after delivery.

A saved page must lay out correctly before Home is ever displayed. Its heading
and explanation use the visible page width, with their own coalesced resize
events. Hidden dashboard sizing never sets a narrow permanent page width.
On a narrow window the title moves below the small navigation/disclosure row,
leaving its full width for readable text. Resize changes presentation only;
the existing notebook, controls, unsaved drafts and native owners remain alive.

The Existing/New interface selector remains separate from the Modern/Compact/
Professional/Classic **Layout** selector. Route details remain an explicit
disclosure, and the preferred sidebar width is preserved through narrow views.

Regression checks map a saved Profiles page without visiting Home, then resize
it at larger text scaling. They check title width, header height, usable editor
area, unchanged route and preserved draft text alongside the existing layout
and navigation suite. Native Windows and individual app checks retain private
per-machine receipts; a guest test is not hardware or game acceptance.

The 0.27.26-preview.1 Windows delivery was checked on 2026-10-26. All 24
Modern UI GUI regressions passed. Native checks confirmed the corrected saved
page at the original and a narrower width, plus the parallel UI Preview at two
widths. Typing/filtering with an open list and Escape restoration passed in the
Hub task finder, Preview game selector, Shadow of War saved-profile and mod
selectors, and the shared standalone Game Mod Controls game selector. The
legacy No Rest controller has no editable choice field. Six Desktop launcher
targets remained valid and all 44 protected game/native/Overlay files remained
byte-identical. These are scoped UI checks, not exhaustive accessibility,
gameplay or every-monitor/DPI acceptance. No Apply or Publish operation ran.
