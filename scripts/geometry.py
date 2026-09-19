"""Shared solid-modelling helpers and the gift-specific feature solids (millimetres).

Used by build_parts.py (printable geometry), regions.py (colour partitions) and
build_multicolor.py, so every script works from one definition of each feature.
Coordinates: X along the car (nose at -80, tail at +80), Y across (driver side -Y),
Z up (underside at 6, wheel centres at 11.65). Wheels use a local frame: back face
on z=0, visible face up, local +x towards the nose once assembled.
"""
from pathlib import Path
import math
import numpy as np
import trimesh
import manifold3d as md
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reference_assets/thingiverse_3192801/files/mustangBodyOnly.stl'
Y_OFFSET, Z_OFFSET, SCALE = 17.805959701538086, 23.417420, 160 / 140
WHEEL_R = 11.65
WHEEL_INNER = 22.8
WHEEL_X = [-48.4472, 42.4928]
LENGTH = 160.0

# ---------------------------------------------------------------- primitives
def manifold(mesh):
    mesh = mesh.copy()
    mesh.merge_vertices(); mesh.remove_unreferenced_vertices(); mesh.fix_normals()
    result = md.Manifold(md.Mesh(np.asarray(mesh.vertices, dtype=np.float32), np.asarray(mesh.faces, dtype=np.uint32)))
    if result.status() != md.Error.NoError:
        raise ValueError(str(result.status()))
    return result

def meshof(m):
    a = m.to_mesh()
    return trimesh.Trimesh(np.array(a.vert_properties[:, :3]), np.array(a.tri_verts), process=True)

def union(parts):
    parts = list(parts)
    return parts[0] if len(parts) == 1 else md.Manifold.batch_boolean(parts, md.OpType.Add)

def box(size, center):
    m = trimesh.creation.box(extents=size); m.apply_translation(center); return manifold(m)

def box_lohi(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return box(hi - lo, (hi + lo) / 2)

def cylinder(r, depth, center, axis=(0, 0, 1), n=96):
    m = trimesh.creation.cylinder(radius=r, height=depth, sections=n)
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], axis)); m.apply_translation(center)
    return manifold(m)

def ellipsoid(center, size):
    m = trimesh.creation.icosphere(subdivisions=3); m.apply_scale(np.array(size) / 2); m.apply_translation(center)
    return manifold(m)

def beam(a, b, r):
    a, b = np.array(a, float), np.array(b, float); v = b - a
    return cylinder(r, np.linalg.norm(v), (a + b) / 2, v) + ellipsoid(a, [r * 2] * 3) + ellipsoid(b, [r * 2] * 3)

def hull(points):
    return manifold(trimesh.convex.convex_hull(np.asarray(points, float)))

def lathe(profile, n=160):
    """Closed radial cross-section (r, z) revolved around local Z."""
    return md.CrossSection([np.array(profile, dtype=float)]).revolve(circular_segments=n)

def prism(points, axes, lo, hi):
    """Convex polygon in a coordinate plane (axes e.g. [0,2] = XZ), extruded along the third axis."""
    points = np.asarray(points, float)
    other = next(i for i in range(3) if i not in axes)
    v = np.zeros((len(points) * 2, 3))
    for k in (0, 1):
        v[k * len(points):(k + 1) * len(points), axes[0]] = points[:, 0]
        v[k * len(points):(k + 1) * len(points), axes[1]] = points[:, 1]
    v[:len(points), other] = lo; v[len(points):, other] = hi
    return hull(v)

def polygon_prism(points, axes, lo, hi):
    """Arbitrary (possibly concave) simple polygon extruded along the third axis."""
    points = np.asarray(points, float)
    x, y = points[:, 0], points[:, 1]
    if (x * np.roll(y, -1) - np.roll(x, -1) * y).sum() < 0:
        points = points[::-1]  # CrossSection needs counter-clockwise winding
    other = next(i for i in range(3) if i not in axes)
    cs = md.CrossSection([points])
    solid = cs.extrude(hi - lo)  # built in XY, extruded along +Z
    # Map local (x, y, z) -> world axes: local x -> axes[0], local y -> axes[1], local z -> other
    m = meshof(solid)
    v = np.zeros_like(m.vertices); v[:, axes[0]] = m.vertices[:, 0]; v[:, axes[1]] = m.vertices[:, 1]; v[:, other] = m.vertices[:, 2] + lo
    return manifold(trimesh.Trimesh(v, m.faces))

# ------------------------------------------------------------- source shells
_shells = None
def source_shells():
    """The 169 open panel shells of the reference body, normalised to this model's frame."""
    global _shells
    if _shells is None:
        raw = trimesh.load_mesh(SOURCE).split(only_watertight=False, repair=False)
        _shells = []
        for p in raw:
            v = p.vertices.copy(); v[:, 1] -= Y_OFFSET; v[:, 2] += Z_OFFSET; v *= SCALE
            _shells.append(trimesh.Trimesh(v, p.faces.copy(), process=False))
    return _shells

def source_prism(index, axes, lo, hi, shrink=1.0):
    """Convex outline of one source shell in a coordinate plane, extruded (used for paint regions)."""
    q = source_shells()[index].vertices[:, axes]
    h = q[ConvexHull(q).vertices]
    h = (h - h.mean(axis=0)) * shrink + h.mean(axis=0)
    return prism(h, axes, lo, hi)

# ------------------------------------------------------- photo-fit transform
def fit_drop(x, z):
    """Photo-derived shape correction (validation/likeness): aligned on the wheel centres,
    the source roof sits ~0.6 mm and its fastback/deck ~2 mm above the side photograph.
    Returns how far to lower a point: 0 ahead of the windscreen, 0.6 mm over the roof,
    2.0 mm from x=50 back, fading to nothing below the beltline (z 28)."""
    x, z = np.asarray(x, float), np.asarray(z, float)
    smooth = lambda t: (lambda u: u * u * (3 - 2 * u))(np.clip(t, 0, 1))
    drop = 0.6 * smooth((x + 25.0) / 15.0) + 1.4 * smooth((x - 10.0) / 40.0)
    return drop * np.clip((z - 28.0) / 14.0, 0, 1)

def fit_to_photo(mesh):
    v = mesh.vertices.copy(); v[:, 2] -= fit_drop(v[:, 0], v[:, 2])
    return trimesh.Trimesh(v, mesh.faces.copy(), process=False)

def fitted_xz(points):
    """Apply fit_drop to (x, z) outline points drawn in the source body frame."""
    pts = np.asarray(points, float).copy(); pts[:, 1] -= fit_drop(pts[:, 0], pts[:, 1]); return pts

# ------------------------------------------------------------- body features
def pony_emblem(grow=0.0):
    """The running-pony grille badge, lifted from the source (shell 17) and scaled to
    ~7.2 mm wide (a touch over 1:30 of the real 190 mm emblem so it reads at gift size).
    Its back is buried in the recessed grille floor; the face stands 1.4 mm proud of it.
    grow>0 gives a slightly larger copy for use as a colour mask."""
    p = source_shells()[17].copy()
    c = p.bounds.mean(axis=0)
    v = (p.vertices - c) * np.array([1.8, 1.26, 1.26]) + c
    v[:, 0] += (-78.4 - v[:, 0].min())  # face at x = -78.4, back at about -76.6
    if grow:
        c = v.mean(axis=0); v = (v - c) * (1 + grow / 3.0) + c; v[:, 0] -= grow
    return manifold(trimesh.Trimesh(v, p.faces))

GRILLE_FLOOR_X = -77.0       # recessed upper-grille floor
LOWER_GRILLE_FLOOR_X = -76.3

def grille_outline():
    """2018 GT upper grille: wide trapezoid between the headlamps, (y, z) in mm."""
    return [[-14.0, 26.3], [14.0, 26.3], [19.6, 21.0], [19.6, 18.2], [17.8, 17.6], [-17.8, 17.6], [-19.6, 18.2], [-19.6, 21.0]]

def lower_intake_outline():
    """Wide lower intake; the bumper lip below it (z 9.4-10.4) stays body colour."""
    return [[-17.5, 10.4], [17.5, 10.4], [15.5, 15.0], [-15.5, 15.0]]

def drl_bar_outline(side, y0):
    """One of the three LED daytime-running slashes at the inner end of a headlamp,
    (y, z) parallelogram leaning outboard at the top like the real '///' signature."""
    s = side
    return [[s * (y0 - 0.32), 23.4], [s * (y0 + 0.32), 23.4], [s * (y0 + 0.32 + 0.9), 25.6], [s * (y0 - 0.32 + 0.9), 25.6]]

DRL_Y = (17.3, 18.9, 20.5)

def corner_slot_outline(side):
    """Slim horizontal vent slot at each bumper corner below the headlamp, (y, z)."""
    s = side
    return [[s * 18.0, 17.0], [s * 27.0, 17.0], [s * 27.0, 18.6], [s * 18.0, 18.6]]

def skin_recess(body, window, depth, side=0):
    """Solid that, subtracted from body, recesses the front skin inside `window`
    (a YZ prism through the nose) by about `depth` mm: the window minus a copy of the
    body pushed back along the local outward direction (nose -X, plus a little
    outboard on a corner)."""
    shift = np.array([depth, -side * depth * 0.55, 0.0])
    return window - body.translate(shift)

def headlamp_outline(side):
    """Slim slanted headlamp unit rising towards the outer corner, (y, z) in mm."""
    s = side
    return [[s * 15.0, 22.7], [s * 16.2, 26.4], [s * 30.2, 27.7], [s * 29.2, 24.4]]

def grille_cutters():
    """Recess the upper grille and lower intake so they read as dark cavities even unpainted."""
    return [prism(grille_outline(), [1, 2], -90, GRILLE_FLOOR_X),
            prism(lower_intake_outline(), [1, 2], -90, LOWER_GRILLE_FLOOR_X)]

MIRROR_SHELL = {-1: 46, 1: 88}

def mirror(side, grow=0.0):
    """Mustang mirror: the head is the convex envelope of the source's own mirror
    shell (teardrop plan, flat glass face at the back, x -17..-9, z 32.4-36.8), so its
    proportions match the photographs. The source's thin blade stalk is replaced by a
    3 x 1.6 mm blade rooted in the door top for print strength."""
    s, g = side, grow
    v = source_shells()[MIRROR_SHELL[side]].vertices
    head_pts = v[s * v[:, 1] >= 29.0]
    if g:
        c = head_pts.mean(axis=0); head_pts = (head_pts - c) * (1 + g / 2.2) + c
    head = hull(head_pts)
    stalk = hull([[-17.8 - g, s * 26.6, 32.0 - g], [-14.6 + g, s * 26.6, 32.0 - g], [-17.8 - g, s * 26.6, 33.6 + g], [-14.6 + g, s * 26.6, 33.6 + g],
                  [-16.0 - g, s * (30.4 + g), 32.9 - g], [-13.2 + g, s * (30.4 + g), 32.9 - g], [-16.0 - g, s * (30.4 + g), 34.3 + g], [-13.2 + g, s * (30.4 + g), 34.3 + g]])
    return head + stalk

def side_glazing_outline():
    """Door glass + black B-pillar + quarter window as one (x, z) outline per side, in the
    photo-fitted body frame: bottom edge on the beltline, top edge on the roof rail,
    quarter window tapering to its point at x=39.5."""
    top = [[-21.2, 32.2], [-18.8, 34.5], [-14.5, 37.2], [-9.4, 39.9], [-5.6, 41.65], [-2.9, 42.56], [0.1, 43.3], [3.0, 43.75],
           [6.2, 44.0], [10.2, 44.05], [15.3, 43.7], [20.0, 43.05], [24.7, 42.3], [29.7, 41.2], [35.0, 39.8], [37.7, 39.05],
           [38.9, 38.6], [39.6, 38.1]]
    bottom = [[39.4, 37.3], [38.3, 36.0], [36.5, 34.8], [34.0, 34.0], [31.2, 33.6], [27.7, 33.3], [20.3, 32.9], [12.0, 32.6], [0.0, 32.4]]
    return fitted_xz(top + bottom)

def spoiler_leading_edge(y):
    """Lip spoiler plan shape (from the side photograph): the centre section starts
    at x=62.5 behind the rear glass, the ends sweep forward along the quarter-panel
    shoulders to x=47."""
    t = np.clip((abs(y) - 16.0) / 8.0, 0, 1)
    return 62.5 - 15.5 * (t * t * (3 - 2 * t))

def spoiler_blade(deck_z, grow=0.0):
    """Low black lip spoiler: a 1.0 mm blade lying on the rear deck from its leading
    edge (spoiler_leading_edge) to a trailing edge at x=71.4, ends resting on the
    quarter-panel shoulders. deck_z(x, y) returns the body's top surface height.
    grow>0 = colour mask copy."""
    verts = []
    g = grow
    n_y, n_x = 45, 6
    for y in np.linspace(-26.5 - g, 26.5 + g, n_y):
        le = spoiler_leading_edge(y) - g
        for x in np.r_[np.linspace(le, 68.0, n_x - 1), 71.4 + g]:
            base = deck_z(min(max(x, le), 69.0), min(max(y, -26.5), 26.5)) - 0.35 - g
            lift = 0.6 if x >= 71.0 else 0.0
            verts += [[x, y, base], [x, y, base + 1.0 + lift + 2 * g]]
    pts = np.array(verts)
    # Convex hull would bridge the deck's centre dip; build ribbon panels instead.
    faces = []
    idx = lambda iy, ix, top: (iy * n_x + ix) * 2 + top
    for iy in range(n_y - 1):
        for ix in range(n_x - 1):
            for top in (0, 1):
                a, b, c, d = idx(iy, ix, top), idx(iy, ix + 1, top), idx(iy + 1, ix + 1, top), idx(iy + 1, ix, top)
                faces += [[a, b, c], [a, c, d]] if top else [[a, c, b], [a, d, c]]
        for ix in (0, n_x - 1):  # front and rear edges
            a, b, c, d = idx(iy, ix, 0), idx(iy, ix, 1), idx(iy + 1, ix, 1), idx(iy + 1, ix, 0)
            faces += [[a, b, c], [a, c, d]] if ix == 0 else [[a, c, b], [a, d, c]]
    for iy in (0, n_y - 1):  # end caps
        for ix in range(n_x - 1):
            a, b, c, d = idx(iy, ix, 0), idx(iy, ix + 1, 0), idx(iy, ix + 1, 1), idx(iy, ix, 1)
            faces += [[a, b, c], [a, c, d]] if iy == 0 else [[a, c, b], [a, d, c]]
    m = trimesh.Trimesh(pts, faces); m.fix_normals()
    return manifold(m)

EXHAUST_Y = (-21.4, -17.6, 17.6, 21.4)

def exhaust_tips(grow=0.0):
    """Quad tips, 2.9 mm diameter, rooted 4+ mm into the bumper (its rear face sits at
    x 72-76 here) and standing proud to x = 79.4."""
    return [cylinder(1.45 + grow, 8.4 + 2 * grow, [75.2 + grow, y, 11.0], axis=[1, 0, 0], n=48) for y in EXHAUST_Y]

FIN_X = 29.4   # shark-fin antenna position along the roof (from the side photograph)

def shark_fin(grow=0.0, base_z=45.15):
    """Shark-fin antenna on the rear roof; base_z is the roof height there."""
    g = grow
    return hull(np.vstack([meshof(ellipsoid([FIN_X, 0, base_z], [3.0 + 2 * g, 1.7 + 2 * g, 1.5 + 2 * g])).vertices,
                           meshof(box([2.2 + 2 * g, 1.2 + 2 * g, 0.4 + 2 * g], [FIN_X + 0.5, 0, base_z - 0.25])).vertices]))

def splitter(outline_xy):
    """Black chin splitter: the bumper's plan outline at z=10, pushed 0.9 mm forward,
    as a 1.6 mm plate under the nose. outline_xy: Nx2 array of (x, y) at z=10."""
    pts = np.asarray(outline_xy, float)
    # Smooth the ray-sampled outline with a symmetric quartic so the plate edge is clean.
    c = np.linalg.lstsq(np.c_[np.ones(len(pts)), pts[:, 1] ** 2, pts[:, 1] ** 4], pts[:, 0], rcond=None)[0]
    ys = np.linspace(pts[:, 1].min(), pts[:, 1].max(), 41)
    pts = np.c_[c[0] + c[1] * ys ** 2 + c[2] * ys ** 4, ys]
    lo = np.c_[pts[:, 0] - 0.9, pts[:, 1], np.full(len(pts), 7.4)]
    hi = np.c_[pts[:, 0] - 0.9, pts[:, 1], np.full(len(pts), 9.4)]
    back = np.array([[-62.0, -24.0, 7.4], [-62.0, 24.0, 7.4], [-62.0, -24.0, 9.4], [-62.0, 24.0, 9.4]])
    return hull(np.vstack([lo, hi, back]))

BADGE_CENTRE_X = -30.6625   # midpoint of the 5.0 glyph run along the car

def badge_5_0(side):
    """Readable '5.0' fender badge: 0.5 mm strokes, 0.45 mm relief on a buried base.
    The glyphs are drawn as read from the driver's side (nose to the left); the
    passenger-side copy is mirrored about BADGE_CENTRE_X so it also reads 5.0 from
    outside the car instead of a back-to-front 0.2."""
    s = side
    bars = []
    def glyphbar(x, z, w, h):
        if s > 0: x = 2 * BADGE_CENTRE_X - x
        return box([w, .95, h], [x, s * 30.775, z])
    for z in [22.0, 23.0, 24.0]: bars.append(glyphbar(-32.0, z, 1.55, .5))
    bars.append(glyphbar(-32.525, 23.5, .5, 1.0))
    bars.append(glyphbar(-31.475, 22.5, .5, 1.0))
    bars.append(glyphbar(-30.65, 22.0, .5, .5))
    for z in [22.0, 24.0]: bars.append(glyphbar(-29.3, z, 1.5, .5))
    for x in [-29.8, -28.8]: bars.append(glyphbar(x, 23.0, .5, 2.0))
    return bars

# --------------------------------------------------------------- rear plate
# The source bumper has its own plate recess (floor x 77.3-78.4, z 17.8-22.4, tilted).
# A 9.6 x 4.8 mm plate (a US 12 x 6 in plate at this scale) sits in it, face at x = 79.0,
# 0.3 mm behind the rear-panel ledge above. Set PLATE_TEXT to the real registration; the
# lettering is embossed 0.25 mm in a narrow bold face and coloured black by regions.py.
# Empty text leaves a blank white plate.
PLATE_TEXT = ''
PLATE_FACE_X = 79.0
PLATE_HALF_W, PLATE_Z0, PLATE_Z1 = 4.8, 17.75, 22.55
PLATE_FONTS = ['/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
               '/System/Library/Fonts/Helvetica.ttc', 'C:/Windows/Fonts/arialbd.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']

def plate_solid():
    """Plate slab: back buried in the bumper, face standing proud of the recess floor."""
    return box_lohi([76.0, -PLATE_HALF_W, PLATE_Z0], [PLATE_FACE_X, PLATE_HALF_W, PLATE_Z1])

def text_outlines(text, px_per_mm=100):
    """Glyph outlines of `text` in mm (origin bottom-left, y up), as a list of closed
    contours (outer boundaries and holes mixed; use an even-odd fill). Rendered with
    PIL from the first available PLATE_FONTS face and traced with OpenCV, so no font
    library is needed beyond what the pipeline already uses."""
    from PIL import Image, ImageDraw, ImageFont
    import cv2
    font = None
    for path in PLATE_FONTS:
        if Path(path).exists():
            font = ImageFont.truetype(path, 10 * px_per_mm); break
    if font is None:
        raise FileNotFoundError('no plate font found; edit geometry.PLATE_FONTS')
    x0, y0, x1, y1 = font.getbbox(text)
    pad = px_per_mm // 2
    img = Image.new('L', (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), 0)
    ImageDraw.Draw(img).text((pad - x0, pad - y0), text, fill=255, font=font)
    a = np.asarray(img)
    contours, _ = cv2.findContours((a > 127).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    h = a.shape[0]
    outlines = []
    for c in contours:
        c = cv2.approxPolyDP(c, 0.6, True)[:, 0, :].astype(float)
        if len(c) < 3: continue
        outlines.append(np.c_[c[:, 0], h - c[:, 1]] / px_per_mm)
    return outlines

def plate_text_solid(text=None, relief=0.25):
    """Embossed registration: lettering fitted inside the plate with 0.6 mm margins
    (cap height at most 2.2 mm, condensed to 75 % before it is made shorter), buried
    0.15 mm into the plate face and standing `relief` mm proud. None when text is empty."""
    text = PLATE_TEXT if text is None else text
    if not text.strip():
        return None
    outlines = text_outlines(text)
    pts = np.vstack(outlines)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    w, h = hi - lo
    max_w, max_h = 2 * PLATE_HALF_W - 1.2, 2.2
    sx = sy = max_h / h                       # cap height 2.2 mm ...
    if w * sx > max_w:                        # ... condensed to at most 75 % to fit the width,
        sx = max(max_w / w, 0.75 * sy)
        if w * sx > max_w:                    # ... then made shorter for very long numbers
            sy = sx = max_w / w
    centre = (lo + hi) / 2
    scaled = [np.c_[(o[:, 0] - centre[0]) * sx, (o[:, 1] - centre[1]) * sy] for o in outlines]
    cs = md.CrossSection(scaled, md.FillRule.EvenOdd)
    solid = cs.extrude(relief + 0.15)              # local z = relief direction
    m = meshof(solid)
    v = np.zeros_like(m.vertices)
    v[:, 1] = m.vertices[:, 0]                     # read left-to-right from behind: +Y
    v[:, 2] = m.vertices[:, 1] + (PLATE_Z0 + PLATE_Z1) / 2
    v[:, 0] = m.vertices[:, 2] + PLATE_FACE_X - 0.15
    return manifold(trimesh.Trimesh(v, m.faces))

def plate_text_mask():
    """Everything proud of the plate face inside the plate margins, i.e. the lettering."""
    return box_lohi([PLATE_FACE_X + 0.06, -PLATE_HALF_W + 0.1, PLATE_Z0 + 0.1], [PLATE_FACE_X + 2.0, PLATE_HALF_W - 0.1, PLATE_Z1 - 0.1])

# ------------------------------------------------------------------- wheel
SPOKES = 7
RIM_FACE_Z = 8.85     # spoke face height at the rim
HUB_FACE_Z = 7.95     # dished towards the centre
FLOOR_Z = 6.4         # visible floor between the spokes (brake side)
ARM_SPREAD = math.radians(12.9)

def _plate(p0, w0, p1, w1, z0, z1):
    """Flat tapered plate between polar-plane points p0->p1 (XY), widths w0/w1, z0..z1."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0; d /= np.linalg.norm(d); n = np.array([-d[1], d[0]])
    pts = []
    for p, w, z in [(p0, w0, z0), (p0, w0, z1[0]), (p1, w1, z0), (p1, w1, z1[1])]:
        pts += [[*(p + n * w / 2), z], [*(p - n * w / 2), z]]
    return hull(pts)

def wheel_face_z(r):
    t = (r - 2.2) / (9.4 - 2.2)
    return HUB_FACE_Z + (RIM_FACE_Z - HUB_FACE_Z) * max(0.0, min(1.0, t))

def spoke_solids(grow=0.0):
    """Seven Y-spokes: a wide stem from the hub splits at ~half radius into two arms
    that meet the rim 25.7 degrees apart, giving fourteen evenly spaced rim contacts.
    grow>0 widens every plate for use as a colour mask."""
    g = grow
    parts = []
    for j in range(SPOKES):
        a = 2 * math.pi * j / SPOKES + math.pi / 2
        u = np.array([math.cos(a), math.sin(a)])
        stem0, stem1 = u * 2.2, u * 4.9
        parts.append(_plate(stem0, 1.7 + 2 * g, stem1, 1.45 + 2 * g, FLOOR_Z - 0.5 - g, (wheel_face_z(2.2) + g, wheel_face_z(4.9) + g)))
        for d in (-ARM_SPREAD, ARM_SPREAD):
            v = np.array([math.cos(a + d), math.sin(a + d)])
            parts.append(_plate(u * 4.55, 1.1 + 2 * g, v * 9.45, 0.95 + 2 * g, FLOOR_Z - 0.5 - g, (wheel_face_z(4.55) + g, wheel_face_z(9.45) + g)))
    return parts

def caliper_solid(grow=0.0):
    """Red caliper visible through the spokes on the rear side (local -x).
    grow>0 gives a slightly larger copy for use as a colour mask."""
    g = grow
    pts = []
    for t in np.linspace(math.pi - math.radians(28 + 2 * g), math.pi + math.radians(28 + 2 * g), 14):
        pts.append([(7.75 + g) * math.cos(t), (7.75 + g) * math.sin(t)])
    for t in np.linspace(math.pi + math.radians(28 + 2 * g), math.pi - math.radians(28 + 2 * g), 14):
        pts.append([(5.9 - g) * math.cos(t), (5.9 - g) * math.sin(t)])
    return polygon_prism(pts, [0, 1], FLOOR_Z - 0.3 - g, 7.55 + g)

def tyre_solid():
    # Solid-backed tyre; inside the rim the floor sits at FLOOR_Z so the spokes stand proud.
    return lathe([[0, 0], [10.75, 0], [11.35, .45], [11.65, 1.5], [11.65, 6.3], [11.4, 7.7], [10.9, 8.4], [9.7, 8.4],
                  [9.15, 7.0], [8.75, 7.0], [8.75, FLOOR_Z], [0, FLOOR_Z]])

def rim_solid():
    return lathe([[8.75, 6.6], [9.8, 6.6], [9.8, 8.6], [9.6, 8.95], [9.05, 8.95], [8.75, 8.6]])

CAP_R, CAP_FACE_Z = 1.75, 8.9   # centre cap: 3.5 mm across, face at local z 8.9

def hub_solid(grow=0.0):
    g = grow
    return cylinder(2.7 + g, 2.6 + 2 * g, [0, 0, FLOOR_Z - 0.5 + 1.3], n=64) + cylinder(CAP_R + g, 0.9 + 2 * g, [0, 0, 8.05 + 0.45 - 0.05], n=48)

# RTR centre-cap monogram (the car wears RTR Aero 7 wheels: a mirrored R, a T whose stem
# drops below the bar, and an R, joined into one outline, chrome on a black cap inside a
# chrome ring). Drawn as filled strokes in units of the logo half-width, (u right,
# w down from the top of the bar), traced from RTR's own cap photograph; strokes are
# fattened to 0.19 units so they survive at 2.6 mm across.
_RTR_S = 1.3                       # logo half-width in mm on the 3.5 mm cap
_RTR_T = 0.19                      # stroke
def _rtr_quads():
    t = _RTR_T
    quads = [[(-0.905, 0.0), (0.905, 0.0), (0.905, t), (-0.905, t)],            # shared top bar
             [(-0.085, 0.0), (0.085, 0.0), (0.085, 0.77), (-0.085, 0.77)]]     # T stem
    for m in (-1, 1):                                                           # the two R's
        R = lambda u, w: (m * u, w)
        quads.append([R(-0.905, 0.0), R(-0.715, 0.0), R(-0.715, 0.47), R(-0.905, 0.47)])      # stem
        quads.append([R(-0.905, 0.32), R(-0.265, 0.32), R(-0.265, 0.47), R(-0.905, 0.47)])    # bowl bar
        quads.append([R(-0.30, 0.44), R(-0.265, 0.47), R(-0.922, 0.745), R(-1.012, 0.643), R(-0.718, 0.507)])  # leg: pointed at the bar tip
        quads.append([R(-0.905, 0.46), R(-0.715, 0.47), R(-0.718, 0.507), R(-1.012, 0.643)])   # knee: stem flows into the leg
    return quads

def rtr_emblem(grow=0.0):
    """Monogram + ring standing 0.2 / 0.15 mm proud of the cap face, roots buried 0.1 mm.
    Local +y is up once the wheel is mounted, so w runs down -y; the logo is symmetric
    about the T stem, which is why one wheel file suits both sides of the car.
    grow>0 pads every stroke (a diamond Minkowski sum) for use as a colour mask."""
    g = grow
    z0, z1 = CAP_FACE_Z - 0.1 - g, CAP_FACE_Z + 0.2 + g
    parts = []
    for q in _rtr_quads():
        pts = np.array([[u * _RTR_S, (0.385 - w) * _RTR_S] for u, w in q])
        if g:
            pts = np.vstack([pts + d for d in ([g, 0], [-g, 0], [0, g], [0, -g])])
        parts.append(prism(pts, [0, 1], z0, z1))
    # Ring inset 0.05 mm from the cap edge so its wall never coincides with the cap wall.
    ring = cylinder(CAP_R - 0.05 + g, CAP_FACE_Z + 0.15 + g - z0, [0, 0, (z0 + CAP_FACE_Z + 0.15 + g) / 2], n=96) - cylinder(1.50 - g, 4.0, [0, 0, CAP_FACE_Z], n=96)
    return union(parts + [ring])

def wheel_solid():
    """Complete face-up printable wheel: solid-backed, nothing floating."""
    w = union([tyre_solid(), rim_solid(), hub_solid(), caliper_solid(), rtr_emblem()] + spoke_solids())
    for j in range(5):
        a = j * 2 * math.pi / 5
        w = w - cylinder(.36, 1.0, [2.15 * math.cos(a), 2.15 * math.sin(a), 8.5], n=24)
    return w.simplify(.012)
