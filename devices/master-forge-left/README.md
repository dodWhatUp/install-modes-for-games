# Master Forge — shared left-hand gaming base

For the current Hebrew operating guide, profile/layer transitions, Configurator action names, QMK-like capability notes and physical-test status, see [USAGE-GUIDE-HE.md](USAGE-GUIDE-HE.md).

Profile 2 is **B** in CharaChorder Device Manager. B1 is primary; B2 is active while the left pinky is held west/outward. V is on pinky south. This exception was explicitly selected for this device on 2026-09-20.

From typing profile A, chord left index, middle and ring **south together**, then release together: E+O+U enters B. Perform the initial check in a harmless text field. To return to A, hold pinky west and press Aux 1 east, then release. Selecting A/B/C at the top of the web manager selects an editor target, not the active physical typing profile.

| Left switch | North (away) | East (right) | South (toward body) | West (left) |
|---|---|---|---|---|
| Pinky | Tab | Alt | V | Hold B2 |
| Ring | 3 | 4 | Ctrl | G |
| Middle | 1 | 2 | Shift | Q |
| Index | E | R | Space | F |
| Aux 1, under ring | Esc | I | Enter | M |
| Aux 2, under middle | 5 | 6 | X | C |
| Upper thumb | W | D | S | A |
| Lower thumb | T | B | H | Z |

All listed letters/numbers use raw keyboard scancodes; Space uses the vendor-preferred space action. Game action labels in `MAPPING.json` are suggestions, not verified effective game bindings. Graphics function keys on B2 retain the meanings of already installed game-specific mappings; no graphics add-on was installed by this task.

Connect the left half's front-left USB-C data/power port to the PC and open [Device Manager](https://charachorder.io/config/layout/) in Chrome. Connect to `FORGE M4G S3`, select B, and select B1/B2 to inspect. `M4GR` denotes the separate right half. Export before editing and Apply only intended changes.

The keyboard was configured through its native Serial interface after the web connection proved unreliable. Configuration was committed and independently read back. Physical and gameplay validation remain distinct; see [history](HISTORY.md). Recovery exports, the uncommitted pre-existing browser draft, private recognition details and diagrams are stored in the user's private archive/Drive.

Do not treat a downward 3D press as an independent button: the Master Forge actuates all four directions together. Use the directional movements shown in the diagrams. No ongoing mapper or background helper is required for this native layout.

## One-handed keyboard and desktop profile C

C preserves the gaming base B and the original typing profile A. From B hold pinky west and tap index east, then release all controls. This enters C. The former duplicate F at B2/index-east is the only changed gaming assignment.

- C1: frequent letters, space and editing; lower thumb west holds Mirror to reach the other letters from the right map stored on the left device.
- C2: hold pinky west for numbers/symbols; release returns C1. Mirror adds the numeric keypad.
- C3: tap pinky north to latch mouse/Windows controls; tap again for C1. Upper thumb moves the pointer; index south/east/west gives left/right/middle click.
- C4: tap pinky east to latch F1–F12 and other full-keyboard functions; tap again for C1.
- Aux2 north/east/west always retains Copy/Paste/Screenshot. Activate these with held layer/mirror keys released.
- To leave C, first enter C3, hold Mirror and tap ring east for B or ring north for A; release all controls.

The final mapping covers standard 104-key keyboard functions, including both modifier sides, numpad, arrows, navigation, locks and punctuation. Character output follows Windows input language. Coverage is a mapping audit, not a claim of physical/play-tested comfort. See [C mapping](MAPPING-C.json) and [the expansion guide](ONE-HAND-GUIDE.md). The private Hebrew HTML guide provides searchable keys and 24 keys/actions/combined diagrams of the actual left-device geometry.

C uses three fixed native macros and ordinary held-modifier shortcuts. B chording stays disabled. C chording is enabled with minimum keys 1, autocorrect and arpeggiates off. Raw typing scan codes have no collision with the pre-existing 501-entry library.

## Physical-use note — 2026-09-24

The user reported that the A→B three-finger E+O+U entry chord is intermittent in real use. No mapping or setting was changed in response. Treat the cause as unknown until individual E/O/U directions and Chording press/release tolerance are tested. Adjacent-direction diagonal input on one physical switch also remains NOT_RUN; see the Hebrew usage guide.
