# Generator tools

`kicadgen.py` is a small from-scratch KiCad **schematic** generator used to
build this project's 7 schematic sheets programmatically from the pin data
in `docs/cs1800.qsf`, `docs/pinout_backplane.md`, `docs/Eurocard.md`, etc.,
instead of hand-placing ~400 pins in the GUI.

`pcbgen.py` + `build_pcb.py` are the **PCB**-side counterpart (2026-10-09):
kicad-cli has no "update PCB from schematic" command (that's GUI/IPC-only),
so getting the schematic's ~89 components onto the board at all required
the same from-scratch approach. `pcbgen.py` parses `kicad-cli sch export
netlist` output for component→footprint/value and net→(ref,pin)
connectivity, parses real `.kicad_mod` footprint files (staged in
`fpstage/`, same idea as `symstage/` for symbols) for their pad sets, and
places each component's full footprint definition on the board with pads
wired to the right net — `build_pcb.py` is the per-project placement
script (declarative X/Y per component, grouped into Eurocard.md's
functional regions). PCB footprint coordinates are already in the board's
native Y-down space (unlike schematic symbol libraries), so no Y-flip is
needed there — simpler than the schematic side. Run it with
`python3 build_pcb.py` then `kicad-cli10 pcb upgrade
../de0nano_cpu_card.kicad_pcb` then `pcb drc` to validate, same pattern as
the schematic tools. **Only rough-places** components (grouped, not
finely positioned) — see `docs/design_notes.md` §7a for what that means in
practice and what's left for the user's own placement/routing pass. Same
"don't just re-run after the user has started their own work" caveat as
`build_*.py` on the schematic side applies here too.

`gen_de0nano_reference_fp.py` and `gen_din41617_fp.py` build the two
project-local custom footprints (`libraries/footprints/cs1800.pretty/`) --
see their own docstrings.

## Why this exists

Hand-authoring a `.kicad_sch` file is tedious and error-prone at this scale.
`kicadgen.py` instead:

1. Parses real pin geometry (position, angle, electrical type) directly out
   of the actual symbol library files shipped with KiCad 10 (staged in
   `symstage/` — see below), via a small s-expression balanced-paren parser.
2. Embeds each used symbol's full definition into the sheet's `lib_symbols`
   cache (flattening `extends`-based symbols like `MAX3232`/`RaspberryPi_Pico_W`
   into a fully self-contained copy — see the comment in `cache_text()` for
   why: kicad-cli's ERC doesn't reliably resolve pin connectivity through a
   hand-crafted `(extends ...)` reference).
3. Places component instances and, for every pin that should be wired, draws
   a short stub wire ending in either a `global_label` (ordinary nets — these
   connect across sheets by name) or a stamped power symbol (`+5V`/`+3V3`/
   `GND`/`PWR_FLAG`).
4. Writes the result in KiCad 6-era format, which `kicad-cli sch upgrade`
   then converts to native KiCad 10 format (sidesteps needing to know the
   exact current format version by hand).

## Usage

```
python3 build_level_shifters.py   # (or any of the other build_*.py)
~/bin/kicad-cli10 sch upgrade ../sheets/level_shifters.kicad_sch
~/bin/kicad-cli10 sch erc ../de0nano_cpu_card.kicad_sch   # validate the whole hierarchy
```

**⚠️ As of 2026-10-09, don't just re-run a `build_*.py` anymore.** The user
has since opened the project in the real KiCad GUI and manually rearranged
component positions on several sheets (to de-clutter the generator's naive
grid layout). A `build_*.py` regenerates its sheet completely from scratch —
re-running one would silently throw away that layout work, placing
everything back at the generator's original grid coordinates.

If a pinout/net change is needed on an already-laid-out sheet, write a
small one-off patch script instead (see `patch_level_shifters_pullups.py`
and `patch_fpga_header_series_r.py` for worked examples) that:
1. Reads the *current* `.kicad_sch` file as text.
2. Finds the existing component's *current* position (grep/regex for its
   `(property "Reference" "U4" ...)` block, then the `(at CX CY ROT)` a few
   lines above it — do NOT assume it's still at the position the original
   `build_*.py` placed it).
3. Uses `kicadgen.transform()` with that current position to compute exact
   absolute pin coordinates (don't hand-guess them).
4. Surgically edits: renames a `global_label`'s text in place (for "insert a
   component in series on an existing net"), and/or removes a specific
   `(no_connect (at X Y) (uuid ...))` block and replaces it with a real
   wire+label/power connection (for "this spare pin needs to go from NC to
   pulled-up/tied"), and/or appends new component+wire+label blocks just
   before the file's final closing paren (for "add a new part").
5. Leaves everything else in the file untouched, so the user's layout survives.
6. Validate the same way: `sch upgrade` then `sch erc` on the whole hierarchy.

Only fall back to a full `build_*.py` regeneration if the user confirms
they're fine re-doing their layout pass afterward (or hasn't laid the sheet
out yet).

`build_*.py` still regenerates its sheet from scratch (declarative:
component placement + a `{pin_number: net_name}` map per component) when
that's actually what's wanted — e.g. a sheet nobody has touched in the GUI
yet, or a from-scratch pinout change the user explicitly wants to blow away
prior layout for.

## `symstage/`

Cached copies of the real KiCad 10 symbol library files these scripts parse
(`SN74LVC8T245`, `MAX3232`+its `MAX232` base, `RaspberryPi_Pico_W`+its
`RaspberryPi_Pico` base, `Conn_01x31`, `Conn_02x20_Odd_Even`, `Conn_02x11_Odd_Even`,
`Conn_01x02`, `DE9_Pins`, `R`, `C`, `D_Schottky`, `LED`, `+5V`, `+3V3`, `GND`,
`PWR_FLAG`). Staged here so the scripts don't need the KiCad 10 AppImage
mounted to re-run. If a sheet needs a new stock symbol, pull it from the
AppImage the same way (`--appimage-mount`, copy the one `.kicad_sym` file out
of `share/kicad/symbols/<Library>.kicad_symdir/`) and add a `load(...)` call.

## Known quirks documented in code comments

- Pin coordinates in symbol library files use a Y-up convention; schematic
  placement is Y-down — `transform()` flips Y (and the pin angle) first.
- `(wire ...)` elements don't accept a `(fill ...)` field (KiCad rejects it
  silently as a parse error on load).
- Nested unit sub-symbols in a `lib_symbols` cache entry (e.g. `"R_0_1"`)
  must NOT be prefixed with the library nickname — only the top-level symbol
  name is.
- Most symbols put their pins in unit 1 (`"Name_1_1"`), but some (e.g.
  `PWR_FLAG`) put them in unit 0 (`"Name_0_0"`) — `cache_text()` detects this
  per-symbol rather than assuming.
- A lone `PWR_FLAG` wired to a power-symbol stamp (`+5V`/`+3V3`/`GND`) with
  nothing else sharing that net locally reports as `pin_not_connected` under
  kicad-cli's ERC, even though it's electrically fine. Wire `PWR_FLAG`s via a
  plain net label (the rail's name, e.g. `net="+3V3"`) instead of the
  power-symbol-stamp mechanism to avoid it.
- **Each `build_*.py` numbers its own references starting from 1/2/3,
  independently of every other sheet** — `kicad-cli sch erc` does NOT catch
  the resulting cross-sheet collisions (ERC resolves connectivity by net
  name, not by reference, so e.g. two different "R1"s on two different
  sheets looks fine to ERC). This went unnoticed until PCB work started,
  when `kicad-cli sch export netlist` warned "schematic has annotation
  errors" and the netlist's `(components)` section showed ~19 reference
  names each mapping to 2-4 *different* real parts across sheets (fixed in
  `patch_reannotate_global.py`, 2026-10-09). **Before any new `build_*.py`
  run or hand-added component**, check `kicad-cli10 sch export netlist
  --output /tmp/x.net ../de0nano_cpu_card.kicad_sch` and grep its
  `(components)` section for duplicate `(ref ...)` values — don't rely on
  `sch erc` alone to catch this.
- Each component's reference is stored in **two** places in a `.kicad_sch`
  file: the visible `(property "Reference" "X" ...)` field, AND a
  `(reference "X")` inside its `(instances (project ... (path ... (reference
  "X") (unit N))))` block. `kicad-cli sch export netlist` reads from the
  *second* one — renaming only the property field (the obvious one) leaves
  the netlist unchanged. Any ref-renaming patch must update both.
- `kicad-cli sch export netlist` prints "Warning: schematic has annotation
  errors, please use the schematic editor to fix them" to stderr even after
  the above fix was verified complete (netlist's `(components)` section has
  zero duplicate refs, `sch erc`'s dedicated `duplicate_reference`/
  `unannotated` checks, both "error" severity, find nothing). Seems to be a
  stale/overly-cautious message from the netlist exporter rather than a real
  remaining problem — don't take it at face value, check the actual
  `(components)` section instead.

## PCB-specific quirks (`pcbgen.py` / `build_pcb.py`)

- A hand-written `(net N "NAME")` declared at the board level, and a pad's
  `(net N "NAME")` entry, both survive `pcb upgrade` — but the output only
  ever shows `(net "NAME")` on the pad (no number) and drops the top-level
  per-board `(net N "NAME")` table entirely if nothing else references it
  by number. This looked broken on first encounter but isn't: `pcb drc`
  still correctly resolves connectivity by the net *name*, matching same-
  named pads into one ratsnest-visible net regardless of the missing
  number. Don't be alarmed by the missing net table / missing pad number —
  check `pcb drc`'s `[unconnected_items]`/`[shorting_items]` output (which
  net *names* it reports) to confirm connectivity, not the raw net IDs.
- Don't assume a stock footprint's natural orientation matches what you
  want without checking: `IDC-Header_2x20_P2.54mm_Vertical`'s 40 pads are
  natively narrow-X/tall-Y (pins already run the "long way" along Y) — no
  rotation needed to stand it up next to the DE0-Nano's edge. First attempt
  rotated it 90° assuming it needed standing up like the hand-made
  DIN41617 footprint (which genuinely does need rotating, since *that one*
  was authored with its pin row along X) — check each footprint's actual
  pad coordinate spread (`grep` the `.kicad_mod` for `(at ...)` on its
  pads) before deciding a placement's rotation, rather than assuming.
- `build_pcb.py`'s component footprint has **no reserved clear X-band** of
  its own — it's mechanical/NPTH-only (no copper), so it cannot DRC-short
  against anything and was deliberately left to cosmetically overlap small
  passives in the rough pass rather than eating ~49mm of the board's 160mm
  depth that the 6 other functional groups + 2 headers + 2 connectors also
  need. If this project ever adds a *populated* mechanical reference with
  real copper, it would need genuine clearance instead.
