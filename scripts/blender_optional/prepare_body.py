"""Repair and consolidate the openly licensed reference body in Blender.
Run with Blender -b --factory-startup --python scripts/prepare_body.py.
All dimensions in numerical millimetres; STL exports use those numbers.
"""
from pathlib import Path
import bpy, bmesh, json, math
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work'; WORK.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.wm.stl_import(filepath=str(ROOT/'reference_assets/thingiverse_3192801/files/mustangBodyOnly.stl'))
body=bpy.context.object; body.name='Source body - SadPepe CC BY-NC 4.0'
for v in body.data.vertices:
    v.co.x *= 160/140
    v.co.y = (v.co.y-17.805959701538086)*160/140
    v.co.z = (v.co.z+23.417420)*160/140
bm=bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.015)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(body.data); bm.free()
bpy.ops.wm.stl_export(filepath=str(WORK/'body_source_normalized.stl'),export_selected_objects=True)
body.data.remesh_voxel_size=0.18
body.data.use_remesh_preserve_volume=True
bpy.ops.object.voxel_remesh()
smooth=body.modifiers.new('Gentle surface smoothing','SMOOTH'); smooth.factor=0.28; smooth.iterations=3
bpy.ops.object.modifier_apply(modifier=smooth.name)
for p in body.data.polygons:p.use_smooth=True
bpy.ops.wm.stl_export(filepath=str(WORK/'body_remeshed.stl'),export_selected_objects=True)

scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'; scene.display.shading.studiolight_rotate_z=0.4
scene.display.shading.color_type='SINGLE'; scene.display.shading.single_color=(0.64,0.67,0.7)
scene.display.shading.show_shadows=True; scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'; scene.display.shading.curvature_ridge_factor=1.2; scene.display.shading.curvature_valley_factor=1.2
scene.display.shading.background_type='WORLD'; scene.world.color=(0.055,0.065,0.085)
scene.render.resolution_x=1400; scene.render.resolution_y=900; scene.render.resolution_percentage=100
bpy.ops.object.camera_add(location=(-155,-190,120)); cam=bpy.context.object
cam.rotation_euler=(Vector((0,0,22))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=198;cam.data.clip_end=2000;scene.camera=cam
scene.render.filepath=str(WORK/'body_initial.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'body_work.blend'))
print('BODY_PREP_COMPLETE',len(body.data.vertices),len(body.data.polygons),flush=True)
