# Exported model geometry checks

**GEOMETRY_CHECKS_PASS** — 2026-09-17T07:47:15.425412+00:00

STL coordinates are interpreted as millimetres. This report checks exported geometry; college slicer setup and a physical sample remain required.

| Part | Dimensions (mm) | Triangles | Closed / consistent / one solid | Result |
|---|---|---:|---|---|
| 01_body_160mm.stl | 160.000 × 69.489 × 41.138 | 52,640 | yes / yes / yes | PASS |
| 02_wheel_front_left.stl | 23.300 × 23.300 × 9.000 | 19,608 | yes / yes / yes | PASS |
| 03_wheel_front_right.stl | 23.300 × 23.300 × 9.000 | 19,608 | yes / yes / yes | PASS |
| 04_wheel_rear_left.stl | 23.300 × 23.300 × 9.000 | 19,608 | yes / yes / yes | PASS |
| 05_wheel_rear_right.stl | 23.300 × 23.300 × 9.000 | 19,608 | yes / yes / yes | PASS |
| 06_detail_test_1to1.stl | 30.000 × 20.000 × 11.900 | 2,292 | yes / yes / yes | PASS |

Measured body length: **160.000000 mm** (target 160 mm, tolerance ±0.01 mm).

Assembly dimensions: **160.000 × 69.489 × 47.138 mm**.

All wheels are checked for matching dimensions and identical geometry. Assembly transforms correct winding where the local-to-world transform reflects a part.

| Wheel position | Body intersection (mm³) | Result |
|---|---:|---|
| 02_wheel_front_left.stl | 0.00000000 | PASS |
| 03_wheel_front_right.stl | 0.00000000 | PASS |
| 04_wheel_rear_left.stl | 0.00000000 | PASS |
| 05_wheel_rear_right.stl | 0.00000000 | PASS |

Glue pads are designed to touch wheel backs. Zero overlap volume allows this surface contact; it does not certify contact area, tolerances or successful gluing.

## Strength and printing limits

New mirror connections have a 2.5 mm design diameter; new wheel attachment pads have an 11.2 mm design diameter. These are design dimensions. Fine details inherited from the source have not received an exhaustive minimum-wall measurement.

Every exported part is checked for finite coordinates, closed topology, consistent winding, positive volume, one connected component, zero-area/collapsed faces, manifold-backend acceptance and a Z=0 print origin. Full self-intersection and wall-thickness certification are outside these checks.

## Still required at college

- Actual college printer, material, nozzle and profile are unknown.
- Inspect all final layers and support placement in the actual printer slicer.
- Physically print one wheel and the detail coupon before the full body.
- Confirm wheel pad contact, alignment, finish and adhesive fit with the physical parts.
- Fine inherited grille, badges, panels and mirror surfaces have no blanket minimum-wall pass.

See `geometry_report.json` for exact measurements, tolerances and SHA-256 hashes identifying every tested STL.
