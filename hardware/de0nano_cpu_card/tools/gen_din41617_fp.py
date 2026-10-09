N_PINS = 31
PITCH = 2.5
DRILL = 1.1
PAD = 2.0
MOUNT_DRILL = 2.8
MOUNT_INSET = 5.0   # beyond pin1/pin31, same axis -- cross-checked against
                     # the datasheet's own D=85mm (31-pos) hole-to-hole
                     # dimension: span(75) + 2*MOUNT_INSET(5) = 85. [OK]
ZIGZAG = 2.54       # odd pins at local y=0 ("close to PCB edge" once placed),
                     # even pins 2.54mm further in y ("inward") -- per the
                     # datasheet's PCB-hole-pattern drawing (zigzag row, not
                     # a single straight row) and confirmed against the
                     # physical part by the user, 2026-10-09.
MOUNT_Y_OFFSET = 2.5   # mounting hole is 2.5mm from pin1/pin31 in +y (the
                        # same direction that already makes ODD pins the
                        # "close to board edge" row -- i.e. further toward
                        # the board edge / the connector's mating face, not
                        # further inboard). Per the user's direct read of
                        # the datasheet's PCB-hole-pattern drawing, 2026-10-09.
PLASTIC_EDGE_OFFSET = 4.3   # from the mounting hole to the near edge of the
                             # plastic body (where the solder pins enter the
                             # housing), same +y direction as MOUNT_Y_OFFSET.
                             # Also from the user's datasheet read, 2026-10-09
                             # -- this replaces the old guessed body_y0.

# Local frame: pin 1 at the HIGH-x end, decreasing to pin 31 at x=0. This is
# reversed from a naive "pin1 at x=0" layout on purpose -- J1 is placed
# rotated 90 deg (see build_pcb.py), and with pin1-at-x=0 the rotation put
# pin 1 at the board's bottom and pin 31 at the top, backwards from the
# required pin1-top / pin31-bottom orientation. Flipping which end pin 1
# sits at flips the rotated result without having to reason about KiCad's
# rotation-angle sign convention.
span = (N_PINS - 1) * PITCH   # 75.0
mount_left = -MOUNT_INSET
mount_right = span + MOUNT_INSET
mount_y = ZIGZAG + MOUNT_Y_OFFSET   # 5.04

# Body outline: overall length 90.6mm (datasheet "A" dim) and the near edge
# (where pins enter the plastic) are now real datasheet dimensions; the far
# edge / total depth is still a placeholder -- NOT verified against the
# physical part, see docs/design_notes.md.
body_len = 90.6
body_overhang = (body_len - (mount_right - mount_left)) / 2
body_x0 = mount_left - body_overhang
body_x1 = mount_right + body_overhang
body_y0 = mount_y + PLASTIC_EDGE_OFFSET   # 9.34, real dimension
body_depth_guess = 10.5                   # old y0..y1 span, kept as a
                                           # still-unverified placeholder
body_y1 = body_y0 + body_depth_guess

out = []
out.append(f'''(footprint "DIN41617_31P_Male_Angled"
\t(version 20221018)
\t(generator "cs1800_tools")
\t(generator_version "10.0")
\t(layer "F.Cu")
\t(descr "DIN 41617 male connector, angled/right-angle, 31 positions, plain 1-31 numbering (not A-B-C rows), 2.50mm contact pitch, zigzag pad pattern. Amphenol/Conec 101-A-10119-X. See docs/conec_connectors_din_41617-3009425.pdf and docs/backplane_notes.md. Pad, mounting-hole, and body-near-edge positions are per the datasheet's dimensioned PCB-hole-pattern drawing (cross-checked: span+2*5=85mm matches the datasheet's D dimension); the body's far edge / overall depth is still an UNVERIFIED approximation -- check against the physical part before final fab.")
\t(tags "DIN41617 DIN41612 backplane connector")
\t(property "Reference" "REF**"
\t\t(at {span/2} {body_y0 - 2} 0)
\t\t(layer "F.SilkS")
\t\t(effects (font (size 1 1) (thickness 0.15)))
\t)
\t(property "Value" "DIN41617_31P_Male_Angled"
\t\t(at {span/2} {body_y1 + 2} 0)
\t\t(layer "F.Fab")
\t\t(effects (font (size 1 1) (thickness 0.15)))
\t)
\t(attr through_hole)
\t(duplicate_pad_numbers_are_jumpers no)''')

# Body outline on F.Fab (approximate)
out.append(f'''\t(fp_rect
\t\t(start {body_x0} {body_y0})
\t\t(end {body_x1} {body_y1})
\t\t(stroke (width 0.1) (type solid))
\t\t(fill none)
\t\t(layer "F.Fab")
\t)
\t(fp_rect
\t\t(start {body_x0} {body_y0})
\t\t(end {body_x1} {body_y1})
\t\t(stroke (width 0.12) (type solid))
\t\t(fill none)
\t\t(layer "F.SilkS")
\t)''')

# Courtyard, 0.25mm clearance around the approximate body
cy = 0.25
out.append(f'''\t(fp_rect
\t\t(start {body_x0 - cy} {body_y0 - cy})
\t\t(end {body_x1 + cy} {body_y1 + cy})
\t\t(stroke (width 0.05) (type solid))
\t\t(fill none)
\t\t(layer "F.CrtYd")
\t)''')

# Pin-1 arrow marker on silkscreen, just outside the body near pin1 (now at
# local x = span, the high-x end -- see the local-frame note above)
out.append(f'''\t(fp_line
\t\t(start {span - 2} {body_y0 - 0.6})
\t\t(end {span} {body_y0 - 0.6 - 1.5})
\t\t(stroke (width 0.12) (type solid))
\t\t(layer "F.SilkS")
\t)
\t(fp_line
\t\t(start {span + 2} {body_y0 - 0.6})
\t\t(end {span} {body_y0 - 0.6 - 1.5})
\t\t(stroke (width 0.12) (type solid))
\t\t(layer "F.SilkS")
\t)''')

# Mounting holes (non-plated, mechanical only)
for x in (mount_left, mount_right):
    out.append(f'''\t(pad "" np_thru_hole circle
\t\t(at {x} {mount_y})
\t\t(size {MOUNT_DRILL} {MOUNT_DRILL})
\t\t(drill {MOUNT_DRILL})
\t\t(layers "*.Cu" "*.Mask")
\t)''')

# Signal pads, pin1 = roundrect (polarity marker), rest circular.
# x: pin1 at the high-x end, decreasing toward pin31 at x=0 (see note above).
# y: zigzag -- odd pins at y=ZIGZAG, even pins at y=0. Empirically verified
# (via `kicad-cli pcb render`, since J1's rotation makes this hard to reason
# about by hand) that THIS sign -- not the naive "odd=0, even=ZIGZAG" -- is
# the one that lands odd pins closer to the board edge once J1 is placed
# rotated 90 deg (see build_pcb.py).
for n in range(1, N_PINS + 1):
    x = (N_PINS - n) * PITCH
    y = ZIGZAG if (n % 2 == 1) else 0
    if n == 1:
        out.append(f'''\t(pad "{n}" thru_hole roundrect
\t\t(at {x} {y})
\t\t(size {PAD} {PAD})
\t\t(drill {DRILL})
\t\t(layers "*.Cu" "*.Mask")
\t\t(remove_unused_layers no)
\t\t(roundrect_rratio 0.16)
\t)''')
    else:
        out.append(f'''\t(pad "{n}" thru_hole circle
\t\t(at {x} {y})
\t\t(size {PAD} {PAD})
\t\t(drill {DRILL})
\t\t(layers "*.Cu" "*.Mask")
\t\t(remove_unused_layers no)
\t)''')

out.append('\t(embedded_fonts no)\n)\n')

import os
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                         "libraries", "footprints", "cs1800.pretty",
                         "DIN41617_31P_Male_Angled.kicad_mod")
with open(OUT_PATH, "w") as f:
    f.write("\n".join(out))
print("wrote", OUT_PATH)
print("span", span, "mount_left", mount_left, "mount_right", mount_right)
