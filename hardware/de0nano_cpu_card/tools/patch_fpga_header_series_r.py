"""One-off patch: insert 10-ohm series resistors on TPA/TPB/nMRD/nMWR at the
FPGA end, per backplane_notes.md's signal-integrity note (originally
suggested 33-47ohm, user chose 10ohm). Edits the current saved
sheets/fpga_header.kicad_sch in place -- does NOT regenerate the sheet, to
preserve the user's manual layout rearrangement done in the GUI.

For each of the 4 signals: renames the existing global_label at J1's pin
from e.g. "TPA" to "TPA_FPGA" (same position, same wire -- just relabeled),
then adds a new 10ohm resistor bridging "TPA_FPGA" (at J1) to "TPA" (the
net continuing on to level_shifters.kicad_sch, unchanged there).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet, find_blocks, balanced_block

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "fpga_header.kicad_sch")
FP_R = "Resistor_SMD:R_0603_1608Metric"

r = load("R.kicad_sym", "Device")

text = open(PATH).read()

SIGNALS = ["nMWR", "TPA", "nMRD", "TPB"]

# 1) rename the 4 global_labels at J1's pins: "SIG" -> "SIG_FPGA"
for sig in SIGNALS:
    old = f'(global_label "{sig}"'
    new = f'(global_label "{sig}_FPGA"'
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly 1 occurrence of {old!r}, found {n}")
    text = text.replace(old, new, 1)

# 2) insert the Device:R symbol into lib_symbols (not yet present in this sheet),
#    found precisely via balanced-paren matching rather than a text marker
#    (fpga_header.kicad_sch has multiple "(...)\n\t(no_connect" occurrences,
#    so a naive text-marker match isn't unique).
assert '"Device:R"' not in text, "Device:R already cached, patch script may be stale"
r_cache = r.cache_text()
lib_idx = text.index("(lib_symbols")
lib_block = balanced_block(text, lib_idx)
# insert just before the block's own closing paren
insert_at = lib_idx + len(lib_block) - 1
text = text[:insert_at] + "\n" + r_cache + "\n\t" + text[insert_at:]

# 3) add the 4 series resistors, bridging "<sig>_FPGA" -> "<sig>"
_dummy_sheet = Sheet("dummy")
blocks = []
x, y = 300.0, 20.0
for i, sig in enumerate(SIGNALS):
    c = Component(r, f"R{20+i}", "10", FP_R, x, y, 0)
    c.pin(1, net=f"{sig}_FPGA")
    c.pin(2, net=sig)
    blocks.append(_dummy_sheet._render_component(c))
    y += 15.0

insertion = "\n".join(blocks)
stripped = text.rstrip("\n")
assert stripped.endswith("\n)") or stripped == ")", "unexpected file tail, aborting"
last_paren_idx = stripped.rfind("\n)")
text = stripped[:last_paren_idx] + "\n" + insertion + stripped[last_paren_idx:] + "\n"

with open(PATH, "w") as f:
    f.write(text)
print("patched", PATH)
