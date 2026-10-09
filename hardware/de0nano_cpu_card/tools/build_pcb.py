"""Build de0nano_cpu_card.kicad_pcb from scratch: real 100x160mm Eurocard
outline, the DE0-Nano mechanical reference (outline + 4 real mounting
holes), and all ~89 real components from the schematic netlist, rough-
placed into functional groups roughly matching Eurocard.md's floorplan
(front panel on the left / X=0 edge, backplane connector on the right /
X=160 edge). This is a ROUGH placement only -- final placement (mechanical
fit, ribbon-cable routing, front-panel alignment) and all routing is left
for the user to do in the GUI.

Re-run after `sch export netlist` if the schematic's netlist changes
(component additions/removals, footprint reassignments). This OVERWRITES
de0nano_cpu_card.kicad_pcb completely -- if the user has since done PCB
placement/routing of their own, do NOT just re-run this (same caveat as
the schematic build_*.py scripts, see README.md).
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbgen import Netlist, load_footprint, render_footprint_instance, NetTable

HERE = os.path.dirname(os.path.abspath(__file__))
NET_PATH = "/tmp/cs1800_build.net"
OUT_PCB = os.path.join(HERE, "..", "de0nano_cpu_card.kicad_pcb")
SCH = os.path.join(HERE, "..", "de0nano_cpu_card.kicad_sch")

os.system(f'~/bin/kicad-cli10 sch export netlist --output {NET_PATH} {SCH} >/dev/null 2>&1')
nl = Netlist(NET_PATH)
nt = NetTable()

instances = []

def place(ref, x, y, rot=0):
    fp_id = nl.footprint.get(ref)
    if not fp_id:
        return  # no footprint assigned (e.g. PWR_FLAGs: virtual, not a real part)
    fpdef = load_footprint(fp_id)
    pin_net = nl.pin_net.get(ref, {})
    # only pass nets for pads that actually exist on this footprint
    pin_net = {p: n for p, n in pin_net.items() if p in fpdef.pad_numbers}
    value = nl.value.get(ref, "")
    instances.append(render_footprint_instance(ref, value, fpdef, x, y, rot, pin_net, nt))

def grid(refs, x0, y0, cols, dx, dy, rot=0):
    for i, ref in enumerate(refs):
        c = i % cols
        r = i // cols
        place(ref, x0 + c * dx, y0 + r * dy, rot)

# ---------------------------------------------------------------------
# X-band layout (real-copper components only; the DE0-Nano reference
# outline is mechanical/NPTH-only -- no copper, so it cannot DRC-short
# against anything and isn't given its own reserved clear band: it's
# drawn centered over the H1/H0 header area as a visual anchor, and may
# cosmetically overlap small passives in this ROUGH pass. 160mm total
# depth is tight once DE0-Nano's real 49mm width is accounted for
# alongside 6 functional groups + 2 headers + 2 connectors, so bands
# below are deliberately narrow; this is a starting point for the user's
# own placement pass, not a finished layout.
# ---------------------------------------------------------------------

# Front panel: LEDs + switches/buttons column (X 5-20)
grid(["D2", "D3", "D4", "D5"], 7, 5, 1, 0, 7)
grid(["R_D1", "R_D2", "R_D3", "R_D4"], 14, 5, 1, 0, 7)
grid(["SW1", "SW2", "SW3", "SW4", "SW5", "SW6"], 7, 38, 1, 0, 7)
grid(["R_SW1", "R_SW2", "R_SW3", "R_SW4", "R_SW5", "R_SW6"], 14, 38, 1, 0, 7)

# RS232: MAX3232 + caps + DB9 (X 23-38), own column clear of the above
place("U7", 25, 9, 0)
grid(["C16", "C17", "C18", "C19"], 23, 15, 2, 6, 6)
place("J5", 25, 30, 0)

# Pico-W + passives (X 41-60; module footprint spans ~18x48mm)
place("A1", 43, 50, 0)
place("D1", 23, 50, 0)
place("C15", 23, 56, 0)
place("R32", 23, 62, 0)

# Future-expansion group: U5, U6 + decoupling + pull-ups + J2 (X 63-88)
place("U5", 65, 5, 0)
place("U6", 65, 20, 0)
grid(["C10", "C11"], 75, 3, 2, 5, 0)
grid(["C12", "C13"], 75, 18, 2, 5, 0)
grid(["R17", "R18", "R19", "R20", "R21", "R22", "R23", "R27"], 63, 35, 4, 6, 4)
place("J2", 63, 55, 0)

# GPIO_1/JP2 header, DE0-Nano's left edge (X 91-93, natively tall-Y)
place("J3", 91, 50, 0)

# DE0-Nano mechanical reference (visual anchor only, no copper) + power feed
de0nano_fp = load_footprint("cs1800:DE0Nano_Reference_Outline")
de0nano_inst = render_footprint_instance("DE0NANO", "DE0-Nano (reference)", de0nano_fp, 95, 12, 0, {}, nt)
place("P1", 100, 5, 0)
place("C14", 110, 5, 0)

# GPIO_0/JP1 header, DE0-Nano's right edge (X 146-148, natively tall-Y)
place("J4", 146, 50, 0)

# Backplane-facing group: U1-U4 + decoupling + pull-ups + the 4 series
# resistors (X 125-158, stacked tightly since these are small parts)
place("U1", 126, 5, 0)
place("U2", 126, 20, 0)
place("U3", 126, 35, 0)
place("U4", 126, 50, 0)
grid(["C2", "C3"], 136, 3, 2, 5, 0)
grid(["C4", "C5"], 136, 18, 2, 5, 0)
grid(["C6", "C7"], 136, 33, 2, 5, 0)
grid(["C8", "C9"], 136, 48, 2, 5, 0)
# Stay within X<=141 here (J4 occupies X~146-148.5, Y~50-98 below) --
# everything below is kept in the U1-U4 column's own X band, stacked in Y
grid(["R14", "R15", "R16", "R24", "R25", "R26", "R28", "R29", "R30", "R31"],
     126, 62, 4, 4, 5)
grid([f"R{i}" for i in range(1, 14)], 126, 80, 4, 4, 5)
place("C1", 141, 95, 0)

# Backplane connector (X ~ 153, rotated 90 to run along the board's Y axis
# -- this one I custom-made with pins along local X, so DOES need rotating)
place("J1", 154, 50, 90)  # centered; rotation makes the exact Y-span hard to
# hand-compute precisely (off by a few mm per DRC) -- trivial to nudge in
# the GUI during real placement, not worth further hand-iteration here

# ---------------------------------------------------------------------
# assemble the board
# ---------------------------------------------------------------------
body = "\n".join(instances)

content = f'''(kicad_pcb (version 20221018) (generator pcbnew)
  (general
    (thickness 1.6)
  )
  (paper "A3")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )
  (setup
    (pad_to_mask_clearance 0)
  )
{nt.declarations()}
  (gr_rect (start 0 0) (end 160 100) (layer "Edge.Cuts") (width 0.15) (fill none))
  (gr_text "CS1800 DE0-Nano CPU Card -- ROUGH PLACEMENT, not routed.\\nFront panel at X=0 (left), backplane connector at X=160 (right).\\nSee docs/design_notes.md Sec7 / Eurocard.md for the intended floorplan."
    (at 80 -8 0) (layer "Cmts.User")
    (effects (font (size 2 2) (thickness 0.3)))
  )
{de0nano_inst}
{body}
)
'''

with open(OUT_PCB, "w") as f:
    f.write(content)
print("wrote", OUT_PCB)
print("total footprint instances:", len(instances) + 1)
