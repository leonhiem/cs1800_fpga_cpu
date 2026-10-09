"""One-off patch: add 100nF decoupling caps on both supplies (VCCA=3V3,
VCCB=5V) for all 6 SN74LVC8T245 level shifters -- 12 caps total. Edits the
current saved sheets/level_shifters.kicad_sch in place (does not regenerate
the sheet, to preserve the user's manual layout rearrangement in the GUI).

Placed near each IC's current position (just above it, one cap each side)
so they're easy to find in the schematic -- but the real requirement is
PCB-layout proximity to the IC's VCCA/VCCB pins, which this schematic
placement doesn't guarantee; see the note added to design_notes.md.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet, balanced_block

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "level_shifters.kicad_sch")
FP_C = "Capacitor_SMD:C_0603_1608Metric"

c = load("C.kicad_sym", "Device")
v33 = load("+3V3.kicad_sym", "power")
v5 = load("+5V.kicad_sym", "power")
gnd = load("GND.kicad_sym", "power")

text = open(PATH).read()

ICS = [
    ("U1", 54.61, 59.69),
    ("U2", 129.54, 59.69),
    ("U3", 219.71, 59.69),
    ("U4", 54.61, 166.37),
    ("U5", 129.54, 170.18),
    ("U6", 219.71, 170.18),
]

# 1) insert the Device:C symbol into lib_symbols (not yet present)
assert '"Device:C"' not in text, "Device:C already cached, patch script may be stale"
c_cache = c.cache_text()
lib_idx = text.index("(lib_symbols")
lib_block = balanced_block(text, lib_idx)
insert_at = lib_idx + len(lib_block) - 1
text = text[:insert_at] + "\n" + c_cache + "\n\t" + text[insert_at:]

# 2) place 2 caps (3V3-side, 5V-side) just above each IC
_dummy_sheet = Sheet("dummy")
blocks = []
cidx = 1
for ref, cx, cy in ICS:
    ca = Component(c, f"C{cidx}", "100nF", FP_C, cx - 10, cy - 38, 0)
    ca.pin(1, power=v33)
    ca.pin(2, power=gnd)
    blocks.append(_dummy_sheet._render_component(ca))
    cidx += 1

    cb = Component(c, f"C{cidx}", "100nF", FP_C, cx + 10, cy - 38, 0)
    cb.pin(1, power=v5)
    cb.pin(2, power=gnd)
    blocks.append(_dummy_sheet._render_component(cb))
    cidx += 1

insertion = "\n".join(blocks)
stripped = text.rstrip("\n")
assert stripped.endswith("\n)") or stripped == ")", "unexpected file tail, aborting"
last_paren_idx = stripped.rfind("\n)")
text = stripped[:last_paren_idx] + "\n" + insertion + stripped[last_paren_idx:] + "\n"

with open(PATH, "w") as f:
    f.write(text)
print("patched", PATH, "-- added", cidx - 1, "decoupling caps")
