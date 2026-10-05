# CS1800 DE0-Nano CPU Card — Design Notes

## Purpose

Replacement CPU board for the CS1800 backplane system (originally a CDP1802
CPU board). This board carries a Terasic DE0-Nano (Cyclone IV FPGA) running
a VHDL CDP1802 core, and bridges it electrically and mechanically into the
existing CS1800 rack: DIN41617 backplane connector, 5V backplane power,
double-slot Eurocard form factor, front panel controls, and a USB/RS232
debug path.

## Block diagram (schematic hierarchy)

```
de0nano_cpu_card.kicad_sch (root)
├── sheets/backplane_connector.kicad_sch   DIN41617, 31p male, 5V in + CS1800 bus signals
├── sheets/level_shifters.kicad_sch        4x SN74LVC8T245, 3V3 (A side, DE0-Nano) <-> 5V (B side, backplane)
├── sheets/fpga_header.kicad_sch           40-pin IDC header -> ribbon cable -> DE0-Nano GPIO
├── sheets/power.kicad_sch                 backplane 5V -> DE0-Nano 5V feed, local rails/decoupling
├── sheets/usb_serial_bridge.kicad_sch     FT2232H dual-channel USB-UART/JTAG bridge
├── sheets/rs232.kicad_sch                 MAX3232 + DB9 (RS232 front panel)
└── sheets/frontpanel_io.kicad_sch         3x pushbutton, 3x rocker switch, 4x LED 3mm,
                                            USB connector, DB9 connector (all panel-mount)
```

Signal flow: `DIN41617 backplane (5V domain) <-> SN74LVC8T245 x4 <-> 40-pin header (3V3 domain) <-> ribbon cable <-> DE0-Nano GPIO`.
FT2232H channel A: front-panel USB <-> DE0-Nano (e.g. JTAG/UART/config, TBD which DE0-Nano
interface). FT2232H channel B: front-panel USB <-> MAX3232 <-> front-panel DB9 (RS232).

## Key design facts already fixed by the request

- Backplane: DIN 41617 (a 3-row-derived DIN41612 variant), **31 pins, male**, on the
  CS1800 board (card edge).
- Backplane supplies 5V; DE0-Nano and its 3V3-side logic must be powered from it — no USB
  power, no separate external supply on this card.
- DE0-Nano I/O is 3V3; backplane bus is 5V — hence 4x SN74LVC8T245 (3V3<->5V, 8-bit,
  auto-direction-sensing, bidirectional) between the two domains. Each chip handles 8 bus
  lines, so 4 chips = up to 32 backplane signal lines level-shifted (need the actual
  DIN41617 pinout to know how many of the 31 pins are signal vs. power/ground vs. spare,
  and to assign lines to chips/direction).
- DE0-Nano interface to the card: one 40-pin (2x20) GPIO header, wired via a 40-conductor
  ribbon cable to a matching IDC box header on this board.
- Form factor: Eurocard, double slot, 19" subrack. **Exact outline/pitch not yet fixed —
  see Open Questions.** PCB currently has a 100 x 160 mm placeholder outline
  (`de0nano_cpu_card.kicad_pcb`) purely so the file is valid; do not route against it yet.
- 4x M3 (3mm) mounting holes for the DE0-Nano board — positions not yet placed on the PCB;
  need DE0-Nano's official mechanical/hole-pattern drawing to place accurately (Terasic
  DE0-Nano User Manual has the dimensioned drawing). Do not trust a from-memory guess here.
- Front panel (all panel-mount): 3x pushbutton, 3x rocker switch, 4x LED (3mm), 1x USB
  connector, 1x 9-pin D-sub (RS232).
- USB-serial bridge: FT2232H-class chip, 2 independent channels — channel 1 front-panel
  USB <-> DE0-Nano, channel 2 front-panel USB <-> MAX3232 <-> front-panel DB9.
- Target fab/assembly: JLCPCB (PCBA), so part choice should favor JLCPCB Basic/Extended
  parts to keep assembly cost/lead-time down; anything not in their library becomes
  hand-solder/DNP-for-JLC.

## Proposed JLCPCB-friendly component shortlist (starting point, NOT final)

| Function | Candidate part | Package | JLCPCB fit | Notes |
|---|---|---|---|---|
| Level shifter x4 | Texas Instruments SN74LVC8T245PWR | TSSOP-24 | Extended part, commonly stocked | Auto direction sense (DIR pin ties A/B), OE per chip |
| USB-serial bridge | FTDI FT2232HL | LQFP-64 | Usually Extended/needs stock check | HL = -40..85C, LQFP; confirm current LCSC stock before BOM lock |
| RS232 transceiver | Texas Instruments MAX3232IDR (or MAX3232EIDR) | SOIC-16 | Extended, common | 3.3V-side transceiver, needs 4x 0.1uF charge-pump caps |
| RS232 connector | DB9 (DE-9) right-angle or straight, panel/PCB mount | THT | THT = manual/extra-cost assembly at JLCPCB | Decide PCB-mount-then-panel-cutout vs. cable-to-panel-mount part |
| USB connector | USB Micro-B receptacle | THT or SMT (e.g. Molex 1050170001-class) | On-board part, common/cheap on JLCPCB | Panel itself has USB-C (off-board part) linked to this by a 15cm USB-C-to-Micro-B cable |
| Backplane connector | DIN 41612/41617 31-pin male | THT, high pin count | THT, manual placement at JLCPCB (extra cost, longer lead time) | Need to confirm exact row/pin layout to pick correct LCSC part or source elsewhere (e.g. Amphenol/ERNI) |
| Pushbuttons (panel) | Generic 6mm or 12mm panel-mount tactile switch | Panel-mount, wired to header | Off-board part; board side is just a pin header | |
| Rocker switches (panel) | Generic panel-mount SPDT/SPST rocker | Panel-mount, wired to header | Off-board part | |
| LEDs (panel) | 3mm LED, panel-mount bezel or direct panel hole | Depends on mount style | See open question below | |
| DE0-Nano interface | 2x20 (0.1") IDC box header, 40-pin | THT | Standard, cheap | Mates with ribbon cable to DE0-Nano GPIO_0/GPIO_1 header |

## Open questions (blocking accurate schematic + BOM + PCB outline)

These are called out explicitly rather than guessed, because getting them wrong means
re-spinning the board:

1. **DIN41617 31-pin backplane pinout** — signal name per pin (which pins are +5V, GND,
   CS1800 bus lines — address/data/control — and which are spare/reserved). This drives
   the level-shifter channel assignment and the whole backplane sheet.
2. **DE0-Nano 40-pin header pinout / 1802-core pin mapping** — which of the two DE0-Nano
   GPIO headers (GPIO_0 or GPIO_1) is used, and which FPGA pin (and which 1802 core
   signal) is on each of the 40 header pins. Ideally your VHDL top-level port list /
   `.qsf` pin assignments for the CDP1802 core.
3. **Exact Eurocard "double slot" mechanical envelope** — board width x depth in mm,
   backplane-connector position/orientation on the board edge, card guide/rail pitch, and
   front panel width (so it actually fits the existing CS1800 rack next to the memory and
   serial I/O boards). A photo/measurement of an existing CS1800 board, or its drawing, is
   the fastest way to get this right.
4. **Front-panel control mounting style** — are the pushbuttons/rocker switches/LEDs
   mounted directly on the PCB (PCB sits behind the panel, bushings/actuators poke through
   panel cutouts) or fully panel-mount hardware wired back to on-board headers via a small
   harness? This changes both the footprints needed and the mechanical drawing.
5. ~~USB connector choice~~ **RESOLVED**: front panel carries a USB-C panel-mount
   connector, wired to the board via a 15cm USB-C-to-Micro-B cable. So the PCB itself
   needs a **USB Micro-B receptacle** (not USB-C, not USB-B) as the FT2232H-side
   connector; the USB-C part itself is off-board (panel + cable), not on this PCB's BOM.
6. **FT2232H exact variant/package** (FT2232H vs FT2232HL vs FT2232HQ) — affects footprint
   and whether an external EEPROM (for USB descriptors/serial number) is wanted.
7. **DE0-Nano mounting hole coordinates** — pull from Terasic's official DE0-Nano
   mechanical drawing rather than assume; 4x 3mm holes need to line up with the actual
   board.

## What exists in this repo right now

- Valid KiCad 10 project (`de0nano_cpu_card.kicad_pro`) opening a hierarchical schematic
  with **7 empty placeholder sheets** (one per block above), all internally consistent
  (`kicad-cli sch erc` → 0 violations).
- A placeholder PCB (`de0nano_cpu_card.kicad_pcb`) with just a 100x160mm board-outline
  rectangle and a giant on-board warning note not to route against it yet
  (`kicad-cli pcb drc` → 0 violations, since there's nothing on it yet).
- A project-local library setup (`sym-lib-table` / `fp-lib-table`) pointing at
  `libraries/symbols/cs1800.kicad_sym` and `libraries/footprints/cs1800.pretty/` for the
  custom parts this design will need (DIN41617 connector, DE0-Nano header representation,
  panel-mount parts) once footprints/symbols are sourced or built.
- `~/bin/kicad-cli10` — a wrapper script that runs the KiCad 10.0.6 AppImage's `kicad-cli`
  headlessly (FUSE-mounts the AppImage, runs the command, unmounts) without a multi-hundred-MB
  extraction. Useful for `sch erc`, `pcb drc`, netlist/BOM/gerber export, etc. from the
  command line as the design progresses.

## Next steps once open questions are answered

1. Fill in `sheets/backplane_connector.kicad_sch` with the real DIN41617 pin/net list.
2. Fill in `sheets/fpga_header.kicad_sch` with the real 40-pin header pin/net list.
3. Assign backplane bus lines to the 4 SN74LVC8T245 channels/direction pins in
   `sheets/level_shifters.kicad_sch`.
4. Populate `sheets/power.kicad_sch` (5V backplane -> DE0-Nano 5V pin, decoupling, maybe a
   3V3 rail tap for the level shifters' A-side Vcc if not sourced from the DE0-Nano itself).
5. Populate `sheets/usb_serial_bridge.kicad_sch` and `sheets/rs232.kicad_sch` with the
   FT2232H/MAX3232 reference circuits.
6. Populate `sheets/frontpanel_io.kicad_sch` with switch/LED/connector symbols once mounting
   style is confirmed.
7. Lock the PCB outline, place the backplane connector on the correct edge, place DE0-Nano
   mounting holes, then start placement/routing.
8. Run `kicad-cli10 sch export bom` / JLCPCB BOM+CPL export once parts are placed, and
   check every part against current JLCPCB stock before ordering.
