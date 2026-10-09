
1. Front-panel pushbuttons/rockers/LEDs mounting — soldered directly to the PCB (board sits right behind the panel, actuators poke through cutouts), or separate panel-mount parts wired to on-board headers via a harness?
2. DIN41617 31-pin backplane pinout: docs/pinout_backplane.md  and  docs/backplane_notes.md
3. DE0-Nano 40-pin header / CDP1802 pin mapping: docs/pinout_de0nano_header.md  and  docs/cs1800.qsf
4. Exact "double slot" Eurocard dimensions — board width×depth, backplane connector position, so this actually fits next to the memory/serial boards in the rack.
5. FT2232H exact variant (FT2232H / FT2232HL / FT2232HQ) — affects package/footprint ----> changed to Pico W board, see below


(1), (4)
Eurocard dimensions: depth=160mm width=100mm

```
                                  top
           +-------------------- 160mm --------------------+
           |          +--+       P   +--------+            |
           | led1     |Pi|         H1| P      |H0      L   |
           | led2     |  |         H1|  DE0-  |H0      L   |
frontpanel | led3     |  |         H1|  nano  |H0      L   | backpanel
    100mm  |          +--+     D L H1|        |H0      L   | DIN41617 31pin
           | led4              D L H1|        |H0      L   | (angled, male)
       +-- |                       H1|        |H0      L   |
       |   | 9pin RS232   |MAX|    H1|        |H0          |
       |   |                         +--------+            |
       |   +-------------------- 160mm --------------------+
       |                         bottom
       |       
       +---------> the frontpanel also holds rockerswitches, 
                   pushbuttons, USB-C. As panelmount
```

The size of the DE0-nano board is: 49*75.2mm

Notes on ASCII drawing:
- Marks 'P' is a 2pin header to allow +5V and GND to power the DE0-nano board. The +5V comes from the backplane. (also need a low ESR bulk capacitor here).
- Marks 'H0' is the 40pin header on the Eurocard. The DE0-nano has the same 40pin header "gpio0", so there will be a ribbon cable in between.
- Marks 'H1' is the 40pin header on the Eurocard. The DE0-nano has the same 40pin header "gpio1", so there will be a ribbon cable in between.
- Marks 'L' are the SN74LVC8T245 level shifters. The DE0-nano signals are 3V3, many other signals are 5V
- Marks 'D' are "CDP1802 control pins" which are not exposed on the backpanel, for future ideas connected to level shifters and header.
- Mark 'Pi' is a Raspberry Pi Pico-W module with headers, mounted this orientation that the WiFi antenna faces up to the top
            and the USB micro of the Pico-W faces bottom. There will be a short cable from this USB-micro to the USB-C panelmount
            on the frontpanel.
- Mark 'MAX' is the MAX3232 IC which connects the RSS232 from the frontpanel and pins 6 and 7 of the Pico-W




Frontpanel layout:
------------------

The 4 leds are 3mm and through hole, 90 degrees mounted and soldered on the
board
led1: green, "LED1_fetch"      cathode pin to GND, anode to 220 ohm series resister
led2: yellow,"LED2_execute"    cathode pin to GND, anode to 220 ohm series resister
led3: red,   "LED3_interrupt"  cathode pin to GND, anode to 220 ohm series resister
led4: red,   "LED4_Q"          cathode pin to GND, anode to 220 ohm series resister

rockerswitch "run/halt" panelmount; 2 wires solder to 2pin header on the
board. pin1 is "SW_halt" pin2 is GND.  need 10k pullup resistor

rockerswitch "dog off" panelmount; 2 wires solder to 2 pin header on the
board. pin1 is "SW_dog" pin2 is GND.  need 10k pullup resistor

rockerswitch "LC off" panelmount; 2 wires solder to 2 pin header on the board.
pin1 is "SW_LC_off" pin2 is GND.  need 10k pullup resistor

pushbutton "step" panelmount; 2 wires solder to 2 pin header on the board.
pin1 is "BUT_step" pin2 is GND.  need 10k pullup resistor

pushbutton "reset" panelmount; 2 wires solder to 2 pin header on the board.
pin1 is "BUT_reset" pin2 is GND.  need 10k pullup resistor

pushbutton "qef4" panelmount; 2 wires solder to 2 pin header on the board.
pin1 is "BUT_qef4" pin2 is GND.  need 10k pullup resistor

9pin RS232 connector (pin) 90 degrees mounted and soldered on the board. pin2 is RXD, pin3
is TXD, pin5 is GND

USB-C panelmount with short cable to UsB-micro on Pico-W board


(5)
This FT2232H idea will be replaced by a Raspberry Pi Pico-W module:
- This Pico-W will contain software which allows terminal forwarding to 2 UARTS: 
  * 1 faster UART to the DE-0 nano (3V3) (pin 1 and 2, see also below)
  * 1 slower 4800baud UART to the MAX3232 on the board. (pin 6 and 7, see also below)
- With the Wifi, it will also allow 'telnet' to a terminal
- Other GPIOs for future ideas. (see below)
- Keep in mind that a copper keepout is required for better antenna performance.
  Also the antenna should be close to the top of the rack, which is open.
- The pico-W needs a low ESR bulk capacitor on the powersupply line
- UART0 connect to DE0-nano:
  * pin 1 = "UART0_RXD"
  * pin 2 = "UART0_TXD" 
- UART1 (pin 6=TX and 7=RX) connect to the MAX3232 on the board
- pins 3, 8, 13, 18, 23, 28, 33, 38 = GND
- pin 39 is VSYS, connect to +5V onboard
  (protection against backpowering the rack via the USB)
- Pico GPIOs for future ideas, connect to DE0-nano:
  * pin 19 = "PICO[0]"
  * pin 20 = "PICO[1]"
  * pin 21 = "PICO[2]"
  * pin 22 = "PICO[3]"
  * pin 24 = "PICO[4]"
  * pin 25 = "PICO[5]"
  * pin 26 = "PICO[6]"
  * pin 27 = "PICO[7]"



Other notes:

"CDP1802 control pins"
* "CS[0]" , "CS[1]" , "EX_OUT[0]", "EX_OUT[1]" go via level shifter to headerpin (output)
* "nEF[3]" , "nCLEAR", "nWAIT", "nDMA_OUT", "nDMA_IN", "EX_IN[0]", "EX_IN[1]" go via level shifter to headerpin (input) (need 10k pullup resister)

So there are 4+7=11 header pins, I would like to make this a double row header. 1 row with the signals listed and 1 row all GND.


Level shifters

SN74LVC8T245 level converters to convert the 5V signals to 3V3 signals on the DE0-nano board:
- This IC is available at JCSC or JLCPCB: SN74LVC8T245PWR
- package: TSSOP-24
- priced at $0.35
- note: needs 100nF decoupling caps on both sides 3V3 and 5V, ceramic.
- 2 needed for "CDP1802 control pins"
- 4 needed for backplane


MAX3232

I found 2 available models at LCSC or JLCPCB:
MAX3232EIDR and MAX3232IPW
