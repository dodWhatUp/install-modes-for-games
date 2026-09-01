# DOOM Experimental Files

These settings document the final failed/partial Vulkan test. They are not a working installer.

The process gate successfully isolated add-ons from `idTechLauncher.exe`, but loading renamed companion DLLs caused Feeder's adjacent-file check for `renodx-dlss5.addon64` to fail. NGX then returned `SuperSampling.Available=0`.

Use the current upstream Feeder layout and exact filenames before adapting the gate. Do not compile or deploy the gate as a first step.
