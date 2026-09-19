"""Create the colour/assembly sheet, START_HERE.html and the portable handoff ZIP from checked artifacts.

Run last: after build_parts, paint_mesh, assemble_obj, make_previews, build_multicolor
and validate_parts. Only reviewed deliverables go into the ZIP.
"""
from pathlib import Path
import json, zipfile, hashlib, html, platform
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'previews'
manifest = json.loads((ROOT / 'work/manifest.json').read_text())
geometry = json.loads((ROOT / 'validation/geometry_report.json').read_text())
multicolor = json.loads((ROOT / 'multicolor/validation.json').read_text())
likeness_dir = ROOT / 'validation/likeness/final'
likeness = json.loads((likeness_dir / 'likeness.json').read_text())['summary'] if (likeness_dir / 'likeness.json').exists() else None

FONT_DIRS = {
    'Windows': [('C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/segoeuib.ttf')],
    'Darwin': [('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf')],
    'Linux': [('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')],
}
def font(size, bold=False):
    for regular, heavy in FONT_DIRS.get(platform.system(), []) + [v for vs in FONT_DIRS.values() for v in vs]:
        path = heavy if bold else regular
        if Path(path).exists(): return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)

body_dims = geometry['parts'][0]['dimensions_mm']; wheel_dims = geometry['parts'][1]['dimensions_mm']; asm = geometry['assembly_dimensions_mm']
fmt = lambda d: ' × '.join(f'{x:.2f}' for x in d)

# ---------------------------------------------------------------- colour and assembly sheet
canvas = Image.new('RGB', (2400, 2080), '#1d242c')
draw = ImageDraw.Draw(canvas)
ink, muted, accent = '#f4f5f6', '#b8c6d3', '#8bcced'
draw.text((90, 60), 'YOUR MUSTANG GT', font=font(76, True), fill=ink)
draw.text((94, 159), '160 mm gift miniature  /  Colour and assembly reference', font=font(34), fill=muted)

def panel(file, pos, width):
    im = Image.open(P / file).convert('RGB')
    im = im.resize((width, round(im.height * width / im.width)), Image.Resampling.LANCZOS)
    canvas.paste(im, pos)
    return im.size

draw.text((95, 255), '01  FRONT', font=font(28, True), fill=accent)
draw.text((1265, 255), '02  REAR', font=font(28, True), fill=accent)
panel('01_painted_front.png', (55, 305), 1130)
panel('02_painted_rear.png', (1215, 305), 1130)
draw.line((90, 1040, 2310, 1040), fill='#47515b', width=2)
draw.text((95, 1080), '03  SIDE & SIZE', font=font(28, True), fill=accent)
panel('08_painted_side.png', (45, 1140), 1410)          # orthographic, 181 mm across the image

left = 45 + 1410 * (181 - 160) / (2 * 181)
right = left + 1410 * 160 / 181
y = 1740
draw.line((left, y, right, y), fill=accent, width=3)
for x, direction in [(left, 1), (right, -1)]:
    draw.line((x, y - 22, x, y + 22), fill=accent, width=2)
    draw.polygon([(x, y), (x + direction * 18, y - 8), (x + direction * 18, y + 8)], fill=accent)
draw.rectangle((560, y - 27, 970, y + 30), fill='#1d242c')
draw.text((578, y - 28), '160 mm / 16 cm', font=font(35, True), fill=ink)

draw.text((1570, 1100), 'COLOURS IN THE PREVIEW', font=font(30, True), fill=ink)
colors = [('#F3F2EB', 'White', 'Body, hood, roof, DRL slashes, number plate'),
          ('#16191D', 'Black', 'Glass, mirrors, grille, spoiler, stripe, trim, tyres'),
          ('#0E1114', 'Gloss black', 'Running-pony badge, 5.0 badges, plate lettering'),
          ('#4F545A', 'Gunmetal', 'Wheel spokes, rims and hubs'),
          ('#BF1725', 'Red', 'Six tail-light bars and the brake calipers'),
          ('#C4C6C8', 'Silver', 'RTR wheel-cap monogram and ring, exhaust tips'),
          ('#D9822B', 'Amber', 'Headlamp corner markers')]
for index, (swatch, title, description) in enumerate(colors):
    yy = 1160 + index * 80
    draw.rounded_rectangle((1570, yy, 1624, yy + 54), 11, fill=swatch, outline='#7b8996', width=2)
    draw.text((1650, yy - 4), title, font=font(30, True), fill=ink)
    draw.text((1650, yy + 36), description, font=font(23), fill=muted)
draw.text((1570, 1730), 'Multicolour print: white / black / red / dark grey', font=font(26, True), fill=ink)
draw.text((1570, 1770), 'silver prints white; amber, pony and 5.0 badges print black', font=font(23), fill=muted)
draw.text((1570, 1830), '1 body + 4 fixed wheels', font=font(28, True), fill=ink)
draw.text((1570, 1875), f'Assembly: {fmt(asm)} mm', font=font(26), fill=muted)
draw.text((95, 1930), 'Rendered from the delivered 3D geometry with the same colour regions the multicolour files use. Simplified from your photographs.', font=font(25), fill=muted)
draw.text((95, 1980), 'Printer setup and a physical sample are still required. This sheet is a visual guide, not a scale drawing.', font=font(25), fill=muted)
canvas.save(P / '00_COLOR_AND_ASSEMBLY_DIAGRAM.png')

# ---------------------------------------------------------------- START_HERE.html
score = f"{likeness['score_percent']}% ({likeness['features_passed']}/{likeness['features_total']} photo features, roof/deck profile within {likeness['profile_top_mean_abs_mm']:.2f} mm)" if likeness else 'not run'
plate_text = manifest.get('plate_text', '')
plate_html = f' lettered "{html.escape(plate_text)}"' if plate_text.strip() else ' (blank until the registration is supplied)'
start = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Your Mustang gift</title>
<style>body{{margin:0;background:#eff2f5;color:#162231;font:17px/1.6 system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:36px 24px}}h1{{font-size:clamp(32px,5vw,58px);line-height:1.1}}h2{{font-size:26px}}a{{color:#005985}}img{{width:100%;border-radius:18px}}.card{{background:white;border:1px solid #d8e0e6;border-radius:16px;padding:24px;margin:22px 0}}.tag{{color:#356079;font-weight:650}}li{{margin:10px 0}}.note{{border-left:4px solid #e5aa4b;padding-left:18px}}small{{color:#506070}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}}.grid img{{border-radius:10px}}</style>
<main><p class="tag">160 MM MUSTANG GT · PERSONAL GIFT</p><h1>Your car, made miniature.</h1>
<p>The model files and colour reference are prepared. The college technician must choose the real printer profile, check the slice and run a small sample before the full print.</p>
<img src="previews/00_COLOR_AND_ASSEMBLY_DIAGRAM.png" alt="Front, rear and side renders of the white Mustang model with a colour legend and 160 mm length">
<section class="card"><h2>Take this whole folder to college</h2><ol>
<li>Open the <a href="docs/PRINT_AND_PAINT_GUIDE.html">print and assembly guide</a> with the technician.</li>
<li>If the printer supports multiple colours, use <a href="multicolor/README.md">the multicolour parts and import instructions</a> (white, black, red and dark grey). Keep each physical object's coloured parts aligned together and assign the matching filaments in the slicer.</li>
<li>If it prints one colour, use <a href="print/01_body_160mm.stl">the body STL</a> and the four labelled wheel STLs in <strong>print/</strong>. Print in white and paint to match the colour sheet; the grille, lamps, vents, slots and diffuser are recessed so the details show even unpainted.</li>
<li>Print <a href="print/06_detail_test_1to1.stl">the detail sample</a> and one wheel at full scale. Then print one body and four wheels, finish and glue.</li></ol>
<p class="note">Printer model, material and colour capability are unconfirmed. These files are models for the slicer; no machine-ready G-code is included. Standard STL files do not contain colours.</p></section>
<section class="card"><h2>What the model shows</h2>
<p>Gloss-black running-pony badge in a recessed hexagonal grille, slim smoked headlamps with three LED slashes and amber corner markers, lower intake and chin splitter, twin hood vents, black wedge mirrors, dark door / quarter / windscreen / rear glass, black "5.0" fender badges readable on both sides, the four-hash-mark rocker stripe, seven-Y-spoke gunmetal RTR Aero 7 wheels with the RTR centre-cap monogram and red calipers, tri-bar tail lights, black rear panel and lip spoiler, rear diffuser with quad exhaust tips, a shark-fin antenna and a rear number plate{plate_html}.</p>
<div class="grid"><img src="previews/16_painted_grille_detail.png" alt="Grille and pony badge"><img src="previews/15_painted_wheel_detail.png" alt="RTR wheel with red caliper"><img src="previews/13_painted_front_low.png" alt="Front three-quarter"><img src="previews/14_painted_rear_low.png" alt="Rear three-quarter"></div></section>
<section class="card"><h2>View the complete car</h2><p><a href="viewer.html">Interactive 3D viewer</a> (open the folder with a local web server, e.g. <code>python3 -m http.server</code>, then browse to viewer.html) · <a href="model/Mustang_160mm_assembled.obj">Assembled OBJ</a> + <a href="model/Mustang_160mm_assembled.mtl">matching MTL colours</a></p>
<p>Keep the OBJ and MTL together. The assembly is for viewing; print the separate physical pieces. The wheels are fixed and glued in place.</p></section>
<section class="card"><h2>Checks completed</h2><p><a href="validation/GEOMETRY_REPORT.md">Standard mesh checks</a> pass for all six print STLs (body {fmt(body_dims)} mm, wheel {fmt(wheel_dims)} mm, assembly {fmt(asm)} mm). The multicolour volumes are closed, do not overlap and rebuild each part (<a href="multicolor/validation.json">record</a>). Photo likeness score of the render loop: {score} (<a href="validation/likeness/README.md">how it is measured</a>).</p>
<p>The earlier revision's generic single-colour slicing simulation estimated about 8 hours 37 minutes and 104 g for one body and four wheels; this revision has the same footprint and 2% less volume, so plan for a similar figure. The actual printer may differ; multicolour printing needs its own estimate. The <a href="docs/PLAN_CHECK.md">plan comparison</a> records what is complete and what remains. No physical model has been printed yet.</p></section>
<small>Body adapted from "Ford Mustang GT 2018" by SadPepe, Thingiverse 3192801, CC BY-NC 4.0. Wheels independently generated. See <a href="docs/ATTRIBUTION.md">attribution</a> and <a href="reference_assets/SOURCE_NOTES.md">source notes</a>. This is a simplified photo-inspired miniature, not a measured replica.</small></main></html>'''
(ROOT / 'START_HERE.html').write_text(start, encoding='utf-8')

# ---------------------------------------------------------------- ZIP
# Only reviewed deliverables: no tool runtimes, work files, node_modules, private photographs,
# archived revision-1 outputs or generic simulation machine instructions.
files = [ROOT / 'START_HERE.html', ROOT / 'README.md', ROOT / 'viewer.html']
for directory in ['print', 'multicolor', 'docs', 'previews']:
    files += [p for p in (ROOT / directory).rglob('*') if p.is_file()]
files += [p for p in (ROOT / 'model').glob('*') if p.suffix in {'.obj', '.mtl'}]
files += [ROOT / 'validation/GEOMETRY_REPORT.md', ROOT / 'validation/geometry_report.json', ROOT / 'validation/assembly_export_check.json',
          ROOT / 'validation/likeness/README.md']
files += [likeness_dir / n for n in ('contact_sheet.jpg', 'likeness.json', 'profile_compare.png')]
files += [ROOT / 'reference_assets/SOURCE_NOTES.md', ROOT / 'reference_assets/thingiverse_3192801/README.txt', ROOT / 'reference_assets/thingiverse_3192801/LICENSE.txt']
files = sorted({p for p in files if p.is_file()})
checksums = '\n'.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}' for p in files) + '\n'
(ROOT / 'PACKAGE_SHA256SUMS.txt').write_text(checksums, encoding='utf-8')
files.append(ROOT / 'PACKAGE_SHA256SUMS.txt')
target = ROOT / 'Mustang_Gift_Package.zip'
with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for p in files: archive.write(p, 'Mustang_Gift_Package/' + p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    assert not any('gcode' in x.lower() or '.blend' in x for x in archive.namelist())
print(json.dumps({'archive': str(target), 'bytes': target.stat().st_size, 'files': len(files), 'diagram': str(P / '00_COLOR_AND_ASSEMBLY_DIAGRAM.png')}, indent=2))
