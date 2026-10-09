import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "power.kicad_sch")

conn02 = load("Conn_01x02.kicad_sym", "Connector_Generic")
c = load("C.kicad_sym", "Device")
gnd = load("GND.kicad_sym", "power")
v5 = load("+5V.kicad_sym", "power")
v33 = load("+3V3.kicad_sym", "power")
pwrflag = load("PWR_FLAG.kicad_sym", "power")

sheet = Sheet("Power (5V in, DE0-Nano feed, rails)", paper="A4")
FP_HDR2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_C_BULK = "Capacitor_SMD:C_1210_3225Metric"

# "P" header: backplane +5V/GND -> DE0-Nano power feed (hand-wired off-board per Eurocard.md)
P = Component(conn02, "P1", "DE0Nano_5V_feed", FP_HDR2, 40, 40, 0)
P.pin(1, power=v5)
P.pin(2, power=gnd)
sheet.add(P)

# Low-ESR bulk capacitor on the DE0-Nano feed
C1 = Component(c, "C1", "100uF_LowESR", FP_C_BULK, 70, 40, 0)
C1.pin(1, power=v5)
C1.pin(2, power=gnd)
sheet.add(C1)

# +5V is sourced off-board (the backplane); +3V3 is sourced by the DE0-Nano's
# own VCC3P3 pin (see fpga_header.kicad_sch, J1 pin 29). Neither has a
# power_out-type pin anywhere in this design (generic connector pins are all
# "passive"), so each needs a PWR_FLAG to tell ERC the net is externally
# driven. GND does NOT need one: the Pico-W module's own GND pin (pico_w_bridge
# sheet) is typed power_out by its symbol, which already satisfies ERC -- an
# extra PWR_FLAG there would conflict with it (two power_out pins on one net).
for i, (ref, net) in enumerate([("PF1", "+5V"), ("PF2", "+3V3")]):
    pf = Component(pwrflag, ref, "PWR_FLAG", "", 110 + i * 20, 40, 0)
    pf.pin(1, net=net)   # plain label (not a power-symbol stamp) avoids a
                         # kicad-cli ERC quirk where a lone PWR_FLAG+power-symbol
                         # pair with nothing else local reports as "not connected"
    sheet.add(pf)

with open(OUT, "w") as f:
    f.write(sheet.render())
print("wrote", OUT)
