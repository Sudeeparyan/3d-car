"""Create a technical color sheet and a portable handoff from checked artifacts."""
from pathlib import Path
import json, zipfile, hashlib, html
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'previews'
manifest = json.loads((ROOT / 'work/manifest.json').read_text())
FONT = Path('C:/Windows/Fonts')
def font(size, bold=False):
    return ImageFont.truetype(str(FONT / ('segoeuib.ttf' if bold else 'segoeui.ttf')), size)

canvas = Image.new('RGB', (2400, 1930), '#1d242c')
draw = ImageDraw.Draw(canvas)
ink, muted, accent = '#f4f5f6', '#b8c6d3', '#8bcced'
draw.text((90, 60), 'YOUR MUSTANG GT', font=font(76, True), fill=ink)
draw.text((94, 159), '160 mm gift miniature  /  Color and assembly reference', font=font(34), fill=muted)

def panel(file, pos, width):
    im = Image.open(P / file).convert('RGB')
    im = im.resize((width, round(im.height * width / im.width)), Image.Resampling.LANCZOS)
    canvas.paste(im, pos)
    return im.size

draw.text((95, 255), '01  FRONT', font=font(28, True), fill=accent)
draw.text((1265, 255), '02  REAR', font=font(28, True), fill=accent)
panel('01_painted_front.png', (55, 305), 1130)
panel('02_painted_rear.png', (1215, 305), 1130)
draw.line((90, 1020, 2310, 1020), fill='#47515b', width=2)
draw.text((95, 1070), '03  SIDE & SIZE', font=font(28, True), fill=accent)
side = '08_painted_side.png'
panel(side, (45, 1130), 1410)

# The orthographic side image is 181 mm wide in model space.
left = 45 + 1410 * (181 - 160) / (2 * 181)
right = left + 1410 * 160 / 181
y = 1720
draw.line((left, y, right, y), fill=accent, width=3)
for x, direction in [(left, 1), (right, -1)]:
    draw.line((x, y - 22, x, y + 22), fill=accent, width=2)
    draw.polygon([(x,y),(x+direction*18,y-8),(x+direction*18,y+8)],fill=accent)
label = '160 mm / 16 cm'
draw.rectangle((560, y-27, 970, y+30), fill='#1d242c')
draw.text((578, y-28), label, font=font(35, True), fill=ink)

draw.text((1570, 1100), 'FOUR-COLOR PALETTE', font=font(30, True), fill=ink)
colors = [('#F3F2EB', 'White', 'Body, hood and roof'),
          ('#16191D', 'Black', 'Windows, stripes, trim and tires'),
          ('#4F545A', 'Dark grey', 'Wheel spokes and hubs'),
          ('#BF1725', 'Red', 'Rear lights and brake details')]
for index,(swatch,title,description) in enumerate(colors):
    yy=1170+index*112
    draw.rounded_rectangle((1570, yy, 1624, yy+54), 11, fill=swatch, outline='#7b8996', width=2)
    draw.text((1650, yy-4), title, font=font(30,True), fill=ink)
    draw.text((1650, yy+39), description, font=font(24), fill=muted)
draw.text((1570, 1650), '1 body + 4 fixed wheels', font=font(28,True), fill=ink)
draw.text((1570, 1695), 'Assembly: 160 × 69.49 × 47.14 mm', font=font(26), fill=muted)
draw.text((95, 1810), 'Rendered from the delivered 3D geometry. Simplified from your photographs; surface detail is approximate.', font=font(26), fill=muted)
draw.text((95, 1860), 'Printer setup and a physical sample are still required. This sheet is a visual guide, not a scale drawing.', font=font(25), fill=muted)
canvas.save(P / '00_COLOR_AND_ASSEMBLY_DIAGRAM.png')

start = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Your Mustang gift</title>
<style>body{margin:0;background:#eff2f5;color:#162231;font:17px/1.6 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:36px 24px}h1{font-size:clamp(32px,5vw,58px);line-height:1.1}h2{font-size:26px}a{color:#005985}img{width:100%;border-radius:18px}.card{background:white;border:1px solid #d8e0e6;border-radius:16px;padding:24px;margin:22px 0}.tag{color:#356079;font-weight:650}li{margin:10px 0}.note{border-left:4px solid #e5aa4b;padding-left:18px}small{color:#506070}</style>
<main><p class="tag">160 MM MUSTANG GT · PERSONAL GIFT</p><h1>Your car, made miniature.</h1>
<p>The model files and color reference are prepared. The college technician must choose the real printer profile, check the slice and run a small sample before the full print.</p>
<img src="previews/00_COLOR_AND_ASSEMBLY_DIAGRAM.png" alt="Front, rear and side renders of the white Mustang model with a four-color legend and 160 mm length">
<section class="card"><h2>Take this whole folder to college</h2><ol>
<li>Open the <a href="docs/PRINT_AND_PAINT_GUIDE.html">print and assembly guide</a> with the technician.</li>
<li>If the printer supports multiple colors, use <a href="multicolor/README.md">the multicolor parts and import instructions</a>. Keep each physical object’s colored parts aligned together and assign the matching filament colors in the slicer.</li>
<li>If it supports one color, use <a href="print/01_body_160mm.stl">the body STL</a> and the four labeled wheel STLs in <strong>print/</strong>. Print in white and paint to match the color sheet.</li>
<li>Print <a href="print/06_detail_test_1to1.stl">the detail sample</a> and one wheel at full scale. Then print one body and four wheels, finish and glue.</li></ol>
<p class="note">Printer model, material and color capability are unconfirmed. These files are models for the slicer; no machine-ready G-code is included. Standard STL files do not contain colors.</p></section>
<section class="card"><h2>View or edit the complete car</h2><p><a href="model/Mustang_160mm_editable.blend">Editable Blender model</a> · <a href="model/Mustang_160mm_assembled.obj">Assembled OBJ</a> + <a href="model/Mustang_160mm_assembled.mtl">matching MTL colors</a></p>
<p>Keep the OBJ and MTL together. The assembly is for viewing and editing; print the separate physical pieces. The wheels are fixed and glued in place.</p></section>
<section class="card"><h2>Checks completed</h2><p><a href="validation/GEOMETRY_REPORT.md">Standard mesh checks</a> and a <a href="validation/generic_slicer/README.md">generic single-color slicing preflight</a> pass. That simulation estimated about 8 hours 37 minutes and 104 g for one body and four wheels. The actual printer may differ; multicolor printing needs its own estimate.</p>
<p>See <a href="multicolor/README.md">the multicolor notes</a> and <a href="validation/multicolor_import/README.md">slicer import audit</a> for color-volume checks and import limits. The <a href="docs/PLAN_CHECK.md">plan comparison</a> records what is complete and what remains. No physical model has been printed yet.</p></section>
<small>Body adapted from “Ford Mustang GT 2018” by SadPepe, Thingiverse 3192801, CC BY-NC 4.0. Wheels independently generated. See <a href="docs/ATTRIBUTION.md">attribution</a> and <a href="reference_assets/SOURCE_NOTES.md">source notes</a>. This is a simplified photo-inspired miniature, not a measured replica.</small></main></html>'''
(ROOT / 'START_HERE.html').write_text(start, encoding='utf-8')

# Only reviewed deliverables go into the handoff; omit tool runtimes, backups,
# private reference photographs and generic simulation machine instructions.
files = [ROOT/'START_HERE.html', ROOT/'README.md', ROOT/'ATTRIBUTION.md']
for directory in ['print','multicolor','docs','previews']:
    files += [p for p in (ROOT/directory).rglob('*') if p.is_file()]
files += [p for p in (ROOT/'model').glob('*') if p.suffix in {'.obj','.mtl','.blend','.glb'}]
files += [ROOT/'validation/GEOMETRY_REPORT.md', ROOT/'validation/geometry_report.json', ROOT/'validation/assembly_export_check.json']
files += [p for p in (ROOT/'validation/generic_slicer').glob('*') if p.suffix in {'.json','.png','.md'}]
files += [p for p in (ROOT/'validation/multicolor_import').glob('*') if p.suffix in {'.json','.png','.md'}]
files += [ROOT/'reference_assets/SOURCE_NOTES.md',ROOT/'reference_assets/thingiverse_3192801/README.txt',ROOT/'reference_assets/thingiverse_3192801/LICENSE.txt']
files = sorted({p for p in files if p.is_file()})
checksums = '\n'.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}' for p in files)+'\n'
(ROOT/'PACKAGE_SHA256SUMS.txt').write_text(checksums,encoding='utf-8')
files.append(ROOT/'PACKAGE_SHA256SUMS.txt')
target=ROOT/'Mustang_Gift_Package.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in files: archive.write(p, 'Mustang_Gift_Package/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    assert not any('gcode' in x.lower() or '.blend1' in x for x in archive.namelist())
print(json.dumps({'archive':str(target),'bytes':target.stat().st_size,'files':len(files),'diagram':str(P/'00_COLOR_AND_ASSEMBLY_DIAGRAM.png')},indent=2))
