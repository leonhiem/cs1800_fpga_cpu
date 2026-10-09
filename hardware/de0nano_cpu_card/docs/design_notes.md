# CS1800 DE0-Nano CPU Card — Design Notes

*Maintained by Claude; the other docs in this directory (`Eurocard.md`,
`backplane_notes.md`, `pinout_backplane.md`, `pinout_de0nano_header.md`,
`cs1800.qsf`, the Conec datasheet) are the user's source material — this file
is the synthesis of them, kept in sync as they change.*

## Status (2026-10-09)

**Architecture and mechanical/sourcing are fully resolved, and all 7
schematic sheets are now wired for real** (generated via the scripts in
`tools/`, see `tools/README.md`). Whole-hierarchy `kicad-cli sch erc` passes
with **0 errors**, 3 known/benign warnings:
- `footprint_link_issues` on the DIN41617 connector — its custom footprint
  hasn't been drawn yet (see §1/§7, Next steps #1).
- `lib_symbol_mismatch` x2 (`RaspberryPi_Pico_W`, `MAX3232`) — cosmetic only:
  kicad-cli compares the generator's flattened symbol cache against the live
  library and sees a structural (not electrical) difference. Opening the
  project in the real GUI will likely offer "update symbol from library",
  safe to accept.

`kicad-cli pcb drc` on the still-placeholder PCB outline: 0 violations.
What remains is PCB-side work: the custom DIN41617 footprint, redrawing the
board outline to the real floorplan, placement, and routing.

## Purpose

Replacement CPU board for the CS1800 backplane system (originally a CDP1802
CPU board). This board carries a Terasic DE0-Nano (Cyclone IV FPGA,
`EP4CE22F17C6N`) running a VHDL CDP1802 core, and bridges it electrically and
mechanically into the existing CS1800 rack: DIN41617 backplane connector, 5V
backplane power, double-slot Eurocard form factor, front panel controls, and
a Pico-W-based UART/WiFi debug path. The rack supplies the real memory
cards, the real CDP1854 SIO board and the real 50Hz line clock — this module
does **not** generate or need its own clock input from the backplane (it
does need its own 4MHz-class clock on-board for the core, since the
backplane doesn't carry one).

## Schematic hierarchy

```
de0nano_cpu_card.kicad_sch (root)
├── sheets/backplane_connector.kicad_sch   DIN41617, 31p male, 5V in + CS1800 bus signals
├── sheets/level_shifters.kicad_sch        6x SN74LVC8T245 total (see below)
├── sheets/fpga_header.kicad_sch           2x 40-pin IDC headers (JP1/GPIO_0, JP2/GPIO_1) -> ribbon cables -> DE0-Nano
├── sheets/power.kicad_sch                 backplane 5V -> DE0-Nano 5V feed, local rails/decoupling
├── sheets/pico_w_bridge.kicad_sch         Raspberry Pi Pico-W module, 2x UART + 8x spare GPIO
├── sheets/rs232.kicad_sch                 MAX3232 + DB9 (RS232 front panel)
└── sheets/frontpanel_io.kicad_sch         3x pushbutton, 3x rocker switch, 4x LED 3mm,
                                            USB-C connector, DB9 connector (all panel-mount)
```

All 7 sheets are now wired with real nets/components (2026-10-09), generated
from the pin data below via `tools/` — `sch erc` is clean. Custom footprints
and PCB layout are the remaining work (see "Next steps").

## 1. The backplane connector

DIN 41617, **31 positions, male, angled**, plain 1-31 numbering (not an
A-B-C multi-row connector). Full pin table: `docs/pinout_backplane.md`.
Design rationale/derivation: `docs/backplane_notes.md`.

| direction (card's view) | count | signals |
|---|---|---|
| out | 16 | `nMWR` `TPA` `nMRD` `TPB` `ADDR[7:0]` `N[2:0]` `Q` |
| inout | 8 | `DATA[7:0]` |
| in | 5 | `LC` (50Hz) `nINT` `nEF[2:0]` (backplane's nEF1-3) |
| power | 2 | pin 1 `+5V`, pin 31 `GND` |

29 signals cross the level shifters; pins 1 and 31 don't. The address bus is
the CDP1802's multiplexed 8-bit bus (`A7/A15` down to `A0/A8`), latched on
the memory cards at TPA's trailing edge. The backplane carries no SC0/SC1,
no DMA lines, no CLEAR/WAIT, and no CLOCK.

**Physical part identified**: Conec/Amphenol DIN41617 male angled, 31-pos,
2.50mm pitch, quality-class-3 hard-silver-plated contacts — **Amphenol
101-A-10119-X** (Mouser-stocked). Datasheet: `docs/conec_connectors_din_41617-3009425.pdf`.
Key mechanical dims for the KiCad footprint (not in any stock KiCad
library — needs a custom footprint):
- contact pitch 2.50mm, 30 spaces pin-to-pin (pins 1→31) = 75.00mm span
- mounting-hole-to-mounting-hole spacing: 85.00mm, holes sit 5.00mm outboard
  of pin 1 / pin 31 on the same axis
- overall body length: 90.6mm (right-angle/male, the variant we're using)
- PCB pad hole diameter: 1.0-1.1mm (pins ~0.8mm)

## 2. Level shifter allocation — 6x SN74LVC8T245, not 4

**Correction from earlier notes: this is 6 chips, not 4.** 4 chips serve the
backplane bus; **2 more** serve an 11-signal "CDP1802 control pins" header
for future expansion (DMA, CLEAR/WAIT, chip-select, extra EF, etc.) that
is *not* exposed on the backplane — see §4. All 6 are
`VCCA`=3.3V (DE0-Nano side), `VCCB`=5V (backplane pin 1 / on-board 5V rail).

### Backplane-facing 4 chips (29 of 32 channels used)

| device | channels used | `DIR` | signals |
|---|---|---|---|
| OUT-1 | 8 | tied high (VCCA) | `ADDR[7:0]` |
| OUT-2 | 8 | tied high (VCCA) | `nMWR` `TPA` `nMRD` `TPB` `N[2:0]` `Q` |
| DATA | 8 | FPGA-driven (`DATA_DIR`) | `DATA[7:0]` |
| IN | 5 (3 spare) | tied low (GND) | `LC` `nINT` `nEF[0:2]` |

On the '8T245, `DIR` high = A→B; with A as the FPGA side, high means the
module drives the backplane. `OE` is active low.

**`OE` must reach the FPGA, not be hard-strapped** (unlike `DIR`, which can
be strapped for the unidirectional groups), for three reasons: (1)
power-up/configuration bus contention — Cyclone IV I/O are high-Z with weak
pull-ups until the core is out of reset, so an always-enabled DATA
transceiver would drive the rack's data bus against real memory on every
power-up; (2) read→write turnaround dead-time (~125ns measured) — `DIR`
swaps direction without ever disabling the driver, only `OE` can create a
genuine dead time; (3) at power-up, with OUT-1/OUT-2 permanently enabled,
`TPA`/`TPB`/`Q` would be driven by the FPGA's weak pull-ups (→ '1') before
the CPU exists.

**Default-state resistors** (must be right *before* the FPGA configures):

| net | resistor | resulting default | why |
|---|---|---|---|
| `DATA_DIR` | pull-down | B→A: backplane drives, card listens | never drive the rack's bus by accident |
| `DATA_nOE` | pull-up | DATA transceiver disabled | no contention at power-up |
| `BUF_nOE` | pull-up | OUT-1/OUT-2 disabled | card silent until CPU runs |

**Pull-ups the backplane itself needs** (5V/B side, not the FPGA side) —
from `pinout_backplane.md`: 10k to +5V on `D0`-`D7`, `LC`, `nEF1`, `nEF2`,
`nEF3`; 10k to +5V **and** 100pF to GND on `nINT`. With the DATA transceiver
disabled these hold the bus at the benign all-ones state.

### CDP1802 control / future-expansion 2 chips (11 of 16 channels used)

Not connected to the backplane — these drive a dedicated on-board header for
future ideas (e.g. a DMA/debug daughter-board):
- Outputs (4): `CS[0]` `CS[1]` `EX_OUT[0]` `EX_OUT[1]`
- Inputs (7, need 10k pull-up each): `nEF[3]` `nCLEAR` `nWAIT` `nDMA_OUT`
  `nDMA_IN` `EX_IN[0]` `EX_IN[1]`

User's plan: a double-row header, 11 pins of signal + 11 pins of GND.

## 3. FPGA pin assignment (`cs1800.qsf`)

Two DE0-Nano GPIO headers are both used, for two different purposes:

**GPIO_0 / JP1 → the backplane**, via the level shifters, via a 40-pin
ribbon cable. 32 of 40 pins used (29 backplane signals + `DATA_DIR` +
`DATA_nOE` + `BUF_nOE`); all `3.3-V LVTTL`. Pin locations: `cs1800.qsf`
lines 129-281. Unused/spare on this header: pins 1, 3, 39, 40 (pins 11/12/29/30
are the DE0-Nano's own VCC_SYS/GND/VCC3P3/GND per `pinout_de0nano_header.md`).

**GPIO_1 / JP2 → local Eurocard wiring** (Pico-W, future-expansion header,
LEDs, switches/buttons), via a second 40-pin ribbon cable. 31 of 40 pins
used. Pin locations: `cs1800.qsf` lines 285-427.

| group | signals | pins (JP2) |
|---|---|---|
| UART to Pico-W (3.3V direct, no level shift) | `UART0_TXD` (out), `UART0_RXD` (in) | 2, 4 |
| Spare GPIO to Pico-W, future ideas | `PICO[7:0]` | 8,9,10,13,14,15,16,17 |
| CDP1802 control, outputs (→ level shifters) | `CS[0]` `CS[1]` `EX_OUT[0]` `EX_OUT[1]` | 18,19,20,21 |
| CDP1802 control, inputs (→ level shifters, need 10k pull-up) | `EX_IN[0]` `EX_IN[1]` `nEF[3]` `nCLEAR` `nWAIT` `nDMA_OUT` `nDMA_IN` | 22,23,24,25,26,27,28 |
| Front-panel LEDs (3.3V direct, FPGA sources through 220Ω to anode, cathode to GND) | `LED1_fetch` `LED2_execute` `LED3_interrupt` `LED4_Q` | 31,32,33,34 |
| Front-panel switches/buttons (3.3V direct in, need 10k pull-up each) | `SW_halt` `SW_dog` `SW_LC_off` `BUT_step` `BUT_reset` `BUT_qef4` | 35,36,37,38,39,40 |

Spare on this header: pins 1, 3, 5, 6, 7 (pins 11/12/29/30 again DE0-Nano's
own VCC_SYS/GND/VCC3P3/GND).

## 4. Pico-W module

Mounted on headers (not soldered down), oriented antenna-edge up (toward the
rack's open top, for WiFi performance — needs a copper keepout underneath),
on-board micro-USB edge down, short cable from that micro-USB to the
front-panel USB-C connector (no separate USB connector part on this PCB's
BOM). Runs software that forwards 2 UARTs to USB/terminal and, via WiFi,
telnet:

| Pico-W physical pin | function | connects to |
|---|---|---|
| 1, 2 | UART0 (fast) | DE0-Nano `UART0_RXD`/`UART0_TXD` (JP2 pins 4/2) |
| 6, 7 | UART1 (slow, 4800 baud) | MAX3232 TTL side |
| 19,20,21,22,24,25,26,27 | `PICO[0:7]` spare GPIO | DE0-Nano JP2 pins 17,16,15,14,13,10,9,8 |
| 3,8,13,18,23,28,33,38 | GND | board GND |
| 39 | VSYS | board +5V, **through a Schottky diode** (e.g. 1N5817): anode on the board's +5V rail, cathode on VSYS pin 39 |

Also needs a low-ESR bulk capacitor on its power supply line. **Back-feed
protection resolved**: the Schottky diode on VSYS does two jobs — stops the
Pico-W's own USB-supplied 5V (when the front-panel USB cable is plugged
into a PC) from back-feeding onto this board's +5V rail, and protects the
board's local +5V rail if something upstream of VSYS ever pushes more than
5V in via USB. Only current flow board-5V → VSYS is allowed.

## 5. RS232 (MAX3232 + DB9)

DB9, 9-pin, 90°/right-angle, soldered directly to the PCB (not panel-mount
hardware): pin2=RXD, pin3=TXD, pin5=GND. MAX3232 TTL side wired to Pico-W
UART1 (pins 6/7). **Part chosen: `MAX3232EIDR`, SOIC-16** (picked over
`MAX3232IPW`/TSSOP-16 for easier hand-handling). Needs 4x 0.1uF charge-pump
ceramic caps.

## 6. Front panel (all confirmed, see `Eurocard.md` for the full floorplan)

- 4x LED, 3mm through-hole, 90°, soldered to PCB: led1 green "fetch", led2
  yellow "execute", led3 red "interrupt", led4 red "Q" — cathode to GND,
  anode through a 220Ω series resistor to the FPGA pin (via GPIO_1, direct
  3.3V, no level shift).
- 3x rocker switch (panel-mount, 2-pin header + wires, pin1=signal/pin2=GND,
  10k pull-up each): "run/halt" (`SW_halt`), "dog off" (`SW_dog`), "LC off"
  (`SW_LC_off`).
- 3x pushbutton (same wiring pattern): "step" (`BUT_step`), "reset"
  (`BUT_reset`), "qef4" (`BUT_qef4`).
- USB-C panel-mount, short cable to the Pico-W's own on-board micro-USB.
- DB9 RS232, soldered directly to PCB (see §5).

## 7. Mechanical / Eurocard floorplan

Board: 100mm (front-panel height) x 160mm (depth) — standard single-Eurocard
3U PCB size. Full component floorplan (ASCII) in `Eurocard.md`. Two 40-pin
headers on this board mate with the DE0-Nano's GPIO_0 (JP1/H0, to backplane
via level shifters, on the backplane-connector side of the floorplan) and
GPIO_1 (JP2/H1, to Pico-W/future-header/front-panel, on the front-panel side
of the floorplan) via ribbon cables. A 2-pin header ("P") feeds the DE0-Nano
+5V/GND from the backplane — needs a low-ESR bulk cap there too.

### DE0-Nano mechanical (from `docs/de0-nano_notes.md`)

Board size **49 x 75.2mm**. No official Terasic-published dimensioned
drawing exists (per the user's research) — these figures come from
community CAD models / the GrabCAD listing (https://grabcad.com/library/altera-de0-nano-1)
and standard pin pitches, not an official Terasic drawing; good enough to
build from, but worth a sanity-check against the physical board before
drilling final holes.

- GPIO_0/GPIO_1 headers: 2x20, 2.54mm pitch both directions, on the two
  long edges, inset ~1.64mm from the 49mm-wide edges. Header-to-header
  spacing (innermost rows) = 40.64mm center-to-center.
- **4x M3 mounting holes**, rectangular pattern, each inset 3.5mm from the
  board edges on both axes → hole-to-hole spacing 68.2mm (long axis) x
  42.0mm (short axis). In board-local coordinates (origin at a corner):
  **(3.5, 3.5), (3.5, 71.7), (45.5, 3.5), (45.5, 71.7)** mm.

### Front panel (from `docs/front-panel-notes.md`)

Standard 19" rack, double-slot: **width 40mm, height 128mm** (128mm matches
the standard 3U rack panel height). This is the overall envelope only —
exact switch/LED/connector hole positions are **not** being engineered in
the PCB/CAD flow; the user will hand-drill those, so this doesn't block PCB
or schematic work.

**Still placeholder**: `de0nano_cpu_card.kicad_pcb` only has a generic
100x160mm outline rectangle — it hasn't been redrawn to the real floorplan
in `Eurocard.md` + the mounting-hole coordinates above yet.

## 8. Signal integrity

DE0-Nano reaches the level shifters over a 40-pin ribbon cable (JP1). LVTTL
edges are 1-2ns regardless of the 4MHz clock rate, so: series termination
~33-47Ω at the FPGA end on the fast outputs (`TPA`, `TPB`, `nMRD`, `nMWR`);
interleave grounds on the ribbon wherever the header allows; keep the DATA
group's ribbon length matched to `TPB`'s (CDP1854 hold-margin budget).

## 9. CDP1802 core — tri-state pattern at the FPGA boundary

```vhdl
entity cs1800_de0nano_top is
  port (
    CLOCK_50 : in    std_logic;                     -- DE0-Nano oscillator
    DATA     : inout std_logic_vector(7 downto 0);
    ADDR     : out   std_logic_vector(7 downto 0);
    TPA, TPB : out   std_logic;
    nMRD, nMWR : out std_logic;
    N        : out   std_logic_vector(2 downto 0);
    Q        : out   std_logic;
    LC, nINT : in    std_logic;
    nEF      : in    std_logic_vector(2 downto 0);
    DATA_DIR : out   std_logic;                     -- '8T245 DIR, high = we drive
    DATA_nOE : out   std_logic;                     -- '8T245 OE, active low
    BUF_nOE  : out   std_logic
  );
end entity;
...
  DATA      <= data_out_i when data_drive = '1' else (others => 'Z');
  data_in_i <= DATA;
  DATA_DIR  <= data_drive;
  DATA_nOE  <= '0' when core_running = '1' and not turnaround else '1';
  BUF_nOE   <= '0' when core_running = '1' else '1';
```

The core's `DATA_IN`/`DATA_OUT`/`DATA_OE` are exposed separately in
`src/vhdl/cdp1802.vhd` for exactly this reason; the top level reassembles
them into the single `inout` pin. Cyclone IV has true bidirectional I/O, so
the data bus costs 8 FPGA pins, not 16 — only *internal* tri-states are
impossible in FPGA fabric, pin-boundary tri-states are normal.

## 10. JLCPCB-oriented BOM shortlist (updated)

| Function | Candidate part | Package | Qty | Notes |
|---|---|---|---|---|
| Level shifter | Texas Instruments SN74LVC8T245PWR | TSSOP-24 | **6** | 4 for backplane bus, 2 for future-expansion header; ~$0.35 ea; 100nF ceramic decoupling on both VCCA and VCCB per chip |
| UART/USB/WiFi bridge | Raspberry Pi Pico-W module | module-on-headers | 1 | hand-placed, not a JLCPCB SMT part; own on-board micro-USB used directly; needs antenna copper keepout + low-ESR bulk cap on VSYS |
| RS232 transceiver | **MAX3232EIDR**, SOIC-16 | SOIC-16 | 1 | chosen over MAX3232IPW (TSSOP-16) for easier hand-handling; 4x 0.1uF ceramic |
| RS232 connector | DB9 (DE-9), 90°, PCB-mount | THT | 1 | pin2=RXD, pin3=TXD, pin5=GND |
| USB connector | — none — | — | 0 | Pico-W's own micro-USB used via cable |
| Backplane connector | **Amphenol 101-A-10119-X** (DIN41617, 31p, male, angled, 2.5mm pitch) | THT | 1 | manual placement at JLCPCB (extra cost/lead time); custom KiCad footprint needed |
| Pushbuttons (panel) x3 | Generic panel-mount tactile switch | panel-mount + 2-pin header | 3 | "step", "reset", "qef4" |
| Rocker switches (panel) x3 | Generic panel-mount SPDT/SPST rocker | panel-mount + 2-pin header | 3 | "run/halt", "dog off", "LC off" |
| LEDs x4 | 3mm LED, THT | THT, 90°, soldered to PCB | 4 | green/yellow/red/red, 220Ω series resistor each |
| DE0-Nano interface headers | 2x20 (0.1") IDC box header, 40-pin | THT | 2 | JP1 (GPIO_0, to level shifters) + JP2 (GPIO_1, to Pico-W/local) |
| DE0-Nano power feed | 2-pin header | THT | 1 | backplane +5V/GND to DE0-Nano, + low-ESR bulk cap |
| Future-expansion header | 2x11 (or 2x12) pin header | THT | 1 | 11 level-shifted CDP1802 control signals + 11 GND |
| Pull-up resistors, 10k | — | 0805/0603 | ~18 | backplane: D0-D7, LC, nEF1-3, nINT (9); control header inputs: nEF[3], nCLEAR, nWAIT, nDMA_OUT, nDMA_IN, EX_IN[0:1] (7); front panel switches/buttons (6) — tally precisely once schematics are wired |
| Misc caps | 100nF ceramic (decoupling), 0.1uF (MAX3232 charge pump), 100pF (nINT filter), low-ESR bulk x2 (DE0-Nano feed, Pico-W VSYS) | 0603/0805 | — | |
| Schottky diode | 1N5817 (or equivalent) | SMA/DO-214AC or THT | 1 | anode on board +5V, cathode on Pico-W VSYS (pin 39) — back-feed protection |

## Open questions

**All architecture and mechanical/sourcing questions are now resolved.**
What's left is execution (schematic capture, footprints, PCB layout), not
open decisions:

1. ~~DIN41617 backplane pinout~~ **RESOLVED**.
2. ~~DE0-Nano header / CDP1802 pin mapping~~ **RESOLVED** — `cs1800.qsf` is
   the source of truth.
3. ~~Front-panel mounting style~~ **RESOLVED**.
4. ~~USB connector~~ **RESOLVED** — Pico-W's own micro-USB.
5. ~~FT2232H~~ **MOOT** — replaced by Pico-W.
6. ~~DE0-Nano mounting hole coordinates~~ **RESOLVED** — see §7
   (community-sourced, not an official Terasic drawing; worth a
   sanity-check against the physical board before drilling final holes).
7. ~~Front panel envelope~~ **RESOLVED** — 40 x 128mm overall; exact
   hole positions are the user's hand-drilling job, not part of this CAD
   flow.
8. ~~MAX3232 variant~~ **RESOLVED** — `MAX3232EIDR`.
9. ~~Pico-W VSYS back-feed protection~~ **RESOLVED** — 1N5817 Schottky
   diode, board-5V → VSYS.

## Next steps

1. ~~Wire up all 7 schematic sheets~~ **DONE (2026-10-09)** — all real nets
   from §1-§6 are in, `sch erc` is clean (0 errors). See `tools/README.md`
   for how they were generated and how to regenerate a sheet after a pinout
   change.
2. Build the custom DIN41617 footprint (dims in §1) and any other missing
   footprints, into `libraries/footprints/cs1800.pretty/`.
3. Redraw the PCB outline to the real 100x160mm floorplan from
   `Eurocard.md`: place the DE0-Nano mounting holes at the coordinates in
   §7, lay out the two 40-pin headers, the DIN41617 connector, the 6 level
   shifters (+ the 2x11 future-expansion header), the Pico-W header,
   MAX3232, DB9, and the 2-pin DE0-Nano power feed, then route.
4. `kicad-cli10 sch export bom` / JLCPCB BOM+CPL export once parts are
   placed; check every part against current JLCPCB/LCSC stock before
   ordering (MAX3232EIDR, the DIN41617 connector as a THT manual-assembly
   item, SN74LVC8T245PWR x6, Pico-W module sourced/placed separately since
   it's not a JLCPCB SMT part).
