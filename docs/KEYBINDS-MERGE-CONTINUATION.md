# Continuation checkpoint — Unified Game Tools 0.25 Keybinds merge

## Current durable result

- Host: Unified Game Tools `0.25.0-preview.2` reviewed local source candidate.
- Keybind component: `0.2.0-preview.1` semantically rebased into the A 0.24 owner architecture.
- Canonical repository owner: `dodWhatUp/install-modes-for-games`.
- Publication: not performed. Git and Drive remain separate future effects.
- Installation/runtime: not performed. The preview uses its own `GameToolHub-Workbench-Preview-0.25.0-preview.2-Keybinds` profile.

## Safest next stages

1. Review the R2 source, focused-change summary and delivery receipt without modifying production.
2. On native Windows, verify the runtime preflight with a trusted Python 3.10+ + Tk interpreter, then confirm that the separate preview profile and shortcuts are created only after the preflight succeeds.
3. Extract the runnable preview and use `OPEN Game Tools.cmd`; verify startup, one Keybinds tab, game selection, Stop/close behavior and zero production-profile changes.
4. Run native known-folder, file-identity, ACL, interruption and rollback fixtures using synthetic files before any real game.
5. Certify one game at a time: identify the active configuration file, preserve its current bytes, bind the exact installation/profile, preview a minimal change, locally approve, read back and roll back.
6. Publish to Git only through a dedicated task branch after refreshing the canonical owner and active writers. Keep Git as the editable master and Drive as a derived delivery snapshot.

## Do not infer

The existence of a named research draft does not mean the game is supported. A successful preview launch does not prove installation, client connection, native file mutation or gameplay acceptance. Do not merge this candidate into `main`, upload it, install it or touch real game files without a separate authorized step and refreshed owner state.
