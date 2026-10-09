import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "level_shifters.kicad_sch")

lvc = load("SN74LVC8T245.kicad_sym", "Logic_LevelTranslator")
r = load("R.kicad_sym", "Device")
gnd = load("GND.kicad_sym", "power")
v33 = load("+3V3.kicad_sym", "power")
v5 = load("+5V.kicad_sym", "power")

sheet = Sheet("Level Shifters (6x SN74LVC8T245)", paper="A2")

FP_TSSOP24 = "Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm"
FP_R = "Resistor_SMD:R_0603_1608Metric"

def add_8t245(ref, x, y, a_nets, b_nets, dir_power=None, dir_net=None,
              oe_power=None, oe_net=None):
    """a_nets/b_nets: dict {1..8: net_or_None}. dir_power/oe_power: SymbolDef or None.
    dir_net/oe_net: net name string, used if *_power is None."""
    c = Component(lvc, ref, "SN74LVC8T245", FP_TSSOP24, x, y, 0)
    c.pin(1, power=v33)                      # VCCA
    if dir_power:
        c.pin(2, power=dir_power)
    else:
        c.pin(2, net=dir_net)
    for k in range(1, 9):
        pin_a = 2 + k
        net = a_nets.get(k)
        if net:
            c.pin(pin_a, net=net)
        else:
            c.pin(pin_a, nc=True)
    c.pin(11, power=gnd)
    c.pin(12, power=gnd)
    c.pin(13, power=gnd)
    for k in range(1, 9):
        pin_b = 22 - k
        net = b_nets.get(k)
        if net:
            c.pin(pin_b, net=net)
        else:
            c.pin(pin_b, nc=True)
    if oe_power:
        c.pin(22, power=oe_power)
    else:
        c.pin(22, net=oe_net)
    c.pin(23, power=v5)
    c.pin(24, power=v5)
    sheet.add(c)
    return c

# OUT-1: ADDR[7:0], DIR tied high (always drive out), OE = BUF_nOE
add_8t245("U1", 40, 60,
    a_nets={1:"ADDR[7]",2:"ADDR[6]",3:"ADDR[5]",4:"ADDR[4]",5:"ADDR[3]",6:"ADDR[2]",7:"ADDR[1]",8:"ADDR[0]"},
    b_nets={1:"BP_ADDR[7]",2:"BP_ADDR[6]",3:"BP_ADDR[5]",4:"BP_ADDR[4]",5:"BP_ADDR[3]",6:"BP_ADDR[2]",7:"BP_ADDR[1]",8:"BP_ADDR[0]"},
    dir_power=v33, oe_net="BUF_nOE")

# OUT-2: nMWR,TPA,nMRD,TPB,N[2:0],Q, DIR tied high, OE = BUF_nOE (shared with OUT-1)
add_8t245("U2", 130, 60,
    a_nets={1:"nMWR",2:"TPA",3:"nMRD",4:"TPB",5:"N[2]",6:"N[1]",7:"N[0]",8:"Q"},
    b_nets={1:"BP_nMWR",2:"BP_TPA",3:"BP_nMRD",4:"BP_TPB",5:"BP_N[2]",6:"BP_N[1]",7:"BP_N[0]",8:"BP_Q"},
    dir_power=v33, oe_net="BUF_nOE")

# DATA: DATA[7:0], DIR = DATA_DIR (FPGA-driven), OE = DATA_nOE (FPGA-driven)
add_8t245("U3", 220, 60,
    a_nets={1:"DATA[7]",2:"DATA[6]",3:"DATA[5]",4:"DATA[4]",5:"DATA[3]",6:"DATA[2]",7:"DATA[1]",8:"DATA[0]"},
    b_nets={1:"BP_DATA[7]",2:"BP_DATA[6]",3:"BP_DATA[5]",4:"BP_DATA[4]",5:"BP_DATA[3]",6:"BP_DATA[2]",7:"BP_DATA[1]",8:"BP_DATA[0]"},
    dir_net="DATA_DIR", oe_net="DATA_nOE")

# IN: LC, nINT, nEF[0:2] (5 used, 3 spare), DIR tied low (backplane drives, card listens),
# OE tied low (always enabled -- pure inputs, no contention risk)
add_8t245("U4", 40, 170,
    a_nets={1:"LC",2:"nINT",3:"nEF[0]",4:"nEF[1]",5:"nEF[2]"},
    b_nets={1:"BP_LC",2:"BP_nINT",3:"BP_nEF[0]",4:"BP_nEF[1]",5:"BP_nEF[2]"},
    dir_power=gnd, oe_power=gnd)

# CTRL-OUT: future-expansion header outputs, CS[0:1], EX_OUT[0:1] (4 used, 4 spare),
# DIR tied high, OE tied low (header not populated yet, no contention risk)
add_8t245("U5", 130, 170,
    a_nets={1:"CS[0]",2:"CS[1]",3:"EX_OUT[0]",4:"EX_OUT[1]"},
    b_nets={1:"EXP_CS[0]",2:"EXP_CS[1]",3:"EXP_EX_OUT[0]",4:"EXP_EX_OUT[1]"},
    dir_power=v33, oe_power=gnd)

# CTRL-IN: future-expansion header inputs, EX_IN[0:1],nEF[3],nCLEAR,nWAIT,nDMA_OUT,nDMA_IN
# (7 used, 1 spare), DIR tied low, OE tied low
add_8t245("U6", 220, 170,
    a_nets={1:"EX_IN[0]",2:"EX_IN[1]",3:"nEF[3]",4:"nCLEAR",5:"nWAIT",6:"nDMA_OUT",7:"nDMA_IN"},
    b_nets={1:"EXP_EX_IN[0]",2:"EXP_EX_IN[1]",3:"EXP_nEF[3]",4:"EXP_nCLEAR",5:"EXP_nWAIT",6:"EXP_nDMA_OUT",7:"EXP_nDMA_IN"},
    dir_power=gnd, oe_power=gnd)

# Default-state resistors (10k) for the FPGA-controlled DIR/OE lines, per backplane_notes.md:
# DATA_DIR pull-down (B->A default), DATA_nOE pull-up (disabled default), BUF_nOE pull-up (disabled default)
def pulldown(ref, x, y, net):
    c = Component(r, ref, "10k", FP_R, x, y, 0)
    c.pin(1, net=net)
    c.pin(2, power=gnd)
    sheet.add(c)

def pullup(ref, x, y, net):
    c = Component(r, ref, "10k", FP_R, x, y, 0)
    c.pin(1, power=v33)
    c.pin(2, net=net)
    sheet.add(c)

pulldown("R1", 280, 60, "DATA_DIR")
pullup("R2", 290, 60, "DATA_nOE")
pullup("R3", 300, 60, "BUF_nOE")

# Future-expansion header: 11 level-shifted CDP1802 control signals (2x11,
# row 1 = signals, row 2 = GND), per Eurocard.md / backplane_notes.md
conn211 = load("Conn_02x11_Odd_Even.kicad_sym", "Connector_Generic")
FP_HDR22 = "Connector_PinHeader_2.54mm:PinHeader_2x11_P2.54mm_Vertical"
J2 = Component(conn211, "J2", "EXP_HEADER_2x11", FP_HDR22, 280, 170, 0)
EXP_SIGNALS = [
    "EXP_CS[0]", "EXP_CS[1]", "EXP_EX_OUT[0]", "EXP_EX_OUT[1]",
    "EXP_EX_IN[0]", "EXP_EX_IN[1]", "EXP_nEF[3]", "EXP_nCLEAR",
    "EXP_nWAIT", "EXP_nDMA_OUT", "EXP_nDMA_IN",
]
# Odd_Even connector: row 1 = odd pin numbers (1,3,5,...), row 2 = even (2,4,6,...)
for i, net in enumerate(EXP_SIGNALS):
    J2.pin(2 * i + 1, net=net)
    J2.pin(2 * i + 2, power=gnd)
sheet.add(J2)

with open(OUT, "w") as f:
    f.write(sheet.render())
print("wrote", OUT)
