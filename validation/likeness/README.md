# Photo likeness loop

`final/` holds the report of the last accepted design iteration: how closely the
assembled model matches the six reference photographs of the real car.

## How it is measured (`scripts/validate_likeness.py`)

1. **Side profile.** The silhouette of the real car is cut out of the side
   photograph (`photo3_mask.png`, GrabCut seeded by a traced outline) and aligned to
   an orthographic side render on the two wheel-hub centres (10.94 px per model mm).
   The upper outline from the windscreen base to the tail is compared in millimetres;
   the hood is excluded because perspective in a phone photo shows the far fender
   there. `profile_top_mean_abs_mm` below 0.6 mm counts as a match.
2. **Feature checks.** Flat-colour renders (no lighting, one exact colour per
   material) are inspected for the signature details in the photographs: black
   grille with a visible gloss-black pony badge, smoked headlamps with three DRL
   slashes and an amber marker each side, black splitter, two hood vents, white roof,
   six red tail-light bars, black rear panel, lip spoiler, four exhaust tips, black
   diffuser, the four-hash-mark stripe, the 5.0 badge on both sides (equal size and
   reading "5" then "0" from outside on each side), red caliper, open spokes and the
   silver RTR centre-cap monogram in the wheel, black mirror and dark side glass.
3. **Score** = 50 % feature pass rate + 50 % profile agreement (1 at 0 mm, 0 at 2.5 mm).

`contact_sheet.jpg` pairs each photograph with the matching render;
`profile_compare.png` overlays the two outlines (red photo, black render).

## Re-running

```
scripts/iterate.sh <name> [--skip-body]   # build -> paint -> OBJ -> render -> score into validation/likeness/<name>
scripts/promote_likeness.sh <name>        # copy the accepted run to validation/likeness/final
```

The loop is deterministic: same scripts, same photographs, same score. It measures
outline and colour layout, not surface finish, and it cannot replace looking at the
printed part next to the photographs.
