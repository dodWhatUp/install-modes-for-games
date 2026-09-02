# Hogwarts Legacy — History

## Current documented baseline

- Local build observed: `1.0.1569535`; RTX 5070 Ti, driver 616.56; 3840×2160 borderless.
- Real executable: `Phoenix\Binaries\Win64\HogwartsLegacy.exe`.
- Working separation: native game DLSS Balanced and native Streamline FG/MFG remained the frame-generation owner; OptiScaler loaded beside the real executable with its own FG disabled and experimental neural rendering enabled.
- Ultra Plus was installed separately and launch-tested.
- Positive evidence: correct executable/API/GPU detection, OptiPatcher game patch, stock NVIDIA component discovery, and more than 10,000 processed Streamline frames before cleanup.

## Failed/ambiguous paths

- Forced OptiScaler Dynamic MFG around native game FG produced inconsistent startup/overlay behavior. It was removed from the stable profile.
- Forced numeric SR/RR presets were build-specific and had no proven image-quality benefit.
- Changing Ultra Plus, Engine.ini dynamic resolution, model overrides, forced MFG, and neural rendering together made early crashes impossible to attribute.

## Reusable lessons

- Install beside the real rendering executable, not the launcher.
- Let exactly one component own FG/MFG.
- Keep native feature controls and experimental neural processing as separate test dimensions.
- Ultra Plus and alternative performance/Engine.ini packages can edit the same systems; treat them as alternatives unless their authors document compatibility.
