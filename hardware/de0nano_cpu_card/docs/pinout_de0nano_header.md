# DE0-Nano 40-pin GPIO Header (fill in and send back)

Which header: `GPIO_0` or `GPIO_1`? (DE0-Nano has two 2x20 headers; GPIO_1 shares some
pins with the onboard ADC.)

| Header pin | DE0-Nano silkscreen name | Cyclone IV pin | 1802-core signal (your VHDL top-level port) | Notes |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| ... | | | | |
| 40 | | | | |

Also useful:
- Is this the full CDP1802 signal set (address/data/control/clock/reset/DMA/interrupt) or
  a subset — are any 1802 signals brought out elsewhere (e.g. straight to the FPGA's other
  header, or not brought off-chip at all)?
- Any pins reserved for power/GND on the header itself (some GPIO headers carry 3.3V/5V/GND
  pins alongside I/O)?
- Your VHDL top-level entity port list or `.qsf`/`.sdc` pin assignment file is the fastest
  way to hand this over accurately — happy to parse that directly instead of a hand-typed
  table.
