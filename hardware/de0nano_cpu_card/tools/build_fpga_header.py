import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "fpga_header.kicad_sch")

conn = load("Conn_02x20_Odd_Even.kicad_sym", "Connector_Generic")
gnd = load("GND.kicad_sym", "power")
v33 = load("+3V3.kicad_sym", "power")

sheet = Sheet("DE0-Nano GPIO Header / Ribbon I-F", paper="A2")
FP_IDC = "Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical"

# JP1 / GPIO_0 -> backplane (through level shifters)
J1 = Component(conn, "J1", "GPIO_0_JP1", FP_IDC, 50, 50, 0)
J1_PINS = {
    2: "LC", 4: "nINT", 5: "nMWR", 6: "TPA", 7: "nMRD", 8: "TPB",
    9: "DATA_DIR", 10: "DATA_nOE", 13: "BUF_nOE",
    14: "DATA[7]", 15: "DATA[6]", 16: "DATA[5]", 17: "DATA[4]",
    18: "DATA[3]", 19: "DATA[2]", 20: "DATA[1]", 21: "DATA[0]",
    22: "ADDR[7]", 23: "ADDR[6]", 24: "ADDR[5]", 25: "ADDR[4]",
    26: "ADDR[3]", 27: "ADDR[2]", 28: "ADDR[1]", 31: "ADDR[0]",
    32: "nEF[0]", 33: "nEF[1]", 34: "nEF[2]",
    35: "N[2]", 36: "N[1]", 37: "N[0]", 38: "Q",
}
for pin, net in J1_PINS.items():
    J1.pin(pin, net=net)
J1.pin(12, power=gnd)
J1.pin(30, power=gnd)
J1.pin(29, power=v33)   # VCC3P3 -- the board's +3V3 rail is SOURCED here
for pin in (1, 3, 11, 39, 40):   # 11=VCC_SYS (DE0-Nano 5V out, unused -- power enters via the dedicated 2-pin header)
    J1.pin(pin, nc=True)
sheet.add(J1)

# JP2 / GPIO_1 -> local Eurocard wiring (Pico-W, future header, front panel)
J2 = Component(conn, "J2", "GPIO_1_JP2", FP_IDC, 220, 50, 0)
J2_PINS = {
    2: "UART0_TXD", 4: "UART0_RXD",
    8: "PICO[7]", 9: "PICO[6]", 10: "PICO[5]", 13: "PICO[4]",
    14: "PICO[3]", 15: "PICO[2]", 16: "PICO[1]", 17: "PICO[0]",
    18: "CS[0]", 19: "CS[1]", 20: "EX_OUT[0]", 21: "EX_OUT[1]",
    22: "EX_IN[0]", 23: "EX_IN[1]", 24: "nEF[3]", 25: "nCLEAR",
    26: "nWAIT", 27: "nDMA_OUT", 28: "nDMA_IN",
    31: "LED1_fetch", 32: "LED2_execute", 33: "LED3_interrupt", 34: "LED4_Q",
    35: "SW_halt", 36: "SW_dog", 37: "SW_LC_off",
    38: "BUT_step", 39: "BUT_reset", 40: "BUT_qef4",
}
for pin, net in J2_PINS.items():
    J2.pin(pin, net=net)
J2.pin(12, power=gnd)
J2.pin(30, power=gnd)
J2.pin(29, nc=True)    # VCC3P3 also present here; +3V3 already sourced via J1 pin29
J2.pin(11, nc=True)    # VCC_SYS, unused
for pin in (1, 3, 5, 6, 7):
    J2.pin(pin, nc=True)
sheet.add(J2)

with open(OUT, "w") as f:
    f.write(sheet.render())
print("wrote", OUT)
