"""One-off patch: add pull-ups/ties the user found missing during GUI review,
WITHOUT regenerating the sheet (which would discard the user's manual layout
rearrangement in the GUI). Directly edits the current saved
sheets/level_shifters.kicad_sch in place: removes specific no_connect
markers and splices in new resistor/wire/label/power content.

Changes:
- 7x 10k pull-up to +5V on EXP_EX_IN[0], EXP_EX_IN[1], EXP_nEF[3],
  EXP_nCLEAR, EXP_nWAIT, EXP_nDMA_OUT, EXP_nDMA_IN (already-wired nets,
  just adding a pull-up branch)
- U4 pins 14/15/16 (B8/B7/B6, spare backplane-side input channels):
  remove their no_connect, pull up to +5V with 10k each
- U6 pin 14 (B8, spare future-expansion input channel): remove its
  no_connect, pull up to +5V with 10k
- U5 pins 7/8/9/10 (A5-A8, spare future-expansion output channels):
  remove their no_connect, hard-tie to GND (no resistor -- these are
  unused chip INPUTS on the FPGA side, direct tie avoids floating)
"""
import sys, os, re, math, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet, transform, u

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "level_shifters.kicad_sch")

lvc = load("SN74LVC8T245.kicad_sym", "Logic_LevelTranslator")
r = load("R.kicad_sym", "Device")
v5 = load("+5V.kicad_sym", "power")
gnd = load("GND.kicad_sym", "power")

FP_R = "Resistor_SMD:R_0603_1608Metric"

text = open(PATH).read()

def remove_no_connect(text, x, y):
    pat = re.compile(
        r'\t\(no_connect\n\t\t\(at ' + re.escape(str(x)) + r' ' + re.escape(str(y)) + r'\)\n\t\t\(uuid "[a-f0-9-]+"\)\n\t\)\n'
    )
    new_text, n = pat.subn('', text)
    if n != 1:
        raise RuntimeError(f"expected exactly 1 no_connect match at ({x},{y}), got {n}")
    return new_text

def pin_abs(cx, cy, rot, pinnum):
    p = lvc.pins[str(pinnum)]
    ax, ay, aangle = transform(p['x'], p['y'], p['angle'], cx, cy, rot)
    return round(ax, 3), round(ay, 3), aangle

def rewire_stub(ax, ay, aangle, net=None, power=None):
    """Emit the wire + (label or power-stamp) for an existing pin that used
    to be no_connect, exactly like kicadgen's normal per-pin wiring."""
    out_dir = int(round((aangle + 180) % 360))
    rad = math.radians(out_dir)
    STUB = 2.54
    ex, ey = round(ax + STUB * math.cos(rad), 3), round(ay + STUB * math.sin(rad), 3)
    lines = [f'\t(wire (pts (xy {ax} {ay}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{u()}"))']
    if power:
        lines.append(_power_stamp(power, ex, ey))
    else:
        lines.append(f'\t(global_label "{net}" (shape input) (at {ex} {ey} {out_dir}) (effects (font (size 1.27 1.27))) (uuid "{u()}"))')
    return "\n".join(lines) + "\n"

def _power_stamp(psym, x, y):
    return (f'\t(symbol (lib_id "{psym.lib_id()}") (at {x} {y} 0) (unit 1) '
            f'(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")\n'
            f'\t\t(property "Reference" "#PWR" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'\t\t(property "Value" "{psym.name}" (at {x} {y-2.54} 0) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(pin "1" (uuid "{uuid.uuid4()}"))\n'
            f'\t)\n')

_dummy_sheet = Sheet("dummy")

def render_pullup_to_5v(ref, x, y, net):
    c = Component(r, ref, "10k", FP_R, x, y, 0)
    c.pin(1, power=v5)
    c.pin(2, net=net)
    return _dummy_sheet._render_component(c)

# --- 1) The 7 already-wired EXP_* nets: just add a pull-up branch each ---
EXP_NETS = [
    "EXP_EX_IN[0]", "EXP_EX_IN[1]", "EXP_nEF[3]", "EXP_nCLEAR",
    "EXP_nWAIT", "EXP_nDMA_OUT", "EXP_nDMA_IN",
]
new_blocks = []
x, y = 350.0, 20.0
for i, net in enumerate(EXP_NETS):
    new_blocks.append(render_pullup_to_5v(f"R{10+i}", x, y, net))
    y += 15.0

# --- 2) U4 pins 14/15/16 (B8/B7/B6): remove NC, rewire to new spare nets, pull up ---
U4_AT = (54.61, 166.37, 0)
U4_SPARES = [(16, "U4_SPARE_B6"), (15, "U4_SPARE_B7"), (14, "U4_SPARE_B8")]
ridx = 17
for pin, net in U4_SPARES:
    ax, ay, aangle = pin_abs(*U4_AT, pin)
    text = remove_no_connect(text, ax, ay)
    new_blocks.append(rewire_stub(ax, ay, aangle, net=net))
    new_blocks.append(render_pullup_to_5v(f"R{ridx}", x, y, net))
    y += 15.0
    ridx += 1

# --- 3) U6 pin 14 (B8): remove NC, rewire to new spare net, pull up ---
U6_AT = (219.71, 170.18, 0)
ax, ay, aangle = pin_abs(*U6_AT, 14)
text = remove_no_connect(text, ax, ay)
new_blocks.append(rewire_stub(ax, ay, aangle, net="U6_SPARE_B8"))
new_blocks.append(render_pullup_to_5v(f"R{ridx}", x, y, "U6_SPARE_B8"))
y += 15.0
ridx += 1

# --- 4) U5 pins 7/8/9/10 (A5-A8): remove NC, hard-tie to GND ---
U5_AT = (129.54, 170.18, 0)
for pin in (7, 8, 9, 10):
    ax, ay, aangle = pin_abs(*U5_AT, pin)
    text = remove_no_connect(text, ax, ay)
    new_blocks.append(rewire_stub(ax, ay, aangle, power=gnd))

# --- splice new component/wire/label blocks in just before the final closing paren ---
insertion = "\n".join(new_blocks)
assert text.endswith(")\n") or text.endswith(")")
stripped = text.rstrip("\n")
assert stripped.endswith("\n)") or stripped == ")", "unexpected file tail, aborting"
# the file's last line is a bare ")" closing (kicad_sch ...); insert just before it
last_paren_idx = stripped.rfind("\n)")
text = stripped[:last_paren_idx] + "\n" + insertion + stripped[last_paren_idx:] + "\n"

with open(PATH, "w") as f:
    f.write(text)
print("patched", PATH)
print("removed 8 no_connect markers, added", len(new_blocks), "new blocks")
