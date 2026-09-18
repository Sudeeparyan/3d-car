# White Mustang birthday model

A **160 mm long display model** inspired by the six photographs: white body, black windows and trim, dark wheels, and red brake and rear-light details. The finished gift has one body and four glued, fixed wheels.

**Open [START HERE](START_HERE.html)** for the finished model and file links. See the [color and assembly diagram](previews/00_COLOR_AND_ASSEMBLY_DIAGRAM.png) and [print and finishing guide](docs/PRINT_AND_PAINT_GUIDE.html) before taking the files to college. A [plain-text guide](docs/PRINT_AND_PAINT_GUIDE.md) is also available.

## Take these to the college

- `multicolor/` — separate color volumes for a compatible multicolor printer. Keep each assembly's parts in their shared positions and assign white, black, dark grey and red in the actual slicer. Consult the folder's file list and validation notes.
- `print/` — one body STL, four labeled wheel STLs and a small detail sample. These are the single-material option; paint the details after printing. The four labeled wheels have identical geometry.
- `previews/` — appearance and color references. Bring your original six photos too.
- `docs/` — the guide and attribution.
- `validation/GEOMETRY_REPORT.md` — digital checks of the six single-material STL exports.

STLs contain geometry only. A colored preview or OBJ does not make a printer reproduce those colors automatically. The college printer's model and multicolor capability are still unknown. The technician must select its actual profile, check the layer preview and print samples before the full body. **No successful physical print or machine-ready college G-code is claimed.**

## Which multicolor files go together

| Physical object | Grouped file | Alternative: import these STLs together as parts | Copies and orientation |
|---|---|---|---|
| Body | [body_color_parts.3mf](multicolor/body_color_parts.3mf) | [body_white.stl](multicolor/body_white.stl), [body_black.stl](multicolor/body_black.stl), [body_red.stl](multicolor/body_red.stl) | **One** body, upright on its flat underside |
| Wheel | [wheel_color_parts.3mf](multicolor/wheel_color_parts.3mf) | [wheel_black.stl](multicolor/wheel_black.stl), [wheel_dark_grey.stl](multicolor/wheel_dark_grey.stl), [wheel_red.stl](multicolor/wheel_red.stl) | **Four** complete wheels, visible face up and flat inner face down |

Use either a grouped 3MF or the corresponding STL set. Import each STL set as **parts of one physical object**. Keep shared positions: some color volumes intentionally do not touch the bed. Never arrange, center or drop those individual volumes onto the bed. Silver is optional detail paint, not a fifth filament requirement.

Both grouped 3MFs passed an import/export check in **PrusaSlicer 2.9.6**: one grouped object with three named color volumes, preserved dimensions and relative positions, and no recorded repairs. **PrusaSlicer did not retain the standard display colors**, so assign filaments manually to the named regions and verify them in the color preview. Other slicers are untested; confirm the same grouping and positions, or use the grouped STL alternative. See the [3MF import audit](validation/multicolor_import/README.md).

Read the [multicolor notes](multicolor/README.md) and [color-volume validation record](multicolor/validation.json). The color-volume geometry checks passed: the regions are closed, have no material overlap beyond numerical tolerance, and combine to reproduce each original complete part. These checks are separate from the six single-material STL checks and do not confirm filament assignments or a successful physical print.

For planning only, the generic single-material simulation estimated **about 8 hours 37 minutes and 104 g** for the body and four wheels. The detail coupon adds about 14 minutes and 2 g. **Multicolor time and material are unknown**; the actual slicer must estimate color changes, purge waste and supports. See the [generic simulation notes](validation/generic_slicer/README.md).

## View or edit the model

- [Editable Blender project](model/Mustang_160mm_editable.blend)
- [Assembled OBJ](model/Mustang_160mm_assembled.obj) — keep its MTL file with it for materials.

Measured body print size: **160.00 × 69.49 × 41.14 mm**. Assembled size: **160.00 × 69.49 × 47.14 mm**. One wheel: **23.30 × 23.30 × 9.00 mm**. Import millimetres at 100% scale; never auto-fit parts individually.

The single-material exports passed the recorded geometry checks on 17 September 2026. That report does not certify every fine feature or the separate color volumes. A physical wheel and detail sample, followed by a dry fit against the printed body's pads, remain part of the plan.

This is a simplified miniature derived from an existing Mustang model and customized using the photographs; it is not an exact 3D scan of the car.

## Attribution

Body adapted from **Ford Mustang GT 2018 by SadPepe**, [Thingiverse 3192801](https://www.thingiverse.com/thing:3192801), under **CC BY-NC 4.0**. Final wheels were independently generated; source-wheel geometry is not used. See [the attribution and original license notice](docs/ATTRIBUTION.md). Preserve those credits and the retained source license when sharing the model. Intended as a personal, noncommercial gift.
