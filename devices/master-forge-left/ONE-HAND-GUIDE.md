# Master Forge left — profile C reference

Profile C provides a complete standard keyboard and desktop mouse using the left half. The right mappings within C serve as a mirrored bank; the separate right device is unchanged.

| Mode | Control | Return |
|---|---|---|
| C2 numbers | Hold pinky west | Release to C1 |
| C3 desktop | Tap pinky north | Tap again to C1 |
| C4 function | Tap pinky east | Tap again to C1 |
| Mirror bank | Hold lower thumb west | Release |

C1 common letters: ring N/E/W D/L/H; middle N/E/W T/I/N; index N/E/S/W R/S/E/A; upper thumb N/E/S/W O/U/Space/C; lower thumb N/E/S G/M/V. Mirror finger letters: ring B/J/K; middle P/Q/W; index X/Y/Z/F. Ctrl is ring south, Shift middle south, Alt Aux1 south, Win Aux2 south.

C3 ordinary shortcuts: pinky south Ctrl plus Aux1 N/E/W = Undo/Redo/Select All. Win plus lower-thumb north = Explorer; Alt plus lower-thumb east = app switching; Win plus lower-thumb south = input language. In C3 Mirror, index N/E/S/W are Left/Right/Up/Down arrows; combine with Win for window positioning.

Copy, Paste and Screenshot always occupy Aux2 N/E/W and use pseudo actions 600/601/602. These native outputs hold modifiers with PRESS_NEXT, send the target scancode, release in reverse order with RELEASE_NEXT, then append KSC_00 to inhibit a trailing space.

To add a macro, export first, use a free pseudo action in the primary map, keep that trigger consistent across layer/bank variants, add its chord entry and explicitly release all pressed modifiers. The shared library is global across A/B/C; do not overwrite an existing entry. Keep gaming chording disabled.

CCOS 3.0.0 ZERO simulation demonstrated that chord lookup is based on the primary mapping. Assigning a pseudo action only in a secondary layer did not invoke its pseudo-key chord. The tested design keeps each macro trigger fixed. Direct and latched-layer macros passed; held-layer macro activation did not emit in this simulator. Do not advertise held-layer macros as verified on the physical M4G.

Momentary layers retain the same layer action at the same target location. The tested native toggle pattern assigns the target layer in C1 and Primary Layer at that location in the target. This is not a timed tap/hold dual-action key. Profile A/B/C actions persist until another profile action; no temporary profile hold is configured.

Use physical directions, not a downward press (which actuates all four directions). Start with a blank text field: D / hold Mirror then B / release then D, followed by C2 digit 1 and release, C3 mouse and C4 F1. Verify no stuck keys/buttons, reconnect persistence, then a game's training area.

Native B settings remain 16/16 ms debounce, 1000 Hz polling, 12-key rollover and layer warp off. No game executable or Windows settings were changed. Mouse speeds in C remain baseline 50/250. Adjust only after observing cursor behavior.

Sources: [Master Forge](https://docs.charachorder.com/Master%20Forge.html), [installed action metadata](https://charachorder.io/firmware/m4g_s3/3.0.0/actions.json), [installed recipes](https://charachorder.io/firmware/m4g_s3/3.0.0/recipes.json), [same-commit simulator metadata](https://charachorder.io/firmware/zero_wasm/3.0.0/meta.json). Older prose docs mention three layers; firmware metadata and live reads support four here.
