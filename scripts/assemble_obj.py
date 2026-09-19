"""Write the assembled, colour-labelled OBJ/MTL from the painted body and wheel meshes.

Reads work/body_painted.npz and work/wheel_painted.npz (vertices, faces, material index)
and writes model/Mustang_160mm_assembled.obj + .mtl. Material names start with a two-digit
code that viewer.html and scripts/render/render.html use to pick shading.
"""
from pathlib import Path
import json
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work'
OUT = ROOT / 'model'
WHEEL_X = [-48.4472, 42.4928]
WHEEL_R = 11.65
WHEEL_INNER = 22.8

MATERIALS = [  # index -> (name, linear Kd, description)
    ('01_Pearl_white_-_paint_or_white_filament', (.83, .85, .87)),
    ('02_Black_trim_and_opaque_glazing', (.009, .012, .016)),
    ('03_Red_lamps_and_brake_calipers', (.60, .016, .022)),
    ('04_Gunmetal_wheels', (.075, .09, .11)),
    ('05_Brake_backing_shadow', (.055, .064, .075)),
    ('06_Chrome_RTR_cap_logo_and_exhaust_tips', (.62, .64, .66)),
    ('07_Amber_headlamp_markers', (.80, .30, .04)),
    ('08_Gloss_black_badges', (.012, .014, .018)),
]

def wheel_transform(vertices, x, side):
    """Local wheel (back on z=0, face up) -> assembled position; local +x points to the nose."""
    u, v, h = vertices.T
    out = np.c_[x - u, side * (WHEEL_INNER + h), WHEEL_R + v]
    return out

def write_mtl(path):
    lines = ['# 160 mm Mustang gift - material reference (Kd is linear colour)']
    for name, kd in MATERIALS:
        lines += [f'newmtl {name}', 'Ns 400.0', 'Ka 0.2 0.2 0.2', 'Kd %.4f %.4f %.4f' % kd, 'Ks 0.5 0.5 0.5', 'Ni 1.5', 'd 1.0', 'illum 3', '']
    path.write_text('\n'.join(lines))

def creased_normals(vertices, faces, angle_deg=35.0):
    """Split vertices along edges sharper than angle_deg and return (positions, normals,
    faces) with area-weighted smooth normals inside each smoothing group. Face order is
    preserved so per-face material labels stay valid."""
    m = trimesh.Trimesh(vertices, faces, process=False)
    adjacency, angles = m.face_adjacency, m.face_adjacency_angles
    smooth_edges = adjacency[angles < np.radians(angle_deg)]
    groups = trimesh.graph.connected_component_labels(smooth_edges, node_count=len(faces))
    keys = faces.astype(np.int64) * (groups.max() + 1) + groups[:, None]
    unique, inverse = np.unique(keys, return_inverse=True)
    new_faces = inverse.reshape(-1, 3)
    positions = vertices[unique // (groups.max() + 1)]
    weighted = m.face_normals * m.area_faces[:, None]
    normals = np.zeros((len(unique), 3))
    for k in range(3):
        np.add.at(normals, new_faces[:, k], weighted)
    length = np.linalg.norm(normals, axis=1); length[length == 0] = 1
    return positions, normals / length[:, None], new_faces

def write_obj(path, objects, mtl_name):
    """objects: list of (name, vertices, faces, material_index per face)."""
    out = ['# 160 mm Mustang gift, assembled. Millimetres, Z up, nose towards -X.', f'mtllib {mtl_name}']
    offset = 1
    for name, verts, faces, mats in objects:
        verts, normals, faces = creased_normals(np.asarray(verts, float), np.asarray(faces))
        out.append('o ' + name.replace(' ', '_'))
        out.extend('v %.5f %.5f %.5f' % tuple(v) for v in verts)
        out.extend('vn %.4f %.4f %.4f' % tuple(n) for n in normals)
        order = np.argsort(mats, kind='stable')
        current = -1
        for i in order:
            if mats[i] != current:
                current = int(mats[i]); out.append('usemtl ' + MATERIALS[current][0])
            a, b, c = faces[i] + offset
            out.append(f'f {a}//{a} {b}//{b} {c}//{c}')
        offset += len(verts)
    path.write_text('\n'.join(out) + '\n')

def main():
    OUT.mkdir(exist_ok=True)
    body = np.load(WORK / 'body_painted.npz'); wheel = np.load(WORK / 'wheel_painted.npz')
    objects = [('Body | 160 mm | print STL is lowered 6 mm', body['vertices'], body['faces'], body['material'])]
    for axle, x in [('Front', WHEEL_X[0]), ('Rear', WHEEL_X[1])]:
        for side, s in [('Left', -1), ('Right', 1)]:
            v = wheel_transform(wheel['vertices'], x, s)
            f = wheel['faces'] if s > 0 else wheel['faces'][:, ::-1]  # mirrored side: keep outward normals
            objects.append((f'{axle} {side} wheel | glue flat back to body pad', v, f, wheel['material']))
    write_mtl(OUT / 'Mustang_160mm_assembled.mtl')
    write_obj(OUT / 'Mustang_160mm_assembled.obj', objects, 'Mustang_160mm_assembled.mtl')
    tris = sum(len(o[2]) for o in objects)
    allv = np.vstack([o[1] for o in objects])
    used = sorted({int(m) for o in objects for m in np.unique(o[3])})
    (ROOT / 'validation/assembly_export_check.json').write_text(json.dumps({
        'status': 'PASS',
        'assembled_obj_dimensions_mm': (allv.max(axis=0) - allv.min(axis=0)).round(6).tolist(),
        'assembled_obj_bounds_mm': [allv.min(axis=0).round(4).tolist(), allv.max(axis=0).round(4).tolist()],
        'triangles': int(tris),
        'physical_objects': [o[0] for o in objects],
        'materials': [MATERIALS[i][0] for i in used],
        'note': 'Assembled OBJ/MTL is for viewing and painting reference; print the separate STLs. Wheels sit on the body pads at y = +/-22.8 mm, body underside at z = 6 mm.',
        'limits': 'Does not replace actual machine slicing or a physical test.'}, indent=2))
    print('ASSEMBLED_OBJ_DONE', OUT / 'Mustang_160mm_assembled.obj', tris, 'triangles')

if __name__ == '__main__':
    main()
