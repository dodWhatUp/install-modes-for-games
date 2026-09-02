# DOOM: The Dark Ages — Options for a Future Explicit Resume

Do not present these as a reminder. Refresh upstream versions and compatibility when the user independently asks to continue.

| # | Goal and stack | Expected benefit | Main conflict/risk | Difficulty | Confidence |
|---|---|---|---|---|---|
| 1 | **Recommended:** keep stock native HDR + native DLSS/RR/FG | Best stability and full native engine inputs | No community neural pass | 1 | High |
| 2 | Rebuild the pinned RenoDX v4.55 + Feeder 0.8 beta boundary at exclusive 2560×1440 | Returns to the only locally proven feature-18 path | Estimated motion vectors, processed HUD, extra VRAM, experimental Vulkan transport | 4 | Medium for operation; Low for final visual quality |
| 3 | Research and test a current game-specific RenoDX HDR/profile path without Feeder neural rendering | Potential HDR/tonemap improvement with less neural memory cost | Profile may not exist or may conflict with native HDR/ReShade Vulkan behavior | 3–4 | Low until refreshed |
| 4 | Re-evaluate current OptiScaler/bridge support while keeping Feeder absent | Could use richer native temporal inputs if Vulkan support is now real | Earlier path was inconclusive; proxy/API and FG ownership conflicts | 4 | Low |
| 5 | Develop/validate a game-specific adapter that captures native Vulkan inputs | Best theoretical input quality and control | Requires code, Vulkan/Streamline analysis, and extensive testing | 5 | Low |

For any experimental choice: take a new stock baseline first; install one layer at a time; keep the output at 2560×1440 initially; verify HDR, native SR/RR/FG ownership, moving-scene vectors, VRAM, recreation, and shutdown; preserve a one-command stock rollback.
