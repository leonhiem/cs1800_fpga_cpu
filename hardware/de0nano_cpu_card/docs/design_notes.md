# CS1800 DE0-Nano CPU Card — Design Notes

*Maintained by Claude; the other docs in this directory (`Eurocard.md`,
`backplane_notes.md`, `pinout_backplane.md`, `pinout_de0nano_header.md`,
`cs1800.qsf`, the Conec datasheet) are the user's source material — this file
is the synthesis of them, kept in sync as they change.*

## Status (2026-10-09)

**Architecture and mechanical/sourcing are fully resolved, all 7 schematic
sheets are wired for real** (generated via the scripts in `tools/`, see
`tools/README.md`), **and the custom DIN41617 footprint now exists**
(`libraries/footprints/cs1800.pretty/DIN41617_31P_Male_Angled.kicad_mod`).
Whole-hierarchy `kicad-cli sch erc` passes with **0 errors**, 2 known/benign
cosmetic warnings (`lib_symbol_mismatch` on `RaspberryPi_Pico_W` and
`MAX3232` — kicad-cli compares the generator's flattened symbol cache
against the live library and sees a structural, not electrical, difference;
the GUI will likely offer "update symbol from library", safe to accept).

`kicad-cli pcb drc` on the still-placeholder PCB outline: 0 violations. What
remains is PCB-side work: any other missing footprints, redrawing the board
outline to the real floorplan, placement, and routing.

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

**Custom footprint built** (not in any stock KiCad library): `cs1800:DIN41617_31P_Male_Angled`
in `libraries/footprints/cs1800.pretty/`, built by
`tools/gen_din41617_fp.py` from the datasheet's dimensioned PCB-hole-pattern
drawing:
- contact pitch 2.50mm, 30 spaces pin-to-pin (pins 1→31) = 75.00mm span,
  pin1 at the footprint's local origin
- mounting-hole-to-mounting-hole spacing: 85.00mm, holes sit 5.00mm outboard
  of pin 1 / pin 31 on the same axis (NPTH, 2.8mm drill)
- signal pads: 1.1mm drill, 2.0mm pad, pin1 marked with a square/roundrect pad
- overall body length: 90.6mm (right-angle/male, the variant we're using)
- **the body/silkscreen/courtyard outline is an unverified approximation**
  (only the overall 90.6mm length is from the datasheet; depth is a
  placeholder) — the electrical pad/mounting-hole positions are
  datasheet-precise, but check the outline against the physical part (or a
  3D model, if Amphenol publishes one) before finalizing silkscreen/courtyard
  clearances.

## 2. Level shifter allocation — 6x SN74LVC8T245, not 4

**Correction from earlier notes: this is 6 chips, not 4.** 4 chips serve the
backplane bus; **2 more** serve an 11-signal "CDP1802 control pins" header
for future expansion (DMA, CLEAR/WAIT, chip-select, extra EF, etc.) that
is *not* exposed on the backplane — see §4. All 6 are
`VCCA`=3.3V (DE0-Nano side), `VCCB`=5V (backplane pin 1 / on-board 5V rail).

**Decoupling (2026-10-09, found during GUI schematic review)**: each of the
6 chips needs a 100nF ceramic cap on *both* supplies — 12 caps total
(`level_shifters.kicad_sch`, C1-C12). Schematically placed near each IC for
readability, but the requirement that actually matters is a **PCB-layout**
one: each cap needs to sit physically close to its IC's VCCA/VCCB pin when
placing parts — the schematic placement doesn't guarantee that, it's a
placement-phase TODO (see "Next steps").

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
  `nDMA_IN` `EX_IN[0]` `EX_IN[1]` — **implemented**: 10k to +5V on each
  `EXP_*` net (B-side, i.e. the header side) in `level_shifters.kicad_sch`.

User's plan: a double-row header, 11 pins of signal + 11 pins of GND.

**Spare-channel handling (2026-10-09, found during GUI schematic review)**:
with 11 of 16 channels on the two future-expansion chips in use, and 5 of 8
on the backplane "IN" chip, the spare channels needed a defined state rather
than floating:
- U4 (backplane IN chip) B-side spares (pins 14/15/16, i.e. B8/B7/B6 —
  backplane-side, currently unused capacity): 10k pull-up to +5V each, same
  treatment as the real backplane inputs they sit alongside.
- U6 (future-expansion IN chip) B-side spare (pin 14, B8): 10k pull-up to +5V.
- U5 (future-expansion OUT chip) A-side spares (pins 7/8/9/10, i.e. A5-A8 —
  FPGA side, unused chip inputs since DIR is tied A→B): hard-tied to GND
  (no resistor — these are unused transceiver *inputs*, not nets needing a
  weak pull, so a direct tie is correct and avoids a floating CMOS input).
  ERC reports this as a `pin_to_pin` warning ("Bidirectional and Power
  output are connected") — expected and benign, exactly what a hard tie to
  GND looks like from ERC's perspective.
- U4's own A-side spares and U5/U6's *other*-side spares (A6-A8 on U4;
  B5-B8 on U5; A8 on U6) were left as `no_connect` — genuinely unused chip
  capacity on our own side, nothing external to float against.

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

Mounted on headers (not soldered down) — **footprint**:
`cs1800:RaspberryPi_Pico_W_SocketHeaders_2x1x20_P2.54mm` (built by
`tools/gen_pico_socket_fp.py`), two 1x20 2.54mm-pitch socket-strip rows,
17.78mm (0.7") apart — genuine Pico/Pico W spacing, cross-checked against
KiCad's own `Module:RaspberryPi_Pico_Common_THT` footprint. Socketing
(rather than direct-soldering the module) is required, not just a nicety:
the Pico-W needs to sit elevated above this board so its own micro-USB port
has room for a cable to actually plug in. **When sourcing the socket strips,
pick a "tall"/stacking-header-height part, not a low-profile one** — the
footprint only fixes pad positions, not standoff height, so getting enough
USB-cable clearance is a BOM part choice, not something the footprint
enforces. Oriented antenna-edge up (toward the rack's open top, for WiFi
performance — needs a copper keepout underneath), on-board micro-USB edge
down, short cable from that micro-USB to the front-panel USB-C connector (no
separate USB connector part on this PCB's BOM). Runs software that forwards
2 UARTs to USB/terminal and, via WiFi, telnet:

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

**PCB now has the real 100x160mm outline, the DE0-Nano mechanical
reference + its 4 mounting holes, and all 86 real components placed**
(2026-10-09, `tools/build_pcb.py` + `tools/pcbgen.py`) — see §7a below.
Rough-placed only; the user is doing final placement + routing.

## 7a. PCB layout status (2026-10-09)

All 86 real footprints (89 schematic components minus the 3 virtual
`PWR_FLAG`s, which have no physical footprint) are placed on the board via
`tools/build_pcb.py`, which pulls the netlist straight from the schematic
(`kicad-cli sch export netlist`) so every pad's net assignment is
authoritative — no hand-copied connectivity. Grouped roughly per
Eurocard.md's left-to-right floorplan (front panel / LEDs+switches+RS232+
Pico-W on the left, future-expansion level shifters, GPIO_1/JP2, the
DE0-Nano reference, GPIO_0/JP1, backplane-facing level shifters, DIN41617
on the right), but genuinely **rough**: `pcb drc` on the result shows

- **0 electrical shorts** (`shorting_items`) — the real correctness bar for
  "is this safe to open and place", and it's clean.
- **309 unrouted connections** (`unconnected_items`) — expected, nothing
  has been routed yet.
- **73 cosmetic/mechanical placement warnings** (silkscreen overlaps,
  courtyard overlaps, a couple of board-edge/hole clearance nits) — this is
  the "not finely placed" part; resolving these is exactly the user's
  placement pass, not something to chase further here. One specific one
  worth knowing about going in: J1 (the DIN41617 connector, rotated 90°)
  has one pad slightly over the top board edge — trivial to nudge once
  placing it for real; hand-computing its exact rotated span wasn't worth
  the iteration time versus just doing it in the GUI.

**2026-10-09 (later): J1 pin order + zigzag corrected.** The user caught
two mistakes in the `cs1800:DIN41617_31P_Male_Angled` footprint from a
visual GUI inspection against the datasheet's PCB-hole-pattern drawing
(`docs/conec_connectors_din_41617-3009425.pdf`):
- Pin 1 was at the board's bottom-right instead of top-right (pin 31 was
  top instead of bottom) — the footprint's local pin-numbering direction
  was reversed relative to what J1's 90° placement rotation needed.
- All 31 pads were on one straight line; the real part's PCB-hole pattern
  is a **zigzag**: odd pins sit one row, even pins a second row offset
  2.54mm "inward" (toward the board's interior / away from the connector's
  board edge).
Both fixed in `tools/gen_din41617_fp.py` (regenerate with
`python3 gen_din41617_fp.py`, then `python3 build_pcb.py`). The fix was
verified with `kicad-cli pcb render` (cropped renders of the J1 corner),
not just reasoned about by hand, since J1's rotation makes the local→board
coordinate mapping non-obvious — see the comments in
`gen_din41617_fp.py` for the verified odd/even → y-offset sign.
`pcb drc` after the fix: still 0 electrical shorts, 309 unrouted
(unchanged), cosmetic warnings now 73 (down from 77).

**2026-10-09 (later still): J1 mounting holes + body near-edge corrected.**
The user read 3 more real dimensions off the datasheet's PCB-hole-pattern
drawing: each mounting hole is 2.5mm from its nearest end pin (pin 1 /
pin 31) in the same direction that already makes the odd-pin row the
"close to board edge" row (not inward); the two mounting holes are 85mm
apart center-to-center (matches the datasheet's own 31-position "D"
dimension exactly: span(75) + 2x5mm outboard inset = 85 -- a useful
cross-check that the existing along-row hole placement was already
right, only the perpendicular/depth offset was missing); and the plastic
body's near edge (where the solder pins enter the housing) is a further
4.3mm out from the mounting hole, same direction. Fixed in
`tools/gen_din41617_fp.py` (`MOUNT_Y_OFFSET`, `PLASTIC_EDGE_OFFSET`). The
body's far edge / overall depth is still an unverified placeholder (no
datasheet dimension for it yet) -- only the near edge moved to a real
value. `pcb drc`: still 0 shorts, 309 unrouted, 72 cosmetic warnings.

Side effect worth flagging: with the mounting holes now correctly offset
further toward the board edge than the pads, and J1's current rough
X-placement (154mm, see `build_pcb.py`) already putting the nearest pads
right at the edge (the pre-existing nit above), the mounting holes now
visibly overhang past the board edge in a render. This isn't a new
footprint-geometry bug -- it's the existing "J1's X placement needs a
small inward nudge" issue becoming more visible now that there's a real
mounting hole sitting further out than the pads were. Left for the same
placement pass as the pad-edge nit, not fixed here.

**2026-10-09 (later still, correction): body rectangle had the near/far
edges backwards.** The first pass put `PLASTIC_EDGE_OFFSET` (4.3mm) on
`body_y0`, meaning the whole body rectangle sat entirely *beyond* the
mounting holes and pads -- i.e. the pads/holes were outside the drawn
outline instead of inside it, which the user caught immediately. Fixed:
the 4.3mm dimension is the body's FAR edge (`body_y1`, beyond the
mounting holes, toward the board edge/mating face); the near edge
(`body_y0`, just behind the pad row) is still an unverified small-margin
placeholder, now correctly on the *other* end. Verified with another
`kicad-cli pcb render` crop that the pads and both mounting holes now
fall strictly inside the outline. `pcb drc`: still 0 shorts, 309
unrouted, 73 cosmetic warnings.

The DE0-Nano reference footprint (`cs1800:DE0Nano_Reference_Outline`) is
mechanical-only (NPTH mounting holes, no copper pads), so it can't
electrically short against anything and wasn't given its own reserved
clear zone — it may cosmetically overlap small passives in this rough
view near the GPIO_0/GPIO_1 headers.

Re-running `tools/build_pcb.py` regenerates the board **from scratch** —
once the user starts real placement/routing, don't re-run it (same caveat
as the schematic `build_*.py` scripts).

## 8. Signal integrity

DE0-Nano reaches the level shifters over a 40-pin ribbon cable (JP1). LVTTL
edges are 1-2ns regardless of the 4MHz clock rate, so: series termination
at the FPGA end on the fast outputs (`TPA`, `TPB`, `nMRD`, `nMWR`) —
**implemented as 10Ω** (`fpga_header.kicad_sch`, R20-R23, between J1's pins
and the `*_FPGA`-suffixed net that feeds the level shifter; the plain net
name continues on unchanged into `level_shifters.kicad_sch`), chosen by the
user over the originally-suggested 33-47Ω range; interleave grounds on the
ribbon wherever the header allows; keep the DATA group's ribbon length
matched to `TPB`'s (CDP1854 hold-margin budget).

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
| Pico-W socket headers | 2x 1x20, 2.54mm pitch, THT, **tall/stacking-height** (not low-profile) | THT | 2 | soldered to this board; Pico-W plugs in — needed for USB-cable clearance, see §4 |
| RS232 transceiver | **MAX3232EIDR**, SOIC-16 | SOIC-16 | 1 | chosen over MAX3232IPW (TSSOP-16) for easier hand-handling; 4x 0.1uF ceramic |
| RS232 connector | DB9 (DE-9), 90°, PCB-mount | THT | 1 | pin2=RXD, pin3=TXD, pin5=GND |
| USB connector | — none — | — | 0 | Pico-W's own micro-USB used via cable |
| Backplane connector | **Amphenol 101-A-10119-X** (DIN41617, 31p, male, angled, 2.5mm pitch) | THT | 1 | manual placement at JLCPCB (extra cost/lead time); custom KiCad footprint built (`cs1800:DIN41617_31P_Male_Angled`) |
| Pushbuttons (panel) x3 | Generic panel-mount tactile switch | panel-mount + 2-pin header | 3 | "step", "reset", "qef4" |
| Rocker switches (panel) x3 | Generic panel-mount SPDT/SPST rocker | panel-mount + 2-pin header | 3 | "run/halt", "dog off", "LC off" |
| LEDs x4 | 3mm LED, THT | THT, 90°, soldered to PCB | 4 | green/yellow/red/red, 220Ω series resistor each |
| DE0-Nano interface headers | 2x20 (0.1") IDC box header, 40-pin | THT | 2 | JP1 (GPIO_0, to level shifters) + JP2 (GPIO_1, to Pico-W/local) |
| DE0-Nano power feed | 2-pin header | THT | 1 | backplane +5V/GND to DE0-Nano, + low-ESR bulk cap |
| Future-expansion header | 2x11 (or 2x12) pin header | THT | 1 | 11 level-shifted CDP1802 control signals + 11 GND |
| Pull-up resistors, 10k | — | 0603 | 29 | backplane: D0-D7, LC, nEF1-3, nINT (12); future-expansion header inputs EXP_* (7); spare level-shifter channels U4/U6 (4); front panel switches/buttons (6) |
| Series resistors, 10Ω | — | 0603 | 4 | `TPA`/`TPB`/`nMRD`/`nMWR`, at the FPGA end (`fpga_header.kicad_sch`), per `backplane_notes.md`'s signal-integrity note |
| Level-shifter decoupling, 100nF | — | 0603 | 12 | 2 per SN74LVC8T245 (VCCA/3V3 + VCCB/5V) x6 chips — **PCB layout: place each cap close to its IC's respective supply pin**, not just electrically on the right net |
| Misc caps | 0.1uF (MAX3232 charge pump), 100pF (nINT filter), low-ESR bulk x2 (DE0-Nano feed, Pico-W VSYS) | 0603/0805 | — | |
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
2. ~~Build the custom DIN41617 footprint~~ **DONE (2026-10-09)** — see §1.
   ~~Fix the Pico-W footprint~~ **DONE (2026-10-09)** — now uses socket
   headers, see §4. Still need: a footprint/drawing for the DE0-Nano's 4x M3
   mounting holes (coordinates already known, §7).
3. ~~Redraw the PCB outline, place all components~~ **DONE, roughly
   (2026-10-09)** — see §7a. Real floorplan, DE0-Nano reference + mounting
   holes, all 86 footprints placed with correct nets (0 electrical shorts).
   **Still needed**: the user's real placement pass (mechanical fit,
   ribbon-cable-friendly header positions, the 12 decoupling caps actually
   close to each IC's VCCA/VCCB pins per §2, front-panel alignment) and all
   routing — this was explicitly left for the user, not attempted here.
4. `kicad-cli10 sch export bom` / JLCPCB BOM+CPL export once parts are
   placed; check every part against current JLCPCB/LCSC stock before
   ordering (MAX3232EIDR, the DIN41617 connector as a THT manual-assembly
   item, SN74LVC8T245PWR x6, Pico-W module sourced/placed separately since
   it's not a JLCPCB SMT part).
