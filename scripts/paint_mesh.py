"""Face-material painting of the exact printable meshes by solid partition.

Each printable solid (work/body_assembled.stl, work/wheel_master.stl) is split by
the ordered colour masks in regions.py. The pieces are concatenated back into one
labelled mesh per part (work/body_painted.npz, work/wheel_painted.npz) for the
assembled OBJ, the Blender scene and the previews. build_multicolor.py groups the
very same pieces by filament, so the preview never shows a colour edge the print
files do not have.
"""
from pathlib import Path
import json, time
import numpy as np
import trimesh
import geometry as G
import regions as R

ROOT = G.ROOT
WORK = ROOT / 'work'

def labelled_mesh(pieces):
    verts, faces, mats = [], [], []
    offset = 0
    for material, piece in pieces:
        m = G.meshof(piece)
        verts.append(m.vertices); faces.append(m.faces + offset); mats.append(np.full(len(m.faces), material, dtype=np.int32))
        offset += len(m.vertices)
    return np.vstack(verts), np.vstack(faces), np.concatenate(mats)

def main():
    t0 = time.time()
    body_mesh = trimesh.load_mesh(WORK / 'body_assembled.stl')
    deck = lambda x, y: (lambda loc: float(loc[:, 2].max()) if len(loc) else 30.0)(
        body_mesh.ray.intersects_location([[x, y, 100.0]], [[0, 0, -1.0]], multiple_hits=False)[0])
    R.set_deck_sampler(deck)
    body = G.manifold(body_mesh)
    regions, default = R.body_regions()
    print('body masks built', f'{time.time()-t0:.1f}s', flush=True)
    pieces = R.partition(body, regions, default)
    v, f, m = labelled_mesh(pieces)
    np.savez_compressed(WORK / 'body_painted.npz', vertices=v, faces=f, material=m)
    counts = {int(k): int(c) for k, c in zip(*np.unique(m, return_counts=True))}
    print('body painted', len(f), 'triangles, per material:', counts, f'{time.time()-t0:.1f}s', flush=True)

    wheel = G.manifold(trimesh.load_mesh(WORK / 'wheel_master.stl'))
    wregions, wdefault = R.wheel_regions()
    wpieces = R.partition(wheel, wregions, wdefault)
    v, f, m = labelled_mesh(wpieces)
    np.savez_compressed(WORK / 'wheel_painted.npz', vertices=v, faces=f, material=m)
    wcounts = {int(k): int(c) for k, c in zip(*np.unique(m, return_counts=True))}
    print('wheel painted', len(f), 'triangles, per material:', wcounts, flush=True)
    (WORK / 'paint_summary.json').write_text(json.dumps({'body_faces_per_material': counts, 'wheel_faces_per_material': wcounts}, indent=1))
    print('PAINT_DATA_COMPLETE', f'{time.time()-t0:.1f}s')

if __name__ == '__main__':
    main()
