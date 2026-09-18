"""Partition the gift STL solids into four real, non-overlapping filament colors.

The result is printer-neutral geometry, not printer-specific instructions. Original
print/ meshes are never modified. Source body attribution stays CC BY-NC 4.0.
"""
from pathlib import Path
from itertools import combinations
import hashlib, json, math, zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import manifold3d as md
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'multicolor'
OUT.mkdir(exist_ok=True)
PALETTE = {'white': '#F3F2EB', 'black': '#16191D', 'red': '#BF1725', 'dark_grey': '#4F545A'}

def solid(mesh):
    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    # Keep cavity shells inward-facing; independently flipping nested components
    # would turn material boundaries into overlapping filled solids.
    mesh.fix_normals(multibody=False)
    result = md.Manifold(md.Mesh64(np.asarray(mesh.vertices, dtype=np.float64), np.asarray(mesh.faces, dtype=np.uint64)))
    if result.status() != md.Error.NoError:
        raise ValueError(f'Manifold import: {result.status()}')
    return result

def meshof(m):
    a = m.to_mesh64()
    return trimesh.Trimesh(np.asarray(a.vert_properties[:, :3]), np.asarray(a.tri_verts), process=True)

def box(lo, hi):
    lo, hi = np.asarray(lo), np.asarray(hi)
    m = trimesh.creation.box(hi-lo)
    m.apply_translation((hi+lo)/2)
    return solid(m)

def prism(points, axes, lo, hi):
    """Convex polygon projected into a requested coordinate plane and extruded."""
    points = np.asarray(points)
    other = next(i for i in range(3) if i not in axes)
    v = np.zeros((len(points)*2, 3))
    v[:len(points), axes[0]] = points[:, 0]
    v[:len(points), axes[1]] = points[:, 1]
    v[len(points):, axes[0]] = points[:, 0]
    v[len(points):, axes[1]] = points[:, 1]
    v[:len(points), other] = lo
    v[len(points):, other] = hi
    return solid(trimesh.convex.convex_hull(v))

def union(parts):
    return md.Manifold.batch_boolean(parts, md.OpType.Add)

def cylinder(r, h, center, axis=(0,0,1), n=96):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=n)
    m.apply_transform(trimesh.geometry.align_vectors([0,0,1], axis))
    m.apply_translation(center)
    return solid(m)

def ellipsoid(center, size):
    m = trimesh.creation.icosphere(subdivisions=3)
    m.apply_scale(np.array(size)/2)
    m.apply_translation(center)
    return solid(m)

def beam(a, b, r):
    a,b = np.asarray(a),np.asarray(b)
    v=b-a
    return cylinder(r,np.linalg.norm(v),(a+b)/2,v) + ellipsoid(a,[2*r]*3) + ellipsoid(b,[2*r]*3)

def lathe(profile):
    return md.CrossSection([np.asarray(profile, dtype=float)]).revolve(circular_segments=160)

source_path=ROOT/'reference_assets/thingiverse_3192801/files/mustangBodyOnly.stl'
source=trimesh.load_mesh(source_path).split(only_watertight=False, repair=False)
def source_prism(index, axes, lo, hi, shrink=1.0):
    v = source[index].vertices.copy()
    v[:,1] -= 17.805959701538086
    v[:,2] += 23.417420
    v *= 160/140
    q = v[:, axes]
    hull=q[ConvexHull(q).vertices]
    hull=(hull-hull.mean(axis=0))*shrink+hull.mean(axis=0)
    return prism(hull, axes, lo, hi)

body_path=ROOT/'work/body_assembled.stl'
wheel_path=ROOT/'work/wheel_master.stl'
body = solid(trimesh.load_mesh(body_path))
wheel = solid(trimesh.load_mesh(wheel_path))
print('Partitioning body colors',flush=True)
black_masks=[]
# Side glazing is projected from the source window outline onto both sides.
for lo,hi in [(-45,-20),(20,45)]:
    black_masks.append(source_prism(22,[0,2],lo,hi) ^ box([-90,-50,31],[90,50,60]))
black_masks.append(source_prism(5,[0,1],31,60))
# Front windscreen: a tapered top-view outline avoids a rectangular paint edge.
black_masks.append(prism([[-24.5,-24],[-24.5,24],[-5.1,20.4],[-5.1,-20.4]], [0,1],34.2,60))
# Front grille and lower grille; rear central panel and both taillamp surrounds.
for index,lo,hi in [(1,-90,-68),(24,-90,-68),(27,70,90),(31,68.1,90),(37,68.1,90)]:
    black_masks.append(source_prism(index,[1,2],lo,hi,shrink=1.03 if index in [31,37] else 1.0))
# Simplified smoked headlamps.
for index in [28,30]:
    # Source headlamp housings wrap onto the nose. A y/z projection covers their
    # front-facing surfaces as well as their upper ledges.
    black_masks.append(source_prism(index,[1,2],-85,-59.9))
# Solid-backed hood vents.
for y in [-12.6,12.6]:
    black_masks.append(box([-66.95,y-2.85,29],[-60.45,y+2.85,60]))
# Mirror heads and reinforced attachments.
for s in [-1,1]:
    ymin,ymax = (25.8,45) if s>0 else (-45,-25.8)
    black_masks.append(box([-20,ymin,31.5],[-8,ymax,37.5]))
# Curved rear lip. Upper mask follows the existing spoiler curve with a small
# allowance for its mesh simplification; intersection cannot add any geometry.
verts=[]
for y in np.linspace(-28.2,28.2,43):
    t=(min(abs(y),28)/28)**2
    xf=68.6-4*t; xb=74.3-4*t
    z=32.55-1.7*t
    verts.extend([[xf,y,z],[xb,y,z],[xb,y,60],[xf,y,60]])
faces=[]
for i in range(42):
    for j in range(4):
        a=i*4+j;b=i*4+(j+1)%4;c=(i+1)*4+(j+1)%4;d=(i+1)*4+j
        faces.extend([[a,b,c],[a,c,d]])
faces.extend([[0,2,1],[0,3,2],[168,169,170],[168,170,171]])
black_masks.append(solid(trimesh.Trimesh(verts,faces)))
# Lower side stripe, with the three diagonal white interruptions in the photos.
stripe=box([-35,-45,9.5],[31,45,13.8])
gaps=[]
for a,b in [(-32,-30),(-26,-24),(-20,-18)]:
    gaps.append(prism([[a,9.5],[b,9.5],[b+.7*4.3,13.8],[a+.7*4.3,13.8]],[0,2],-50,50))
stripe=stripe-union(gaps)
stripe=stripe^(box([-90,-45,0],[90,-26,60])+box([-90,26,0],[90,45,60]))
black_masks.append(stripe)
# Low skirts/splitter and dark fender badge relief.
black_masks.extend([box([-90,-45,0],[90,-24,9.1]),box([-90,24,0],[90,45,9.1]),box([-90,-50,0],[-62,50,10])])
for lo,hi in [(-45,-31.15),(31.15,45)]:
    black_masks.append(box([-33,lo,21.7],[-28.4,hi,24.3]))

red_mask=union([source_prism(i,[1,2],69.05,90,shrink=.92) for i in [32,34,36,38,40,42]])
red,remaining=body.split(red_mask)
black,white=remaining.split(union(black_masks))
body_colors={'white':white.translate((0,0,-6)),'black':black.translate((0,0,-6)),'red':red.translate((0,0,-6))}
body_print=body.translate((0,0,-6))

print('Partitioning wheel colors',flush=True)
# Recreate the original independently generated rim/disc/spoke masks. Their
# intersection with the final wheel keeps the delivered outer surface intact.
rim=lathe([[8.95,6.9],[9.8,6.9],[9.8,8.6],[9.6,8.95],[9.1,8.95],[8.95,8.6]])
disc=cylinder(8.1,.28,[0,0,7.1])
hub=cylinder(2.45,1.8,[0,0,8.1])
spokes=[]
for j in range(7):
    angle=2*math.pi*j/7+math.pi/2
    p=np.array([2*math.cos(angle),2*math.sin(angle),8.15])
    q=np.array([4.8*math.cos(angle+.035),4.8*math.sin(angle+.035),8.15])
    spokes.append(beam(p,q,.66))
    for d in [-.14,.17]:
        spokes.append(beam(q,[9.3*math.cos(angle+d),9.3*math.sin(angle+d),8.18],.60))
spoke_mask=union([rim,hub]+spokes)
# Preserve the dark spokes where they pass in front of the red caliper.
caliper=box([-7.30,-1.75,7.12],[-5.0,4.15,7.96])-spoke_mask
wr,wr_remain=wheel.split(caliper)
# A single inset radial material boundary keeps the dark rim/disc/spokes
# continuous, without thin leftover tyre-colored slivers on simplified spokes.
wg,wb=wr_remain.split(cylinder(9.88,4.0,[0,0,8.7],n=160))
wheel_colors={'black':wb,'dark_grey':wg,'red':wr}

def hashfile(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def export_and_validate(prefix, pieces, original):
    result={'files':{},'pairwise_overlap_mm3':{},'units':'mm'}
    imported=[]
    for name,part in pieces.items():
        path=OUT/f'{prefix}_{name}.stl'
        m=meshof(part)
        print(prefix,name,'manifold_volume',part.volume(),'mesh_volume',m.volume,flush=True)
        m.export(path,file_type='stl_ascii')
        r=trimesh.load_mesh(path,process=True)
        rs=solid(r)
        imported.append((name,rs))
        result['files'][name]={'path':str(path.relative_to(ROOT)),'sha256':hashfile(path),'triangles':len(r.faces),'volume_mm3':float(rs.volume()),'watertight':bool(r.is_watertight),'winding_consistent':bool(r.is_winding_consistent),'positive_volume':bool(r.volume>0),'connected_solids':len(rs.decompose()),'bounds_mm':r.bounds.tolist()}
        if not r.is_watertight or not r.is_winding_consistent or r.volume<=0:
            raise ValueError(f'{path.name} exported solid failed validation')
    for (an,a),(bn,b) in combinations(imported,2):
        vol=abs((a^b).volume())
        result['pairwise_overlap_mm3'][an+' / '+bn]=vol
        if vol>.02:raise ValueError(f'Color overlap {an}/{bn}: {vol}')
    merged=union([a for _,a in imported])
    missing=abs((original-merged).volume())
    added=abs((merged-original).volume())
    result.update({'original_volume_mm3':original.volume(),'union_volume_mm3':merged.volume(),'missing_volume_mm3':missing,'added_volume_mm3':added,'max_union_difference_tolerance_mm3':.02,'outer_dimensions_mm':meshof(merged).extents.tolist()})
    if missing>.02 or added>.02:raise ValueError(f'Reconstruction difference missing={missing} added={added}')
    result['status']='PASS'
    return result

print('Validating exported body volumes',flush=True)
body_result=export_and_validate('body',body_colors,body_print)
print('Validating exported wheel volumes',flush=True)
wheel_result=export_and_validate('wheel',wheel_colors,wheel)

NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)
def tag(t):return '{'+NS+'}'+t
def make_3mf(name,pieces):
    model=ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    ET.SubElement(model,tag('metadata'),{'name':'Title'}).text=f'Mustang gift — {name} color volumes'
    ET.SubElement(model,tag('metadata'),{'name':'Description'}).text='Printer-neutral aligned material parts. Assign each named part to its matching filament in your slicer; no printer profile or G-code included.'
    ET.SubElement(model,tag('metadata'),{'name':'Copyright'}).text='Body adapted from SadPepe, https://www.thingiverse.com/thing:3192801, CC BY-NC 4.0. Wheel geometry independently generated.'
    resources=ET.SubElement(model,tag('resources'))
    mats=ET.SubElement(resources,tag('basematerials'),{'id':'1'})
    for color in PALETTE:
        ET.SubElement(mats,tag('base'),{'name':color.replace('_',' ').upper(),'displaycolor':PALETTE[color]+'FF'})
    ids=[]
    for object_id,(color,part) in enumerate(pieces.items(),start=2):
        ids.append(object_id)
        obj=ET.SubElement(resources,tag('object'),{'id':str(object_id),'type':'model','name':name.upper()+' — '+color.replace('_',' ').upper(),'pid':'1','pindex':str(list(PALETTE).index(color))})
        m=meshof(part)
        mesh=ET.SubElement(obj,tag('mesh'));verts=ET.SubElement(mesh,tag('vertices'))
        for v in m.vertices:
            ET.SubElement(verts,tag('vertex'),dict(zip(('x','y','z'),[f'{x:.9g}' for x in v])))
        faces=ET.SubElement(mesh,tag('triangles'))
        for f in m.faces:
            ET.SubElement(faces,tag('triangle'),dict(zip(('v1','v2','v3'),map(str,f))))
    parent_id=max(ids)+1
    parent=ET.SubElement(resources,tag('object'),{'id':str(parent_id),'type':'model','name':name.upper()+' — KEEP COLOR PARTS GROUPED'})
    components=ET.SubElement(parent,tag('components'))
    for i in ids:ET.SubElement(components,tag('component'),{'objectid':str(i)})
    build=ET.SubElement(model,tag('build'));ET.SubElement(build,tag('item'),{'objectid':str(parent_id)})
    content_types='<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    relationships='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    path=OUT/f'{name}_color_parts.3mf'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',content_types)
        z.writestr('_rels/.rels',relationships)
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
    from repair_multicolor_3mf import ensure_multipart
    ensure_multipart(path)
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:raise ValueError('3MF ZIP CRC failed')
        ET.fromstring(z.read('3D/3dmodel.model'))
    return str(path.relative_to(ROOT))

report={'status':'GEOMETRY_CHECKS_PASS','palette':PALETTE,'inputs_sha256':{str(p.relative_to(ROOT)):hashfile(p) for p in [body_path,wheel_path,source_path]},'body':body_result,'wheel':wheel_result,'3mf_files':[make_3mf('body',body_colors),make_3mf('wheel',wheel_colors)],'printer_model':'UNKNOWN — color capability also unconfirmed','slicer_profile':'NOT CONFIGURED','physical_sample':'NOT PRINTED','printing_note':'Each color STL contains aligned material volumes and must remain grouped with the other colors. Do not auto-arrange colors independently. The 3MF packages include PrusaSlicer named-volume metadata and standard display colors, not filament assignments. Grouping was tested in PrusaSlicer 2.9.6; other slicers may require the grouped STL fallback.'}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
(OUT/'README.md').write_text('''# Four-color Mustang gift files

The outer geometry matches the validated 160 mm body and one fixed wheel. These
files contain real, closed color volumes for **white, black, red and dark grey**.

## Import checked in PrusaSlicer 2.9.6

The 3MF files include named-volume metadata tested with PrusaSlicer 2.9.6.
Other slicers may require the grouped STL fallback below. The technician must
assign filament manually; PrusaSlicer does not retain the standard display colors.

1. Open `body_color_parts.3mf` in PrusaSlicer. Keep it as one object with
   three material parts. It should measure **160 x 69.49 x 41.14 mm**.
2. Assign WHITE to white filament, BLACK to black, and RED to red.
3. Open `wheel_color_parts.3mf`. Keep the three wheel color parts grouped.
   Assign BLACK, DARK GREY and RED. One wheel is **23.30 x 23.30 x 9.00 mm**.
4. Print **four copies** of the grouped wheel, all visible faces upward.
5. Body orientation: upright, flat hidden underside on the bed. Wheel orientation:
   flat back on the bed, visible spoke face up. Configure supports and material
   changes using the actual college machine profile.

## If the slicer does not preserve 3MF material parts

Import all three `body_*.stl` files together as **one object with multiple parts**,
then assign each named part its filament. Do the same for the three `wheel_*.stl`
files. All body parts share one coordinate system; all wheel parts share another.
**Do not center, drop or arrange individual colors separately.** Only place the
whole grouped body or wheel on the bed. Some color volumes intentionally start
above z=0 and are supported by other colors below them.

## Appearance and scope

- White body; black windows, mirrors, rear spoiler, vents, grille, skirts, smoked
  headlamp regions and lower side stripes with three diagonal white breaks.
- Six red rear lamp bars; black tyres; dark grey wheel discs, rims and spokes;
  red caliper relief. All detail is simplified for this 160 mm birthday model.
- There is no separate silver filament. Dark grey is used for the wheel metal.
- Colors partition the existing solid; they do not add stickers or protrusions.
- Small badge strokes and caliper areas may be merged or omitted by a particular
  nozzle/profile. Inspect actual sliced layers, then test one wheel and the
  existing `print/06_detail_test_1to1.stl` before committing to the full body.

## Checked and still pending

The exported color solids pass closed-solid, positive-volume and consistent-face
checks. Pairwise overlap and combined shape reproduction are recorded in
`validation.json`. A real PrusaSlicer 2.9.6 import/export check retained one
grouped object with three named volumes for each 3MF, with dimensions and color
region positions preserved. See [the import audit](../validation/multicolor_import/README.md).
Other slicers have not been tested. Manual filament assignments remain required.
**The college printer model, filament assignments, actual sliced layers and a
physical sample remain to be checked. These packages contain no printer G-code.**

These color files are material regions for a multicolor print; do not print them
as separate loose pieces for gluing. Only the complete body and the four complete
wheels are the five physical gift pieces.

## Attribution

Body adapted from “Ford Mustang GT 2018” by SadPepe:
https://www.thingiverse.com/thing:3192801 — CC BY-NC 4.0,
https://creativecommons.org/licenses/by-nc/4.0/ . Changes include size, repair,
reinforcement, fixed-wheel attachment pads, hood, mirrors, spoiler and color
partitions. Wheel geometry was independently created. Original source records
are in `../reference_assets/`. Personal, non-commercial birthday gift use only.
''',encoding='utf-8')
print('MULTICOLOR_COMPLETE',json.dumps({'body_volume_error':body_result['missing_volume_mm3']+body_result['added_volume_mm3'],'wheel_volume_error':wheel_result['missing_volume_mm3']+wheel_result['added_volume_mm3'],'3mf':report['3mf_files']}),flush=True)
