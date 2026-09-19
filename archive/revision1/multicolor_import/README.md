# Multicolor import audit

**PASS for grouping and geometry in PrusaSlicer 2.9.6. Manual filament assignment is required.**

The final `multicolor/body_color_parts.3mf` and `multicolor/wheel_color_parts.3mf`
were imported and exported through the installed Windows CLI. Inspection of the
actual exported XML confirms one physical object with three named material
volumes in each file. The body measures **160 × 69.489 × 41.138 mm** and the wheel
measures **23.300 × 23.300 × 9.000 mm**, with each complete object on z=0.

Every color volume retains its position, triangle count and dimensions. Maximum
vertex change is below **0.0001 mm**. No mesh repair counts were reported. Source
file hashes and per-volume measurements are in `summary.json`.

The initial component-based container was corrected because PrusaSlicer treated
its colors as independent objects and dropped wheel regions to the bed. The
final container includes explicit named-volume metadata that preserves the
shared coordinates. No STL geometry was changed for this correction.

## Using these files

- In PrusaSlicer, preserve the one multipart object. Assign the three named
  body parts to white, black and red filament; assign the wheel parts to black,
  dark grey and red filament. Make four copies of the complete grouped wheel.
- Standard 3MF display colors do **not** survive this PrusaSlicer roundtrip.
  Named parts do survive; filament assignment remains a technician step.
- Other slicers are untested. If they discard named parts, import all three
  matching body STLs together as one object with multiple parts. Repeat for the
  wheel. Never center, arrange or drop individual color regions separately.
- The `number_of_parts` in CLI mesh statistics means connected geometry islands;
  it is not the named material-volume count. Each body/wheel has three material
  volumes even though a color may contain several disconnected detail regions.

The college printer and its color capability are still unknown. This is a file
import check, not an actual-machine multicolor slice or a physical print test.
The technician must select the machine profile, assign filaments, inspect sliced
layers and supports, and print a sample. Files marked `AUDIT_ONLY` are local test
exports and are excluded from the gift download.
