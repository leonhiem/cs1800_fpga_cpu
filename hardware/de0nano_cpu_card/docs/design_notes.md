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
├── sheets/pico_w_bridge.kicad_sch         Raspberry Pi Pico-W module, 2x on-board UART bridge
├── sheets/rs232.kicad_sch                 MAX3232 + DB9 (RS232 front panel)
└── sheets/frontpanel_io.kicad_sch         3x pushbutton, 3x rocker switch, 4x LED 3mm,
                                            USB-C connector, DB9 connector (all panel-mount)
```
(renamed from `usb_serial_bridge.kicad_sch` — **2026-10-05: FT2232H dropped**, see below)

Signal flow: `DIN41617 backplane (5V domain) <-> SN74LVC8T245 x4 <-> 40-pin header (3V3 domain) <-> ribbon cable <-> DE0-Nano GPIO`.
Pico-W UART0 (3V3, native — no level shifter needed): Pico-W <-> DE0-Nano GPIO header, fast
UART, terminal-forwarded over USB and/or WiFi/telnet. Pico-W UART1 (slower, 4800 baud):
Pico-W <-> MAX3232 <-> front-panel DB9 (RS232). Pico-W's own on-board micro-USB port is
used directly (short cable to the front-panel USB-C panel-mount connector) — no separate
USB connector part needed on this PCB's BOM.

### 2026-10-05 — FT2232H replaced by Raspberry Pi Pico-W

Decision: drop the FT2232H dual-UART USB bridge in favor of a Raspberry Pi Pico-W module,
mounted on 2.54mm headers (orientation: WiFi antenna edge up, toward the open top of the
rack; on-board micro-USB edge down, short cable to the front-panel USB-C connector).
**Why:** FT2232H is comparatively expensive and far faster than needed — this design only
needs 2 simple UARTs. The Pico-W does that plus gives WiFi/telnet-to-terminal for free,
plus spare GPIOs for future ideas, at a fraction of the cost.
Design consequences to carry into the Pico-W/power sheets:
- Needs a copper keepout under/around the Pico-W's antenna area for WiFi performance.
- Needs reverse-power protection so the backplane 5V rail and the Pico-W's USB-supplied
  5V (when the front-panel USB cable is connected) can't back-feed each other. (Check
  whether the Pico-W module's own on-board VSYS/VBUS Schottky diode already covers this,
  or whether an additional diode/load-switch is needed on this board's power sheet.)

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
- Form factor: Eurocard, double slot, 19" subrack. **Board outline RESOLVED**: 100mm
  (front-panel height) x 160mm (depth), i.e. standard single-Eurocard-3U PCB dimensions —
  see `docs/Eurocard.md` for the full component floorplan (DE0-Nano, Pico-W, header,
  level shifters, DIN41617 connector, front panel). "Double slot" governs the metal front
  panel's width (HP units along the rack) to fit all the controls — that width isn't
  pinned down in mm/HP yet, but it doesn't affect the PCB outline itself. The PCB in this
  repo (`de0nano_cpu_card.kicad_pcb`) is still the old 100x160mm *placeholder rectangle*
  with no real component placement — needs to be redrawn to match the actual floorplan in
  `Eurocard.md` before routing.
- Backplane pinout RESOLVED — see `docs/pinout_backplane.md`. 31 pins total: pin1=+5V,
  pin31=GND (not through level shifters), the other 29 are CDP1802 signals (data x8,
  address x8 muxed as A/15..A/8 style pairs, TPA/TPB, nMRD/nMWR, nINT, nEF1-3, Q, n0-n2,
  LC 50Hz) all of which go through the SN74LVC8T245 level shifters. Several inputs need
  external pull-ups (10k to +5V, plus 100pF to GND on nINT) — noted per-pin in that file.
- 4x M3 (3mm) mounting holes for the DE0-Nano board — positions not yet placed on the PCB;
  need DE0-Nano's official mechanical/hole-pattern drawing to place accurately (Terasic
  DE0-Nano User Manual has the dimensioned drawing). Do not trust a from-memory guess here.
- Front panel, finalized layout and wiring — see `docs/Eurocard.md` for the full ASCII
  drawing. All switches/buttons are panel-mount, wired to on-board 2-pin headers (pin1 =
  signal, pin2 = GND): rocker "run/halt" (pin1=halt), rocker "dog off" (pin1=dog), rocker
  "LC off" (pin1=LC), pushbutton "step", pushbutton "reset", pushbutton "qef4". The 4x
  LEDs (3mm) are through-hole, 90°-mounted and soldered directly to the PCB (not
  panel-mount): led1 green "fetch", led2 yellow "execute", led3 red "interrupt", led4 red
  "Q". The DB9 (RS232) is also soldered straight to the PCB, 90°-mounted: pin2=RXD,
  pin3=TXD, pin5=GND. USB-C is panel-mount, linked by a short cable to the Pico-W's own
  on-board micro-USB port (see Pico-W note below) — not a separate on-board connector.
- USB-serial/UART bridge: **Raspberry Pi Pico-W module** (replaces the originally-planned
  FT2232H — see dated decision note below), 2 UARTs — one fast UART (3V3, direct, no
  level shifting needed) to the DE0-Nano, one slower 4800-baud UART to the MAX3232/DB9.
  WiFi gives telnet-to-terminal as a bonus; spare GPIOs reserved for future ideas.
- Target fab/assembly: JLCPCB (PCBA), so part choice should favor JLCPCB Basic/Extended
  parts to keep assembly cost/lead-time down; anything not in their library becomes
  hand-solder/DNP-for-JLC.

## Proposed JLCPCB-friendly component shortlist (starting point, NOT final)

| Function | Candidate part | Package | JLCPCB fit | Notes |
|---|---|---|---|---|
| Level shifter x4 | Texas Instruments SN74LVC8T245PWR | TSSOP-24 | JLCPCB-stocked, ~$0.35 | DE0-Nano drives the DIR lines; needs 100nF ceramic decoupling per chip |
| UART/USB bridge | Raspberry Pi Pico-W module (on headers, not soldered directly) | Module-on-pins | Not a JLCPCB SMT part — hand-placed module on headers | Replaces FT2232H (2026-10-05 decision, see above); own on-board micro-USB used directly |
| RS232 transceiver | Texas Instruments MAX3232IDR (or MAX3232EIDR) | SOIC-16 | Extended, common | 3.3V-side transceiver (Pico-W side), needs 4x 0.1uF charge-pump caps |
| RS232 connector | DB9 (DE-9), 90°/right-angle, PCB-mount | THT | THT = manual/extra-cost assembly at JLCPCB | Soldered directly to PCB per `Eurocard.md`; pin2=RXD, pin3=TXD, pin5=GND |
| USB connector | — none on this PCB — | — | — | Pico-W's own on-board micro-USB port is used via a short cable to the front-panel USB-C; no separate connector part needed |
| Backplane connector | DIN 41612/41617 31-pin male, angled | THT, high pin count | THT, manual placement at JLCPCB (extra cost, longer lead time) | Pinout fixed (`pinout_backplane.md`); still need to pick/source the actual physical part (e.g. Amphenol/ERNI/HARTING DIN41612 31p male angled) |
| Pushbuttons (panel) x3 | Generic panel-mount tactile switch | Panel-mount, 2-pin header + wires on board | Off-board part; board side is just a 2-pin header | "step", "reset", "qef4" |
| Rocker switches (panel) x3 | Generic panel-mount SPDT/SPST rocker | Panel-mount, 2-pin header + wires on board | Off-board part | "run/halt", "dog off", "LC off" |
| LEDs x4 | 3mm LED, through-hole | THT, 90°, soldered directly to PCB | Standard, cheap | green "fetch", yellow "execute", red "interrupt", red "Q" |
| DE0-Nano interface | 2x20 (0.1") IDC box header, 40-pin | THT | Standard, cheap | Mates with ribbon cable to DE0-Nano GPIO header (which one: TBD, see open questions) |
| DE0-Nano power feed | 2-pin header ("P" in Eurocard.md) | THT | Standard, cheap | Carries backplane +5V/GND to the DE0-Nano board |

## Open questions (blocking accurate schematic + BOM + PCB outline)

These are called out explicitly rather than guessed, because getting them wrong means
re-spinning the board:

1. ~~DIN41617 31-pin backplane pinout~~ **RESOLVED** — see `docs/pinout_backplane.md`.
2. **DE0-Nano 40-pin header pinout / 1802-core pin mapping** — **IN PROGRESS**, user is
   defining this via the FPGA's `.qsf` pin-assignment file over the coming days. Ideally
   hand this over as the `.qsf`/VHDL top-level port list directly rather than a hand-typed
   table (`docs/pinout_de0nano_header.md` has the fill-in template if a table is easier).
   Also still need: which of the two DE0-Nano GPIO headers (GPIO_0 or GPIO_1) is used.
3. ~~Exact Eurocard mechanical envelope~~ **RESOLVED** (100x160mm PCB, full floorplan) —
   see `docs/Eurocard.md`. Still open within that: the metal front panel's width in
   HP/mm (a separate fabrication item from the PCB, e.g. for a Schaeffer/Frontplattenexpress
   order) isn't pinned down numerically yet, and the DIN41617 connector's precise
   board-edge position/orientation will fall out once the PCB is redrawn to this floorplan.
4. ~~Front-panel control mounting style~~ **RESOLVED** — see `docs/Eurocard.md` and the
   "Key design facts" section above (switches/buttons panel-mount + 2-pin header/wires;
   LEDs and DB9 soldered straight to the PCB).
5. ~~USB connector choice~~ **RESOLVED** — front panel carries a USB-C panel-mount
   connector, linked by a short cable directly to the **Raspberry Pi Pico-W module's own
   on-board micro-USB port**. No separate USB connector part on this PCB's BOM.
6. ~~FT2232H exact variant~~ **MOOT** — FT2232H dropped entirely in favor of a Raspberry
   Pi Pico-W module (2026-10-05 decision, see "Key design facts"/dated note above).
7. **DE0-Nano mounting hole coordinates** — still open; pull from Terasic's official
   DE0-Nano mechanical drawing rather than assume, so the 4x 3mm holes actually line up.
8. **New, from the Pico-W decision**: copper keepout area + placement for the Pico-W's
   WiFi antenna (needs to be near the open top of the rack per the user's note), and
   whether the Pico-W module's own on-board power-input protection is sufficient to stop
   backplane-5V/USB-5V back-feed or whether this board needs to add its own — to resolve
   when drawing `sheets/power.kicad_sch` and `sheets/pico_w_bridge.kicad_sch`.
9. **New**: source/select the actual physical DIN41612/41617 31-pin male angled connector
   part (manufacturer + part number) — pinout is fixed, part itself isn't picked yet.

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
5. Populate `sheets/pico_w_bridge.kicad_sch` (Pico-W module footprint/headers, antenna
   keepout) and `sheets/rs232.kicad_sch` (MAX3232 reference circuit).
6. Populate `sheets/frontpanel_io.kicad_sch` with switch/LED/connector symbols once mounting
   style is confirmed.
7. Lock the PCB outline, place the backplane connector on the correct edge, place DE0-Nano
   mounting holes, then start placement/routing.
8. Run `kicad-cli10 sch export bom` / JLCPCB BOM+CPL export once parts are placed, and
   check every part against current JLCPCB stock before ordering.
