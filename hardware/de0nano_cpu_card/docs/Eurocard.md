Still open, whenever you're ready (no rush, not blocking further scaffolding):

1. Front-panel pushbuttons/rockers/LEDs mounting — soldered directly to the PCB (board sits right behind the panel, actuators poke through cutouts), or separate panel-mount parts wired to on-board headers via a harness?
2. DIN41617 31-pin backplane pinout — whenever convenient, per docs/pinout_backplane_TEMPLATE.md.
3. DE0-Nano 40-pin header / CDP1802 pin mapping — per docs/pinout_de0nano_header_TEMPLATE.md, or just point me at your VHDL top-level/.qsf.
4. Exact "double slot" Eurocard dimensions — board width×depth, backplane connector position, so this actually fits next to the memory/serial boards in the rack.
5. FT2232H exact variant (FT2232H / FT2232HL / FT2232HQ) — affects package/footprint.


(1), (4)
Eurocard dimensions: depth=160mm width=100mm

```
                                  top
           +-------------------- 160mm --------------------+
           |          +--+           +--------+            |
           | led1     |Pi|         P | P      |  H     L   |
           | led2     |  |           |  DE0-  |  H     L   |
frontpanel | led3     |  |           |  nano  |  H     L   | backpanel
    100mm  |          +--+         D |        |  H     L   | DIN41617 31pin
           | led4                  D |        |  H     L   | (angled, male)
       +-- |                         |        |  H     L   |
       |   | 9pin RS232   |MAX|      |        |  H         |
       |   |                         +--------+            |
       |   +-------------------- 160mm --------------------+
       |                         bottom
       |       
       +---------> the frontpanel also holds rockerswitches, 
                   pushbuttons, USB-C. As panelmount
```


Notes on ASCII drawing:
- Marks 'P' is a 2pin header to allow +5V and GND to power the DE0-nano board. The +5V comes from the backplane
- Marks 'H' is the 40pin header on the Eurocard. The DE0-nano has the same 40pin header, so there will be a ribbon cable in between.
- Marks 'L' are the SN74LVC8T245 level shifters. The DE0-nano signals are 3V3 and the backplane 5V
- Marks 'D' are header pins of the CDP1802 pins which are not exposed on the backpanel, for example the DMA pins, for future ideas.
- Mark 'Pi' is a Raspberry Pi Pico-W module with headers, mounted this orientation that the WiFi antenna faces up to the top
            and the USB micro of the Pico-W faces down. There will be a short cable from this USB-micro to the USB-C panelmount
            on the frontpanel.
- Mark 'MAX' is the MAX3232 IC which connects the RSS232 from the frontpanel to the GPIOs of the Pico-W

Frontpanel layout:
The 4 leds are 3mm and through hole, 90 degrees mounted and soldered on the
board
led1: green, "fetch"
led2: yellow,"execute"
led3: red,   "interrupt"
led4: "red"  "Q"

rockerswitch "run/halt" panelmount; 2 wires solder to 2pin header on the
board. pin1 is "halt" pin2 is GND

rockerswitch "dog off" panelmount; 2 wires solder to 2 pin header on the
board. pin1 is "dog" pin2 is GND

rockerswitch "LC off" panelmount; 2 wires solder to 2 pin header on the board.
pin1 is "LC" pin2 is GND

pushbutton "step" panelmount; 2 wires solder to 2 pin header on the board.
pin1 is "step" pin2 is GND

pushbutton "reset" panelmount; 2 wires solder to 2 pin header on the board.
pin1 is "reset" pin2 is GND

pushbutton "qef4" panelmount; 2 wires solder to 2 pin header on the board.
pin1 is "qef4" pin2 is GND

9pin RS232 connector (pin) 90 degrees mounted and soldered on the board. pin2 is RXD, pin3
is TXD, pin5 is GND

USB-C panelmount with short cable to UsB-micro on Pico-W board


(5)
This FT2232H idea will be replaced by a Raspberry Pi Pico-W module:
- This Pico-W will contain software which allows terminal forwarding to 2 UARTS: 
  * 1 faster UART to the DE-0 nano (3V3)
  * 1 slower 4800baud UART to the MAX3232 on the board.
- With the Wifi, it will also allow 'telnet' to a terminal
- Other GPIOs for future ideas.
- Keep in mind that a copper keepout is required for better antenna performance.
  Also the antenna should be close to the top of the rack, which is open.
- Also keep in mind that there is protection against backpowering the rack via the USB

Other notes:

SN74LVC8T245 level converters to convert the 5V backplane signals to 3V3 signals on the DE0-nano board:
- the DE0-nano will drive the DIR lines.
- This IC is available at JCSC or JLCPCB: SN74LVC8T245PWR
- package: TSSOP-24
- priced at $0.35
- note: needs 100nF decoupling cap, ceramic.

