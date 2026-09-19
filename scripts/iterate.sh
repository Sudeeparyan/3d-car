#!/bin/zsh
# One likeness-loop iteration: rebuild geometry, paint, assemble, render, validate.
# Usage: scripts/iterate.sh <iteration-name> [--skip-body]
set -e
cd "$(dirname "$0")/.."
NAME=${1:-current}
OUT=validation/likeness/$NAME
mkdir -p "$OUT"
PY=.venv/bin/python
if [[ "$2" != "--skip-body" ]]; then $PY scripts/build_body.py | tail -1; fi
$PY scripts/build_parts.py | tail -1
$PY scripts/paint_mesh.py | tail -1
$PY scripts/assemble_obj.py
node scripts/render_views.mjs --obj model/Mustang_160mm_assembled.obj --out "$OUT" \
  --views three,side,sideR,side_persp,front,rear,rear34,top,wheel,grille,frontlow,rearlow --modes shaded,flat,silhouette
$PY scripts/validate_likeness.py "$OUT"
# Keep the scored iterations out of git (validation/likeness/iter_*); promote a run with
#   scripts/promote_likeness.sh <name>   -> validation/likeness/final (tracked, in the package)
