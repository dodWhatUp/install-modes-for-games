# General User Preferences

Last confirmed: 2026-09-14

Library catalog request, 2026-09-14: cover all actually installed games and compare manager/foundations, performance, QoL, configuration/UI, graphics/DLSS, animation/movement, enemy behaviour, unique abilities/perks, magic/tools, new mechanics and added playable content. Keep curated first-playthrough, later-play and replay combinations separate from the full catalog. Upload dated information/configuration exports to Google Drive with original download links. Skyrim's basic setup is explicitly authorized for installation; the other games are research-only for this request.

These are defaults, not permission to ignore a game-specific conflict or a newer explicit request. More specific preferences override general ones.

## Decision and safety preferences

- For this game-modding knowledge base, the default GitHub destination is `dodWhatUp/install-modes-for-games`. Confirm the authenticated GitHub identity before writing; never substitute another account or create a second similarly named repository.
- Show numbered options before a new modding path so the user can answer with the desired number. Include a warning beside any option likely to conflict, corrupt visuals, destabilize the game, or complicate rollback.
- Preserve a known-working state and take a just-in-time snapshot of files/settings likely to change.
- Prefer quick, reversible profile switching over reinstalling, where the files and tools permit it safely.
- Preserve stock files. Prefer side-by-side add-ons, installer manifests, and configuration deltas over blind replacement.
- Use offline/single-player paths for injectors and unsigned add-ons. Do not risk anti-cheat-protected play.
- Do not create reminders for paused experiments. Resume only when the user asks.

## Graphics and performance preferences

- Favor the best practical image quality while keeping enough VRAM and performance headroom for stability.
- User request, 2026-09-14: expose SR resolution, RR, FG/MFG/Dynamic MFG and NR in one OptiScaler or ReShade interface wherever the exact game supports it. Prefer extending the existing host over installing a second consumer. Native engine inputs/presentation can remain underneath that common interface.
- Use the latest compatible documented NVIDIA models, with SR explicitly pinned to **L rather than M**. Model hints 0–3 in NR are independent parameters, not ranked versions. Preserve the user's personal NR slots.
- SR render resolution and NR parameters should apply during gameplay without a game restart or save reload. Show actual input/output dimensions and distinguish a requested setting from a verified change. Model/resource recreation may still cause a brief hitch; record any game-specific unsupported control.
- User requested target-FPS dynamic DLSS SR on 2026-09-14. Use an engine-supported controller and evaluate base rendered FPS separately from MFG output. Cyberpunk's selected starting target is **30 rendered FPS**; expose the target and supported resolution bounds in F12. This is separate from the Dynamic MFG display-FPS target.
- Check for graphics DLL updates **once a month**, not at every launch. Cyberpunk's monthly maintenance is authorized while the game/store/compilers are closed, with verified provenance, a just-in-time snapshot and rollback. Preserve custom controls during host upgrades and stage incompatible updates rather than overwriting them. This is not permission to replace loaded DLLs or automatically launch games.
- Investigate missing NVIDIA features—newer DLSS models, Multi Frame Generation, Ray Reconstruction, and neural rendering—whenever a game has only part of the DLSS stack.
- Prefer the least problematic supported route: native game support or official NVIDIA override first, then a proven game integration, then OptiScaler/another bridge, and only then a synthetic-input experiment.
- Keep native DLSS components active when an add-on can safely add only the missing feature. Do not duplicate ownership of SR, RR, FG/MFG, or the swapchain.
- Consider performance/bug-fix mods by default unless they materially block graphics modding, overwrite the same settings, reduce desired quality, or introduce a larger compatibility risk. Explain that tradeoff.
- Re-research current graphics combinations after a meaningful game/tool update or when the last review is stale.


### RHI default management/orchestration layer — confirmed 2026-09-20

- For every future requested PC-game setup or graphics-modding installation, check **RHI** first and normally integrate it as the management/orchestration layer when the exact game/API/tool combination is supported. This is a workflow default, not permission to force an incompatible component.
- Use RHI, where supported, for game detection and launch plus install/update/uninstall/profile management of compatible graphics tooling: ReShade; RenoDX and Luma; ReShade shader/addon packs including Lilium HDR Shaders; OptiScaler; DLSS/DLSS-D/DLSS-G and Streamline versions/defaults; NVIDIA per-game overrides; and related managed components. Prefer one RHI-managed deployment over parallel manual copies when capability and version requirements are equivalent.
- RHI is an **orchestrator/manager**, not the renderer, temporal-input source, or neural consumer. Existing one-owner rules for SR/RR/FG/MFG/neural features, proxy/swapchain ownership, real-input verification, rollback, and game-specific compatibility remain authoritative.
- If RHI can only surface an external mod link (for example Ultra+) rather than install it, use RHI as the discovery/management entry point but treat the external mod as its own component with independent compatibility and rollback evidence.
- Preserve exact upstream component versions and links so a later RHI update or architecture migration does not blur which underlying implementation was actually selected.

### Special renderer / path-tracing overhaul discovery default — confirmed 2026-09-20

- When a game has a maintained game-specific mod that changes or improves the underlying ray-tracing/path-tracing renderer, sampling, denoising, lighting/radiance cache, or related rendering algorithms—not merely a post-process preset—surface that mod as an explicit graphics option during installation planning.
- Keep these renderer overhauls separate from ordinary ReShade presets, texture packs and color/HDR profiles. Compare them against stock/native RT/PT and the active DLSS/RR/FG/NR stack, and validate overlap before installation.
- Cyberpunk 2077's **Ultra+** is the current reference example: classify it as a path-tracing/rendering overhaul, not as an “Ultra preset.”

## DLSS extensions, real inputs, and minimum dependencies

User confirmed on 2026-09-14: when installing or extending DLSS, pursue as many useful, compatible features as the game and hardware can actually support, using real engine inputs and the fewest necessary components. The earlier preference for OptiScaler was motivated by its access to game inputs; it is not a requirement to use that product in every game.

- First establish the minimum working path for DLSS or access to the game's real buffers. Keep native features where they work. If inputs are inaccessible, investigate a supported game/engine integration, including Luma, RenoDX-based adapters, or other mods that actually expose them, before falling back to estimated inputs.
- Expand from that baseline: check SR/DLAA and newer models, RR, FG/MFG, neural rendering, and supported live/dynamic SR controls. For each feature, state what the previous stage already supplies and add only its missing prerequisites. Do not stop at a loaded interceptor or the first working feature.
- Prefer an existing component's supported capability over another program doing the same job. Compare OptiScaler forks, DLSS enablers/interceptors, RenoDX-derived consumers and game integrations by their exact capabilities, input provenance, quality, stability, overhead and controls. Product names alone do not establish compatibility.
- Minimize additional running processes, loaders, bridges, consumers and maintenance burden; count required runtime DLLs and preset files separately from background programs. Keep essential hosts, runtimes and helpers. Do not sacrifice real inputs, requested features or stability merely to reduce the component count.
- Treat each input independently: engine color, depth, motion vectors, jitter, exposure, UI data and ray data can have different origins. Record captured/converted engine data, reconstructed data, estimated data and unknowns; do not call a mixed or fallback path fully engine-native. A preset or renamed DLL cannot create a missing engine integration.
- When a feature cannot work, record the missing input/API/hardware requirement or conflict and the smallest plausible addition that could resolve it. Keep unsupported features off. Distinguish DLAA from actual lower-resolution SR, and driver/optical-flow FG from engine-integrated DLSS FG/MFG.

## ReShade and RenoDX as a separate visual stage

- Include ReShade plus a compatible game-specific RenoDX mod/profile in future requested graphics installations, especially when a maintained profile exists for that game. Check its required settings and SDR/HDR support; do not force a generic preset onto an unsupported game.
- Evaluate this visual stage separately from the DLSS/input stage, then validate both together. Reuse one compatible ReShade host and a documented load chain. Investigate compatible settings/load order instead of assuming RenoDX and a DLSS enabler cannot coexist.
- Distinguish a RenoDX HDR/color/shader mod from a RenoDX-derived neural consumer. Keep exactly one consumer per neural feature, one FG owner, and coordinated shader/tonemap/swapchain ownership. If Luma or another mod already handles the same visual work, resolve that overlap before combining them.
- Prefer the combined setup when it works well. If it conflicts, keep the working baseline and explain the exact limitation and closest supported alternative. Do not silently drop the requested visual stage, or claim that fewer components proves better image quality.
- These are defaults for future requested installations, not a bulk migration of installed games or a restart of paused experiments. Apply existing graphics hotkeys where supported. Use [Feature Decision](../docs/FEATURE-DECISION.md) to present the minimum baseline, useful extensions and separate visual stage without asking the user to repeat these preferences.

## Graphics add-on controls — all implementations

User confirmed on 2026-09-13, after the Batman F9 installation: make these controls the default whenever installing these graphics add-ons, regardless of which implementation is selected. Apply them as part of future requested installations without asking the user to select the same mapping again. Scope includes OptiScaler, RenoDX-derived neural add-ons, ReShade/Feeder chains, and equivalent implementations that expose the corresponding feature.

| Key | Default action |
|---|---|
| Delete | Open/close the active graphics add-on's full controls; retain Home for ReShade when it is a separate host |
| F12 | Open/close unified graphics controls: NR and supported native SR/RR/FG controls |
| F11 | Recall personal NR settings slots 0 → 1 → 2 → 3; Save Settings stores the selected slot |
| F10 | Enable/disable neural rendering |
| F8 | Unbound; user removed the placement shortcut |
| F7 | Toggle NR working dimensions between 25% and 100% only |
| F6 | Cycle supported live DLSS SR quality: DLAA → Quality → Balanced → Performance; expose beside NR controls where supported |
| Page Up | Unbound; user does not want the add-on FPS overlay shortcut |
| Page Down | Unbound; user does not want the add-on FPS information shortcut |

- Preserve these action meanings across tools. F7 affects only NR model dimensions; F6 changes the selected upscaler's real quality mode. Keep F9 available for game actions, including Cyberpunk Quick Load. Numeric model hints belong inside a personal settings slot and are not the slot itself. Do not invent quality labels for undocumented models.
- Latest feedback on 2026-09-13: the user confirmed that F11 should save and recall their own settings per number, removed F8/Page Up/Page Down, reaffirmed F7 25%/100% only, and prefers NVIDIA statistics. Implemented in Cyberpunk first; existing Requiem/Batman/Hogwarts installations were not migrated in this Cyberpunk repair.
- Prefer existing bindings/settings; otherwise use a compatible implementation or a validated adapter for the exact game/build. An INI alone cannot add missing code, engine inputs, a compact menu, or native SR modes. Cyberpunk's CET adapter remains game-specific.
- Bind one owner per action and resolve key collisions with the game and other overlays. If an action cannot be implemented for that stack, leave it unbound, record why, and report it clearly; do not silently assign a different effect.
- Prefer a visible value/mode notification, key-release handling, protection against rapid model recreation, and a documented way to save selections in the responsible component's settings/profile. OptiScaler uses **Save Settings**; ReShade preset saving does not automatically persist another add-on's configuration.
- Apply this default to new installations and requested control updates. Preserve existing game-specific forks, ownership, and known-good profiles; this preference update does not migrate every installed game or make one DLL universal. See [installation procedure](../docs/GRAPHICS-CONTROLS.md).
- Latest 2026-09-13 request supersedes both earlier F9 cycles (100/75/50/25% and 100/75/67/50%): F7 must toggle only 25% and 100%. This update was installed in Cyberpunk, Requiem and Batman. Older histories/patches keep their original evidence. F6 for separate live SR is the collision-avoiding implementation choice because F9 is Cyberpunk Quick Load; the user explicitly selected F7 for NR, not F6 for SR. See each game's verification boundary.

## Mod discovery preferences

For each game, maintain separate catalog sections for:

1. Frameworks, loaders, bug fixes, and performance.
2. Graphics, HDR, upscaling, ray tracing, and frame generation.
3. Quality of life, movement, traversal, and controls.
4. UI, menus, HUD, accessibility, and keybinds.
5. Gameplay changes and challenge/balance variants.
6. Large overhauls, added systems, expansion-scale content, and total conversions.
7. Cosmetic, audio, photo-mode, and other potentially interesting mods.

Keep the complete catalog separate from curated combinations. Curated recommendations should distinguish core/highly recommended, optional/interesting, experimental, and avoid; also separate first playthrough, after familiarity, and post-game.

## Evidence preferences

- Record failures as carefully as successes so later work does not repeat them.
- Use exact versions, hashes, effective resolution, process/API, relevant log evidence, performance/VRAM observations, confidence, and remaining unknowns.
- When a feature appears active, verify the actual input and output path. For temporal features, check motion vectors, depth, color/HDR contract, UI handling, frame evaluation, and recreation—not only the overlay.

## Azeron and per-game keybindings

User confirmed 2026-09-15: apply [Azeron and game controls](../docs/AZERON-GAME-CONTROLS.md) to every game when controls are in scope. Use one shared base setup with multiple layers; create separate game profiles only for exceptional needs. Retain and rename the current starting profiles to GENERAL 1, GENERAL 2, GENERAL 3, and EMPTY. Archive old game profiles in Google Drive before removal, preserving importable data and readable button/key/action references for future suggestions.

Check authoritative game defaults, effective saved bindings, user changes and relevant mod bindings. Prefer reversible edits and configuration checks without entering the game when supported; separately record whether gameplay behavior and visible prompts have actually been verified. Produce three consistent, clear Azeron-layout images per game/layer: keys, actions, and keys plus actions. Maintain a versioned source mapping so diagrams and configuration stay aligned. Store recovery data and images in Drive and reusable instructions/sanitized game records in the canonical GitHub repository. These are defaults for requested work, not a bulk migration of all games.

Reinstall default, confirmed 2026-09-15: when a game already has an archived keybinding setup, find it, compare current game/mod bindings, preserve current settings, and restore or adapt the game's own bindings alongside the shared Azeron setup. Save and restore a personal Steam Input layout when applicable, but keep game keybinding backups separately and verify Cloud coverage. Regenerate the three diagrams from the reconciled mapping and record configuration versus gameplay/prompt verification.

Layer-button default, clarified 2026-09-15: preserve a normal action on a short tap; use a brief long press for the secondary layer only while held, and return automatically on release without another press. Current selection: GENERAL 1 button #6 keeps V/melee on tap; a 150 ms hold enters GENERAL 2. Use Long Press layering with Toggle on hold enabled. With this combination the tap is recognized on release, so do not promise both immediate button-down output and exclusive tap-versus-hold behavior. Preserve this preference for future shared layouts and verify transitions with the user.

Device/software extension, confirmed 2026-09-15: apply every part of this game-control workflow to reWASD and other supported keyboards/keypads, including devices with an Azeron-like shape. Preserve a baseline the user has already configured. Enroll the device once using [device identification and physical mapping](../docs/INPUT-DEVICE-REGISTRY.md): save its identity privately, verify which physical position produces each input, and retain a versioned geometry and logical-base adaptation. On later requested tasks, inspect connected devices and reuse an unambiguous saved match so the user does not need to identify it again. Ask again only for missing, ambiguous or materially changed information; do not claim an always-on Codex listener.

For reWASD, record native exports, device/group and executable associations, Shift layers, activators/timing, input/output modes and restoration steps. Preserve the tap/long-hold/automatic-return preference using verified features rather than assuming Azeron's settings transfer directly. Reconcile the game's actual bindings and mod controls, restore them after reinstall, and generate keys-only, actions-only and combined images using the actual device shape and game-facing outputs. Keep one logical base across games/devices, with exceptions only when needed. Save recovery/enrollment data and diagrams in Drive and reusable instructions/sanitized records in GitHub. When user action is necessary, state the exact action, why it is needed, the expected result and what to report, then continue independent work where possible.
