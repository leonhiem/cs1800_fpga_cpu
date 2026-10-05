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

## Status

Project skeleton only — see `docs/design_notes.md` for the full architecture writeup,
the JLCPCB-oriented component shortlist, and the **open questions list** that's currently
blocking real schematic capture (backplane pinout, DE0-Nano header/1802 pin mapping, exact
Eurocard "double slot" dimensions, front-panel mounting style, USB connector/FT2232H
variant choice). Two fill-in templates are provided for the two pinouts:
`docs/pinout_backplane_TEMPLATE.md` and `docs/pinout_de0nano_header_TEMPLATE.md`.

## Layout

```
de0nano_cpu_card.kicad_pro/.kicad_sch/.kicad_pcb   top-level project + root (hierarchical) schematic + PCB
sheets/                                             one schematic per functional block
libraries/symbols/cs1800.kicad_sym                  project-local custom symbols
libraries/footprints/cs1800.pretty/                 project-local custom footprints
docs/                                                design notes, pinout templates
jlcpcb/                                              (empty for now) gerbers/BOM/CPL export target once ready
```
