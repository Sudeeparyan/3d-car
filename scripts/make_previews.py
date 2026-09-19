"""Render the previews/ image set from the assembled OBJ with the headless three.js
renderer (scripts/render_views.mjs), replacing the earlier Blender/Cycles previews.

Painted views show the seven preview materials of the OBJ/MTL; grey views show the
same geometry as one matte filament, i.e. what a single-colour print looks like
before painting. Run after assemble_obj.py.
"""
from pathlib import Path
import shutil, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = ROOT / 'previews'
PLAN = {  # output name: (view, mode)
    '01_painted_front.png': ('three', 'shaded'),
    '02_painted_rear.png': ('rear34', 'shaded'),
    '03_grey_side_left.png': ('side', 'grey'),
    '04_grey_front.png': ('front', 'grey'),
    '05_grey_rear.png': ('rear', 'grey'),
    '06_grey_side_right.png': ('sideR', 'grey'),
    '07_grey_three_quarter.png': ('three', 'grey'),
    '08_painted_side.png': ('side', 'shaded'),
    '09_painted_front_straight.png': ('front', 'shaded'),
    '10_painted_rear_straight.png': ('rear', 'shaded'),
    '11_painted_top.png': ('top', 'shaded'),
    '12_painted_side_right.png': ('sideR', 'shaded'),
    '13_painted_front_low.png': ('frontlow', 'shaded'),
    '14_painted_rear_low.png': ('rearlow', 'shaded'),
    '15_painted_wheel_detail.png': ('wheel', 'shaded'),
    '16_painted_grille_detail.png': ('grille', 'shaded'),
    '17_grey_wheel_detail.png': ('wheel', 'grey'),
    '18_grey_grille_detail.png': ('grille', 'grey'),
}

def main():
    views = sorted({v for v, _ in PLAN.values()})
    modes = sorted({m for _, m in PLAN.values()})
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['node', str(ROOT / 'scripts/render_views.mjs'), '--obj', 'model/Mustang_160mm_assembled.obj', '--out', tmp,
                        '--views', ','.join(views), '--modes', ','.join(modes), '--w', '2000', '--h', '1250'], check=True, cwd=ROOT)
        PREVIEWS.mkdir(exist_ok=True)
        for name, (view, mode) in PLAN.items():
            shutil.copyfile(Path(tmp) / f"{view}{'' if mode == 'shaded' else '_' + mode}.png", PREVIEWS / name)
    print('PREVIEWS_COMPLETE', len(PLAN), 'images in', PREVIEWS.relative_to(ROOT))

if __name__ == '__main__':
    sys.exit(main())
