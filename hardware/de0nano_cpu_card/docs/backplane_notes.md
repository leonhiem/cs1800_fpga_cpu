# DE0-Nano CPU-card module for the CS1800 backplane

A custom PCB carrying a **Terasic DE0-Nano** (Altera Cyclone IV
`EP4CE22F17C6N`) and **4x SN74LVC8T245** level translators, which plugs
into the CS1800 rack in place of its original CDP1802 CPU card. The FPGA
runs this repository's CDP1802 core; the rack supplies the real memory
cards, the real CDP1854 SIO board and the real 50 Hz line clock.


---

## 1. The connector

`pinout_backplane.md` has the full map: a **31-pin DIN41617**, plain 1-31,
- not an A-C or A-B-C connector.
- The datasheet of this connector is here: ./conec_connectors_din_41617-3009425.pdf
- Kicad might not have a footprint, may have to draw it ourself. Some specs I found:
  Pin Pitch: Exactly 2.50 mm. Total Pin-to-Pin Span (Pins 1 to 31): 30 spaces × 2.50 mm = 75.00 mm. 
  Mounting Hole Spacing: 85.00 mm center-to-center. The mounting holes sit exactly 5.00 mm out from Pin 1 and Pin 31 along the same axis line. 
  Overall Body Length: 89.6 mm (for straight male plugs) or 90.6 mm (for right-angle male plugs). 
  Recommended Pad Hole Diameter: 1.0 mm to 1.1 mm (solder pins are roughly 0.8 mm thick).


| direction (card's view) | count | signals |
|---|---|---|
| out | 16 | `nMWR` `TPA` `nMRD` `TPB` `ADDR[7:0]` `N[2:0]` `Q` |
| inout | 8 | `DATA[7:0]` |
| in | 5 | `LC` (50 Hz) `nINT` `nEF[2:0]` |
| power | 2 | pin 1 `+5V`, pin 31 `GND` |

**29 signals cross the level shifters.** Pins 1 and 31 do not.

The address bus is the CDP1802's multiplexed 8-bit bus: `A7/A15` down to
`A0/A8`, with the high byte latched on the rack's own memory cards at
TPA's trailing edge. Note what the backplane does **not** carry: no SC0/SC1
state codes, no DMA request lines, no CLEAR/WAIT, and **no CLOCK** — so
the module generates its own 4 MHz.

---

## 2. Level shifter allocation

29 signals into 4x 8-bit transceivers fits exactly, with 3 channels spare.
`VCCA` = 3.3 V (from the DE0-Nano), `VCCB` = 5 V (backplane pin 1).

| device | channels used | `DIR` | signals |
|---|---|---|---|
| OUT-1 | 8 | **tied high** (VCCA) | `ADDR[7:0]` |
| OUT-2 | 8 | **tied high** (VCCA) | `nMWR` `TPA` `nMRD` `TPB` `N[2:0]` `Q` |
| DATA | 8 | **FPGA-driven** (`DATA_DIR`) | `DATA[7:0]` |
| IN | 5 (3 spare) | **tied low** (GND) | `LC` `nINT` `nEF[2:0]` |

On the '8T245, `DIR` high = A→B. With A as the FPGA side, **high means the
module drives the backplane**. `OE` is active low.

### Do NOT tie `OE`

`DIR` can be strapped on the PCB for the unidirectional groups. `OE`
should not be — all four need to reach the FPGA, or at least the DATA one
and a shared line for the two OUT devices. Three reasons, in order of how
much they matter:

1. **Power-up contention on the data bus.** During configuration and until
   the core leaves reset, the Cyclone IV's I/O are high-Z with weak
   pull-ups. If the DATA transceiver is enabled and `DIR` is high, this
   card drives the rack's data bus against the real memory — on every
   power-up, not just at turnaround.
2. **Turnaround dead time.** The core stops reading and starts driving
   125 ns later (measured). `DIR` alone cannot cover that: it swaps
   direction without ever turning the driver off. `OE` can, and at 6.8 ns
   (`OE`→B) it can be placed precisely. Not strictly needed with the
   current 2764-20 (see §5), but it makes turnaround a design parameter
   instead of something that happens to fit.
3. **The outgoing signals at power-up.** With OUT-1/OUT-2 permanently
   enabled, the rack sees `TPA`, `TPB` and `Q` driven to whatever the weak
   pull-ups give — '1'. No strobe is active so it is probably harmless,
   but it means this card holds the memory cards' address latches
   transparent before the CPU exists. Cheap to avoid.

### Default-state resistors

The states that must be right **before the FPGA is configured**:

| net | resistor | resulting default | why |
|---|---|---|---|
| `DATA_DIR` | **pull-down** | B→A: backplane drives, card listens | never drive the rack's bus by accident |
| `DATA_nOE` | **pull-up** | DATA transceiver disabled | no contention at power-up |
| `BUF_nOE` | **pull-up** | OUT-1/OUT-2 disabled | card is silent until the CPU runs |

### Pull-ups the backplane itself needs

From `pinout_backplane.md`, on the **5 V (B) side**, not the FPGA side:

- 10k to +5V: `D0`-`D7`, `LC`, `nEF1`, `nEF2`, `nEF3`
- 10k to +5V **and 100 pF to GND**: `nINT`

With the DATA transceiver disabled these hold the bus at all-ones, which
is the benign state.

---

## 3. The FPGA side

**The Cyclone IV has true bidirectional I/O**, so the data bus costs 8
pins, not 16. Every general-purpose pin has a tri-state output buffer;
Quartus infers it from an `inout` port and a `'Z'` assignment. (Only
*internal* tri-states are impossible in FPGA fabric — at the pin boundary
they are normal.)

The core in `src/vhdl/cdp1802.vhd` exposes `DATA_IN` / `DATA_OUT` /
`DATA_OE` separately for exactly that reason, so the top level reassembles
them:

```vhdl
entity cs1800_de0nano_top is
  port (
    CLOCK_50 : in    std_logic;                     -- DE0-Nano oscillator
    -- to the backplane, through the level shifters
    DATA     : inout std_logic_vector(7 downto 0);
    ADDR     : out   std_logic_vector(7 downto 0);
    TPA, TPB : out   std_logic;
    nMRD, nMWR : out std_logic;
    N        : out   std_logic_vector(2 downto 0);
    Q        : out   std_logic;
    LC, nINT : in    std_logic;
    nEF      : in    std_logic_vector(2 downto 0);
    -- level shifter control
    DATA_DIR : out   std_logic;                     -- '8T245 DIR, high = we drive
    DATA_nOE : out   std_logic;                     -- '8T245 OE, active low
    BUF_nOE  : out   std_logic
  );
end entity;
...
  -- the tri-state lives at the pin boundary
  DATA      <= data_out_i when data_drive = '1' else (others => 'Z');
  data_in_i <= DATA;

  DATA_DIR  <= data_drive;        -- high only while we actually drive
  DATA_nOE  <= '0' when core_running = '1' and not turnaround else '1';
  BUF_nOE   <= '0' when core_running = '1' else '1';
```

`data_drive` is the core's `DATA_OE`; `turnaround` is the dead-time window
around a change of `data_drive`. The same tri-state pattern, written out,
is in the original [cdp1802](https://github.com/leonhiem/cdp1802) repo's
`src/vhdl/cdp1802.vhd`, which keeps the datasheet's bidirectional bus.

### Pin assignments

All in `cs1800.qsf`, on **GPIO_0 (JP1)**, all `3.3-V LVTTL`: the 29
backplane signals plus `DATA_DIR` , `DATA_nOE`  and
`BUF_nOE` . Cross-check the locations against the DE0-Nano user
manual's GPIO_0 table before fabrication.

---

## 4. Signal integrity

The DE0-Nano reaches the level shifters over a **40-pin ribbon** from JP1.
LVTTL edges are 1-2 ns regardless of the 4 MHz clock rate, so:

- series termination, ~33-47 Ω at the FPGA end, on the fast outputs:
  `TPA`, `TPB`, `nMRD`, `nMWR`;
- interleave grounds on the ribbon wherever the header allows;
- keep the DATA group's ribbon length matched to `TPB`'s, since the
  CDP1854's hold margin is consumed by skew between them (§5).

---

