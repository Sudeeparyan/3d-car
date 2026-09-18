# Generic digital slicing preflight

PrusaSlicer 2.9.6 completed CLI slicing of the body, one wheel, and the detail coupon. This is a simulated generic FDM profile, not the college printer profile. Physical print samples and the technician's final layer review remain required.

Profile: 0.4 mm nozzle, 0.2 mm layers, 3 walls, 15% gyroid, automatic snug supports at 45 degrees, 0.2 mm support gap, 220 x 220 mm assumed bed. PLA density 1.24 g/cm3. Simulated speeds: 40 mm/s walls, 25 mm/s visible walls, 60 mm/s infill. Temperatures disabled. All unlisted settings are PrusaSlicer defaults. The INI and full embedded toolpath config preserve the setup.

| Part | Simulated time | Simulated PLA | Model layers | Support layers | CLI warning/error lines |
|---|---:|---:|---:|---:|---:|
| body | 7h 42m 34s | 94.46 g | 206 | 134 | 0 |
| wheel | 13m 45s | 2.37 g | 45 | 1 | 0 |
| coupon | 13m 40s | 2.08 g | 59 | 21 | 0 |

Each STL was read as manifold with one connected part by the slicer. Mesh dimensions are in the separate mesh_info files. The JSON report records source hashes and slice timestamps so later geometry edits cannot silently reuse stale results. All three parts have continuous model extrusion at every 0.2 mm model-layer height between their first and last extruded layers. Some additional heights contain support only because PrusaSlicer uses independently spaced support layers; these are not missing model layers.

Layer previews show selected actual toolpath layers. No missing-detail guarantee follows from a clean CLI result: very small relief, badge lettering, groove continuity, support accessibility, first-layer adhesion and surface quality still require visual review and physical samples. The wheel simulation generates a small support interface on its face features; inspect this in the college slicer and decide whether support blocking improves the test wheel.

Selected-layer visual review: the body has continuous underside and roof toolpaths with support around wheel arches, bumpers and mirror regions. The wheel has a flat first layer and visible split-spoke relief at 8.0-8.4 mm. The detail coupon includes its groove pattern and supported mirror-style arm. These selected views do not replace scrubbing all layers in the actual college slicer.

The simulated body footprint including support and skirt is 177.4 x 87.2 mm. Body plus four individual wheels is about 8 h 37 min and 104 g in this generic profile; the detail coupon adds about 14 min and 2 g. These estimates include the simulated supports and skirts.

The body plus four wheels is approximately the body estimate plus four individual wheel estimates; plate arrangement, acceleration, cooling, start/heating time, brim and machine profile can change actual duration and material. Do not rely on this simulation as a print appointment duration.

Toolpaths are deliberately named SIMULATION_DO_NOT_PRINT.gcode.txt. They have no calibrated printer profile or heating instructions. Do not include these text files in the printer handoff or rename them for printing.

To repeat after STL changes, run PowerShell: `powershell -NoProfile -ExecutionPolicy Bypass -File validation/generic_slicer/run_preflight.ps1` from the workspace. This re-slices the three representative files, checks source hashes did not change during the run, and regenerates this report and layer images.
