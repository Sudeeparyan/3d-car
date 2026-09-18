# Four-color Mustang gift files

The outer geometry matches the validated 160 mm body and one fixed wheel. These
files contain real, closed color volumes for **white, black, red and dark grey**.

## Import checked in PrusaSlicer 2.9.6

The 3MF files include named-volume metadata tested with PrusaSlicer 2.9.6.
Other slicers may require the grouped STL fallback below. The technician must
assign filament manually; PrusaSlicer does not retain the standard display colors.

1. Open `body_color_parts.3mf` in PrusaSlicer. Keep it as one object with
   three material parts. It should measure **160 x 69.49 x 41.14 mm**.
2. Assign WHITE to white filament, BLACK to black, and RED to red.
3. Open `wheel_color_parts.3mf`. Keep the three wheel color parts grouped.
   Assign BLACK, DARK GREY and RED. One wheel is **23.30 x 23.30 x 9.00 mm**.
4. Print **four copies** of the grouped wheel, all visible faces upward.
5. Body orientation: upright, flat hidden underside on the bed. Wheel orientation:
   flat back on the bed, visible spoke face up. Configure supports and material
   changes using the actual college machine profile.

## If the slicer does not preserve 3MF material parts

Import all three `body_*.stl` files together as **one object with multiple parts**,
then assign each named part its filament. Do the same for the three `wheel_*.stl`
files. All body parts share one coordinate system; all wheel parts share another.
**Do not center, drop or arrange individual colors separately.** Only place the
whole grouped body or wheel on the bed. Some color volumes intentionally start
above z=0 and are supported by other colors below them.

## Appearance and scope

- White body; black windows, mirrors, rear spoiler, vents, grille, skirts, smoked
  headlamp regions and lower side stripes with three diagonal white breaks.
- Six red rear lamp bars; black tyres; dark grey wheel discs, rims and spokes;
  red caliper relief. All detail is simplified for this 160 mm birthday model.
- There is no separate silver filament. Dark grey is used for the wheel metal.
- Colors partition the existing solid; they do not add stickers or protrusions.
- Small badge strokes and caliper areas may be merged or omitted by a particular
  nozzle/profile. Inspect actual sliced layers, then test one wheel and the
  existing `print/06_detail_test_1to1.stl` before committing to the full body.

## Checked and still pending

The exported color solids pass closed-solid, positive-volume and consistent-face
checks. Pairwise overlap and combined shape reproduction are recorded in
`validation.json`. A real PrusaSlicer 2.9.6 import/export check retained one
grouped object with three named volumes for each 3MF, with dimensions and color
region positions preserved. See [the import audit](../validation/multicolor_import/README.md).
Other slicers have not been tested. Manual filament assignments remain required.
**The college printer model, filament assignments, actual sliced layers and a
physical sample remain to be checked. These packages contain no printer G-code.**

These color files are material regions for a multicolor print; do not print them
as separate loose pieces for gluing. Only the complete body and the four complete
wheels are the five physical gift pieces.

## Attribution

Body adapted from “Ford Mustang GT 2018” by SadPepe:
https://www.thingiverse.com/thing:3192801 — CC BY-NC 4.0,
https://creativecommons.org/licenses/by-nc/4.0/ . Changes include size, repair,
reinforcement, fixed-wheel attachment pads, hood, mirrors, spoiler and color
partitions. Wheel geometry was independently created. Original source records
are in `../reference_assets/`. Personal, non-commercial birthday gift use only.
