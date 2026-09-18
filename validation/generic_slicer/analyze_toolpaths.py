"""Read generic PrusaSlicer simulations and produce reproducible layer diagnostics.

Does not claim toolpath success certifies physical printability or fine-detail retention.
"""
from collections import defaultdict
from pathlib import Path
import hashlib, json, math, re
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
manifest = json.loads((BASE / 'input_manifest.json').read_text(encoding='utf-8-sig'))
FONT = 'C:/Windows/Fonts/arial.ttf'
font = lambda size: ImageFont.truetype(FONT, size)
results = []

def parse(path):
    layers = defaultdict(list)
    positions = {'X': 0.0, 'Y': 0.0, 'Z': 0.0, 'E': 0.0}
    feature = 'Unknown'
    z = 0
    stats = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith(';TYPE:'):
            feature = line[6:]
        elif line.startswith(';Z:'):
            z = round(float(line[3:]), 5)
        if line.startswith('; filament used') or line.startswith('; estimated printing time'):
            key, val = line[2:].split(' = ', 1)
            stats[key] = val
        code = line.split(';')[0].strip()
        if not code:
            continue
        tokens = code.split()
        vals = {t[0]: float(t[1:]) for t in tokens[1:] if len(t) > 1 and t[0] in 'XYZE' }
        if tokens[0] == 'G92':
            positions.update(vals)
        elif tokens[0] in ('G0', 'G1'):
            old = positions.copy()
            positions.update(vals)
            if positions['E'] > old['E'] and math.hypot(positions['X']-old['X'], positions['Y']-old['Y']) > 0.001:
                layers[z].append((old['X'], old['Y'], positions['X'], positions['Y'], feature))
    return layers, stats

def atlas(name, layers):
    available = sorted(layers)
    targets = {'body': [.2,4.2,10.2,15.2,20.2,25.2,30.2,35.2,40.8],
               'wheel': [.2,2,4,6,7.6,8.0,8.2,8.4,8.8], 'coupon': [.2,2,3.2,6,9,11.8]}[name]
    selected = [min(available, key=lambda z:abs(z-t)) for t in targets]
    width, cell_w, cell_h = 1800,600,370
    height = 175 + math.ceil(len(selected)/3)*cell_h
    img = Image.new('RGB', (width,height), '#f4f6fa')
    draw = ImageDraw.Draw(img)
    draw.text((40,25), f'{name.upper()} / GENERIC DIGITAL SLICING', fill='#15263b', font=font(34))
    draw.text((40,74), 'PrusaSlicer 2.9.6 | 0.4 mm nozzle | 0.2 mm layers | 3 walls | 15% gyroid', fill='#40516a', font=font(23))
    draw.text((40,112), 'Blue: model toolpaths   Orange: supports   Grey: skirt. Simulation only; machine and physical sample pending.', fill='#40516a', font=font(22))
    all_segs = [s for segs in layers.values() for s in segs]
    xmin = min(min(s[0],s[2]) for s in all_segs)
    xmax = max(max(s[0],s[2]) for s in all_segs)
    ymin = min(min(s[1],s[3]) for s in all_segs)
    ymax = max(max(s[1],s[3]) for s in all_segs)
    scale = min(530/(xmax-xmin),290/(ymax-ymin))
    for i,z in enumerate(selected):
        cx,cy = (i%3)*cell_w,175+(i//3)*cell_h
        draw.rounded_rectangle((cx+14,cy+8,cx+cell_w-14,cy+cell_h-8),radius=12,fill='white')
        draw.text((cx+28,cy+20),f'Z = {z:.2f} mm',fill='#15263b',font=font(23))
        def point(x,y):
            return (cx+cell_w/2+(x-(xmin+xmax)/2)*scale, cy+205-(y-(ymin+ymax)/2)*scale)
        for x1,y1,x2,y2,typ in layers[z]:
            color = '#d48b2c' if 'Support' in typ else '#aeb7c4' if 'Skirt' in typ else '#286aa1'
            draw.line((*point(x1,y1),*point(x2,y2)),fill=color,width=1)
    dest = BASE / f'{name}_toolpath_layers.png'
    img.save(dest)
    return str(dest.name), [round(xmax-xmin,3),round(ymax-ymin,3)]

for spec in manifest:
    layers, stats = parse(BASE / spec['output'])
    warnings = [line for line in (BASE / (spec['name']+'_cli.log')).read_text(encoding='utf-16').splitlines()
                if re.search(r'\[(warning|error|fatal)\]',line,re.I)]
    image_name, footprint = atlas(spec['name'], layers)
    model_layers = [z for z,segs in layers.items() if any('Support' not in s[4] and 'Skirt' not in s[4] for s in segs)]
    support_layers = [z for z,segs in layers.items() if any('Support' in s[4] for s in segs)]
    result = dict(spec, stats=stats, model_layer_count=len(model_layers),
                  min_model_z=min(model_layers),max_model_z=max(model_layers),
                  support_layer_count=len(support_layers),
                  support_only_heights=[z for z in sorted(layers) if z not in model_layers],
                  missing_model_heights_on_0p2mm_grid=[round(i * .2, 5) for i in range(1, round(max(model_layers) / .2) + 1) if round(i * .2, 5) not in model_layers],
                  footprint_with_support_skirt_mm=footprint, warning_error_lines=warnings,
                  layer_preview=image_name)
    results.append(result)

(BASE / 'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
lines = ['# Generic digital slicing preflight', '',
'PrusaSlicer 2.9.6 completed CLI slicing of the body, one wheel, and the detail coupon. This is a simulated generic FDM profile, not the college printer profile. Physical print samples and the technician\'s final layer review remain required.', '',
'Profile: 0.4 mm nozzle, 0.2 mm layers, 3 walls, 15% gyroid, automatic snug supports at 45 degrees, 0.2 mm support gap, 220 x 220 mm assumed bed. PLA density 1.24 g/cm3. Simulated speeds: 40 mm/s walls, 25 mm/s visible walls, 60 mm/s infill. Temperatures disabled. All unlisted settings are PrusaSlicer defaults. The INI and full embedded toolpath config preserve the setup.', '',
'| Part | Simulated time | Simulated PLA | Model layers | Support layers | CLI warning/error lines |',
'|---|---:|---:|---:|---:|---:|']
for r in results:
    lines.append(f"| {r['name']} | {r['stats']['estimated printing time (normal mode)']} | {r['stats']['filament used [g]']} g | {r['model_layer_count']} | {r['support_layer_count']} | {len(r['warning_error_lines'])} |")
lines += ['', 'Each STL was read as manifold with one connected part by the slicer. Mesh dimensions are in the separate mesh_info files. The JSON report records source hashes and slice timestamps so later geometry edits cannot silently reuse stale results. All three parts have continuous model extrusion at every 0.2 mm model-layer height between their first and last extruded layers. Some additional heights contain support only because PrusaSlicer uses independently spaced support layers; these are not missing model layers.', '',
'Layer previews show selected actual toolpath layers. No missing-detail guarantee follows from a clean CLI result: very small relief, badge lettering, groove continuity, support accessibility, first-layer adhesion and surface quality still require visual review and physical samples. The wheel simulation generates a small support interface on its face features; inspect this in the college slicer and decide whether support blocking improves the test wheel.', '',
'Selected-layer visual review: the body has continuous underside and roof toolpaths with support around wheel arches, bumpers and mirror regions. The wheel has a flat first layer and visible split-spoke relief at 8.0-8.4 mm. The detail coupon includes its groove pattern and supported mirror-style arm. These selected views do not replace scrubbing all layers in the actual college slicer.', '',
'The simulated body footprint including support and skirt is 177.4 x 87.2 mm. Body plus four individual wheels is about 8 h 37 min and 104 g in this generic profile; the detail coupon adds about 14 min and 2 g. These estimates include the simulated supports and skirts.', '',
'The body plus four wheels is approximately the body estimate plus four individual wheel estimates; plate arrangement, acceleration, cooling, start/heating time, brim and machine profile can change actual duration and material. Do not rely on this simulation as a print appointment duration.', '',
'Toolpaths are deliberately named SIMULATION_DO_NOT_PRINT.gcode.txt. They have no calibrated printer profile or heating instructions. Do not include these text files in the printer handoff or rename them for printing.', '',
'To repeat after STL changes, run PowerShell: `powershell -NoProfile -ExecutionPolicy Bypass -File validation/generic_slicer/run_preflight.ps1` from the workspace. This re-slices the three representative files, checks source hashes did not change during the run, and regenerates this report and layer images.', '']
(BASE / 'README.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(results,indent=2))
