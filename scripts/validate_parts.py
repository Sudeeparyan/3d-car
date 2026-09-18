"""Read-only geometry checks for exported Mustang print parts, in millimetres.

Run with .venv/Scripts/python.exe scripts/validate_parts.py.
Writes validation/geometry_report.json and validation/GEOMETRY_REPORT.md.
This does not certify a print profile or replace a physical test print.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import manifold3d as md
import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
LENGTH_TOLERANCE_MM = 0.01
BED_TOLERANCE_MM = 0.001
COLLISION_TOLERANCE_MM3 = 0.001
ZERO_AREA_TOLERANCE_MM2 = 1e-12


def backend(mesh: trimesh.Trimesh) -> md.Manifold:
    return md.Manifold(md.Mesh(
        np.asarray(mesh.vertices, dtype=np.float32),
        np.asarray(mesh.faces, dtype=np.uint32),
    ))


def inspect(path: Path) -> tuple[trimesh.Trimesh, dict]:
    # Keep all original faces. Only weld coincident STL vertices for topology.
    mesh = trimesh.load_mesh(path, process=False)
    original_faces = len(mesh.faces)
    finite = bool(np.isfinite(mesh.vertices).all())
    area = mesh.area_faces
    degenerate = int(np.count_nonzero(area <= ZERO_AREA_TOLERANCE_MM2))
    mesh.merge_vertices(digits_vertex=8)
    repeated_indices = int(np.count_nonzero(
        (mesh.faces[:, 0] == mesh.faces[:, 1]) |
        (mesh.faces[:, 1] == mesh.faces[:, 2]) |
        (mesh.faces[:, 0] == mesh.faces[:, 2])
    ))
    components = mesh.split(only_watertight=False, repair=False)
    bounds = mesh.bounds
    solid = backend(mesh)
    checks = {
        'finite_coordinates': finite,
        'watertight': bool(mesh.is_watertight),
        'consistent_winding': bool(mesh.is_winding_consistent),
        'positive_volume': bool(mesh.volume > 0),
        'single_connected_solid': len(components) == 1,
        'no_zero_area_triangles': degenerate == 0,
        'no_collapsed_faces_after_vertex_weld': repeated_indices == 0,
        'manifold_backend_accepts_mesh': solid.status() == md.Error.NoError,
        'flat_print_origin_at_z_zero': abs(float(bounds[0, 2])) <= BED_TOLERANCE_MM,
    }
    row = {
        'file': path.relative_to(ROOT).as_posix(),
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'triangles': original_faces,
        'vertices_after_coincident_vertex_weld': len(mesh.vertices),
        'bounds_mm': bounds.tolist(),
        'dimensions_mm': mesh.extents.tolist(),
        'volume_mm3': float(mesh.volume),
        'connected_components': len(components),
        'zero_area_triangles': degenerate,
        'collapsed_index_faces': repeated_indices,
        'backend_status': str(solid.status()),
        'checks': checks,
        'passed': all(checks.values()),
    }
    return mesh, row


def assembled_wheel(mesh: trimesh.Trimesh, x: float, side: int,
                    inner_y: float, center_z: float) -> trimesh.Trimesh:
    # Print-local x/y form the wheel face; local z is its depth.
    # x_world = x_center + local_x; y_world = side*(inner_y+local_z);
    # z_world = center_z + local_y. Trimesh handles negative determinant winding.
    transform = np.array([
        [1, 0, 0, x],
        [0, 0, side, side * inner_y],
        [0, 1, 0, center_z],
        [0, 0, 0, 1],
    ], dtype=float)
    result = mesh.copy()
    result.apply_transform(transform)
    return result


def main() -> int:
    manifest_path = ROOT / 'work/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    files = manifest['files']
    meshes = {}
    rows = []
    for filename in files:
        mesh, row = inspect(ROOT / 'print' / filename)
        meshes[filename] = mesh
        rows.append(row)
        print(filename, 'PASS' if row['passed'] else 'FAIL',
              row['dimensions_mm'], flush=True)

    body_name = '01_body_160mm.stl'
    body = meshes[body_name].copy()
    body.apply_translation(manifest['body_print_origin_offset'])
    body_solid = backend(body)
    wheel_files = [name for name in files if '_wheel_' in name]
    reference = meshes[wheel_files[0]]
    identical_dimensions = all(np.allclose(
        meshes[name].extents, reference.extents, rtol=0, atol=1e-6
    ) for name in wheel_files)
    identical_geometry = all(
        np.array_equal(meshes[name].vertices, reference.vertices) and
        np.array_equal(meshes[name].faces, reference.faces)
        for name in wheel_files
    )
    exact_length = float(meshes[body_name].extents[0])
    assembly_checks = {
        'body_length_160mm_within_0_01mm': abs(exact_length - 160.0) <= LENGTH_TOLERANCE_MM,
        'four_wheel_files': len(wheel_files) == 4,
        'identical_wheel_dimensions': identical_dimensions,
        'identical_wheel_geometry': identical_geometry,
    }
    clearances = []
    assembled = [body]
    front_x, rear_x = manifest['wheel_center_x_mm']
    for name in wheel_files:
        side = 1 if '_left' in name else -1
        center_x = front_x if '_front_' in name else rear_x
        wheel = assembled_wheel(reference, center_x, side,
                                manifest['wheel_inner_face_y_mm'],
                                manifest['wheel_center_z_mm'])
        assembled.append(wheel)
        wheel_solid = backend(wheel)
        collision = body_solid ^ wheel_solid
        overlap_volume = max(0.0, float(collision.volume()))
        passed = (wheel.is_volume and collision.status() == md.Error.NoError
                  and overlap_volume <= COLLISION_TOLERANCE_MM3)
        clearances.append({
            'wheel': name,
            'world_center_mm': [center_x,
                                side * manifest['wheel_inner_face_y_mm'],
                                manifest['wheel_center_z_mm']],
            'consistent_winding_after_transform': bool(wheel.is_winding_consistent),
            'positive_volume_after_transform': bool(wheel.volume > 0),
            'body_intersection_volume_mm3': overlap_volume,
            'intersection_backend_status': str(collision.status()),
            'no_volumetric_collision': bool(passed),
        })
        print(name, 'body overlap mm3:', overlap_volume, flush=True)
    assembly_checks['no_wheel_body_volumetric_collisions'] = all(
        item['no_volumetric_collision'] for item in clearances)
    assembly_bounds = np.array([
        np.min(np.stack([part.bounds[0] for part in assembled]), axis=0),
        np.max(np.stack([part.bounds[1] for part in assembled]), axis=0),
    ])
    passed = all(row['passed'] for row in rows) and all(assembly_checks.values())
    report = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'units': 'mm',
        'status': 'GEOMETRY_CHECKS_PASS' if passed else 'GEOMETRY_CHECKS_FAIL',
        'tested_export_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'tolerances': {
            'body_length_mm': LENGTH_TOLERANCE_MM,
            'bed_origin_mm': BED_TOLERANCE_MM,
            'zero_triangle_area_mm2': ZERO_AREA_TOLERANCE_MM2,
            'volumetric_collision_mm3': COLLISION_TOLERANCE_MM3,
        },
        'parts': rows,
        'assembly_checks': assembly_checks,
        'measured_body_length_mm': exact_length,
        'assembly_bounds_mm': assembly_bounds.tolist(),
        'assembly_dimensions_mm': (assembly_bounds[1] - assembly_bounds[0]).tolist(),
        'wheel_body_intersections': clearances,
        'design_targets_not_universal_wall_certification': {
            'added_mirror_connection_diameter_mm': 2.5,
            'added_wheel_attachment_pad_diameter_mm': 11.2,
            'source_detail_minimum_wall_thickness': 'NOT exhaustively measured',
        },
        'remaining_checks': [
            'Actual college printer, material, nozzle and profile are unknown.',
            'Inspect all final layers and support placement in the actual printer slicer.',
            'Physically print one wheel and the detail coupon before the full body.',
            'Confirm wheel pad contact, alignment, finish and adhesive fit with the physical parts.',
            'Fine inherited grille, badges, panels and mirror surfaces have no blanket minimum-wall pass.',
        ],
        'limits': [
            'No printer-specific G-code has been validated by this script.',
            'Topology/backend acceptance is not exhaustive self-intersection or wall-thickness certification.',
            'A zero intersection volume permits designed tangent glue contact; it is not a fit guarantee.',
            'The finite surface meshes are measured as exported; STL itself stores no unit metadata.',
        ],
    }
    output = ROOT / 'validation'
    output.mkdir(exist_ok=True)
    (output / 'geometry_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    lines = [
        '# Exported model geometry checks', '',
        f"**{report['status']}** — {report['created_utc']}", '',
        'STL coordinates are interpreted as millimetres. This report checks exported geometry; '
        'college slicer setup and a physical sample remain required.', '',
        '| Part | Dimensions (mm) | Triangles | Closed / consistent / one solid | Result |',
        '|---|---|---:|---|---|',
    ]
    for row in rows:
        dims = ' × '.join(f'{value:.3f}' for value in row['dimensions_mm'])
        topology = ' / '.join('yes' if row['checks'][key] else 'NO' for key in
                              ['watertight', 'consistent_winding', 'single_connected_solid'])
        lines.append(f"| {Path(row['file']).name} | {dims} | {row['triangles']:,} | "
                     f"{topology} | {'PASS' if row['passed'] else 'FAIL'} |")
    lines.extend(['', f'Measured body length: **{exact_length:.6f} mm** '
                  f'(target 160 mm, tolerance ±{LENGTH_TOLERANCE_MM} mm).',
                  '', 'Assembly dimensions: **' + ' × '.join(
                      f'{x:.3f}' for x in report['assembly_dimensions_mm']) + ' mm**.',
                  '', 'All wheels are checked for matching dimensions and identical geometry. '
                  'Assembly transforms correct winding where the local-to-world transform reflects a part.', '',
                  '| Wheel position | Body intersection (mm³) | Result |',
                  '|---|---:|---|'])
    for item in clearances:
        lines.append(f"| {item['wheel']} | {item['body_intersection_volume_mm3']:.8f} | "
                     f"{'PASS' if item['no_volumetric_collision'] else 'FAIL'} |")
    lines.extend(['', 'Glue pads are designed to touch wheel backs. Zero overlap volume allows this '
                  'surface contact; it does not certify contact area, tolerances or successful gluing.', '',
                  '## Strength and printing limits', '',
                  'New mirror connections have a 2.5 mm design diameter; new wheel attachment pads '
                  'have an 11.2 mm design diameter. These are design dimensions. Fine details inherited '
                  'from the source have not received an exhaustive minimum-wall measurement.', '',
                  'Every exported part is checked for finite coordinates, closed topology, consistent '
                  'winding, positive volume, one connected component, zero-area/collapsed faces, '
                  'manifold-backend acceptance and a Z=0 print origin. Full self-intersection and '
                  'wall-thickness certification are outside these checks.', '',
                  '## Still required at college', ''])
    lines.extend('- ' + note for note in report['remaining_checks'])
    if not passed:
        lines.extend(['', '## Failed checks', ''])
        for row in rows:
            for key, value in row['checks'].items():
                if not value:
                    lines.append(f"- {row['file']}: {key}")
        for key, value in assembly_checks.items():
            if not value:
                lines.append('- Assembly: ' + key)
    lines.extend(['', 'See `geometry_report.json` for exact measurements, tolerances and SHA-256 '
                  'hashes identifying every tested STL.', ''])
    (output / 'GEOMETRY_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    print(report['status'], flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
