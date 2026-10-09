"""Generic board mounting hole: a single NPTH, no copper, with a small
silkscreen reference circle so it's visible in the PCB editor/plots. Used
for the 2 front-panel mounting holes (left edge of the board) -- see
docs/design_notes.md / docs/front-panel-notes.md and build_pcb.py for
placement. Not tied to any particular connector/part, just a plain hole.
"""
import os

DRILL = 2.8

out = []
out.append(f'''(footprint "MountingHole_2.8mm"
\t(version 20221018)
\t(generator "cs1800_tools")
\t(generator_version "10.0")
\t(layer "Dwgs.User")
\t(descr "Plain NPTH board mounting hole, 2.8mm drill, no copper -- mechanical only.")
\t(tags "mounting hole")
\t(attr exclude_from_pos_files exclude_from_bom)
\t(property "Reference" "REF**"
\t\t(at 0 -3.5 0)
\t\t(layer "Dwgs.User")
\t\t(effects (font (size 1 1) (thickness 0.15)))
\t)
\t(property "Value" "MountingHole_2.8mm"
\t\t(at 0 3.5 0)
\t\t(layer "Dwgs.User")
\t\t(effects (font (size 1 1) (thickness 0.15)))
\t)''')

out.append(f'''\t(fp_circle
\t\t(center 0 0)
\t\t(end {DRILL/2 + 0.5} 0)
\t\t(stroke (width 0.12) (type solid))
\t\t(fill none)
\t\t(layer "Dwgs.User")
\t)
\t(pad "" np_thru_hole circle
\t\t(at 0 0)
\t\t(size {DRILL} {DRILL})
\t\t(drill {DRILL})
\t\t(layers "*.Cu" "*.Mask")
\t)''')

out.append('\t(embedded_fonts no)\n)\n')

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                         "libraries", "footprints", "cs1800.pretty",
                         "MountingHole_2.8mm.kicad_mod")
with open(OUT_PATH, "w") as f:
    f.write("\n".join(out))
print("wrote", OUT_PATH)
