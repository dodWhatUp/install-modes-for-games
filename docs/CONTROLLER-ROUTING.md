# Controllers in Unified Game Tools

The **Controllers** workspace adds read-only discovery, deliberate held-input
identification, scoped preferences, controller keymap drafts and DOOM saved-binding
inspection to the existing application. Open it from **Controls → Controllers**
or Find. Existing Game profiles, Overlay Studio and native review owners remain.

## Common workflow

1. **Refresh devices**. Review physical, virtual and unknown endpoints. Device
   interfaces belonging to one physical controller are not independent gamepads.
2. **Identify held input**. Release controls first, then hold one button or stick
   during the bounded read. Mirrored slots, initial held input, short taps and
   ambiguous results must not silently select a physical device.
3. Choose the controller and scope, then **Save preference**. Scope precedence is
   game, group, genre, global. Equal-specificity conflicts remain ambiguous.
4. Preview the route. Save and automatic preference display change no Windows
   priority, native mapping, Steam Input setting, game file or published Overlay.
5. Link an existing reWASD setup when appropriate. **Review native controls**
   navigates to its existing exact reviewed Apply / Remap Off owner.

The saved preference is separate from effective game input. XInput indexes are
temporary observations, not persistent controller identities or proof of which
controller the game reads. Hardware identity and physical button positions can
remain unverified even when a sustained slot-level input is recognized.

## Native and Steam routes

Routes distinguish native controller input, a reWASD virtual output, and a
reWASD virtual output routed through per-game Steam Input. The successful
Shadow of War case is user-reported evidence for that game's combined route:

physical Vader → reWASD mappings/layers → virtual Xbox → Steam Input → game

That route differs from Steam directly opening the physical Flydigi. Preserve
per-game exceptions and prior settings. Do not generalize one successful route
into a global Steam Input change or exhaustive button/layer acceptance.

Normal reWASD layer changes do not recreate a controller in this workspace.
Native automatic config selection remains owned by reWASD Autodetect.

## Isolation and restoration boundaries

There is no general Windows device-disable, forced XInput-index write, blind
disconnect-all, or automatic native remap operation in this version. Unknown
physical/virtual relationships cannot justify disabling an endpoint. Keep the
physical/HID feeder needed by a selected virtual controller connected.

The existing reviewed **Remap Off** can stop remapping for its linked reWASD
device; it is not a hardware disconnect. The separate reviewed **Apply** restores
the exact saved config to its slot after hash checks. A timeout has an unknown
outcome and must not be retried automatically.

## Persistence and recovery

Controller preferences live separately in private
controller-routing/preferences.json. Explicit saves use revision checks,
exclusive locking, retained history, atomic replacement and readback. Discovery,
typing, list opening and cancellation do not save preferences. Local opaque
identity references stay in private machine data; public inventory summaries
remove identities, assignments and raw input state.

Changing the selected controller, route, scope or native setup clears inherited
acceptance in the UI. User-reported acceptance remains distinct from observed
device state and exhaustive gameplay verification.

See [controller keymap drafts](CONTROLLER-KEYMAP-DRAFTS.md) and
[DOOM binary inspection](DOOM-BINARY-BINDING-INSPECTION.md) for their narrower
capabilities. Neither publishes an Overlay or applies native/game bindings.
