"""One-off patch: make every component reference designator globally unique
across the whole project. Each sheet's build_*.py script numbered its own
parts starting from 1/2/3 independently, so e.g. "R1", "C1", "J1", "U1" each
refer to 3-4 DIFFERENT real components across different sheets -- harmless
for schematic ERC (which resolves connectivity by net name, not reference),
but fatal for PCB work: you can't place "the" footprint for "J1" when J1
means three unrelated physical parts.

Found via `kicad-cli sch export netlist` (which warned "schematic has
annotation errors") and cross-checked by parsing the netlist's (components)
section for duplicate (ref) values -- 19 colliding reference names across
89 total components.

Renumbering: within each reference-letter prefix (R, C, J, U, D, PF),
sheets are processed in the root schematic's hierarchy order (backplane,
level_shifters, fpga_header, power, pico_w_bridge, rs232, frontpanel_io)
and renumbered sequentially from 1. Already-unique refs (SW1-6, R_D1-4,
R_SW1-6, A1, P1, and single-instance D/PF/U/J refs) are left alone.

Uses a two-phase (temp-name) rename within each file, since old and new
numbers overlap (e.g. level_shifters' old R14 -> new R21, while old R1 ->
new R14 -- a naive single-pass replace would corrupt the second one).
"""
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets")

# Per-file {old_ref: new_ref}. Only entries that actually change are listed.
RENAMES = {
    "backplane_connector.kicad_sch": {
        "R2": "R1", "R3": "R2", "R8": "R3", "R10": "R4", "R12": "R5",
        "R14": "R6", "R16": "R7", "R18": "R8", "R20": "R9", "R22": "R10",
        "R24": "R11", "R26": "R12", "R28": "R13",
        "C3": "C1",
    },
    "level_shifters.kicad_sch": {
        "R1": "R14", "R2": "R15", "R3": "R16",
        "R10": "R17", "R11": "R18", "R12": "R19", "R13": "R20",
        "R14": "R21", "R15": "R22", "R16": "R23", "R17": "R24",
        "R18": "R25", "R19": "R26", "R20": "R27",
        "C1": "C2", "C2": "C3", "C3": "C4", "C4": "C5", "C5": "C6",
        "C6": "C7", "C7": "C8", "C8": "C9", "C9": "C10", "C10": "C11",
        "C11": "C12", "C12": "C13",
        # J2, U1-U6 already unique (first in hierarchy order), unchanged
    },
    "fpga_header.kicad_sch": {
        "R20": "R28", "R21": "R29", "R22": "R30", "R23": "R31",
        "J1": "J3", "J2": "J4",
    },
    "power.kicad_sch": {
        "C1": "C14",
        # P1, PF1, PF2 already unique, unchanged
    },
    "pico_w_bridge.kicad_sch": {
        "R1": "R32",
        "C1": "C15",
        "PF1": "PF3",
        # A1, D1 already unique, unchanged
    },
    "rs232.kicad_sch": {
        "C1": "C16", "C2": "C17", "C3": "C18", "C4": "C19",
        "J1": "J5",
        "U1": "U7",
    },
    "frontpanel_io.kicad_sch": {
        "D1": "D2", "D2": "D3", "D3": "D4", "D4": "D5",
        # R_D*, R_SW*, SW* already unique, unchanged
    },
}

# Each component's reference is stored in TWO places: the visible
# (property "Reference" "X" ...) field, AND a (reference "X") inside its
# (instances (project ... (path ... (reference "X") (unit N)))) block --
# the latter is what `kicad-cli sch export netlist` actually reads from.
# Both need updating.
PATTERNS = [
    lambda ref: f'(property "Reference" "{ref}"',
    lambda ref: f'(reference "{ref}")',
]

total_renames = 0
for fname, mapping in RENAMES.items():
    path = os.path.join(BASE, fname)
    text = open(path).read()

    for mk_pat in PATTERNS:
        # Phase 1: old -> unique temp placeholder
        temp_map = {old: f"__TMP_{i}__" for i, old in enumerate(mapping)}
        for old, temp in temp_map.items():
            pat = mk_pat(old)
            n = text.count(pat)
            if n != 1:
                raise RuntimeError(f"{fname}: expected exactly 1 occurrence of {pat!r}, found {n}")
            text = text.replace(pat, mk_pat(temp), 1)

        # Phase 2: temp placeholder -> final new ref
        for old, temp in temp_map.items():
            new = mapping[old]
            pat = mk_pat(temp)
            assert text.count(pat) == 1
            text = text.replace(pat, mk_pat(new), 1)

    open(path, "w").write(text)
    print(f"{fname}: renamed {len(mapping)} references (both property + instances)")
    total_renames += len(mapping)

print("total renames:", total_renames)
