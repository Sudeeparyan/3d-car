"""Score how closely a render set matches the six reference photographs.

Usage: .venv/bin/python scripts/validate_likeness.py <render_dir>
The render_dir comes from scripts/render_views.mjs with modes shaded,flat,silhouette.
Writes <render_dir>/likeness.json, profile_compare.png and contact_sheet.jpg.

Quantitative part: the side photograph's silhouette (validation/likeness/photo3_mask.png)
is aligned to the orthographic side render using the wheel centres, and the upper
body profile (hood, windscreen, roof, deck, spoiler) is compared in millimetres.
Feature part: the flat-colour renders are checked for the signature details.
"""
from pathlib import Path
import json, sys
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LIKE = ROOT / 'validation/likeness'
WHEEL_X = (-48.4472, 42.4928)
WHEEL_R = 11.65
SIDE_SCALE, FRONT_SCALE, TOP_SCALE = 181.0, 98.0, 181.0
FLAT = {'white': (255, 255, 255), 'black': (0, 0, 0), 'red': (255, 0, 0), 'gunmetal': (0x60, 0x68, 0x70),
        'backing': (0x40, 0x40, 0x40), 'silver': (0xc0, 0xc0, 0xc0), 'amber': (0xff, 0x88, 0x00), 'gloss': (0x28, 0x28, 0x28), 'bg': (0, 0, 255)}

def colour_mask(img, name, tol=40):
    r, g, b = FLAT[name]
    d = np.abs(img[..., ::-1].astype(int) - np.array([r, g, b])).sum(-1)
    return d < tol

def components(mask, min_px=8):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    return [stats[i] for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= min_px]

class View:
    """Pixel <-> model-mm mapping for an orthographic render (camera looks along an axis)."""
    def __init__(self, img, scale, centre, horiz_sign, target_h, target_v):
        self.img = img; h, w = img.shape[:2]
        self.ppm = w / scale; self.cx, self.cy = w / 2, h / 2
        self.hs, self.th, self.tv = horiz_sign, target_h, target_v
    def px(self, hmm, vmm):
        return int(round(self.cx + self.hs * (hmm - self.th) * self.ppm)), int(round(self.cy - (vmm - self.tv) * self.ppm))
    def box(self, h0, h1, v0, v1):
        (x0, y1), (x1, y0) = self.px(min(h0, h1), min(v0, v1)), self.px(max(h0, h1), max(v0, v1))
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
        return (slice(max(y0, 0), y1), slice(max(x0, 0), x1))

def side_profile(mask, x_of_px, z_of_py, xs):
    """Top and bottom z (mm) for each requested model x, from a binary side mask."""
    h, w = mask.shape
    cols = np.arange(w); top = np.full(w, np.nan); bot = np.full(w, np.nan)
    for c in cols:
        ys = np.where(mask[:, c])[0]
        if len(ys): top[c], bot[c] = ys.min(), ys.max()
    xmm = x_of_px(cols)
    ok = ~np.isnan(top)
    return (np.interp(xs, xmm[ok], z_of_py(top[ok]), left=np.nan, right=np.nan),
            np.interp(xs, xmm[ok], z_of_py(bot[ok]), left=np.nan, right=np.nan))

def main(d):
    d = Path(d); report = {'render_dir': str(d), 'checks': {}, 'profile': {}}
    load = lambda n: cv2.imread(str(d / n))
    # ---------- side profile vs photo 3 ----------
    photo = cv2.imread(str(LIKE / 'photo3_mask.png'), 0)
    pm = json.loads((LIKE / 'photo3_metrics.json').read_text())
    xs = np.arange(-62, 58.01, 0.5)
    # Orthographic side render vs the photograph, both aligned on the wheel centres. The hood
    # segment is reported but not scored: in any perspective photo its top edge is the far
    # fender (camera above the hood), which lifts it 1-2 mm relative to a true side elevation.
    ren = load('side_silhouette.png')
    rmask = ren[..., 0] > 127; H, W = rmask.shape; rppm = W / SIDE_SCALE
    r_top, r_bot = side_profile(rmask, lambda px: (px - W / 2) / rppm, lambda py: 21 + (H / 2 - py) / rppm, xs)
    ppm = pm['px_per_model_mm']; fcx = pm['wheels']['front']['cx']; wcy = pm['wheel_centre_y']
    p_top, p_bot = side_profile(photo > 127, lambda px: WHEEL_X[0] + (px - fcx) / ppm, lambda py: WHEEL_R + (wcy - py) / ppm, xs)
    dtop = r_top - p_top; ok = ~np.isnan(dtop)
    mid = ok & (xs > -30) & (xs < 25); dbot = r_bot - p_bot
    segs = {'hood': (xs < -25), 'windscreen_roof': (xs >= -25) & (xs < 30), 'deck_spoiler': xs >= 30}
    scored = ok & (xs >= -25)
    report['profile'] = {
        'top_mean_abs_mm': float(np.nanmean(np.abs(dtop[scored]))), 'top_max_abs_mm': float(np.nanmax(np.abs(dtop[scored]))),
        'top_bias_mm': float(np.nanmean(dtop[scored])), 'scored_range': 'windscreen, roof, deck, spoiler (x >= -25 mm)',
        'segments_mean_abs_mm': {k: float(np.nanmean(np.abs(dtop[ok & s]))) for k, s in segs.items()},
        'rocker_bottom_mean_abs_mm': float(np.nanmean(np.abs(dbot[mid]))),
        'x_range_mm': [float(xs[ok].min()), float(xs[ok].max())],
    }
    # plot
    fig = np.full((520, 1400, 3), 255, np.uint8)
    def P(x, z): return int(100 + (x + 80) * 7.5), int(470 - z * 8)
    for px_, col, lab in [(p_top, (0, 0, 220), 'photo 3 (aligned on wheel centres)'), (r_top, (30, 30, 30), 'render')]:
        pts = [P(x, z) for x, z in zip(xs, px_) if not np.isnan(z)]
        cv2.polylines(fig, [np.array(pts, np.int32)], False, col, 2)
    for x, z in zip(xs, p_bot):
        if not np.isnan(z): cv2.circle(fig, P(x, z), 1, (0, 0, 220), -1)
    for x, z in zip(xs, r_bot):
        if not np.isnan(z): cv2.circle(fig, P(x, z), 1, (30, 30, 30), -1)
    for wx in WHEEL_X: cv2.circle(fig, P(wx, WHEEL_R), int(WHEEL_R * 8), (160, 160, 160), 1)
    cv2.putText(fig, f"top profile (windscreen/roof/deck): mean |d| {report['profile']['top_mean_abs_mm']:.2f} mm, max {report['profile']['top_max_abs_mm']:.2f} mm, bias {report['profile']['top_bias_mm']:+.2f} mm   (red = photo, black = render)",
                (20, 30), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 0, 0), 1)
    for k, v in report['profile']['segments_mean_abs_mm'].items():
        cv2.putText(fig, f'{k}: {v:.2f} mm', (20, 60 + 22 * list(segs).index(k)), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 0, 0), 1)
    cv2.imwrite(str(d / 'profile_compare.png'), fig)

    # ---------- feature checks on flat renders ----------
    C = report['checks']
    def check(name, value, ok, expect):
        C[name] = {'value': value, 'pass': bool(ok), 'expect': expect}
    f = load('front_flat.png'); fv = View(f, FRONT_SCALE, None, -1, 0, 23)   # image right = -Y (looking +X from -X)
    grille = f[fv.box(-15, 15, 17, 25.5)]
    check('front.grille_black_fraction', float(colour_mask(grille, 'black').mean()), colour_mask(grille, 'black').mean() > .45, '> 0.45')
    check('front.pony_logo_gloss_black_px', int(colour_mask(grille, 'gloss').sum()), colour_mask(grille, 'gloss').sum() > 120, '> 120 px (gloss-black pony badge on the matte grille)')
    hl = [colour_mask(f[fv.box(s * 17, s * 28, 23.2, 26.4)], 'black').mean() for s in (-1, 1)]
    check('front.headlamps_black_fraction', [float(v) for v in hl], min(hl) > .45, '> 0.45 each side')
    drl = [len(components(colour_mask(f[fv.box(s * 16.6, s * 21.2, 23.5, 25.5)], 'white'), 10)) for s in (-1, 1)]
    check('front.drl_bars', drl, drl == [3, 3], '3 white bars each side')
    amb = [int(colour_mask(f[fv.box(s * 17, s * 31, 20, 27)], 'amber').sum()) for s in (-1, 1)]
    check('front.amber_marker_px', amb, min(amb) > 15, '> 15 px each side')
    sp = f[fv.box(-30, 30, 6.2, 9.4)]
    check('front.splitter_black_fraction', float(colour_mask(sp, 'black').mean()), colour_mask(sp, 'black').mean() > .5, '> 0.5')
    t = load('top_flat.png'); tv = View(t, TOP_SCALE, None, 1, 0, 0)  # top view: image right = +X, image up = +Y
    vents = components(colour_mask(t[tv.box(-70, -56, -18, 18)], 'black'), 20)
    check('top.hood_vents', len(vents), len(vents) == 2, '2 black vents')
    roofw = colour_mask(t[tv.box(-5, 30, -14, 14)], 'white').mean()
    check('top.roof_white_fraction', float(roofw), roofw > .9, '> 0.9')
    r = load('rear_flat.png'); rv = View(r, FRONT_SCALE, None, 1, 0, 23)  # looking -X from +X: image right = +Y
    bars = components(colour_mask(r[rv.box(-27, 27, 24, 32)], 'red'), 25)
    check('rear.tail_light_bars', len(bars), len(bars) == 6, '6 red bars')
    panel = colour_mask(r[rv.box(-12, 12, 25.5, 30.5)], 'black').mean()
    check('rear.centre_panel_black_fraction', float(panel), panel > .6, '> 0.6')
    spoil = int(colour_mask(r[rv.box(-28, 28, 33, 40)], 'black').sum())
    check('rear.spoiler_black_px', spoil, spoil > 400, '> 400 px')
    exh = components(colour_mask(r[rv.box(-24, 24, 7, 14)], 'silver'), 12)
    check('rear.exhaust_tips', len(exh), len(exh) == 4, '4 silver tips')
    diff = colour_mask(r[rv.box(-22, 22, 7, 12.5)], 'black').mean()
    check('rear.diffuser_black_fraction', float(diff), diff > .4, '> 0.4')
    s = load('side_flat.png'); sv = View(s, SIDE_SCALE, None, 1, 0, 21)   # image right = +X
    stripe = components(colour_mask(s[sv.box(-35, 29, 9.7, 13.5)], 'black'), 15)
    check('side.stripe_segments', len(stripe), len(stripe) == 5, '5 (4 hash marks + solid stripe)')
    badge = int(colour_mask(s[sv.box(-35, -26, 20.5, 25.5)], 'gloss').sum())
    check('side.badge_5_0_px', badge, badge > 25, '> 25 px (gloss black)')
    # The passenger-side badge is mirrored per side; both must show the same glyph area.
    sr = load('sideR_flat.png') if (d / 'sideR_flat.png').exists() else None
    if sr is not None:
        srv = View(sr, SIDE_SCALE, None, -1, 0, 21)   # looking -Y from +Y: image right = -X
        badge_r = int(colour_mask(sr[srv.box(-35, -26, 20.5, 25.5)], 'gloss').sum())
        check('sideR.badge_5_0_px', badge_r, abs(badge_r - badge) <= max(12, 0.15 * badge), f'within 15% of the left badge ({badge} px)')
        # Glyph order: read from outside the car, the left glyph must be the "5" (three
        # full-width bars) and the right glyph the "0" (two) on both sides of the car.
        def reads_5_0(mask):
            glyphs = sorted(components(mask, 8), key=lambda st: st[cv2.CC_STAT_LEFT])
            if len(glyphs) < 2: return None
            def bars(st):
                x, y, w, h = st[cv2.CC_STAT_LEFT], st[cv2.CC_STAT_TOP], st[cv2.CC_STAT_WIDTH], st[cv2.CC_STAT_HEIGHT]
                rows = mask[y:y + h, x:x + w].sum(axis=1); full = rows >= 0.8 * rows.max()
                return int((full & ~np.r_[False, full[:-1]]).sum())
            return [bars(glyphs[0]), bars(glyphs[-1])]
        bl = reads_5_0(colour_mask(s[sv.box(-35, -26, 20.5, 25.5)], 'gloss'))
        br = reads_5_0(colour_mask(sr[srv.box(-35, -26, 20.5, 25.5)], 'gloss'))
        check('side.badge_reads_5_0_both_sides', {'left_side_bars': bl, 'right_side_bars': br}, bl == [3, 2] and br == [3, 2],
              '[3, 2] bars per glyph on both sides: a "5" then a "0" reading nose-to-tail from outside')
    cx, cy = sv.px(WHEEL_X[0], WHEEL_R); rr = int(9.6 * sv.ppm)
    yy, xx = np.ogrid[:s.shape[0], :s.shape[1]]; disc = (xx - cx) ** 2 + (yy - cy) ** 2 < rr * rr
    red_in = int((colour_mask(s, 'red') & disc).sum()); gm = float((colour_mask(s, 'gunmetal') & disc).sum() / disc.sum())
    check('side.caliper_red_px_in_wheel', red_in, red_in > 40, '> 40 px')
    check('side.wheel_face_gunmetal_fraction', gm, .3 < gm < .75, '0.3-0.75 (open spokes)')
    capdisc = (xx - cx) ** 2 + (yy - cy) ** 2 < (2.0 * sv.ppm) ** 2
    cap = int((colour_mask(s, 'silver') & capdisc).sum())
    check('side.wheel_cap_rtr_logo_silver_px', cap, cap > 20, '> 20 px (chrome RTR monogram and ring on the centre cap)')
    mirror = int(colour_mask(s[sv.box(-21, -7, 30.5, 38.5)], 'black').sum())
    check('side.mirror_black_px', mirror, mirror > 80, '> 80 px')
    win = colour_mask(s[sv.box(-2, 30, 36, 42)], 'black').mean()
    check('side.window_black_fraction', float(win), win > .8, '> 0.8')

    passed = sum(c['pass'] for c in C.values()); total = len(C)
    prof = report['profile']['top_mean_abs_mm']
    report['summary'] = {'features_passed': passed, 'features_total': total,
                         'profile_top_mean_abs_mm': prof, 'profile_ok': prof < 0.6,
                         'score_percent': round(100 * (0.5 * passed / total + 0.5 * max(0, 1 - prof / 2.5)), 1)}
    (d / 'likeness.json').write_text(json.dumps(report, indent=1))

    # ---------- contact sheet: photo | render ----------
    def fit(img, w, h):
        s_ = min(w / img.shape[1], h / img.shape[0]); im = cv2.resize(img, None, fx=s_, fy=s_)
        canvas = np.full((h, w, 3), 40, np.uint8); y0 = (h - im.shape[0]) // 2; x0 = (w - im.shape[1]) // 2
        canvas[y0:y0 + im.shape[0], x0:x0 + im.shape[1]] = im; return canvas
    P = lambda n: cv2.imread(str(ROOT / 'images' / n))
    pairs = [(P('3.jpg')[380:960, :], load('side_persp.png')[300:1000, :]), (P('5.jpg'), load('three.png')),
             (P('6.jpg'), load('rear34.png')), (P('1.jpg')[500:1500, :], load('front.png'))]
    rows = [np.hstack([fit(a, 700, 360), fit(b, 700, 360)]) for a, b in pairs]
    sheet = np.vstack(rows)
    cv2.putText(sheet, f"score {report['summary']['score_percent']}%  features {passed}/{total}  profile {prof:.2f} mm", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 255), 2)
    cv2.imwrite(str(d / 'contact_sheet.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 82])
    print(json.dumps(report['summary']))
    for k, c in C.items(): print(f"  {'PASS' if c['pass'] else 'FAIL'} {k}: {c['value']}  (expect {c['expect']})")
    return report

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else LIKE / 'current')
