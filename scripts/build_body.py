"""Turn the openly licensed reference body into one clean printable solid (no Blender needed).

Steps: normalise the source to 160 mm -> voxelise and fill the open panel shells ->
volume-constrained Laplacian smoothing (flattens voxel stair-stepping) ->
quadric decimation. Writes work/body_source_normalized.stl, work/body_filled.stl
and work/body_clean.stl, then build_parts.py adds the gift-specific geometry.

Usage: .venv/bin/python scripts/build_body.py [--pitch 0.22] [--filter laplacian] [--iters 25] [--tolerance 0.03]
"""
from pathlib import Path
import argparse, json, time
import numpy as np
import scipy.ndimage as ndi
import trimesh
import manifold3d as md

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work'
WORK.mkdir(exist_ok=True)
SOURCE = ROOT / 'reference_assets/thingiverse_3192801/files/mustangBodyOnly.stl'
# Source is 140 mm long; these offsets centre it and put the underside near z=6.
Y_OFFSET, Z_OFFSET, SCALE = 17.805959701538086, 23.417420, 160 / 140

def normalise(mesh):
    v = mesh.vertices.copy()
    v[:, 1] -= Y_OFFSET
    v[:, 2] += Z_OFFSET
    v *= SCALE
    return trimesh.Trimesh(v, mesh.faces.copy(), process=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pitch', type=float, default=0.22, help='voxel size, mm')
    ap.add_argument('--filter', default='laplacian', choices=['laplacian', 'taubin', 'humphrey'])
    ap.add_argument('--iters', type=int, default=25, help='smoothing iterations')
    ap.add_argument('--lamb', type=float, default=0.5)
    ap.add_argument('--nu', type=float, default=0.53, help='Taubin only')
    ap.add_argument('--post-taubin', type=int, default=0, help='extra Taubin iterations after the main filter')
    ap.add_argument('--tolerance', type=float, default=0.03, help='decimation tolerance, mm')
    a = ap.parse_args()
    t0 = time.time()
    src = normalise(trimesh.load_mesh(SOURCE))
    src.merge_vertices(merge_tex=True, merge_norm=True)
    src.export(WORK / 'body_source_normalized.stl')
    print('normalised', src.extents.round(2).tolist(), flush=True)

    cache = WORK / 'body_filled.json'
    if cache.exists() and json.loads(cache.read_text()).get('pitch_mm') == a.pitch and (WORK / 'body_filled.stl').exists():
        filled = trimesh.load_mesh(WORK / 'body_filled.stl')
        print('filled (cached)', len(filled.faces), 'tris', flush=True)
    else:
        v = src.voxelized(pitch=a.pitch)
        grid = np.pad(v.matrix, 3)
        print('voxel grid', grid.shape, f'{time.time()-t0:.0f}s', flush=True)
        grid = ndi.binary_closing(grid, iterations=2)
        grid = ndi.binary_fill_holes(grid)
        labels, _ = ndi.label(grid)
        counts = np.bincount(labels.ravel()); counts[0] = 0
        grid = labels == counts.argmax()
        filled = trimesh.voxel.ops.matrix_to_marching_cubes(grid, pitch=a.pitch)
        filled.apply_translation(v.transform[:3, 3] - 3 * a.pitch)
        filled.export(WORK / 'body_filled.stl')
        cache.write_text(json.dumps({'pitch_mm': a.pitch, 'triangles': len(filled.faces)}))
        print('filled', len(filled.faces), 'tris, watertight', filled.is_watertight, f'{time.time()-t0:.0f}s', flush=True)

    # Volume-constrained Laplacian flattens the marching-cubes terraces; the sharp gift
    # features (grille recess, badges, vents, spoiler) are added afterwards in build_parts.py.
    smooth = filled.copy()
    if a.filter == 'laplacian':
        smooth = trimesh.smoothing.filter_laplacian(smooth, lamb=a.lamb, iterations=a.iters)
    elif a.filter == 'taubin':
        smooth = trimesh.smoothing.filter_taubin(smooth, lamb=a.lamb, nu=a.nu, iterations=a.iters)
    else:
        smooth = trimesh.smoothing.filter_humphrey(smooth, alpha=0.1, beta=0.5, iterations=a.iters)
    if a.post_taubin:
        smooth = trimesh.smoothing.filter_taubin(smooth, lamb=0.5, nu=0.53, iterations=a.post_taubin)
    print('smoothed', a.filter, a.iters, f'{time.time()-t0:.0f}s', flush=True)
    # Topology-safe decimation: manifold3d keeps the solid closed at a set tolerance.
    solid = md.Manifold(md.Mesh(np.asarray(smooth.vertices, dtype=np.float32), np.asarray(smooth.faces, dtype=np.uint32)))
    if solid.status() != md.Error.NoError:
        raise ValueError(str(solid.status()))
    out = solid.simplify(a.tolerance).to_mesh()
    clean = trimesh.Trimesh(np.array(out.vert_properties[:, :3]), np.array(out.tri_verts), process=True)
    clean.export(WORK / 'body_clean.stl')
    info = {'pitch_mm': a.pitch, 'filter': a.filter, 'iterations': a.iters, 'post_taubin': a.post_taubin, 'lamb': a.lamb, 'nu': a.nu,
            'simplify_tolerance_mm': a.tolerance, 'triangles': len(clean.faces),
            'watertight': bool(clean.is_watertight), 'extents_mm': clean.extents.tolist(), 'volume_mm3': float(clean.volume)}
    (WORK / 'body_clean.json').write_text(json.dumps(info, indent=1))
    print('BODY_CLEAN_DONE', json.dumps(info), f'{time.time()-t0:.0f}s', flush=True)

if __name__ == '__main__':
    main()
