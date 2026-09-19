#!/bin/zsh
# Copy one likeness iteration's report and key renders to validation/likeness/final.
# Usage: scripts/promote_likeness.sh <iteration-name>
set -e
cd "$(dirname "$0")/.."
SRC=validation/likeness/${1:?iteration name}
DST=validation/likeness/final
rm -rf "$DST"; mkdir -p "$DST"
for f in likeness.json contact_sheet.jpg profile_compare.png three.png rear34.png side.png front.png rear.png top.png wheel.png grille.png frontlow.png rearlow.png side_persp.png; do
  cp "$SRC/$f" "$DST/$f"
done
echo "promoted $SRC -> $DST"
