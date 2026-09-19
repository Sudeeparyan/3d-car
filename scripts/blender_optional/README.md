# Optional Blender scripts (not needed)

These scripts were the first-revision pipeline and need Blender 4.x (`blender -b -P ...`):

- `prepare_body.py`, `solidify_body.py`, `smooth_body.py` - body repair; replaced by
  `scripts/build_body.py` (trimesh voxel fill + manifold3d), which needs no Blender.
- `render_package.py` - Cycles previews and the `.blend` scene; replaced by
  `scripts/make_previews.py` (headless three.js). It still lists only five materials
  and reads the old multicolour parts, so it would need updating before use.

The current deliverables are produced without Blender; see the README at the root.
