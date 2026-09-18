"""Create a filled volume from the reference's disconnected/open surface panels.
Surface voxelization is independent of the inconsistent source triangle normals.
The 0.24 mm sampling grid closes sub-print-resolution cracks; it is not a claimed
accuracy of the replica. This intermediate is smoothed and simplified in Blender.
"""
from pathlib import Path
import numpy as np
import scipy.ndimage as ndi
import trimesh
ROOT=Path(__file__).resolve().parents[1]
mesh=trimesh.load_mesh(ROOT/'work/body_source_normalized.stl')
print('voxelize',flush=True)
v=mesh.voxelized(pitch=0.24)
matrix=np.pad(v.matrix,3)
print('voxel grid',matrix.shape,flush=True)
matrix=ndi.binary_closing(matrix,iterations=2)
matrix=ndi.binary_fill_holes(matrix)
labels,n=ndi.label(matrix)
counts=np.bincount(labels.ravel());counts[0]=0
matrix=labels==counts.argmax()
del labels
print('extract surface',int(matrix.sum()),flush=True)
result=trimesh.voxel.ops.matrix_to_marching_cubes(matrix,pitch=0.24)
result.apply_translation(v.transform[:3,3]-3*.24)
result.export(ROOT/'work/body_filled.stl')
print('filled',result.is_watertight,result.volume,result.extents.tolist(),flush=True)
