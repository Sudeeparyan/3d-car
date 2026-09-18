"""Millimetre geometry for the fixed-wheel Mustang gift.

The body is a repaired/adapted SadPepe Mustang (CC BY-NC 4.0).
Wheels, spoiler, reinforcing geometry and coupon are generated here independently.
Run after prepare_body.py, solidify_body.py and smooth_body.py.
"""
from pathlib import Path
import json, math
import numpy as np
import trimesh
import manifold3d as md
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'print'; OUT.mkdir(exist_ok=True)
WORK=ROOT/'work'
WHEEL_R=11.65
WHEEL_INNER=22.8
WHEEL_X=[-48.4472,42.4928]

def manifold(mesh):
    mesh.merge_vertices();mesh.remove_unreferenced_vertices();mesh.fix_normals()
    result=md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
    if result.status()!=md.Error.NoError:raise ValueError(str(result.status()))
    return result

def meshof(m):
    a=m.to_mesh()
    return trimesh.Trimesh(np.array(a.vert_properties[:,:3]),np.array(a.tri_verts),process=True)

def box(size,center):
    m=trimesh.creation.box(extents=size);m.apply_translation(center);return manifold(m)

def cylinder(r,depth,center,axis=(0,0,1),n=96):
    m=trimesh.creation.cylinder(radius=r,height=depth,sections=n)
    m.apply_transform(trimesh.geometry.align_vectors([0,0,1],axis));m.apply_translation(center)
    return manifold(m)

def ellipsoid(center,size):
    m=trimesh.creation.icosphere(subdivisions=3);m.apply_scale(np.array(size)/2);m.apply_translation(center);return manifold(m)

def beam(a,b,r):
    a,b=np.array(a),np.array(b);v=b-a
    return cylinder(r,np.linalg.norm(v),(a+b)/2,v)+ellipsoid(a,[r*2]*3)+ellipsoid(b,[r*2]*3)

def union(parts):return md.Manifold.batch_boolean(parts,md.OpType.Add)

def lathe(profile,n=160):
    # A closed radial cross-section revolved around local Z.
    return md.CrossSection([np.array(profile,dtype=float)]).revolve(circular_segments=n)

def spoiler():
    vertices=[]
    for y in np.linspace(-28,28,41):
        t=(abs(y)/28)**2; xb=74.0-4.0*t;xf=xb-5.3
        zf=35.0-1.7*t;zb=37.0-2.0*t
        vertices += [[xf,y,zf-2.2],[xb,y,zb-2.2],[xb,y,zb],[xf,y,zf]]
    faces=[]
    for i in range(40):
        for j in range(4):
            a=i*4+j;b=i*4+(j+1)%4;c=(i+1)*4+(j+1)%4;d=(i+1)*4+j
            faces.extend([[a,b,c],[a,c,d]])
    faces.extend([[0,2,1],[0,3,2],[160,161,162],[160,162,163]])
    m=trimesh.Trimesh(vertices,faces);m.fix_normals();return manifold(m)

print('load clean body',flush=True)
base=trimesh.load_mesh(WORK/'body_clean.stl')
parts=base.split(only_watertight=False,repair=False)
base=max(parts,key=lambda p:abs(p.volume))
body=manifold(base)
additions=[body,box([130,37,3.4],[0,0,7.7])]
# Replace the source hood's overlapping micro-surfaces with its clean convex
# envelope; preserve its long tapered outline, then cut two solid-backed vents.
source=trimesh.load_mesh(ROOT/'reference_assets/thingiverse_3192801/files/mustangBodyOnly.stl')
hood=source.split(only_watertight=False,repair=False)[6]
hv=hood.vertices.copy();hv[:,1]-=17.805959701538086;hv[:,2]+=23.417420;hv*=160/140
hv[:,2]+=.2
hc=trimesh.convex.convex_hull(np.vstack([hv,hv-[0,0,2.5]]))
additions.append(manifold(hc))
for x in WHEEL_X:
    for side in [-1,1]:
        additions.append(cylinder(5.6,5.8,[x,side*19.9,WHEEL_R],axis=[0,1,0]))
for side in [-1,1]:
    additions.append(beam([-14.7,side*24.7,33.1],[-13.5,side*32.0,33.9],1.25))
    additions.append(ellipsoid([-13.8,side*32.0,34.6],[7.6,5.0,3.6]))
additions.append(spoiler())
# Readable 5.0 fender badges: 0.5 mm strokes, 0.45 mm relief on a buried base.
for side in [-1,1]:
    def glyphbar(x,z,w,h):return box([w,.95,h],[x,side*30.775,z])
    for z in [22.0,23.0,24.0]:additions.append(glyphbar(-32.0,z,1.55,.5))
    additions.append(glyphbar(-32.525,23.5,.5,1.0))
    additions.append(glyphbar(-31.475,22.5,.5,1.0))
    additions.append(glyphbar(-30.65,22.0,.5,.5))
    for z in [22.0,24.0]:additions.append(glyphbar(-29.3,z,1.5,.5))
    for x in [-29.8,-28.8]:additions.append(glyphbar(x,23.0,.5,2.0))
body=union(additions)
for y in [-12.6,12.6]:
    # Cutter starts at the actual hull height, leaving a shallow painted vent.
    hits,_,_=hc.ray.intersects_location([[-63.7,y,80]],[[0,0,-1]])
    surface=float(hits[:,2].max())
    body=body-box([6.4,5.6,2.0],[-63.7,y,surface+.55])
# A common flat underside and exact 160 mm longitudinal envelope.
body=body ^ box([160,100,80],[0,0,46])
body=body.simplify(.035)
bodymesh=meshof(body)
# Normalize X only by a few microns after repair so the delivered length is exact.
bodymesh.vertices[:,0]=(bodymesh.vertices[:,0]-bodymesh.bounds[:,0].mean())*(160/bodymesh.extents[0])
bodymesh=meshof(manifold(bodymesh))
bodymesh.export(WORK/'body_assembled.stl')
bodyprint=bodymesh.copy();bodyprint.apply_translation([0,0,-6])
bodyprint.export(OUT/'01_body_160mm.stl')
print('body done',len(bodymesh.faces),bodymesh.extents.tolist(),flush=True)

# One full-backed wheel, face up, flat back on z=0. All rim/spoke geometry
# intersects the backing: there are no floating spokes or loose calipers.
tyre=lathe([[0,0],[10.75,0],[11.35,.45],[11.65,1.5],[11.65,6.3],[11.4,7.7],[10.9,8.4],[9.7,8.4],[9.15,7.0],[0,7.0]])
rim=lathe([[8.95,6.9],[9.8,6.9],[9.8,8.6],[9.6,8.95],[9.1,8.95],[8.95,8.6]])
disc=cylinder(8.1,.28,[0,0,7.1])
hub=cylinder(2.45,1.8,[0,0,8.1])
spokes=[]
for j in range(7):
    angle=2*math.pi*j/7+math.pi/2
    p=np.array([2.0*math.cos(angle),2.0*math.sin(angle),8.15])
    q=np.array([4.8*math.cos(angle+.035),4.8*math.sin(angle+.035),8.15])
    spokes.append(beam(p,q,.58))
    for d in [-.14,.17]:
        end=[9.3*math.cos(angle+d),9.3*math.sin(angle+d),8.18]
        spokes.append(beam(q,end,.52))
caliper=box([2.4,6.0,.8],[-6.15,1.2,7.5])
wheel=union([tyre,rim,disc,hub,caliper]+spokes)
for j in range(5):
    a=j*2*math.pi/5
    wheel=wheel-cylinder(.4,1.0,[1.6*math.cos(a),1.6*math.sin(a),9.0],n=32)
wheel=wheel.simplify(.015)
wm=meshof(wheel)
wm.export(WORK/'wheel_master.stl')
labels=['02_wheel_front_left.stl','03_wheel_front_right.stl','04_wheel_rear_left.stl','05_wheel_rear_right.stl']
for filename in labels:wm.export(OUT/filename)

# Full-size detail coupon with a mirror-style 2.5 mm connection and grooves.
coupon=union([box([30,20,2.5],[0,0,1.25]),box([4,5,7],[1,0,5.5]),beam([1,0,8.6],[9,0,9.4],1.25),ellipsoid([10,0,10.1],[7.6,5,3.6])])
for x,w in [(-10,.6),(-7,.8),(-4,1.0)]:coupon=coupon-box([w,12,1],[x,0,2.6])
coupon=meshof(coupon.simplify(.01));coupon.export(OUT/'06_detail_test_1to1.stl')

manifest={
 'units':'mm','length_mm':160,'body_print_origin_offset':[0,0,6],
 'wheel_radius_mm':WHEEL_R,'wheel_inner_face_y_mm':WHEEL_INNER,
 'wheel_center_x_mm':WHEEL_X,'wheel_center_z_mm':WHEEL_R,
 'body_dimensions_mm':bodyprint.extents.tolist(),'wheel_dimensions_mm':wm.extents.tolist(),
 'assembly_dimensions_mm':[160,max(bodymesh.extents[1],2*(WHEEL_INNER+wm.bounds[1,2])),float(bodymesh.bounds[1,2])],
 'body_ground_clearance_mm':6.0,
 'wheel_attachment':'Flat 11.2 mm diameter pads at y=+/-22.8 mm; wheel backs glue directly to these. All four wheels are identical; caliper relief is rotated toward the rear when glued.',
 'files':['01_body_160mm.stl']+labels+['06_detail_test_1to1.stl'],
 'physical_print_test':'NOT RUN - requires college printer',
 'college_printer_profile':'UNKNOWN',
 'source_body':{'author':'SadPepe','url':'https://www.thingiverse.com/thing:3192801','license':'CC BY-NC 4.0'},
 'source_wheel_geometry_used':False,
}
(ROOT/'work/manifest.json').write_text(json.dumps(manifest,indent=2))
print('PARTS_COMPLETE',json.dumps(manifest),flush=True)
