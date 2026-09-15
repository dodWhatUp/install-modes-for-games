# Agent Rules for This Game-Modding Repository

This repository is the durable memory for game-modding work. Apply these rules whenever an agent works in this project or is asked to update this repository.

## Read before deciding

1. Read `preferences/GENERAL.md`.
2. Read `docs/OPERATING-STANDARD.md` and `docs/FEATURE-DECISION.md`.
3. Search `games/` for the exact game, executable, renderer, tool, feature, error, and DLL name.
4. Read that game's overview, `HISTORY.md`, `PREFERENCES.md`, `MOD-CATALOG.md`, and `RECOMMENDATIONS.md` when present.
5. Treat local logs and tested history as stronger evidence than a generic guide. Treat old results as historical, not automatically current.

## Before changing a game

- Identify the real rendering executable, bitness, API, store build, game build, GPU/driver, display mode, native DLSS/FSR/XeSS/HDR features, anti-cheat, mod loader, and all existing hooks.
- Refresh upstream information when the game/tool changed, an experimental-tool review is over 30 days old, a normal mod review is over 90 days old, or the user asks for the latest state.
- Unless the user already selected one exact action, present a short numbered option list. Each option must name its goal, stack, expected benefit, important conflicts, difficulty, confidence, and rollback. Mark the recommended option; do not silently choose a materially different path.
- Prefer official in-game or driver overrides when they expose the desired feature. Use a bridge only when the game supplies the required inputs, and use a feeder only when its supported API and input requirements are met.
- For DLSS installs/extensions, follow the 2026-09-14 defaults in `preferences/GENERAL.md`: establish the minimum path using real engine inputs, research a supported game-specific input adapter if necessary, then add the missing dependencies for each useful compatible feature. Reuse existing capabilities and minimize programs/hooks without discarding essential dependencies or desired features. OptiScaler is a candidate, not a mandatory product.
- Include ReShade and a compatible game-specific RenoDX visual profile as a separate stage of requested graphics installs, then validate the combined stack. Distinguish HDR/shader profiles from neural consumers, share supported hosts, resolve overlapping hooks/tonemapping, and record any reason the combined stage cannot be used.
- Make a just-in-time snapshot immediately before mutation. Preserve both the last known-good baseline and the current state if they differ. Record hashes, versions, settings, launch options, and external configuration—not just the game directory.

An explicit emergency rollback may skip the option menu, but it must still preserve a resumable current-state snapshot when safe.

## During installation and testing

- Change one layer, or one tightly related setting group, at a time.
- Apply the user-selected graphics hotkeys in `preferences/GENERAL.md` and `docs/GRAPHICS-CONTROLS.md` as part of every requested compatible graphics add-on installation, regardless of tool. Configure supported actions without asking for the same preference again; record unavailable actions and game-specific exceptions.
- Never allow two components to own the same proxy, swapchain, frame-generation path, or neural consumer unless the upstream projects explicitly support that chain.
- Prefer reversible profiles and validated switch scripts over repeated installation. Never switch loaded DLLs while the game, launcher, store client, helper, or shader compiler is running.
- If verification is in scope, test stock first, then each layer, then a repeatable gameplay scene. Check startup, menu transition, motion, UI, HDR, performance, resolution recreation, alt-tab, and clean shutdown in proportion to risk.
- A loaded overlay is not proof. Require component-specific creation, evaluation, delivery, presentation, and stability evidence.
- Stop an unstable test before risking saves, global configuration, or other games. Separate observation from inference and record uncertainty.

## After work

- Update the game history with what was attempted, what happened, why that conclusion is justified, the exact rollback, and a resumable next boundary.
- Promote a lesson to general documentation only when it is reusable. Keep game-specific exceptions in that game's folder.
- When asked to update or upload this repository, search the relevant game history and include newly discovered conflicts, failures, solutions, and preference changes automatically.
- For GitHub publishing in this game-modding context, use only the canonical repository `https://github.com/dodWhatUp/install-modes-for-games.git` and follow `docs/GITHUB-PUBLISHING.md`. Verify that the authenticated account is `dodWhatUp`. Do not create a duplicate repository, publish through another connected account, replace a different existing remote silently, or force-push.
- Keep catalogs separate from recommendations. Recommendations must be grouped for first playthrough, later play, and post-game/experimental use.
- Never commit proprietary game files, third-party binaries, archives, saves, private paths, credentials, full raw logs, or personal identifiers.
- Do not schedule reminders or resume a paused experiment unless the user explicitly asks.

Use the templates in `templates/` for new games and experiments.

## Azeron and controls defaults

For any game-control, keypad-profile, input-mod, keybinding or control-diagram task, read `docs/AZERON-GAME-CONTROLS.md` and use `templates/GAME-KEYBINDS.example.json`. Apply these defaults to every game: one shared layered base setup, archived old game profiles, verified sources and effective game/mod bindings, offline configuration edits where supported, and separate keys/actions/combined diagrams. Preserve recovery exports in Drive and sanitized instructions/history in the canonical GitHub repository. Distinguish configuration verification from observed gameplay prompts and behavior.

For a reinstall or renewed keybinding setup of a previously configured game, recovering and reconciling the game's own saved bindings is a default step. Include its personal Steam Input layout when applicable; do not assume Steam Cloud backs up its keybinding files. Follow the reinstall sequence in `docs/AZERON-GAME-CONTROLS.md`.
