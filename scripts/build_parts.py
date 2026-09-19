"""Millimetre geometry for the fixed-wheel Mustang gift.

The body is a repaired/adapted SadPepe Mustang (CC BY-NC 4.0), see build_body.py.
Wheels, spoiler, mirrors, splitter, exhaust tips, grille recess, pony badge, rear plate
and the coupon are generated here from scripts/geometry.py. Run after build_body.py.
Outputs work/body_assembled.stl, work/wheel_master.stl, print/*.stl, work/manifest.json.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
import geometry as G
from geometry import box, cylinder, union, manifold, meshof, hull

ROOT = G.ROOT
OUT = ROOT / 'print'; OUT.mkdir(exist_ok=True)
WORK = ROOT / 'work'

print('load clean body', flush=True)
base = trimesh.load_mesh(WORK / 'body_clean.stl')
base = max(base.split(only_watertight=False, repair=False), key=lambda p: abs(p.volume))

base = G.fit_to_photo(base)   # photo-derived roof/deck correction, see geometry.fit_drop

def surface_sampler(mesh):
    """deck_z(x, y): top-surface height of the mesh by a downward ray."""
    def deck_z(x, y):
        loc, _, _ = mesh.ray.intersects_location([[x, y, 100.0]], [[0, 0, -1.0]], multiple_hits=False)
        return float(loc[:, 2].max()) if len(loc) else 30.0
    return deck_z

def nose_outline(mesh, z=10.0):
    """Plan outline (x, y) of the front bumper at height z, from rays towards +X."""
    ys = np.linspace(-27.5, 27.5, 23)
    origins = np.array([[-100.0, y, z] for y in ys]); dirs = np.tile([1.0, 0, 0], (len(ys), 1))
    loc, idx, _ = mesh.ray.intersects_location(origins, dirs, multiple_hits=False)
    pts = np.full((len(ys), 2), np.nan)
    for l, i in zip(loc, idx): pts[i] = [l[0], l[1]]
    return pts[~np.isnan(pts[:, 0])]

deck_z = surface_sampler(base)
body = manifold(base)
additions = [body, box([130, 37, 3.4], [0, 0, 7.7])]

def glass_surface(mesh, xs, half_width):
    """Smooth replacement skin for a glazed area: the source's windscreen and rear
    glass are lumpy, so their top surface is sampled on a grid, fitted with a low-order
    polynomial (cubic along the car, quartic and symmetric across it) and rebuilt as a
    2.5 mm thick slab that sits 0.1 mm above the mean skin. half_width(x) gives the
    sampled span across the car at each x."""
    ny = 29
    xs = np.asarray(xs, float)
    grid = np.array([[x, y] for x in xs for y in np.linspace(-half_width(x), half_width(x), ny)])
    origins = np.c_[grid, np.full(len(grid), 100.0)]
    loc, idx, _ = mesh.ray.intersects_location(origins, np.tile([0, 0, -1.0], (len(grid), 1)), multiple_hits=False)
    z = np.full(len(grid), np.nan); z[idx] = loc[:, 2]
    ok = ~np.isnan(z)
    x, y = grid[:, 0] - xs.mean(), grid[:, 1]
    A = np.c_[np.ones(len(grid)), x, x ** 2, x ** 3, y ** 2, x * y ** 2, y ** 4]
    coef = np.linalg.lstsq(A[ok], z[ok], rcond=None)[0]
    top = A @ coef + 0.1
    resid = np.abs(top[ok] - 0.1 - z[ok]); print(f'  glass fit x {xs[0]:.0f}..{xs[-1]:.0f}: mean |resid| {resid.mean():.3f} max {resid.max():.3f} mm')
    nx = len(xs); vid = lambda i, j, bottom: bottom * nx * ny + i * ny + j
    verts = np.vstack([np.c_[grid, top], np.c_[grid, top - 2.5]])
    faces = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            a, b, c, d = vid(i, j, 0), vid(i + 1, j, 0), vid(i + 1, j + 1, 0), vid(i, j + 1, 0)
            faces += [[a, b, c], [a, c, d]]
            a, b, c, d = vid(i, j, 1), vid(i + 1, j, 1), vid(i + 1, j + 1, 1), vid(i, j + 1, 1)
            faces += [[a, c, b], [a, d, c]]
    for i in range(nx - 1):            # side walls along x (j = 0 and j = ny-1)
        for j, flip in ((0, True), (ny - 1, False)):
            a, b, c, d = vid(i, j, 0), vid(i + 1, j, 0), vid(i + 1, j, 1), vid(i, j, 1)
            faces += [[a, c, b], [a, d, c]] if flip else [[a, b, c], [a, c, d]]
    for j in range(ny - 1):            # end walls (i = 0 and i = nx-1)
        for i, flip in ((0, False), (nx - 1, True)):
            a, b, c, d = vid(i, j, 0), vid(i, j + 1, 0), vid(i, j + 1, 1), vid(i, j, 1)
            faces += [[a, c, b], [a, d, c]] if flip else [[a, b, c], [a, c, d]]
    m = trimesh.Trimesh(verts, faces); m.fix_normals()
    return manifold(m)

additions.append(glass_surface(base, np.arange(-23.5, -5.5, 0.6), lambda x: 20.4 + (24.0 - 20.4) * (-5.1 - x) / 19.4 - 0.6))   # windscreen
additions.append(glass_surface(base, np.arange(31.0, 57.5, 0.6), lambda x: 18.0))    # rear glass

# Replace the source hood's overlapping micro-surfaces with its clean convex envelope,
# preserving its long tapered outline; two solid-backed vents are cut below.
hood = G.source_shells()[6]
hv = hood.vertices.copy(); hv[:, 2] += .2
hc = trimesh.convex.convex_hull(np.vstack([hv, hv - [0, 0, 2.5]]))
additions.append(manifold(hc))

for x in G.WHEEL_X:                       # glue pads for the wheels
    for side in [-1, 1]:
        additions.append(cylinder(5.6, 5.8, [x, side * 19.9, G.WHEEL_R], axis=[0, 1, 0]))
for side in [-1, 1]:
    additions.append(G.mirror(side))
    additions.extend(G.badge_5_0(side))
additions.append(G.spoiler_blade(deck_z))
additions.append(G.shark_fin(base_z=deck_z(G.FIN_X, 0)))
additions.append(G.splitter(nose_outline(base)))
additions.append(G.plate_solid())          # rear plate in the bumper recess
plate_text = G.plate_text_solid()          # None until geometry.PLATE_TEXT is set
if plate_text is not None: additions.append(plate_text)
body = union(additions)

for cutter in G.grille_cutters():         # recess the grille and lower intake
    body = body - cutter
# Recess the headlamps, the bumper corner slots and the rear diffuser panel by ~0.5 mm
# so their outlines print as crisp steps even on a single-colour printer.
for s in (-1, 1):
    body = body - G.skin_recess(body, G.prism(G.headlamp_outline(s), [1, 2], -90, -50), 0.45, s)
    body = body - G.skin_recess(body, G.prism(G.corner_slot_outline(s), [1, 2], -90, -62), 0.5, s)
body = body - (G.box_lohi([72, -26, 0], [90, 26, 13.8]) - body.translate([-0.5, 0, 0]))
body = body + union(G.exhaust_tips())     # tips stand proud of the recessed diffuser
body = body + G.pony_emblem()             # then stand the pony proud of the recess floor
for y in [-12.6, 12.6]:                   # hood vents, cut from the actual hull height
    hits, _, _ = hc.ray.intersects_location([[-63.7, y, 80]], [[0, 0, -1]])
    surface = float(hits[:, 2].max())
    body = body - box([6.4, 5.6, 2.0], [-63.7, y, surface + .55])
# A common flat underside and the exact 160 mm longitudinal envelope.
body = body ^ box([160, 100, 80], [0, 0, 46])
body = body.simplify(.03)
# Booleans on the lumpy source skin can leave dust-sized detached slivers; the
# printable body must be one solid, so keep the main solid and report what was dropped.
islands = sorted(body.decompose(), key=lambda m: -m.volume())
dropped = [round(m.volume(), 4) for m in islands[1:]]
if any(v > 0.5 for v in dropped):
    raise ValueError(f'body is not one solid; detached volumes mm3: {dropped}')
if dropped: print('dropped sliver islands (mm3):', dropped, flush=True)
body = islands[0]
bodymesh = meshof(body)
# Normalize X by a few microns after repair so the delivered length is exact.
bodymesh.vertices[:, 0] = (bodymesh.vertices[:, 0] - bodymesh.bounds[:, 0].mean()) * (160 / bodymesh.extents[0])
bodymesh = meshof(manifold(bodymesh))
bodymesh.export(WORK / 'body_assembled.stl')
bodyprint = bodymesh.copy(); bodyprint.apply_translation([0, 0, -6])
bodyprint.export(OUT / '01_body_160mm.stl')
print('body done', len(bodymesh.faces), bodymesh.extents.tolist(), 'watertight', bodymesh.is_watertight, flush=True)

wm = meshof(G.wheel_solid())
wm.export(WORK / 'wheel_master.stl')
labels = ['02_wheel_front_left.stl', '03_wheel_front_right.stl', '04_wheel_rear_left.stl', '05_wheel_rear_right.stl']
for filename in labels: wm.export(OUT / filename)
print('wheel done', len(wm.faces), wm.extents.tolist(), 'watertight', wm.is_watertight, flush=True)

# Full-size detail coupon: mirror-style 2.5 mm stalk, spoke-width plates and grooves.
coupon = union([box([30, 20, 2.5], [0, 0, 1.25]), box([4, 5, 7], [1, 0, 5.5]), G.beam([1, 0, 8.6], [9, 0, 9.4], 1.25),
                G.ellipsoid([10, 0, 10.1], [7.6, 5, 3.6]),
                box([1.0, 8, 2.0], [-12, 5, 3.4]), box([1.45, 8, 2.0], [-9.5, 5, 3.4])])
for x, w in [(-10, .6), (-7, .8), (-4, 1.0)]: coupon = coupon - box([w, 12, 1], [x, -4, 2.6])
coupon = meshof(coupon.simplify(.01)); coupon.export(OUT / '06_detail_test_1to1.stl')

manifest = {
    'units': 'mm', 'length_mm': 160, 'body_print_origin_offset': [0, 0, 6],
    'wheel_radius_mm': G.WHEEL_R, 'wheel_inner_face_y_mm': G.WHEEL_INNER,
    'wheel_center_x_mm': G.WHEEL_X, 'wheel_center_z_mm': G.WHEEL_R,
    'body_dimensions_mm': bodyprint.extents.tolist(), 'wheel_dimensions_mm': wm.extents.tolist(),
    'assembly_dimensions_mm': [160, max(bodymesh.extents[1], 2 * (G.WHEEL_INNER + wm.bounds[1, 2])), float(bodymesh.bounds[1, 2])],
    'body_ground_clearance_mm': 6.0,
    'wheel_attachment': 'Flat 11.2 mm diameter pads at y=+/-22.8 mm; wheel backs glue directly to these. All four wheels are identical; the red caliper is rotated toward the rear when glued.',
    'files': ['01_body_160mm.stl'] + labels + ['06_detail_test_1to1.stl'],
    'features': ['recessed hexagonal grille with silver running-pony badge', 'recessed slim headlamps with tri-bar DRL and amber markers', 'seven Y-spoke wheels with red calipers',
                 'source-shape mirror heads on blade stalks', 'low black lip spoiler', 'chin splitter', 'recessed bumper corner slots', 'recessed rear diffuser with quad exhaust tips',
                 'shark-fin antenna', '5.0 fender badges (mirrored per side so both read 5.0)', 'twin hood vents', 'tri-bar tail lights and black rear panel (paint regions)',
                 'RTR centre-cap monogram and chrome ring on each wheel', 'rear number plate' + (f' lettered "{G.PLATE_TEXT}"' if G.PLATE_TEXT.strip() else ' (blank until the registration is supplied)')],
    'plate_text': G.PLATE_TEXT,
    'plate_mm': {'width': 2 * G.PLATE_HALF_W, 'height': G.PLATE_Z1 - G.PLATE_Z0, 'face_x': G.PLATE_FACE_X},
    'physical_print_test': 'NOT RUN - requires college printer',
    'college_printer_profile': 'UNKNOWN',
    'source_body': {'author': 'SadPepe', 'url': 'https://www.thingiverse.com/thing:3192801', 'license': 'CC BY-NC 4.0'},
    'source_wheel_geometry_used': False,
    'source_emblem_shell_used': True,
}
(WORK / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('PARTS_COMPLETE', json.dumps({k: manifest[k] for k in ['body_dimensions_mm', 'wheel_dimensions_mm', 'assembly_dimensions_mm']}), flush=True)
