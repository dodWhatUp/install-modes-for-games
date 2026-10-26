# Passive controller inventory

`GameToolControllerInventory.Inventory` adds read-only evidence to the existing Game Tools controller/profile owners. It does not apply a native config, disable or reconnect a device, inject input, create a virtual device, send vibration, change Steam Input or install a driver.

## Integration

- `Inventory().snapshot(include_state=False)` reads bounded present Windows PnP metadata, four XInput capability slots and the saved reWASD collection/current-user assignments. Run the Windows query on the UI's existing worker path; it has a 15-second timeout and bounded output/device counts. The default never calls XInputGetState.
- `Inventory().sample_hold(duration=3)` is an explicitly started, bounded passive identification window. It requires a neutral baseline followed by a sustained button, trigger or stick input. Initial held controls, short taps and stick drift do not identify a route. Cancellation, time/count budgets and connection changes terminate or invalidate acceptance.
- `export_summary(snapshot)` omits local identifiers, native assignment references and sampled input state. UI rows should use labels, not local identifiers or raw source metadata.

The module obtains the fixed Windows system directory and invokes only its fixed PowerShell read query. No supplied profile, path, label or device string becomes a shell fragment. XInput loads only the system DLL and obtains GetCapabilities/GetState; it has no output function.

## Evidence limits

PnP type classification is **inferred**, including physical USB enumeration: virtual USB emulation can resemble a physical device. A device named Xbox 360 is not automatically virtual. VID/PID equality is not sufficient to group devices or identify an individual controller.

Relationships are emitted only for actual current PnP parent/container metadata or exact equality with a saved reWASD ContainerId. Their `observed` status describes the stated metadata observation, not an observed physical press or successful game route. Saved reWASD rows have `present: null`, and saved remap/slot assignments explicitly do not establish live remapping, hiding, native output or gameplay acceptance. Unmatched records remain separate; no virtual endpoint is guessed from the physical device's name.

An XInput index is a session slot, not a stable physical identifier. Even one sustained candidate leaves `selected_device_id` unset and `physical_identity_verified` false. Multiple/mirrored slots are ambiguous and never selected automatically. Physical source identification needs a verified native relation or a further deliberate user/device check. See Microsoft's [GetState](https://learn.microsoft.com/en-us/windows/win32/api/xinput/nf-xinput-xinputgetstate) and [GetCapabilities](https://learn.microsoft.com/en-us/windows/win32/api/xinput/nf-xinput-xinputgetcapabilities) contracts.

## Private identity and preference scope

Deterministic local hashes of native instance/container/source identities let private preferences refer to unchanged devices across refreshes and restarts. Keep those IDs in private machine data only; they are not public fingerprints or hardware attestation. Public export strips them. Device re-enumeration, a port/mode change or native identity changes can require reconciliation rather than silently migrating an accepted route.

Keep requested preferences separate from observed acceptance. Game, genre, global and explicit device-group preferences must report ambiguity rather than picking the first matching rule. A native layer/config revision, changed source identity or changed group membership invalidates the corresponding observed acceptance. A new downstream per-game Steam Input override affects that game's route; it does not automatically change a shared physical/reWASD exclusion.

## Existing native owners and continuity

`GameToolRewasd.Native` remains the reviewed apply/off owner with exact config hash, native recovery and structured arguments. Game Tools profile selection and automatic display matching do not arm reWASD; native Autodetect retains its separate owner. See [saved profiles](GAME-PROFILES.md) and [device records](INPUT-DEVICE-REGISTRY.md).

Ordinary reWASD Shift-layer switching should be kept inside the chosen native configuration and output family, rather than implemented as disconnect/reconnect or repeated whole-profile application. Continuity of the actual virtual identity is a separate observation; no preference toggle proves it. The official [General preferences](https://www.help.rewasd.com/preferences/general.html) document an option to leave a virtual controller present after physical disconnection, but that is not a guarantee of unchanged identity after remap-off, output-type changes or re-enumeration. Group membership and output assignment have separate [native semantics](https://www.help.rewasd.com/how-to-remap/group-of-devices.html).

No scoped disconnect/reconnect backend is implemented by this adapter. Its capability fields stay false. User-facing controls must explain that limitation instead of reporting a successful hardware operation. Future native operations require their own supported backend, exact device/group scope, reversal plan, current-state checks and observed readback; they must preserve the user's ordinary keyboard, mouse and unrelated controllers.

## Validation

Disposable tests cover ABI sizes, repeatable private IDs, container/parent joins, no VID/PID guessing, inferred classification, current-user native assignment boundaries, default state privacy, export redaction, source limits, neutral/sustained/release gates, initial-hold rejection, mirrored ambiguity, drift/tap rejection, disconnect invalidation, cancellation and stalled-clock budgets. These tests do not establish physical device identification or game acceptance. Physical DOOM input testing remains deferred by the user.
