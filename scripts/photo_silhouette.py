"""Extract the car silhouette from the side photograph (images/3.jpg).

GrabCut alone fails on the white car against the white garage wall, so a
hand-traced outline seeds it and the roof edge is forced from the trace.
Writes validation/likeness/photo3_mask.png and photo3_metrics.json.
"""
from pathlib import Path
import json
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'validation/likeness'
OUT.mkdir(parents=True, exist_ok=True)
WHEELBASE_MM = 90.94  # model wheel centre spacing (build_parts.WHEEL_X)

img = cv2.imread(str(ROOT / 'images/3.jpg'))
h, w = img.shape[:2]
# Traced outline (photo pixels). The nose is clipped by the left image edge.
outline = np.array([
    (0, 900), (0, 620), (0, 600), (100, 582), (200, 562), (300, 547), (400, 532), (460, 522), (470, 520),
    (640, 445), (700, 428), (800, 420), (900, 424), (1000, 436), (1100, 462), (1180, 492), (1240, 506),
    (1300, 512), (1400, 535), (1500, 553), (1490, 566), (1480, 572), (1495, 600), (1500, 700), (1485, 780),
    (1440, 832), (1400, 848), (1340, 852), (1330, 860), (1320, 900), (1270, 930), (1150, 932), (1100, 900),
    (1085, 850), (1075, 840), (1040, 900), (600, 908), (380, 905), (350, 880), (330, 910), (280, 928),
    (150, 928), (110, 900), (95, 850), (85, 830), (60, 900)], np.int32)
roof = np.array([(600, 462), (640, 443), (700, 426), (800, 414), (900, 416), (1000, 428), (1100, 450),
                 (1180, 478), (1240, 500), (1240, 560), (600, 560)], np.int32)

base = np.zeros((h, w), np.uint8)
cv2.fillPoly(base, [outline], 255)
k = lambda n: np.ones((n, n), np.uint8)
mask = np.full((h, w), cv2.GC_BGD, np.uint8)
mask[cv2.dilate(base, k(41)) > 0] = cv2.GC_PR_BGD
mask[base > 0] = cv2.GC_PR_FGD
mask[cv2.erode(base, k(41)) > 0] = cv2.GC_FGD
cv2.grabCut(img, mask, None, np.zeros((1, 65)), np.zeros((1, 65)), 10, cv2.GC_INIT_WITH_MASK)
m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
m = np.where(lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k(9))
ff = m.copy()
cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 255)
m |= cv2.bitwise_not(ff)
cv2.fillPoly(m, [roof], 255)
cv2.imwrite(str(OUT / 'photo3_mask.png'), m)

# Wheel centres from the dark tyre/rim discs (minimum enclosing circle).
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
wheels = {}
for name, (x0, x1, y0, y1) in {'front': (70, 380, 660, 940), 'rear': (1050, 1360, 660, 940)}.items():
    dark = ((gray[y0:y1, x0:x1] < 90) & (m[y0:y1, x0:x1] > 0)).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, k(15))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(dark)
    blob = (lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    cnts, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    (cx, cy), r = cv2.minEnclosingCircle(max(cnts, key=cv2.contourArea))
    wheels[name] = {'cx': float(cx + x0), 'cy': float(cy + y0), 'r_px': float(r)}
# The dark-blob circle is pulled upwards by the wheel-arch shadow; the centre caps read
# directly from the photograph (3x gridded crops) are the reliable wheel centres.
CAP_CENTRES = {'front': (218.0, 792.0), 'rear': (1213.0, 795.0)}
for name, (cx, cy) in CAP_CENTRES.items():
    wheels[name].update({'blob_cx': wheels[name]['cx'], 'blob_cy': wheels[name]['cy'], 'cx': cx, 'cy': cy})
ppm = (wheels['rear']['cx'] - wheels['front']['cx']) / WHEELBASE_MM
metrics = {'source': 'images/3.jpg', 'wheels': wheels, 'px_per_model_mm': ppm,
           'wheel_centre_y': (wheels['front']['cy'] + wheels['rear']['cy']) / 2,
           'note': 'Nose clipped at x=0. Wheel centres are the hub caps; blob_* are the shadow-biased circle fits.'}
(OUT / 'photo3_metrics.json').write_text(json.dumps(metrics, indent=1))
over = img.copy()
over[m > 0] = (0.55 * over[m > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8)
for v in wheels.values():
    cv2.circle(over, (int(v['cx']), int(v['cy'])), 4, (0, 255, 0), -1)
cv2.imwrite(str(OUT / 'photo3_mask_overlay.jpg'), over, [cv2.IMWRITE_JPEG_QUALITY, 80])
print('PHOTO_SILHOUETTE_DONE', json.dumps(metrics))
