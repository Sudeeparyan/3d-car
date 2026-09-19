# Check against the birthday-model plan

The digital model package is complete. The remaining steps take place at college: configure the real machine, inspect its sliced layers, print a sample, then print and assemble the gift.

| Planned item | Delivered result |
|---|---|
| 160 mm display model | Exported body and assembled OBJ measure 160.000 mm long. |
| Approximately 64 mm body width and 46 mm overall height | Main body is approximately 64 mm wide. Width including mirrors is 69.73 mm; assembled height is 46.59 mm. These are the measured final dimensions. |
| Photo-guided appearance | Roof and deck profile fitted to the side photograph (within 0.6 mm). Gloss-black running-pony grille badge, recessed hexagonal grille and lower intake, slim smoked headlamps with three LED slashes and amber markers, hood vents, source-shape wedge mirrors, dark door / quarter / windscreen / rear glass, black 5.0 badges readable on both sides, four-hash-mark rocker stripe, seven-Y-spoke gunmetal RTR Aero 7 wheels with the RTR centre-cap monogram and red calipers, tri-bar tail lights, black rear panel, lip spoiler, diffuser with quad exhaust tips, shark-fin antenna, rear number plate (lettering pending the registration). A render-versus-photo loop scores 88.4 % (22/22 features). Surface contours remain simplified. |
| Five physical pieces | One body with underside, mirrors and spoiler, plus four identical fixed wheels. |
| Printable STL files | Body, four labeled wheels and a separate full-size detail coupon. Closed-solid checks passed. |
| Color files | Closed material regions and grouped 3MF files generated from the same colour masks as the preview. Keep the regions of each physical object together and assign real filaments in the college slicer. The earlier revision's PrusaSlicer import audit covers the unchanged container format. |
| View and edit | Assembled OBJ/MTL, interactive `viewer.html`, grey and painted views, close-ups and the color/assembly diagram. Everything regenerates from `scripts/`; the earlier Blender project is archived. |
| Digital validation | Geometry checks, assembly dimensions, color-region overlap/union checks and the photo-likeness loop. The generic single-material slicer simulation was run on the earlier revision (same footprint, 2 % less volume now). |
| Actual printer validation | Pending: college printer, build area, material, nozzle, color capability and real profile are unknown. |
| Physical sample and final gift | Pending: print a wheel and detail coupon, check results, print the final parts, finish and glue. |

## Changes from the proposed starting approach

The listed Sketchfab asset required login. An accessible free Mustang body by SadPepe was used instead, under its CC BY-NC 4.0 license, with attribution included. The final wheels were independently generated. This is an adaptation of a 2018-style Mustang base using the photographs, not an exact scan or measured replica of the friend's car.

The final files include multicolor regions in addition to the original STL-and-paint approach. A college printer is not assumed to support multicolor. Standard STLs plus painting remain usable if it prints one color.

Mirror heads follow the source model's own mirror shape on 3 × 1.6 mm blade stalks; wheel glue pads have an 11.2 mm design diameter. This is not a minimum-thickness guarantee for every inherited grille, badge or panel detail. Slicer inspection and the final-size sample determine which small features print successfully.

The earlier revision's generic simulation estimated about 8 hours 37 minutes and 104 g for one body and four wheels, excluding the detail coupon; this revision has a similar volume. It is not the college printer's estimate. Multicolor time, purge waste and material use remain unknown. The birthday schedule depends on machine access and successful physical printing.
