# CS1800 DE0-Nano CPU Card (KiCad project)

Eurocard CPU board that plugs a Terasic DE0-Nano (running a VHDL CDP1802 core) into the
existing CS1800 backplane, replacing the original 1802 CPU board.

## Opening this project

Use **KiCad 10.0.6** (`~/bin/kicad-10.0.6-x86_64.AppImage`), not the older KiCad 6 install
that's on `PATH` — this project's files are in KiCad 10's native format and KiCad 6 will
not open them.

```
~/bin/kicad-10.0.6-x86_64.AppImage hardware/de0nano_cpu_card/de0nano_cpu_card.kicad_pro
```

Headless checks (ERC/DRC/export) can be run without launching the GUI via the wrapper
script `~/bin/kicad-cli10` (FUSE-mounts the AppImage's `kicad-cli` on demand, no full
extraction needed):

```
~/bin/kicad-cli10 sch erc de0nano_cpu_card.kicad_sch
~/bin/kicad-cli10 pcb drc de0nano_cpu_card.kicad_pcb
```

## Status (2026-10-09)

Architecture, mechanical/sourcing, and FPGA pin assignment are all resolved. All 7
schematic sheets are wired with real nets (`kicad-cli sch erc`: 0 errors) — see
`docs/design_notes.md` for the full writeup, the JLCPCB-oriented component shortlist,
and the "Next steps" list (custom footprints, PCB floorplan/routing are what's left).
The sheets were generated via the scripts in `tools/` (see `tools/README.md`) from the
pin data in `docs/cs1800.qsf` and the other `docs/` files — re-run the relevant
`tools/build_*.py` after a pinout change rather than hand-editing the `.kicad_sch` output.

## Layout

```
de0nano_cpu_card.kicad_pro/.kicad_sch/.kicad_pcb   top-level project + root (hierarchical) schematic + PCB
sheets/                                             one schematic per functional block
libraries/symbols/cs1800.kicad_sym                  project-local custom symbols
libraries/footprints/cs1800.pretty/                 project-local custom footprints
docs/                                                design notes, pinout docs, FPGA .qsf, connector datasheet
tools/                                               schematic generator scripts (see tools/README.md)
jlcpcb/                                              (empty for now) gerbers/BOM/CPL export target once ready
```
