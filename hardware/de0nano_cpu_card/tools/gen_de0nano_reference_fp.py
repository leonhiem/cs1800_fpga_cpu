"""Mechanical-reference-only footprint for the DE0-Nano board: just an
outline + its 4 real mounting holes, no pads, no electrical connection --
the DE0-Nano doesn't solder to this board at all, it connects via two
ribbon cables to the JP1/JP2 IDC headers. This exists purely so the board
has a visual/mechanical keepout showing where the DE0-Nano physically sits,
and real holes to bolt it down with standoffs.

Dimensions from docs/de0-nano_notes.md (community-sourced, not an official
Terasic drawing -- sanity-check against the physical board before drilling
final holes): 49 x 75.2mm board, 4x M3 mounting holes at board-local
(3.5,3.5) / (3.5,71.7) / (45.5,3.5) / (45.5,71.7) mm.
"""
import os

W, H = 49.0, 75.2
HOLES = [(3.5, 3.5), (3.5, 71.7), (45.5, 3.5), (45.5, 71.7)]
HOLE_DRILL = 3.2  # M3 clearance

out = []
out.append('''(footprint "DE0Nano_Reference_Outline"
\t(version 20221018)
\t(generator "cs1800_tools")
\t(generator_version "10.0")
\t(layer "Dwgs.User")
\t(descr "Mechanical reference only -- DE0-Nano outline + its 4 real M3 mounting holes. No pads: the DE0-Nano connects via 2 ribbon cables to the JP1/JP2 IDC headers, not by soldering to this board. Dims from docs/de0-nano_notes.md (community-sourced, verify against the physical board).")
\t(tags "DE0-Nano mechanical reference keepout")
\t(attr exclude_from_pos_files exclude_from_bom)
\t(property "Reference" "DE0NANO"
\t\t(at 24.5 -3 0)
\t\t(layer "Dwgs.User")
\t\t(effects (font (size 1.5 1.5) (thickness 0.2)))
\t)
\t(property "Value" "DE0-Nano (mechanical reference, not populated)"
\t\t(at 24.5 79 0)
\t\t(layer "Dwgs.User")
\t\t(effects (font (size 1 1) (thickness 0.15)))
\t)''')

# Board outline on the user/drawing layer (not silkscreen -- this isn't a
# real populated part, so it shouldn't show up as if it were one)
out.append(f'''\t(fp_rect
\t\t(start 0 0)
\t\t(end {W} {H})
\t\t(stroke (width 0.15) (type dash))
\t\t(fill none)
\t\t(layer "Dwgs.User")
\t)''')

for i, (hx, hy) in enumerate(HOLES):
    out.append(f'''\t(pad "" np_thru_hole circle
\t\t(at {hx} {hy})
\t\t(size {HOLE_DRILL} {HOLE_DRILL})
\t\t(drill {HOLE_DRILL})
\t\t(layers "*.Cu" "*.Mask")
\t)''')

out.append('\t(embedded_fonts no)\n)\n')

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                         "libraries", "footprints", "cs1800.pretty",
                         "DE0Nano_Reference_Outline.kicad_mod")
with open(OUT_PATH, "w") as f:
    f.write("\n".join(out))
print("wrote", OUT_PATH)
