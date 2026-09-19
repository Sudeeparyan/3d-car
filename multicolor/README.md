# Four-colour Mustang gift files

The outer geometry is exactly the validated 160 mm body and one fixed wheel from
`print/`. These files split each into real, closed colour volumes for **white,
black, red and dark grey** filament. The regions are the same ones that colour the
preview renders, so what you see in `previews/` is what the printer lays down.

## Import (checked in PrusaSlicer 2.9.6 on an earlier revision of the same files)

1. Open `body_color_parts.3mf`. Keep it as **one object with three material
   parts**. It should measure **160.00 x 69.73 x 40.59 mm**.
2. Assign WHITE to white filament, BLACK to black, RED to red.
3. Open `wheel_color_parts.3mf`. Keep the four wheel colour parts grouped and
   assign BLACK, DARK GREY, RED and WHITE (the tiny RTR cap logo). One wheel is
   **23.30 x 23.30 x 9.10 mm**.
4. Print **four copies** of the grouped wheel, spoke face up.
5. Body orientation: upright, flat hidden underside on the bed. Configure supports
   and the colour-change purge using the actual college machine profile.

## If the slicer does not preserve 3MF material parts

Import all three `body_*.stl` files together as **one object with multiple parts**,
then assign each named part its filament. Do the same for the four `wheel_*.stl`
files. All body parts share one coordinate system; all wheel parts share another.
**Do not centre, drop or arrange individual colours separately.** Only place the
whole grouped body or wheel on the bed. Some colour volumes intentionally start
above z=0 and are supported by other colours below them.

## What is in each colour

- **White body**: paint, hood, roof, the rear number plate and the three LED
  daytime-running slashes in each headlamp.
- **Black body**: windscreen, door / quarter glass and B-pillars, rear glass,
  mirrors, lip spoiler, shark-fin antenna, hood vents, recessed grille and lower
  intake, the running-pony grille badge (gloss black on the car; it still stands
  1.4 mm proud of the grille floor), smoked headlamps with their amber corner
  markers, bumper corner slots, rear panel and lamp surrounds, rear diffuser,
  splitter, skirts, the lower door stripe (four short hash marks then a solid band
  to the rear wheel), the "5.0" fender badges and the plate lettering (the plate is blank until the registration is set in scripts/geometry.py).
- **Red body**: the six tri-bar tail-light bars.
- **Wheel**: black tyre and centre cap, dark grey rim, seven Y-spokes, hub and
  brake backing, red caliper visible between the spokes, and the **white RTR
  monogram and ring on the centre cap** (chrome on the real RTR Aero 7 wheels;
  2.6 mm across with 0.25 mm strokes, so it needs a fine nozzle or it will merge
  into a raised dot - a silver paint-pen dab on the relief is the fallback).
- The exhaust tips are silver in the preview and print white here.

Colours partition the existing solid; they do not add stickers or protrusions.
Small features (badge strokes, DRL slashes, the pony) may merge or drop out with a
coarse nozzle or profile: inspect the sliced layers, then test one wheel and
`print/06_detail_test_1to1.stl` before committing to the full body.

## Checked and still pending

The exported colour solids pass closed-solid, positive-volume and consistent-face
checks; pairwise overlap (tolerance 0.02 mm3) and reproduction of the original shape
(tolerance 0.1 mm3) are recorded in `validation.json`. A PrusaSlicer 2.9.6 import/export audit on
the earlier revision of these files kept one grouped object with three named
volumes; the container format is unchanged, but repeat the import check on the
college machine. **The printer model, filament assignments, actual sliced layers
and a physical sample remain to be checked. No G-code is included.**

These colour files are material regions for a multicolour print; do not print them
as separate loose pieces for gluing. Only the complete body and the four complete
wheels are the five physical gift pieces.

## Attribution

Body adapted from "Ford Mustang GT 2018" by SadPepe:
https://www.thingiverse.com/thing:3192801 - CC BY-NC 4.0,
https://creativecommons.org/licenses/by-nc/4.0/ . Changes include size, repair,
smoothing, photo-matched roof/deck profile, 2018-style front fascia and lamps,
fixed-wheel attachment pads, mirrors, spoiler, badges and colour partitions. Wheel
geometry was independently created. Source records are in `../reference_assets/`.
Personal, non-commercial birthday gift use only.
