# Compact UI and structured content design

User preference confirmed 2026-10-11. Use this as a preferred foundation when creating or improving software interfaces, learning materials, presentations and explanation files whose internal structure should make understanding easier. Combine it with the existing product design system, accessibility guidance and format-specific instructions. Apply it to the requested work; a preference update does not migrate existing applications or native profiles.

## Compact application lessons — adopted 2026-10-26

The user preferred the compact Game Tools header and asked to reuse its ideas
in UI Preview and maintained standalone controllers. Treat this as a preferred
pattern for the user's future scoped app work, not proof of universal usability.
The [previous complete guidance](design-history/UI-AND-CONTENT-DESIGN-2026-10-25.md)
remains an archived alternative; its principles below are retained.

- Group by human intent. **View** answers “what is visible?”, **Layout** answers
  “how is it arranged or styled?”, and **Tools** answers “where can I go or what
  supporting tool can I open?”. Reuse existing variables and callbacks. A small
  app may need fewer groups; do not invent empty menus for visual uniformity.
- Budget pinned space. Keep global navigation and a short page name stable.
  Put route-specific explanations, scope text and optional guidance inside the
  relevant scrollable content card. A longer title or opened help must not
  crowd the working area out of a small window.
- Bound editable choice/search fields to a useful readable width. Extra screen
  width does not require one field to consume the whole row. Preserve full
  labels in choices or adjacent detail, the caret, open-list filtering, keyboard
  navigation, cancellation, stable IDs and explicit commitment. Ordinary text,
  paths, numbers and fixed choices retain controls appropriate to their purpose.
  The tested 28-character request is an example, not a universal size rule.
- Keep frequent navigation easy to reach and consequential actions clear.
  Put occasional helpers behind concise menus or named disclosures. Save,
  Apply, Install/Update and Publish retain their reviewed owners; opening or
  hiding UI must never perform those actions.
- Adapt by removing duplicate shortcuts before compressing useful content.
  At narrow widths, a sidebar shortcut can move into View while search and
  menu labels remain usable. Test long names, larger text, focus and the actual
  minimum window size; avoid tiny type or controls clipped beyond the window.
- Preserve reversibility. Keep an **Original toolbar** or equivalent existing
  layout where practical, save UI choices separately, and retain the prior
  source/guidance with date and hash. Switching presentation must preserve
  drafts, selections, native profiles and operational settings.
- Check behavior and appearance separately. Test menu open/cancel, visibility
  versus enablement, layout round trips, editable search and delayed controls.
  Record source/guest/native/human acceptance distinctly. A preferred design
  and passing fixtures do not establish gameplay or device acceptance.

## Shared foundation

Keep the common task and main explanation visible. Put optional controls, examples and technical depth behind clearly named disclosure controls. Reduce scattered fields, duplicate panels and wasted space while preserving readable labels, useful choices and enough context to understand them. Compactness means fewer unnecessary decisions and less navigation, not tiny text or hidden essential information.

Use a consistent small set of components and terms across pages. Put each control beside the value or content it affects. Preserve the user's choices; do not ask them to select this design preference again. Choose a different component where it improves comprehension or matches the task, and briefly record a material exception.

## Selection, search and entry in one control

Standing interaction rule, 2026-10-25: clicking anywhere in an editable search/dropdown field opens its choices while keeping the caret available. Typing/editing and the filtered list must work simultaneously. Retain keyboard selection, Escape/cancellation and explicit Add/Save. Apply this consistently across maintained authored apps; opening or typing never commits a value. Ordinary text-only and fixed-choice-only fields retain their appropriate behavior.

Prefer one editable searchable selector for a value that can be chosen from existing options or entered as text. The user can choose an option, type to filter/search, and explicitly add a valid new value when creation is supported. Avoid separate dropdown, search box and text field for that same value. At most one small adjacent Browse, Add or Details icon should normally be needed; give it an accessible name and discoverable text explanation.

- Keep selection, search and creation distinct. Typing, opening a list or cancelling must not silently save, create or replace a record. Mark an unsaved entry and make commitment/validation clear. Preserve the previous selection on cancellation.
- Store stable IDs separately from readable labels. Support long names, no results, duplicates, invalid input and disabled options with clear local feedback. Use existing keyboard and text-editing conventions; do not implement a custom widget when a supported native/library component fits.
- Prefer a short contextual editor when creation needs several fields. Do not squeeze a complex form into a selector. Use multi-select, a file picker, radio buttons, checkboxes, sliders or a table when the decision actually requires them.
- Keep essential labels visible. Icons, colour, placeholders and tooltips must not carry the only explanation. Preserve keyboard access, focus indication and adequate readable/clickable sizing.

## Visibility, toggles and menus

Start with a useful simple view. Offer one discoverable View / Show controls menu per page or section for optional panels and advanced controls, with saved visibility where appropriate and a Reset view action. Avoid a separate settings area for every minor display choice. Keep closely related actions in a compact contextual menu.

Use switches/checkboxes for independent states, radio buttons or a selector for mutually exclusive choices, and disclosure buttons for opening detail. Name toggles by their effect: Show advanced controls, Enable automatic selection or Show examples. Display visibility and feature enablement are separate states: hiding a control must not disable its feature. Keep active automation, manual overrides, errors and consequential status visible, and make hidden controls easy to reveal.

Persist view preferences separately from operational settings, profile assignments and source data. Scope them to the relevant user/page/document rather than treating one hidden panel as a global preference. Optional Expand all / Collapse all and Reset view should affect presentation without discarding edits or changing the underlying configuration.

## Learning materials, presentations and explanation files

Lead with the idea, outcome or learning goal, then organise the explanation in a logical sequence. Use meaningful headings and a compact contents/navigation area when length warrants it. Put definitions beside their first use, and use examples, comparisons and diagrams where they reduce the explanation burden.

For an interactive format, use named expandable sections for examples, derivations, sources and advanced depth. Add search/filter, a section selector or learning-depth control only when they improve navigation. Keep the main reasoning, required steps and qualifications needed to interpret a result visible. A collapsed section should say what it contains; learners should not have to open every section to find the next step. Include an easy way to reveal all content when useful for studying or export.

For static slides, Word, Markdown or PDF, adapt the same principle through hierarchy, short main sections, linked contents, bookmarks, examples and appendices. Use actual supported interaction when available; do not draw fake toggles or promise interactivity the delivered format cannot provide. Print/export should retain the necessary detail and reading order. A small explanation does not need an app-like shell or menu.

## Creation and review protocol

1. Identify the main task or learning goal, audience, delivery format and existing component/style conventions. Separate essential content from optional depth and presentation state from actions/data.
2. Reuse one selection/search/entry pattern and one visibility/disclosure pattern where they fit. Extend the existing host and component system before adding parallel controls. Keep related options in context.
3. Decide which choices persist, how the user reveals hidden content, resets the view and cancels an edit. Preserve existing settings and profiles through additive changes. Automatic context selection needs a reliable source, a visible selected state and a manual override.
4. When layout is uncertain, compare a small number of practical variants and choose one consistent approach. Check narrow layouts, long labels, text scaling, keyboard navigation and empty/error states in proportion to the change.
5. Use fast automated checks for implemented selector commitment/cancellation, visibility versus enablement, persisted state, reset and relevant export/navigation behaviour. Prefer observable component behaviour over tests that merely mirror code. For documents, use the applicable render/export checks. State which behaviour was tested and which usability or runtime claims remain unverified.

Include the relevant design decisions and exceptions in the implementation handoff or acceptance notes. This preference supplies a design foundation; it does not justify disabling working features, replacing source masters or reducing verification required by another protocol.

## Future research and deeper integration

Future improvement to consider: a deeper review of the user's real tasks, cognitive load, discoverability, accessibility and learning outcomes across the script application, educational artifacts and explanation files. Compare compact alternatives with realistic tasks, then integrate the supported findings into a shared component library, design tokens, content patterns and automated acceptance checks. This is a recorded follow-up idea, not completed research or a scheduled task, and ordinary requested work can use the foundation now.

## Ownership and reuse

This repository document is the maintained source for this preference. A local Codex skill may carry a byte-verified portable copy so other projects can use the foundation without this repository being present. Keep source date/revision or hash with that copy and reconcile later changes with this owner. Repository routing and local Codex instructions are explicit reuse mechanisms; they do not update unrelated chat services or prove that an already-running chat has reloaded its instructions.
