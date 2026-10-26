# Compact menus in maintained game apps

The standalone Game Tools UI Preview, shared Mod Controls, Shadow of War
controller and No Rest for the Wicked controller reuse their existing controls
under compact menus. View contains visibility choices, Layout contains display
choices, and Tools contains navigation and support. Existing preview, Save and
Apply operations keep their owners and remain explicit.

Editable choice fields use a bounded, useful width in the compact layout.
Clicking the field still opens choices while retaining the caret; typing,
filtering, keyboard navigation and cancellation remain available. Fixed choices
and ordinary text fields retain their purpose. Long labels remain in the choices.
Floating editors inherit the same field treatment when they open.

Choose **Layout → Original toolbar** to recover the previous header and field
geometry. Choose **Compact toolbar** to return. The new layout choices use a
separate UI preference file; opening a menu does not write it. The shared panel
and UI Preview embedded in Unified Game Tools keep the host's header.

General guidance and the retained previous edition are linked from
[UI and content design](UI-AND-CONTENT-DESIGN.md). These are adopted user
preferences, with context-dependent application rather than a universal claim
that three menus or one field width suits every interface.

## Validation boundary

Isolated Linux Tk fixtures passed eight shared menu tests, eighteen UI Preview
GUI cases (split into bounded batches), ten shared Mod Controls tests, sixteen
Shadow controller acceptance checks and five Wicked inline GUI tests. Four
applications also passed menu/original-toolbar roundtrips and screenshots at
large and smaller requested window sizes. One Wicked baseline row-comparison
test was skipped because its historical comparison source was not in that test
fixture. These fixture results do not establish Windows native or gameplay
acceptance. Keep machine-specific installation and native readback receipts
private. No fixture test requires a live game, native input profile or published
Overlay.
