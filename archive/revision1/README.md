# Revision 1 artifacts (reference only)

Outputs of the first revision of this model (17 September 2026), kept for reference.
They do **not** match the current geometry in `print/`, `multicolor/` and `model/`:

- `Mustang_160mm_editable_rev1.blend` / `.blend1` - the Blender scene of revision 1.
  The current revision is generated entirely by `scripts/` without Blender.
- `generic_slicer/` - PrusaSlicer 2.9.6 generic single-colour slicing simulation of the
  revision-1 STLs (about 8 h 37 min and 104 g for body + four wheels). The current
  parts have the same footprint and about 2 % less volume. The `.gcode.txt` files are
  simulation output for analysis only and must never be sent to a printer.
- `multicolor_import/` - PrusaSlicer 2.9.6 import/export audit of the revision-1 3MF
  colour packages. The 3MF container format is unchanged in the current revision.

Nothing in this folder is part of the gift package ZIP.
