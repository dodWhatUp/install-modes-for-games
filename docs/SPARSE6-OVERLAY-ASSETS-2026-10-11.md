# SPARSE6 overlay asset and registration checkpoint

Completed locally on 2026-10-11 after the app builder's handoff. This is a display-only asset/host checkpoint. It does not change native outputs, game/mod bindings or the separately owned PoE2 COMBAT/MENU work.

## Current result

- Generated and registered 90 PNG assets: Keys, Actions and Combined views for all six installed SPARSE6 banks. Every view retains the same 29 source positions, including #36/#37/#38/#41, the exact blank masks, hidden/unassigned #19 and the omitted stick drawing. The stick configuration is unchanged.
- Five additive groups cover the shared map, Cyberpunk 2077, PoE2 and Bayonetta PC. Bayonetta has gameplay/menu contexts and compact/large groups with a saved cycle order.
- Three associations use existing exact gameplay executable paths for Cyberpunk, Bayonetta and PoE2, excluding launchers. The private manifest binds each asset to its actual installed profile ID/hash, keymap revision, bank, context and view. Candidate UUIDs are not used as installed references.
- Hub 0.11.0 is staged in a new versioned local folder and its actual GUI is running. Automatic foreground selection and the Hub display owner are enabled. Existing Studio 2.0.0-beta, its picture/shortcut owners and native profiles were preserved. No startup service or game launch is added.

The original app archive SHA-256 is `9b385a7daf66943a60d702fadb55f84ac2c55720d0afc8c3b3979641cfe8f356`; its source manifest is `8fd91af7aa47cead038295b52d3186e5a2f50866168b7d9c0ae3be07ed53c973`. These identify the builder's private source preview, not a public app release or Git HEAD. The fresh installed asset contract matched the handed-off contract byte-for-byte (`cc6a906501d29b29954991274c88a0991db624114e9db298054f263b0be870b1`).

## Evidence and limitations

| Area | Current evidence |
|---|---|
| Images/import | All 90 managed images decoded, pixel dimensions checked and content hashes read back; additive import through the supported CLI |
| Selection | 72 fixture checks across the game/bank/context/view combinations choose the expected actual managed image |
| Fallback | Five fixture cases cover an unrelated application, launcher, stale foreground, app-owned window and game exit; each hides the map |
| Manual control | Manual group override and Return to Auto fixture checks pass; Bayonetta's two groups retain compatible contexts/views |
| Actual Windows rendering | One registered PNG was presented in a visible passive window with NOACTIVATE/click-through styles and unchanged foreground, then the temporary renderer was closed |
| Actual host | Hub 0.11.0 process and visible window title verified; this is not foreground-game acceptance |
| Preservation | All 29 native profile files and 73 protected source/settings/overlay files remain byte-identical, including after host launch |

Native layer/profile telemetry is unavailable. **BASIC is explicitly Selected**, not Observed. The foreground game can select its group automatically while Hub runs; physical bank changes still require explicit display-layer selection. Unknown or unsupported observations must remain visible rather than inferring a layer from common keyboard events.

Bayonetta action labels are publisher defaults, separately scoped to gameplay and menus; personal settings and gameplay are unverified. Cyberpunk labels are saved/recorded configuration candidates with runtime context/overrides unverified, marked `CFG?`. PoE2 actions remain Unknown because input-bank selection and modifier decoding are unresolved. This checkpoint does not adopt the older R5 label summary as current SPARSE6 effective gameplay evidence. Full source labels and any compact-text truncation are retained in the private asset index.

The user previously reported all five native selector hold/release-return checks passing. Other physical outputs, held-transition/key-up behaviour, comfort, gameplay prompts and actual in-game overlay selection remain untested here. No game, benchmark, recording, graphics change, extended input experiment or MFG/FrameWarp work was resumed.

An initial test expected image dimensions as a tuple; the supported API returns width/height/format metadata. The check was corrected to use explicit metadata plus independent Pillow pixel decoding. The successful registry import was not repeated and the validator was not weakened.

## Ownership, recovery and next boundary

Private source/assets, exact executable associations, installed profile references, operation receipts and scoped backups remain in the owner's local asset revision. Retain the existing native recovery separately. Public documentation excludes personal paths, raw exports and private images.

To stop the new automatic display, use the supported `display` operation with `enabled:false`, `display:false`, `display_target:hub` and the freshly read store hash, or the corresponding Hub controls. Closing Hub stops its polling/display route. Preserve later imports and selections; do not restore the whole native profile store or overwrite Studio settings to undo this display addition. The source preview can be reopened from its versioned folder. Backup bytes and source identity are not a restore test.

The next boundary is separately scoped foreground-game acceptance and, if a reliable supported source becomes available, a native layer adapter. Keep PoE2 COMBAT/MENU and any future binding changes with their existing owner. A later Studio hold-trigger integration needs its own supported source upgrade and session route activation; the original picture trigger was not repurposed in this checkpoint.
