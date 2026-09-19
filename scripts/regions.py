"""Colour regions of the body and wheel as closed solids, in paint priority order.

paint_mesh.py splits the printable solids with these masks to label every face, and
build_multicolor.py groups the same pieces by filament, so the preview, the OBJ and
the multicolour print files always agree.

Preview material indices (see assemble_obj.MATERIALS):
0 white, 1 black, 2 red, 3 gunmetal, 4 brake backing, 5 silver, 6 amber, 7 gloss black.
"""
import numpy as np
import geometry as G
from geometry import box, box_lohi, cylinder, union, prism, polygon_prism, source_prism

WHITE, BLACK, RED, GUNMETAL, BACKING, SILVER, AMBER, GLOSS = range(8)
# GLOSS is the gloss-black badge finish of the real car (pony, 5.0): black filament, but
# a separate preview material so the badges still read against the matte black grille.
BODY_FILAMENT = {WHITE: 'white', BLACK: 'black', RED: 'red', GUNMETAL: 'black', SILVER: 'white', AMBER: 'black', GLOSS: 'black'}
WHEEL_FILAMENT = {BLACK: 'black', RED: 'red', GUNMETAL: 'dark_grey', BACKING: 'dark_grey', SILVER: 'white'}

def both_sides(fn):
    return [fn(-1), fn(1)]

def grown(outline, margin=0.15):
    """Outline pushed outwards by ~margin so a paint mask never shares a face with the
    recess cutter of the same feature (coincident faces leave sliver triangles)."""
    pts = np.asarray(outline, float); c = pts.mean(axis=0)
    d = pts - c; r = np.linalg.norm(d, axis=1, keepdims=True)
    return pts + d / np.maximum(r, 1e-9) * margin

def stripe_masks():
    """Lower door stripe: four forward-slanted hash marks then a solid band to the rear
    wheel, 1.7 mm tall at z 10.6-12.3 as in the photographs."""
    z0, z1, slant, w = 10.6, 12.3, 1.2, 1.8
    quads = []
    for x0 in (-33.0, -29.6, -26.2, -22.8):
        quads.append([[x0, z0], [x0 + w, z0], [x0 + w + slant, z1], [x0 + slant, z1]])
    quads.append([[-19.4, z0], [31.0, z0], [32.2, z1], [-18.2, z1]])
    masks = []
    for q in quads:
        masks += [prism(q, [0, 2], -45, -26), prism(q, [0, 2], 26, 45)]
    return masks

def side_glazing_masks():
    """Door window, blacked-out B-pillar and quarter window as one outline per side."""
    return [polygon_prism(G.side_glazing_outline(), [0, 2], lo, hi) for lo, hi in [(-45, -20), (20, 45)]]

def body_regions():
    """Ordered (material, mask_solid) list; the remainder is white."""
    red = union([source_prism(i, [1, 2], 69.05, 90, shrink=.92) for i in [32, 34, 36, 38, 40, 42]])
    lamps = [prism(grown(G.headlamp_outline(s)), [1, 2], -90, -57) for s in (-1, 1)]
    amber = union([lamp ^ box_lohi([-90, min(s * 26.3, s * 40), 15], [-50, max(s * 26.3, s * 40), 32]) for lamp, s in zip(lamps, (-1, 1))])
    # Tri-bar LED daytime running lights at the inner end of each headlamp: white, before black.
    drl = union([prism(G.drl_bar_outline(s, y), [1, 2], -90, -58) for s in (-1, 1) for y in G.DRL_Y])
    silver = union([cylinder(1.62, 3.0, [78.6, y, 11.0], axis=[1, 0, 0], n=48) for y in G.EXHAUST_Y])
    # Gloss-black badges as on the car: the pony in the grille and the 5.0 on each fender
    # (the fender box catches only what stands proud of the skin, |y| > 31.15).
    gloss = union([G.pony_emblem(grow=0.25),
                   *[box_lohi([-33, lo, 21.7], [-28.4, hi, 24.3]) for lo, hi in [(-45, -31.15), (31.15, 45)]]])
    black = []
    black.append(G.plate_text_mask())                                                    # registration lettering on the rear plate
    black += side_glazing_masks()
    black.append(source_prism(5, [0, 1], 31, 60) ^ box_lohi([-90, -50, 0], [58.5, 50, 60]))  # rear glass, deck lid stays white
    black.append(prism([[-24.5, -24], [-24.5, 24], [-5.1, 20.4], [-5.1, -20.4]], [0, 1], 34.2, 60))  # windscreen
    black.append(prism(grown(G.grille_outline()), [1, 2], -90, -68))                     # upper grille (recessed)
    black.append(prism(grown(G.lower_intake_outline()), [1, 2], -90, -68))               # lower intake (recessed)
    for index, lo, hi in [(27, 70, 90), (31, 68.1, 90), (37, 68.1, 90)]:
        black.append(source_prism(index, [1, 2], lo, hi, shrink=1.03 if index in [31, 37] else 1.0))  # rear panel, lamp surrounds
    black += lamps                                                                       # smoked headlamps
    for y in [-12.6, 12.6]:
        black.append(box_lohi([-66.95, y - 2.85, 29], [-60.45, y + 2.85, 60]))            # hood vents
    black += [G.mirror(s, grow=0.25) for s in (-1, 1)]                                # mirror heads + stalks
    black.append(G.spoiler_blade(_deck_z, grow=0.25))                                    # lip spoiler
    black.append(G.shark_fin(grow=0.3, base_z=_deck_z(G.FIN_X, 0)))                        # antenna
    black += stripe_masks()
    black += [box_lohi([-90, -45, 0], [90, -24, 9.1]), box_lohi([-90, 24, 0], [90, 45, 9.1])]  # skirts
    black.append(box_lohi([-90, -50, 0], [-62, 50, 9.45]))                               # splitter plate (lip above stays white)
    black += [prism(grown(G.corner_slot_outline(s)), [1, 2], -90, -61) for s in (-1, 1)]  # recessed bumper corner slots
    black.append(box_lohi([71.5, -26.2, 0], [90, 26.2, 13.95]))                          # rear diffuser (recessed)
    black.append(box_lohi([30, -40, 0], [66, 40, 9.45]))                                  # flat underside slab behind the rear axle (seen below the diffuser)
    return [(RED, red), (AMBER, amber), (SILVER, silver), (GLOSS, gloss), (WHITE, drl), (BLACK, union(black))], WHITE

_deck_z = None
def set_deck_sampler(fn):
    """The spoiler mask follows the deck surface; build_parts/paint pass the sampler in."""
    global _deck_z
    _deck_z = fn

def wheel_regions():
    # Masks are grown copies of the printed solids so no mask face coincides with a wheel face.
    spokes = union(G.spoke_solids(grow=0.15) + [G.hub_solid(grow=0.15)])
    caliper = G.caliper_solid(grow=0.2) - spokes
    floor = cylinder(8.75, G.FLOOR_Z + 0.06 - 5.9, [0, 0, (G.FLOOR_Z + 0.06 + 5.9) / 2], n=160) - spokes - G.caliper_solid(grow=0.2)
    emblem = G.rtr_emblem(grow=0.04)                                   # chrome RTR monogram + ring, before the cap (small grow keeps the R bowls black)
    cap = cylinder(G.CAP_R, 1.4, [0, 0, 8.42 + 0.7], n=48)
    face = cylinder(9.85, 6.0, [0, 0, 6.3 + 3.0], n=160)
    return [(RED, caliper), (BACKING, floor), (SILVER, emblem), (BLACK, cap), (GUNMETAL, face)], BLACK

def partition(solid, regions, default):
    """Split a manifold by the ordered masks; returns [(material, piece_manifold), ...]."""
    pieces = []; remaining = solid
    for material, mask in regions:
        inside, remaining = remaining.split(mask)
        if inside.num_tri():
            pieces.append((material, inside))
    pieces.append((default, remaining))
    return pieces
