# Compact header menus

Unified Game Tools 0.27.31-preview.1 separates the former mixed View menu by
purpose. The existing sidebar shortcut remains available beside search when
there is room. Narrow windows use View's sidebar toggle to leave search useful.

| Menu | Purpose |
|---|---|
| View | Show/hide sidebar, tabs, page details, field icons and expanded controls; sidebar width and Reset view |
| Layout | Existing Classic/Modern/Compact/Professional styles, plus the existing Interface selector |
| Tools | Browse by Goals/Features/Original tabs, open an existing tool, find APP LAUNCHER and UI identification |

View contains seven choices rather than every application command. The two
sidebar-width commands share a submenu. Tools reuses the existing tool menu;
Layout reuses the existing appearance and interface variables and callbacks.
All three menus remain reachable in the New interface and expanded-control mode.

The editable search field requests 28 characters and keeps its bounded width
in a wide window. At narrow widths it shares the next row with the menus and
fits the available space. It remains the same editable widget: opening its
choices, filtering, caret, keyboard navigation and explicit selection retain
their existing owner. Opening a menu never commits an edit or applies a value.

This is a presentation change. Saved layouts, icon visibility/assignments,
profiles, game bindings and Overlay settings retain their separate owners.
