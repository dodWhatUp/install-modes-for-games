# Master Forge — shared left-hand gaming base

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
