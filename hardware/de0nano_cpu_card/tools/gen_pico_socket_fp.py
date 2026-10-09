"""Footprint for mounting the Pico-W on header SOCKETS (not direct-solder),
so the module sits elevated above this board -- needed so the micro-USB
cable plugged into the Pico-W's own USB port actually has room to fit
without hitting this board.

Two 1x20 rows, 2.54mm pitch within each row, 17.78mm (0.7") between rows --
genuine Raspberry Pi Pico/Pico W mechanical spacing, cross-checked against
KiCad's own Module:RaspberryPi_Pico_Common_THT footprint (pad1 at (0,0),
pad21 at (17.78,48.26)). Pad numbering matches the real Pico's own silkscreen
numbering (and therefore the RaspberryPi_Pico_W schematic symbol's pin
numbers): 1-20 up one row, 21-40 back down the other.

This is the SOCKET side (soldered to this board) -- the Pico-W module itself
needs male header pins (either bought with headers pre-soldered, or the bare
module + 2x 1x20 male headers soldered on) to plug into it. When sourcing
the socket strips, pick a "tall"/stacking-header-height variant rather than
a low-profile one, for USB cable clearance underneath the module -- the
footprint only fixes pad positions, not standoff height, so this is a BOM
part choice, not something this file encodes.
"""
import os

ROW_SPACING = 17.78
PITCH = 2.54
PINS_PER_ROW = 20
PAD = 1.7
DRILL = 1.0

out = []
out.append('''(footprint "RaspberryPi_Pico_W_SocketHeaders_2x1x20_P2.54mm"
\t(version 20221018)
\t(generator "cs1800_tools")
\t(generator_version "10.0")
\t(layer "F.Cu")
\t(descr "Two 1x20 2.54mm-pitch socket-strip rows, 17.78mm (0.7\\") apart -- genuine Raspberry Pi Pico/Pico W header spacing, for mounting the Pico-W on sockets (removable) instead of direct-soldering it. Pad numbers 1-20/21-40 match the Pico's own pin numbering. See tools/gen_pico_socket_fp.py.")
\t(tags "RaspberryPi Pico PicoW socket header")
\t(property "Reference" "REF**"
\t\t(at 8.89 -2.77 0)
\t\t(layer "F.SilkS")
\t\t(effects (font (size 1 1) (thickness 0.15)))
\t)
\t(property "Value" "RaspberryPi_Pico_W_SocketHeaders"
\t\t(at 8.89 51.03 0)
\t\t(layer "F.Fab")
\t\t(effects (font (size 1 1) (thickness 0.15)))
\t)
\t(attr through_hole)
\t(duplicate_pad_numbers_are_jumpers no)''')

# Silkscreen: simple outline box around both rows
x0, x1 = -1.6, ROW_SPACING + 1.6
y0, y1 = -1.6, (PINS_PER_ROW - 1) * PITCH + 1.6
out.append(f'''\t(fp_rect
\t\t(start {x0} {y0})
\t\t(end {x1} {y1})
\t\t(stroke (width 0.12) (type solid))
\t\t(fill none)
\t\t(layer "F.SilkS")
\t)
\t(fp_rect
\t\t(start {x0} {y0})
\t\t(end {x1} {y1})
\t\t(stroke (width 0.1) (type solid))
\t\t(fill none)
\t\t(layer "F.Fab")
\t)''')

cy = 0.25
out.append(f'''\t(fp_rect
\t\t(start {x0 - cy} {y0 - cy})
\t\t(end {x1 + cy} {y1 + cy})
\t\t(stroke (width 0.05) (type solid))
\t\t(fill none)
\t\t(layer "F.CrtYd")
\t)''')

# Row 1: pins 1-20, x=0, y increasing 0 -> 48.26
for i in range(PINS_PER_ROW):
    n = i + 1
    y = i * PITCH
    shape = "rect" if n == 1 else "circle"
    out.append(f'''\t(pad "{n}" thru_hole {shape}
\t\t(at 0 {y})
\t\t(size {PAD} {PAD})
\t\t(drill {DRILL})
\t\t(layers "*.Cu" "*.Mask")
\t\t(remove_unused_layers no)
\t)''')

# Row 2: pins 21-40, x=ROW_SPACING, y DEcreasing from 48.26 -> 0 (pin21 lines
# up with pin20's end of the row, pin40 lines up with pin1's end)
for i in range(PINS_PER_ROW):
    n = 21 + i
    y = (PINS_PER_ROW - 1 - i) * PITCH
    out.append(f'''\t(pad "{n}" thru_hole circle
\t\t(at {ROW_SPACING} {y})
\t\t(size {PAD} {PAD})
\t\t(drill {DRILL})
\t\t(layers "*.Cu" "*.Mask")
\t\t(remove_unused_layers no)
\t)''')

out.append('\t(embedded_fonts no)\n)\n')

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                         "libraries", "footprints", "cs1800.pretty",
                         "RaspberryPi_Pico_W_SocketHeaders_2x1x20_P2.54mm.kicad_mod")
with open(OUT_PATH, "w") as f:
    f.write("\n".join(out))
print("wrote", OUT_PATH)
