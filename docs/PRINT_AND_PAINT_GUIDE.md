# Your white Mustang gift — print, paint and assemble

A small display model of your friend's car: **160 mm target length, one body and four fixed wheels**. The windows are closed surfaces, and the wheels are glued in place. The photos guide the colors and distinctive trim; this is a simplified miniature, not a measured replica.

**To reproduce the colors in your six photographs:** use **white** for the body, **black** for windows, tires, stripes and trim, **dark grey** for wheel faces, and **red** for brake and rear-light details. If the college printer supports the required multicolor job, the technician can import the separate color volumes in `multicolor/` as parts of each physical assembly, preserve their relative positions, and assign those four filaments in the actual slicer. **The printer's multicolor capability is unconfirmed. STL files contain no colors:** a filename or colored diagram does not assign a filament automatically.

**Painting fallback:** print the body in white PLA and wheels in black PLA, then paint the remaining black, dark-grey and red details. The colored views and OBJ materials also serve as a painting reference.

## Start here

Open [START HERE](../START_HERE.html) and the [color and assembly diagram](../previews/00_COLOR_AND_ASSEMBLY_DIAGRAM.png) for the model view and color placement.

1. Take the `multicolor` and `print` folders, this guide and the preview images to the college technician. Bring the original photos on your phone.
2. Ask the technician to select the actual printer and material profile, group and assign the color parts, confirm the scale, inspect the sliced layers, and print the small test pieces first.
3. Print the full model only after reviewing the test pieces. Paint or touch up as needed, then glue the wheels on.

**Current status:** the college printer's model, multicolor capability, nozzle, material, build area and slicer profile have not been confirmed. All six single-material STL files in `print/` passed the recorded digital geometry checks. The separate multicolor geometry checks also passed: each region is closed, the regions have no material overlap beyond numerical tolerance, and their union reproduces the complete part. These are digital checks; inspection in the actual college slicer and a successful physical sample are still required.

## Model details

Dimensions below come from the exported mesh manifest and geometry report, rounded to 0.01 mm. The exact measured body length is **160.000000 mm**. The checks recorded on 17 September 2026 passed for all six STL exports; see [the geometry report](../validation/GEOMETRY_REPORT.md).

| Item | Final value |
|---|---|
| Printable folder and file names | `print/01_body_160mm.stl`; `02_wheel_front_left.stl`; `03_wheel_front_right.stl`; `04_wheel_rear_left.stl`; `05_wheel_rear_right.stl` (all in `print/`) |
| Assembled length × width × height | **160.00 × 69.49 × 47.14 mm** |
| Body print dimensions | **160.00 × 69.49 × 41.14 mm** |
| One wheel print dimensions | **23.30 × 23.30 × 9.00 mm**; flat inner face down |
| Wheel attachment / orientation | Flat wheel backs glue onto **11.2 mm diameter body pads**. All four wheels are identical; turn the caliper relief toward the **rear bumper** (+X in the assembled model). |
| Exact-scale test files | `print/06_detail_test_1to1.stl` plus one copy of `print/02_wheel_front_left.stl` |
| Geometry validation results | **PASS for all six STLs:** closed, consistently oriented, one connected solid, positive volume, and a Z=0 print origin. This does not certify every thin feature, support layout or physical fit. |

The body STL is already placed on the print bed at Z=0. In the finished assembly, its flat underside is **6 mm above the ground**. The OBJ and Blender assembly show that position; do not apply their assembled body height as a print-bed offset.

## At the college: technician checklist

Say: “This is a 160 mm display model with four separately printed wheels and four colors: white, black, dark grey and red. Please import each set of color volumes as parts of one assembly, preserve their relative positions, assign the filaments, check scale and supports, and run samples first.”

### Multicolor import and color assignment

| Physical object | Grouped file | STL alternative: load all three together | Print quantity |
|---|---|---|---|
| Body | [body_color_parts.3mf](../multicolor/body_color_parts.3mf) | [body_white.stl](../multicolor/body_white.stl), [body_black.stl](../multicolor/body_black.stl), [body_red.stl](../multicolor/body_red.stl) | **1**, upright on flat underside |
| Wheel | [wheel_color_parts.3mf](../multicolor/wheel_color_parts.3mf) | [wheel_black.stl](../multicolor/wheel_black.stl), [wheel_dark_grey.stl](../multicolor/wheel_dark_grey.stl), [wheel_red.stl](../multicolor/wheel_red.stl) | **4**, visible faces up, flat inner faces down |

Choose either the grouped 3MF or its corresponding STL set, not both for the same physical object.

Read the [multicolor notes](../multicolor/README.md) and [color-volume validation record](../multicolor/validation.json). Color-volume checks and the six single-material STL checks are recorded separately.

1. First confirm whether the printer supports the proposed four-color job. If it does, select its established multi-material profile and compatible materials with the technician. Otherwise use the single-material STLs and painting instructions.
2. Import all color volumes for the **body together as one object with multiple parts**. Import a wheel's color volumes together as another object with multiple parts. The exact command varies by slicer.
3. Preserve the parts' shared coordinates. **Some color volumes intentionally do not touch the bed.** Do not place, arrange, center, scale or drop each color volume onto the bed separately: doing so can move windows, stripes or wheel details away from their intended positions.
4. Assign **white, black, dark grey and red** to the corresponding named volumes. Confirm assignments in the slicer's color preview; file names and OBJ materials are not a universal printer setup.
5. Arrange the **one complete body assembly upright** and the **four complete wheel assemblies with visible faces up** on the bed. Keep all physical parts at **100% scale**. Duplicate the complete wheel group to make four wheels.
6. Inspect layer previews for gaps, overlaps, missing fine color regions, and unexpected color changes. Let the technician configure purge/flush amounts, any wipe tower, and supports for the actual printer. Include these in bed-space, material and time estimates.
7. Print a multicolor wheel first to check the black, dark-grey and red regions; print the detail coupon to check small structural features. Confirm the body color boundaries in the layer preview before the full print.

A colored OBJ is useful for viewing, but importing it does not guarantee correct material assignments. Both grouped 3MFs passed an import/export check in **PrusaSlicer 2.9.6**: each remained one object with three named color volumes, correct overall dimensions and relative positions, with no recorded repairs. **PrusaSlicer did not retain the standard display colors**, so manually assign and verify each named white, black, dark-grey and red region. Other slicers are untested; confirm grouping and shared positions or use the grouped STL alternative. Read the [3MF import audit](../validation/multicolor_import/README.md). This verifies file import, not a college-printer profile or a physical print.

- [ ] Record printer model, nozzle size, material, filament colors and slicer/profile: ____________________
- [ ] Import the body in **millimetres** and check its bounding dimensions against the table above. STL does not reliably carry a unit convention. Do not auto-fit the model to the bed.
- [ ] Keep the same scale for the body, wheels and test pieces. Do not resize individual parts to make them fit.
- [ ] Confirm the body fits the build area **with supports and any brim**. The assembled car dimensions are not a print-bed footprint.
- [ ] Place the body upright on its flat hidden underside. Place each wheel with its flat inner/glue face down and its visible outer face up.
- [ ] Inspect supports beneath bumpers, mirrors and wheel arches. Make sure support material can be removed without breaking details. Do not leave supports sealed inside a cavity.
- [ ] Check the layer preview for missing thin features, floating sections, gaps and unwanted filled wheel openings.
- [ ] Review estimated print time and material, leaving time for one correction or reprint.
- [ ] Print the **full-size wheel and detail sample**. Check mirror strength, groove visibility and support removal. After printing the body, dry-fit the wheel against its actual mounting pad before gluing; the separate coupon cannot establish the complete assembled fit.
- [ ] If the sample is acceptable, print the body and four wheels. If a feature fails, correct the model or settings before the full run.

**Provisional FDM starting settings:** PLA, 0.4 mm nozzle, 0.16–0.20 mm layers, three walls and 15% infill. Use the college's established PLA profile for temperatures, speeds, cooling and adhesion. The technician chooses support settings after examining the model. These are starting points, not a tested machine profile.

**If the printer uses resin:** the technician must choose resin-specific orientation, supports and any necessary hollowing/drainage, then handle washing and curing. Do not use the FDM settings above.

The **slicer** turns a 3D mesh into instructions for a selected machine. The `print/` STL files describe complete single-material parts; do not print those on top of the equivalent multicolor assembly. OBJ/MTL and the Blender file are for viewing or editing the complete model; they are not printer instructions. No machine-ready G-code is supplied for the college printer. Any generic simulation output retained in the workspace is for analysis only and must not be sent to the printer.

## Paint it to match the photographs

For multicolor printing, use the preview and table below to check the filament assignments. Painting is optional for touch-ups and tiny details, or a fallback if the multicolor workflow cannot be completed. Compare the preview with the real photos; prioritize the overall white-and-black appearance.

| Color | Where it goes |
|---|---|
| White | Body, hood, roof and main bumpers; leave white PLA visible where its finish is acceptable |
| Black / dark charcoal | Closed windows, mirrors, grille, lower splitter, spoiler and lower side stripes |
| Dark grey | Wheel spokes and hubs; keep tires black. Metallic paint is optional. |
| Red | Brake-caliper detail if visible, and the three rear-light bars on each side |
| Silver / pale grey — optional paint only | Small badges and front-light details, where practical. This is **not a fifth filament requirement**; the multicolor model uses white, black, dark grey and red. |

Paint checklist:

- [ ] Carefully remove supports; trim and lightly sand rough spots without rounding off the details.
- [ ] Dry-fit every wheel before painting. Confirm contact with its round mounting pad and ground contact.
- [ ] Keep wheel glue faces and body attachment faces clean and **unpainted**.
- [ ] Use fine masking tape for the lower black side stripe. Copy the diagonal breaks near the front wheels from the photos.
- [ ] Apply thin coats with a small brush. Use plastic-compatible model paint; follow its preparation and drying instructions.
- [ ] Paint wheels separately, including red brake detail where modeled. Let the paint dry fully before assembly.

## Assemble and give the gift

Dry-fit all four wheels on a flat surface first. Temporarily support the body's flat underside **6 mm above the table** using equal-height spacers. Center each flat wheel back on its **11.2 mm round mounting pad**, with the caliper relief pointing toward the rear bumper. All four tires should touch the table. The labeled wheel files contain identical geometry, so any wheel can occupy any corner.

Use a small amount of plastic-compatible adhesive on the unpainted contact faces and follow the adhesive's curing instructions. Keep glue away from the visible wheel faces. Leave the body supported and level while the joints set; remove the temporary spacers when the adhesive has cured. Confirm all four tires touch the same flat surface.

The wheels are fixed: do not try to rotate them after gluing. Allow paint and adhesive to finish drying before wrapping. A small box with soft padding protects the mirrors and spoiler.

**Time budget:** confirm the printer and run samples first; reserve the next printing window for the main parts; keep the final day for cleanup, paint and assembly. The three-day goal depends on machine availability, actual slicer time and the test print. If time is tight, omit tiny painted details before compromising assembly or drying time.

**Planning estimate for the single-material option only:** the generic simulation estimated about **8 hours 37 minutes and 104 g** for one body and four wheels, plus about **14 minutes and 2 g** for the detail coupon. These include simulated supports and skirts, using a generic 0.4 mm nozzle and 0.20 mm layer profile. **Multicolor time and material are unknown.** The college slicer must include color changes, purge waste, supports and the machine's actual speeds. Read the [generic simulation notes](../validation/generic_slicer/README.md).

## Files, source and checks

- **STL parts:** print the body once and the four labeled wheels once each, using the final file list above.
- **Multicolor volumes:** use these as an alternative to the equivalent single-material STL parts. Import and assign colors as described above; retain each assembly's relative placement.
- **Sample STL files:** print at the same scale as the final parts.
- **Assembled OBJ + MTL:** view the finished arrangement and colors; keep the files together.
- **Blender project:** editable model for adjustments.
- **Previews:** visual guidance, not evidence that the mesh has passed print checks.
- **Validation report:** measured dimensions and mesh checks. Slicer and physical-print status must be recorded separately.

The body is adapted from **Ford Mustang GT 2018 by SadPepe**, [Thingiverse 3192801](https://www.thingiverse.com/thing:3192801), licensed under [Creative Commons Attribution–NonCommercial 4.0 (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/). It is resized for a 160 mm personal display model, with prepared print geometry, reinforced mirror connections, wheel mounting pads and custom visual details. The wheels in this package are newly generated; **no original source-wheel geometry is used**.

The preserved original README credits its original wheels to **stunner2211's ACR Viper**. The source wheel files are retained only as workspace references; they are not included among this package's final printable wheels. Preserve the source notes, README and license with shared files. This package is for a personal, noncommercial gift; the source creator's endorsement is not implied.

Read [the handoff attribution](ATTRIBUTION.md), which includes the exact original license notice. Reference and license files are retained in `reference_assets/thingiverse_3192801/`. The HTML version of this guide includes a **20 mm scale square**: print that page at 100% / actual size and measure the square with a ruler. It checks paper scaling only; confirm the STL dimensions separately in the slicer.
