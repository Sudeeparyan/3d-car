from pathlib import Path
import json
import trimesh

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'work'
out.mkdir(exist_ok=True)
data = {}
for filename in ['mustangBodyOnly.stl', 'MustangCompleteWithWheels.stl']:
    mesh = trimesh.load_mesh(ROOT / 'reference_assets/thingiverse_3192801/files' / filename)
    parts = mesh.split(only_watertight=False, repair=False)
    rows=[]
    for i,p in enumerate(parts):
        row={'index':i,'faces':len(p.faces),'bounds':p.bounds.tolist(), 'extents':p.extents.tolist(), 'center':p.bounds.mean(axis=0).tolist(),'closed':p.is_watertight}
        rows.append(row)
    data[filename]=rows
    print(filename, 'component count',len(rows))
    for row in rows:
        if row['faces']>100:
            print(row)
(out/'source_components.json').write_text(json.dumps(data,indent=2))
