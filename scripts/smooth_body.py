from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.wm.stl_import(filepath=str(ROOT/'work/body_filled.stl'))
o=bpy.context.object
m=o.modifiers.new('Remove voxel stair stepping','SMOOTH');m.factor=.6;m.iterations=85
bpy.ops.object.modifier_apply(modifier=m.name)
m=o.modifiers.new('Reduce triangles while preserving the silhouette','DECIMATE');m.ratio=.20
bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.wm.stl_export(filepath=str(ROOT/'work/body_clean.stl'),export_selected_objects=True)
print('SMOOTH_BODY_DONE',len(o.data.polygons),flush=True)
