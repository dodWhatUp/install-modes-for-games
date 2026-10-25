# App launcher convention

User-requested standing delivery rule, 2026-10-25.

Every app we create or deliver includes a convenient double-click launcher in its
app folder or package. Its visible name ends with the exact uppercase suffix
**APP LAUNCHER**, before the operating system's file extension:

`<App Name> APP LAUNCHER`

For example: `Shadow of War Mods APP LAUNCHER.cmd` and the matching Desktop
shortcut `Shadow of War Mods APP LAUNCHER.lnk`.

- Include the launcher with the app, even when a Desktop shortcut also exists.
- Provide an in-app **Show APP LAUNCHER** action or an equivalent discoverable
  location. Existing open windows receive code changes on their next normal open.
- Opening an installed app should not require terminal commands, a reinstall,
  runtime selection or administrator rights. Setup remains a separate operation.
- Keep stable entry points, version pointers, settings and profiles across updates.
  Preserve useful old entry files as forwarding aliases when renaming the primary
  launcher; do not make users repair existing references.
- Verify the launcher's existence, target, arguments, working folder and included
  runtime bindings. Distinguish file verification from an observed GUI launch.
- On Windows, test the normal Desktop/Explorer launch as well as setup-time file
  checks. Packaged apps can see redirected app-data files. Bind the actual
  existing settings location privately when needed; do not create blank game
  settings or reset configuration to suppress a missing-file error.
- Apply this convention automatically to future scoped app creation, packaging
  and delivery work. Migrate existing authored apps when working on their delivery;
  this rule does not authorize bulk renaming unrelated third-party software.

## Current adoption

Shadow of War's graphical controls include the named launcher in the control-panel
package and the workspace root, a matching Desktop shortcut, and **Files & tools >
Show APP LAUNCHER**. The older `Manage Shadow of War Mods.cmd` forwards to the new
entry. Machine-specific runtime/workspace text bindings and recovery remain
private; the portable launcher source is in
[`examples/shadow-of-war-controls`](../examples/shadow-of-war-controls/README.md).

The entry opens the same controller. It does not apply a profile, launch the game
or install mods. Prior gameplay, Luma compatibility and controller acceptance
limits remain in the game's history. This convention does not claim that every
existing app has already been migrated or that all chats automatically loaded it.

## Durable owners

The canonical repository's `AGENTS.md`, `preferences/GENERAL.md` and this document
hold the standing rule. A matching instruction copy is maintained in the existing
private game-tools Drive export folder. Historical source/recovery archives remain
unchanged. Follow the current repository instruction rather than an old snapshot.
