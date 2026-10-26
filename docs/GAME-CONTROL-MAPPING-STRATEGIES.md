# Two ways to implement one game-control plan

Start with the game's actions and the user's logical layout. Research what each action does, its context and press/hold behavior, urgency, frequency, sequences and simultaneous inputs. Choose suitable physical positions using the accepted groups and access rules. Generate the device configuration, game-binding proposal and Overlay from that same versioned plan.

The selected method determines which owner changes. It does not replace the action-planning step.

| Method | Device profile | Game bindings |
|---|---|---|
| Adapt the device to the game | A dedicated game profile sends the game's current effective inputs from the planned action positions. | Retained wherever supported. |
| Adapt the game to the fixed device layout | The accepted letter/number outputs and layers remain fixed. | The game's actions are bound to those outputs through the existing reviewed owner. |

Prepare both alternatives when requested. Record which one is selected; do not silently make a DOOM-only choice the default for other games. Keep useful historical alternatives. Separate game profiles can use identical outputs when the current game bindings already match the chosen positions: isolation, naming and automatic selection are still useful, and unnecessary key changes add no value.

## Preserve the intended order

The user's later clarification adopts the
[`azeron-little-finger-20261026-r1` policy](../templates/GAME-CONTROL-ERGONOMICS.example.json)
for new and requested revised plans. On the enrolled Cyborg II, bottom-up little
rows 1–5 are #37, #1, #2, #3, #4: keep #37 empty unless explicitly requested,
WEAPONS on #1, infrequent actions on #2, MENUS on #3, and an optional useful
combat/overflow layer on #4. Keep TOOLS on #36. This finger-specific rule wins
over the general row order. It replaces the earlier little-finger layer default
without deleting historical alternatives or migrating unrelated games.

When a momentary layer is held, other buttons of its holding finger are
unavailable and may remain empty. Do not count them as missing action capacity.
Evaluate genuinely available empty BASIC positions through the
[quality review method](GAME-CONTROL-QUALITY-METHOD.md), including the effect of
moving an existing action to make room for a layer.

Physical button IDs, physical row numbers, emitted letters/numbers and action-access priorities are different records. A number painted on a button is not its priority score. A weapon-slot number is not a verified weapon name.

For the reported COMBAT R2 layout, physical rows count upward from the bottom; the user's preferred reach order is **2, 4, 3, 5, 1**. The accepted selection bank places **1–3 in physical row 4, 4–6 in row 3, and 7–9 in row 5**, increasing left to right on the ring, middle and index fingers. Alphabet traversal and protected movement/layer positions have their own documented order. Reconcile the actual enrolled baseline before adopting these rules elsewhere.

Use **A20-UF-1**, `P = 4 × (U − 1) + F`, for action access needs: 20 is highest. Keep unknown frequency and score ranges explicit. These are planning priorities, not measurements of physical comfort. Required holds, the layer-holding finger, movement ownership, bundled actions and input aliases can rule out a route regardless of its row preference. Preserve logical roles and groups across games where the actual actions fit; record exceptions instead of forcing unrelated actions into reserved roles.

## Pair the selected configuration and Overlay

Record the method, game/build, effective binding-source revision, device geometry, native/mapper profile family, logical-layout revision, action-plan revision and Overlay generation together. A switch must select a compatible device/game state and its matching Overlay. Never show labels from one alternative while the other alternative is active.

Read the user's **current effective bindings**, including overrides, rather than assuming factory defaults. The device-adaptation method may need no game write at all; the fixed-output method may need a supported game writer or a native-menu step. An unsupported action, combined binding or unavailable output stays an explicit limitation. An Overlay label is never an input remap.

Game/application association, native profile activation and Overlay routing require separate evidence. An executable match does not establish the internal game context. Preserve manual context selection where no verified provider exists, native momentary layers, Overlay hold/release behavior, appearance preferences and desktop/shared fallback.

Keep **Save draft**, **Apply Native Profile**, **Apply Game Bindings** and **Publish Overlay** as distinct operations with their existing review, backup, dependency and readback owners. Selecting a new method does not grant those operations automatically. Retain current-state and known-good recovery separately; do not restore an old whole profile over later unrelated settings without reconciliation.

## Make the action map readable

Prioritize the BASIC gameplay view, then affected layers and contexts. Show the correct game, layer/context, meaningful action name, key and appropriate semantic icon in the supported views. Keep text alongside icons; unknown slots receive neutral markers, not invented weapon art. Record display abbreviations while retaining full action text and explicit tap/hold notes. Render with the existing installed owner and effective appearance, check every view for clipping and verify glyph coverage and bounds.

## Adapt another device separately

Vader 5 Pro needs its own verified geometry, controls, analog behavior, native recovery and reWASD configuration. Keep reWASD as this user's primary mapper and preserve the existing Steam exclusions and input ownership. Reuse logical roles where practical; do not copy Azeron button IDs, native exports or shape. Verify the supported configuration and output path before claiming automatic selection or gameplay acceptance. See [device records](INPUT-DEVICE-REGISTRY.md).

## Evidence and planning records

Keep configuration readback, foreground activation, Overlay routing, visible prompts and physical gameplay acceptance separate. A preserved file hash or successful renderer test proves only its stated scope.

The [planning brief](../templates/GAME-CONTROL-PLANNING-BRIEF.example.json) is data-only guidance, not an app or native-profile import format. Retain the existing [per-game mapping record](../templates/GAME-KEYBINDS.example.json), workbook schemas and [reviewed workflow](GAME-CONTROLS-WORKFLOW.md) as their current owners. The brief adds explicit method selection and acceptance questions; it does not replace those contracts.
