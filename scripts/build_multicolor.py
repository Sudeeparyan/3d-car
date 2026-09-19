"""Group the gift solids into real, non-overlapping filament volumes for a multicolour printer.

The colour regions are exactly those of regions.py (the same masks that paint the
preview OBJ), merged by filament: the body becomes white / black / red, the wheel
black / dark grey / red / white (RTR cap logo). Original print/ meshes are never modified. Outputs
multicolor/*.stl, multicolor/*_color_parts.3mf, multicolor/validation.json.
Run after build_parts.py. Source body attribution stays CC BY-NC 4.0.
"""
from pathlib import Path
from itertools import combinations
import hashlib, json, zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import manifold3d as md
import geometry as G
import regions as R

ROOT = G.ROOT
OUT = ROOT / 'multicolor'
OUT.mkdir(exist_ok=True)
PALETTE = {'white': '#F3F2EB', 'black': '#16191D', 'red': '#BF1725', 'dark_grey': '#4F545A'}
NAMES = {R.WHITE: 'white', R.BLACK: 'black', R.RED: 'red', R.GUNMETAL: 'gunmetal', R.BACKING: 'brake backing', R.SILVER: 'silver', R.AMBER: 'amber', R.GLOSS: 'gloss black badges'}

def solid64(mesh):
    """Exact (float64) manifold of an exported STL, for the re-import checks."""
    mesh.merge_vertices(); mesh.remove_unreferenced_vertices(); mesh.fix_normals(multibody=False)
    result = md.Manifold(md.Mesh64(np.asarray(mesh.vertices, dtype=np.float64), np.asarray(mesh.faces, dtype=np.uint64)))
    if result.status() != md.Error.NoError:
        raise ValueError(f'Manifold import: {result.status()}')
    return result

def masks_of(regions, filament_of, filament):
    return [mask for material, mask in regions if filament_of[material] == filament]

def names_of(regions, filament_of, filament):
    return sorted({NAMES[material] for material, _ in regions if filament_of[material] == filament})

body_path, wheel_path = ROOT / 'work/body_assembled.stl', ROOT / 'work/wheel_master.stl'
body_mesh = trimesh.load_mesh(body_path)
R.set_deck_sampler(lambda x, y: (lambda loc: float(loc[:, 2].max()) if len(loc) else 30.0)(
    body_mesh.ray.intersects_location([[x, y, 100.0]], [[0, 0, -1.0]], multiple_hits=False)[0]))
print('Partitioning body colours', flush=True)
body = G.manifold(body_mesh)
regions, default = R.body_regions()
# Paint priority is red > amber > silver > gloss black > DRL white > black. The white
# details (DRL slashes, exhaust tips) sit inside black regions, so the black filament
# mask is the black/amber/gloss masks with those details cut out; the details then
# fall into the default white piece. The gloss-black pony and 5.0 badges print black. Splitting with merged masks, rather
# than unioning split pieces, leaves no coincident internal faces in the exports.
white_details = G.union(masks_of(regions, R.BODY_FILAMENT, 'white'))
body_masks = [('red', G.union(masks_of(regions, R.BODY_FILAMENT, 'red'))),
              ('black', G.union(masks_of(regions, R.BODY_FILAMENT, 'black')) - white_details)]
body_colors = {name: piece.translate((0, 0, -6)) for name, piece in R.partition(body, body_masks, 'white')}  # print origin: underside on z=0
body_print = body.translate((0, 0, -6))
body_regions_by_filament = {f: names_of(regions, R.BODY_FILAMENT, f) for f in ('white', 'black', 'red')}
body_regions_by_filament['white'].append('body (remainder)')

print('Partitioning wheel colours', flush=True)
wheel = G.manifold(trimesh.load_mesh(wheel_path))
wregions, wdefault = R.wheel_regions()
# Caliper first, then the white RTR cap monogram and ring; the black centre cap is cut
# out of the grey face/floor mask and joins the default black (tyre) piece as its own island.
cap = G.union(masks_of(wregions, R.WHEEL_FILAMENT, 'black'))
wheel_masks = [('red', G.union(masks_of(wregions, R.WHEEL_FILAMENT, 'red'))),
               ('white', G.union(masks_of(wregions, R.WHEEL_FILAMENT, 'white'))),
               ('dark_grey', G.union(masks_of(wregions, R.WHEEL_FILAMENT, 'dark_grey')) - cap)]
wheel_colors = dict(R.partition(wheel, wheel_masks, 'black'))
wheel_regions_by_filament = {f: names_of(wregions, R.WHEEL_FILAMENT, f) for f in ('black', 'dark_grey', 'red', 'white')}
wheel_regions_by_filament['black'].append('tyre (remainder)')

def hashfile(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def export_and_validate(prefix, pieces, original):
    result = {'files': {}, 'pairwise_overlap_mm3': {}, 'units': 'mm'}
    imported = []
    for name, part in pieces.items():
        path = OUT / f'{prefix}_{name}.stl'
        # Collapse the collinear / zero-area triangles a boolean split leaves behind
        # (they become T-junctions once an STL reader welds vertices); 1 um tolerance.
        part = pieces[name] = part.simplify(0.001)
        m = G.meshof(part)
        m.export(path, file_type='stl_ascii')
        r = trimesh.load_mesh(path, process=True)
        rs = solid64(r)
        imported.append((name, rs))
        result['files'][name] = {'path': str(path.relative_to(ROOT)), 'sha256': hashfile(path), 'triangles': len(r.faces), 'volume_mm3': float(rs.volume()),
                                 'watertight': bool(r.is_watertight), 'winding_consistent': bool(r.is_winding_consistent), 'positive_volume': bool(r.volume > 0),
                                 'connected_solids': len(rs.decompose()), 'bounds_mm': r.bounds.tolist()}
        print(f'  {prefix}_{name}: {len(r.faces)} triangles, {rs.volume():.1f} mm3, {len(rs.decompose())} islands', flush=True)
        if not r.is_watertight or not r.is_winding_consistent or r.volume <= 0:
            raise ValueError(f'{path.name} exported solid failed validation')
    for (an, a), (bn, b) in combinations(imported, 2):
        vol = abs((a ^ b).volume())
        result['pairwise_overlap_mm3'][an + ' / ' + bn] = vol
        if vol > .02: raise ValueError(f'Colour overlap {an}/{bn}: {vol}')
    merged = G.union([a for _, a in imported])
    missing = abs((original - merged).volume()); added = abs((merged - original).volume())
    result.update({'original_volume_mm3': original.volume(), 'union_volume_mm3': merged.volume(), 'missing_volume_mm3': missing, 'added_volume_mm3': added,
                   'max_union_difference_tolerance_mm3': .1, 'outer_dimensions_mm': G.meshof(merged).extents.tolist()})
    # 0.1 mm3 over the whole part (4e-7 of the body) covers the 1 um sliver clean-up; a
    # single 0.4 mm extrusion segment 1 mm long is 0.08 mm3, so nothing printable is lost.
    if missing > .1 or added > .1: raise ValueError(f'Reconstruction difference missing={missing} added={added}')
    result['status'] = 'PASS'
    return result

print('Validating exported body volumes', flush=True)
body_result = export_and_validate('body', body_colors, body_print)
print('Validating exported wheel volumes', flush=True)
wheel_result = export_and_validate('wheel', wheel_colors, wheel)

NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('', NS)
def tag(t): return '{' + NS + '}' + t
def make_3mf(name, pieces):
    model = ET.Element(tag('model'), {'unit': 'millimeter', '{http://www.w3.org/XML/1998/namespace}lang': 'en-US'})
    ET.SubElement(model, tag('metadata'), {'name': 'Title'}).text = f'Mustang gift - {name} colour volumes'
    ET.SubElement(model, tag('metadata'), {'name': 'Description'}).text = 'Printer-neutral aligned material parts. Assign each named part to its matching filament in your slicer; no printer profile or G-code included.'
    ET.SubElement(model, tag('metadata'), {'name': 'Copyright'}).text = 'Body adapted from SadPepe, https://www.thingiverse.com/thing:3192801, CC BY-NC 4.0. Wheel geometry independently generated.'
    resources = ET.SubElement(model, tag('resources'))
    mats = ET.SubElement(resources, tag('basematerials'), {'id': '1'})
    for color in PALETTE:
        ET.SubElement(mats, tag('base'), {'name': color.replace('_', ' ').upper(), 'displaycolor': PALETTE[color] + 'FF'})
    ids = []
    for object_id, (color, part) in enumerate(pieces.items(), start=2):
        ids.append(object_id)
        obj = ET.SubElement(resources, tag('object'), {'id': str(object_id), 'type': 'model', 'name': name.upper() + ' - ' + color.replace('_', ' ').upper(), 'pid': '1', 'pindex': str(list(PALETTE).index(color))})
        m = G.meshof(part)
        mesh = ET.SubElement(obj, tag('mesh')); verts = ET.SubElement(mesh, tag('vertices'))
        for v in m.vertices:
            ET.SubElement(verts, tag('vertex'), dict(zip(('x', 'y', 'z'), [f'{x:.9g}' for x in v])))
        faces = ET.SubElement(mesh, tag('triangles'))
        for f in m.faces:
            ET.SubElement(faces, tag('triangle'), dict(zip(('v1', 'v2', 'v3'), map(str, f))))
    parent_id = max(ids) + 1
    parent = ET.SubElement(resources, tag('object'), {'id': str(parent_id), 'type': 'model', 'name': name.upper() + ' - KEEP COLOR PARTS GROUPED'})
    components = ET.SubElement(parent, tag('components'))
    for i in ids: ET.SubElement(components, tag('component'), {'objectid': str(i)})
    build = ET.SubElement(model, tag('build')); ET.SubElement(build, tag('item'), {'objectid': str(parent_id)})
    content_types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    relationships = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    path = OUT / f'{name}_color_parts.3mf'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', relationships)
        z.writestr('3D/3dmodel.model', ET.tostring(model, encoding='utf-8', xml_declaration=True))
    from repair_multicolor_3mf import ensure_multipart
    ensure_multipart(path)
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None: raise ValueError('3MF ZIP CRC failed')
        ET.fromstring(z.read('3D/3dmodel.model'))
    return str(path.relative_to(ROOT))

dims = lambda r: ' x '.join(f'{d:.2f}' for d in r['outer_dimensions_mm'])
plate_note = f' ("{G.PLATE_TEXT}")' if G.PLATE_TEXT.strip() else ' (the plate is blank until the registration is set in scripts/geometry.py)'
report = {'status': 'GEOMETRY_CHECKS_PASS', 'palette': PALETTE,
          'inputs_sha256': {str(p.relative_to(ROOT)): hashfile(p) for p in [body_path, wheel_path, G.SOURCE]},
          'body': body_result, 'wheel': wheel_result,
          'body_regions_by_filament': body_regions_by_filament, 'wheel_regions_by_filament': wheel_regions_by_filament,
          '3mf_files': [make_3mf('body', body_colors), make_3mf('wheel', wheel_colors)],
          'printer_model': 'UNKNOWN - colour capability also unconfirmed', 'slicer_profile': 'NOT CONFIGURED', 'physical_sample': 'NOT PRINTED',
          'printing_note': 'Each colour STL contains aligned material volumes and must remain grouped with the other colours. Do not auto-arrange colours independently. The 3MF packages include PrusaSlicer named-volume metadata and standard display colours, not filament assignments. Grouping of an earlier revision was tested in PrusaSlicer 2.9.6; other slicers may require the grouped STL fallback.'}
(OUT / 'validation.json').write_text(json.dumps(report, indent=2))
(OUT / 'parts_manifest.json').write_text(json.dumps({
    'units': 'millimetres', 'palette': PALETTE, 'printer_model': 'UNKNOWN', 'multicolor_capability': 'UNCONFIRMED',
    'physical_objects': [
        {'name': 'Body', 'quantity': 1, 'preferred_file': 'body_color_parts.3mf', 'parts': {c: f'body_{c}.stl' for c in body_colors},
         'regions_by_filament': body_regions_by_filament, 'orientation': 'upright, hidden flat underside on bed',
         'dimensions_mm': body_result['outer_dimensions_mm'], 'assembly_offset_mm': [0, 0, 6]},
        {'name': 'Wheel', 'quantity': 4, 'preferred_file': 'wheel_color_parts.3mf', 'parts': {c: f'wheel_{c}.stl' for c in wheel_colors},
         'regions_by_filament': wheel_regions_by_filament, 'orientation': 'flat back on bed, visible face upward',
         'dimensions_mm': wheel_result['outer_dimensions_mm']}],
    'instructions': 'Keep the material regions within each physical object in their original shared coordinates. Assign filaments manually; standard 3MF colours are not machine settings. Do not print the material regions as loose pieces.'}, indent=2))
(OUT / 'README.md').write_text(f'''# Four-colour Mustang gift files

The outer geometry is exactly the validated 160 mm body and one fixed wheel from
`print/`. These files split each into real, closed colour volumes for **white,
black, red and dark grey** filament. The regions are the same ones that colour the
preview renders, so what you see in `previews/` is what the printer lays down.

## Import (checked in PrusaSlicer 2.9.6 on an earlier revision of the same files)

1. Open `body_color_parts.3mf`. Keep it as **one object with three material
   parts**. It should measure **{dims(body_result)} mm**.
2. Assign WHITE to white filament, BLACK to black, RED to red.
3. Open `wheel_color_parts.3mf`. Keep the four wheel colour parts grouped and
   assign BLACK, DARK GREY, RED and WHITE (the tiny RTR cap logo). One wheel is
   **{dims(wheel_result)} mm**.
4. Print **four copies** of the grouped wheel, spoke face up.
5. Body orientation: upright, flat hidden underside on the bed. Configure supports
   and the colour-change purge using the actual college machine profile.

## If the slicer does not preserve 3MF material parts

Import all three `body_*.stl` files together as **one object with multiple parts**,
then assign each named part its filament. Do the same for the four `wheel_*.stl`
files. All body parts share one coordinate system; all wheel parts share another.
**Do not centre, drop or arrange individual colours separately.** Only place the
whole grouped body or wheel on the bed. Some colour volumes intentionally start
above z=0 and are supported by other colours below them.

## What is in each colour

- **White body**: paint, hood, roof, the rear number plate and the three LED
  daytime-running slashes in each headlamp.
- **Black body**: windscreen, door / quarter glass and B-pillars, rear glass,
  mirrors, lip spoiler, shark-fin antenna, hood vents, recessed grille and lower
  intake, the running-pony grille badge (gloss black on the car; it still stands
  1.4 mm proud of the grille floor), smoked headlamps with their amber corner
  markers, bumper corner slots, rear panel and lamp surrounds, rear diffuser,
  splitter, skirts, the lower door stripe (four short hash marks then a solid band
  to the rear wheel), the "5.0" fender badges and the plate lettering{plate_note}.
- **Red body**: the six tri-bar tail-light bars.
- **Wheel**: black tyre and centre cap, dark grey rim, seven Y-spokes, hub and
  brake backing, red caliper visible between the spokes, and the **white RTR
  monogram and ring on the centre cap** (chrome on the real RTR Aero 7 wheels;
  2.6 mm across with 0.25 mm strokes, so it needs a fine nozzle or it will merge
  into a raised dot - a silver paint-pen dab on the relief is the fallback).
- The exhaust tips are silver in the preview and print white here.

Colours partition the existing solid; they do not add stickers or protrusions.
Small features (badge strokes, DRL slashes, the pony) may merge or drop out with a
coarse nozzle or profile: inspect the sliced layers, then test one wheel and
`print/06_detail_test_1to1.stl` before committing to the full body.

## Checked and still pending

The exported colour solids pass closed-solid, positive-volume and consistent-face
checks; pairwise overlap (tolerance 0.02 mm3) and reproduction of the original shape
(tolerance 0.1 mm3) are recorded in `validation.json`. A PrusaSlicer 2.9.6 import/export audit on
the earlier revision of these files kept one grouped object with three named
volumes; the container format is unchanged, but repeat the import check on the
college machine. **The printer model, filament assignments, actual sliced layers
and a physical sample remain to be checked. No G-code is included.**

These colour files are material regions for a multicolour print; do not print them
as separate loose pieces for gluing. Only the complete body and the four complete
wheels are the five physical gift pieces.

## Attribution

Body adapted from "Ford Mustang GT 2018" by SadPepe:
https://www.thingiverse.com/thing:3192801 - CC BY-NC 4.0,
https://creativecommons.org/licenses/by-nc/4.0/ . Changes include size, repair,
smoothing, photo-matched roof/deck profile, 2018-style front fascia and lamps,
fixed-wheel attachment pads, mirrors, spoiler, badges and colour partitions. Wheel
geometry was independently created. Source records are in `../reference_assets/`.
Personal, non-commercial birthday gift use only.
''', encoding='utf-8')
print('MULTICOLOR_COMPLETE', json.dumps({'body_volume_error': body_result['missing_volume_mm3'] + body_result['added_volume_mm3'],
                                        'wheel_volume_error': wheel_result['missing_volume_mm3'] + wheel_result['added_volume_mm3'],
                                        'body_mm': body_result['outer_dimensions_mm'], 'wheel_mm': wheel_result['outer_dimensions_mm'],
                                        '3mf': report['3mf_files']}), flush=True)
