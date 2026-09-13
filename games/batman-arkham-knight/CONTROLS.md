# Batman neural-rendering controls

**Active, 2026-09-13:** Luma + ReShade + OptiScaler DLSS-NR. This replaces the disabled Feeder stack. See [latest history](HISTORY.md).

Current local build: wilsjo2 v0.7.7, `e237f89+f7-25-100`, with the existing compact-controls customization. Real engine DLAA inputs come from Batman Luma build 649.

| Key | Action |
|---|---|
| Delete | Full OptiScaler menu; live opening/closing verified at main menu |
| F12 | Compact NR menu; live opening/closing verified |
| F11 | Numeric NR preset 0 → 1 → 2 → 3 → 0; complete live cycle verified |
| F10 | NR on/off; both transitions verified |
| F8 | NR before/after SR; actual execution order verified in logs |
| F7 | NR model dimensions 25% ↔ 100%; both actual model sizes verified |
| F6 | Unavailable: no live engine-resolution adapter; compact panel reports this |
| F9 | Reserved; no NR action |
| Home | Separate ReShade/Luma host menu, configured; automated opening did not succeed |
| Page Up / Page Down | FPS overlay / information mode, configured; interactive cycling not verified |

Allow about one second between model changes. Percentages apply to each NR dimension; 25% uses one sixteenth of the NR pixels. At 3840×2160 output this means 960×540 NR. Game rendering/output remains native 3840×2160 DLAA. The slider remains available separately.

Saved default: NR enabled, 25%, preset 0, one pass after SR. Use **Save Settings** in OptiScaler to persist changes. ReShade preset saving does not save OptiScaler state. F11 numbers are model hints, not invented Quality/Performance labels. F7's inherited Stat StopFile binding remains removed through UserInput.ini.

**Readability update:** ReShade menu/editor font size 18 with 2× scale; OptiScaler font size 18 and menu scale 2×. Saved while the game was closed; next-launch visual verification remains pending. OptiScaler's **Apply NR to the finished picture** option requires native DX12 and should remain off in this Batman bridge. Its warning is separate from regular DLAA/NR support; exact attribution of the user's Home-menu warning remains unconfirmed.

Avoid testing Delete on the game's save-selection screen: the game also uses it for deleting saves. During host-only testing it opened a confirmation, which was cancelled with No; no save was deleted. Use the full graphics menu after entering the main menu or gameplay.

For the text-size change alone, close Batman/helpers and use `Restore-Menus.ps1` in private `menu-readability-20260913-221702`; its hash checks and dry run passed. The full-profile `staging/batman-repair/Restore-LumaTrial.ps1` must have its target library and ownership revalidated after the Steam move; its earlier successful dry run used the old location. Earlier F7/Full scripts belong to a different layout.
