N_PINS = 31
PITCH = 2.5
DRILL = 1.1
PAD = 2.0
MOUNT_DRILL = 2.8
MOUNT_INSET = 5.0   # beyond pin1/pin31, same axis

# Pin 1 at x=0, increasing to pin31 at x=(N-1)*PITCH
span = (N_PINS - 1) * PITCH   # 75.0
mount_left = -MOUNT_INSET
mount_right = span + MOUNT_INSET

# Approximate body outline (overall length 90.6mm per datasheet; depth is a
# placeholder -- NOT verified against the physical part, see docs/design_notes.md)
body_len = 90.6
body_overhang = (body_len - (mount_right - mount_left)) / 2
body_x0 = mount_left - body_overhang
body_x1 = mount_right + body_overhang
body_y0 = -1.5
body_y1 = 9.0

out = []
out.append(f'''(footprint "DIN41617_31P_Male_Angled"
\t(version 20221018)
\t(generator "cs1800_tools")
\t(generator_version "10.0")
\t(layer "F.Cu")
\t(descr "DIN 41617 male connector, angled/right-angle, 31 positions, plain 1-31 numbering (not A-B-C rows), 2.50mm contact pitch. Amphenol/Conec 101-A-10119-X. See docs/conec_connectors_din_41617-3009425.pdf and docs/backplane_notes.md. Pad/mounting-hole positions are per the datasheet's dimensioned PCB-hole-pattern drawing; the body/silkscreen outline below is an UNVERIFIED approximation -- check against the physical part before final fab.")
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

# Pin-1 arrow marker on silkscreen, just outside the body near pin1
out.append(f'''\t(fp_line
\t\t(start -2 {body_y0 - 0.6})
\t\t(end 0 {body_y0 - 0.6 - 1.5})
\t\t(stroke (width 0.12) (type solid))
\t\t(layer "F.SilkS")
\t)
\t(fp_line
\t\t(start 2 {body_y0 - 0.6})
\t\t(end 0 {body_y0 - 0.6 - 1.5})
\t\t(stroke (width 0.12) (type solid))
\t\t(layer "F.SilkS")
\t)''')

# Mounting holes (non-plated, mechanical only)
for x in (mount_left, mount_right):
    out.append(f'''\t(pad "" np_thru_hole circle
\t\t(at {x} 0)
\t\t(size {MOUNT_DRILL} {MOUNT_DRILL})
\t\t(drill {MOUNT_DRILL})
\t\t(layers "*.Cu" "*.Mask")
\t)''')

# Signal pads, pin1 = roundrect (polarity marker), rest circular
for n in range(1, N_PINS + 1):
    x = (n - 1) * PITCH
    if n == 1:
        out.append(f'''\t(pad "{n}" thru_hole roundrect
\t\t(at {x} 0)
\t\t(size {PAD} {PAD})
\t\t(drill {DRILL})
\t\t(layers "*.Cu" "*.Mask")
\t\t(remove_unused_layers no)
\t\t(roundrect_rratio 0.16)
\t)''')
    else:
        out.append(f'''\t(pad "{n}" thru_hole circle
\t\t(at {x} 0)
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
