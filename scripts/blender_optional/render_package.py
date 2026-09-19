"""Editable Blender scene and previews built from the actual exported geometry."""
from pathlib import Path
import bpy, numpy as np, json, math, sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'work';P=ROOT/'previews';P.mkdir(exist_ok=True)
D=ROOT/'model';D.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001;scene.unit_settings.length_unit='MILLIMETERS'

def material(name,c,metal=0,rough=.4):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m
mats=[material('01 Pearl white - paint or white filament',(.83,.85,.87),.12,.28),
      material('02 Black trim and opaque glazing',(.009,.012,.016),0,.43),
      material('03 Red lamps and brake calipers',(.60,.016,.022),.1,.3),
      material('04 Gunmetal wheels and silver details',(.075,.09,.11),.65,.34),
      material('05 Brake backing shadow',(.055,.064,.075),.45,.5)]
car=[]
def load(name,file):
    a=np.load(file);mesh=bpy.data.meshes.new(name);mesh.from_pydata(a['vertices'],[],a['faces']);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    for m in mats:mesh.materials.append(m)
    mesh.polygons.foreach_set('material_index',a['material'].astype(np.int32))
    mesh.polygons.foreach_set('use_smooth',np.ones(len(mesh.polygons),dtype=bool))
    car.append(obj);return obj
def load_parts(name, files, lift=0):
    """Load actual closed color volumes, preserving their shared coordinates."""
    vertices=[];faces=[];indices=[]
    for filename,index in files:
        bpy.ops.wm.stl_import(filepath=str(ROOT/'multicolor'/filename))
        temporary=bpy.context.object
        offset=len(vertices)
        vertices.extend([(v.co.x,v.co.y,v.co.z+lift) for v in temporary.data.vertices])
        faces.extend([tuple(i+offset for i in p.vertices) for p in temporary.data.polygons])
        indices.extend([index]*len(temporary.data.polygons))
        mesh=temporary.data
        bpy.data.objects.remove(temporary,do_unlink=True)
        bpy.data.meshes.remove(mesh)
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    for m in mats:mesh.materials.append(m)
    mesh.polygons.foreach_set('material_index',np.asarray(indices,dtype=np.int32))
    mesh.polygons.foreach_set('use_smooth',np.ones(len(mesh.polygons),dtype=bool))
    car.append(obj);return obj

use_color_parts=(ROOT/'multicolor/body_white.stl').exists()
if use_color_parts:
    body=load_parts('Body | aligned white, black and red volumes | 160 mm',[
        ('body_white.stl',0),('body_black.stl',1),('body_red.stl',2)],lift=6)
else:
    body=load('Body | one solid | 160 mm | print STL is lowered 6 mm',W/'body_painted.npz')
for axle,x in [('Front',-48.4472),('Rear',42.4928)]:
    for side,s in [('Left',-1),('Right',1)]:
        name=f'{axle} {side} wheel | glue flat back to body pad'
        if use_color_parts:
            o=load_parts(name,[('wheel_black.stl',1),('wheel_dark_grey.stl',3),('wheel_red.stl',2)])
        else:
            o=load(name,W/'wheel_painted.npz')
        # Rotate wheel so the red caliper is towards the rear (+X).
        for v in o.data.vertices:
            u,vv,h=v.co.copy();v.co=(x-u,s*(22.8+h),11.65+vv)
        if s<0:
            # Current local transform has negative determinant on this side.
            import bmesh
            bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()

# Preserve source reference in an explicitly hidden collection for editability.
ref=bpy.data.collections.new('REFERENCE - original SadPepe source - hidden');scene.collection.children.link(ref)
bpy.ops.wm.stl_import(filepath=str(W/'body_source_normalized.stl'))
orig=bpy.context.object;orig.name='Original source surface | CC BY-NC 4.0'
for c in list(orig.users_collection):c.objects.unlink(orig)
ref.objects.link(orig);ref.hide_render=True;ref.hide_viewport=True
orig.hide_render=True;orig.hide_set(True)

text=bpy.data.texts.new('READ ME - printing and attribution')
text.write('160 mm Mustang gift. Numerical geometry coordinates are millimetres.\nBody source: Ford Mustang GT 2018 by SadPepe, Thingiverse 3192801, CC BY-NC 4.0.\nBody repaired and adapted; new wheels/spoiler/mirror reinforcement by this project.\nSTLs in print/ are separately laid flat. This assembled scene is for viewing/editing.\nmulticolor/ contains aligned closed color volumes for filament assignment in a compatible slicer.\nColors here are material references, not printer instructions.\nActual college printer/slicer/color capability and physical sample remain to be checked.\nSee START_HERE.html, docs/PRINT_AND_PAINT_GUIDE.html and validation/.\n')

# Export only the five actual car meshes, preserving face material paint guide.
bpy.ops.object.select_all(action='DESELECT')
for o in car:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.wm.obj_export(filepath=str(D/'Mustang_160mm_assembled.obj'),export_selected_objects=True,export_materials=True,forward_axis='Y',up_axis='Z',apply_modifiers=True)

scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
if '--fast' in sys.argv:
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.light='STUDIO'
    scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.24,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
floor=material('Studio floor - not a print part',(.055,.07,.095),.1,.5)
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-.06));plane=bpy.context.object;plane.name='Studio floor - not a print part';plane.data.materials.append(floor)
def light(name,loc,power,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size
    o.rotation_euler=(Vector((0,0,15))-o.location).to_track_quat('-Z','Y').to_euler()
light('Large softbox',(-100,-100,200),600000,180)
light('Rear rim light',(120,90,140),800000,140)
light('Front fill',(-160,120,60),350000,120)
bpy.ops.object.camera_add(location=(-160,-190,115));cam=bpy.context.object;cam.name='Preview camera';cam.data.type='ORTHO';cam.data.clip_end=3000;scene.camera=cam
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=.6
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
def view(filename,loc,scale=194,target=(0,0,21)):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(P/filename);bpy.ops.render.render(write_still=True)
view('01_painted_front.png',(-160,-190,110))
view('02_painted_rear.png',(170,-190,100))
scene.render.resolution_y=640
view('08_painted_side.png',(0,-220,21),181)
scene.render.resolution_y=1000
view('09_painted_front_straight.png',(-220,0,23),98)
view('10_painted_rear_straight.png',(220,0,23),98)
# Neutral grey views expose the real geometry independently of painted colors.
scene.render.engine='BLENDER_WORKBENCH'
scene.view_settings.exposure=0
scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.64,.67,.7)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
scene.display.shading.background_type='WORLD';scene.world.color=(.06,.075,.1)
plane.hide_render=True
for filename,loc,scale in [
    ('03_grey_side_left.png',(0,-220,21),181),('04_grey_front.png',(-220,0,23),98),
    ('05_grey_rear.png',(220,0,23),98),('06_grey_side_right.png',(0,220,21),181),
    ('07_grey_three_quarter.png',(-160,-190,110),194)]:view(filename,loc,scale)
# Store colored scene by default, with clean viewable studio setup.
scene.render.engine='CYCLES';plane.hide_render=False
scene.view_settings.exposure=.6
scene.display.shading.color_type='MATERIAL'
cam.location=(-160,-190,110);cam.rotation_euler=(Vector((0,0,21))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=194
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_distance=210;a.spaces.active.region_3d.view_location=(0,0,22)
            a.spaces.active.clip_end=3000;a.spaces.active.shading.color_type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Mustang_160mm_editable.blend'))
print('RENDER_PACKAGE_COMPLETE',flush=True)
