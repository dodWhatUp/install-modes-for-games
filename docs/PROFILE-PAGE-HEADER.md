# Game profiles content header

## Modern layout follow-up — 0.27.34-preview.1

The Modern Game profiles page also hides the remaining duplicate pinned
“Home / Game profiles” row. Its own heading and help stay in the scrolling
content card, and Home stays accessible in the sidebar. The sidebar and content
now begin at the same height as the dashboard sections. Reapplying Modern or
toggling details does not bring the duplicate row back. Other workspace headers,
layouts, saved detail choices, profile selections and operation owners remain.

## Previous change retained — 0.27.30-preview.1

Unified Game Tools 0.27.30-preview.1 keeps the pinned Game profiles header to
the short page name and existing navigation. Activation/startup explanations
and the runtime-only scope note are in the profile page's scrollable content
card. They wrap with the available content width rather than enlarging the
pinned area. The duplicate Modern Show details button is hidden on this page;
the saved global detail preference remains available on other pages.
The page's width-wrapping handler now adds to the existing scroll-region handler,
so resizing no longer replaces the callback that makes the content scroll.

The route ID, search terms, profile selection, startup choices and all operation
callbacks remain with their existing owners. This changes presentation only;
it does not activate profiles, remap input or publish an Overlay.

The scoped package is composed over the installed source. Only its declared
presentation modules, Hub version, tests and this documentation replace payloads.
Open and Install/Update remain separate, with the existing stable APP LAUNCHER.
