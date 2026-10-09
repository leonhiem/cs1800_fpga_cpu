# Schematic generator tools

`kicadgen.py` is a small from-scratch KiCad schematic generator used to build
this project's 7 schematic sheets programmatically from the pin data in
`docs/cs1800.qsf`, `docs/pinout_backplane.md`, `docs/Eurocard.md`, etc.,
instead of hand-placing ~400 pins in the GUI.

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

Each `build_*.py` regenerates exactly one sheet from scratch (declarative:
component placement + a `{pin_number: net_name}` map per component) — re-run
the relevant one after changing a pinout doc, rather than hand-editing the
`.kicad_sch` output.

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
