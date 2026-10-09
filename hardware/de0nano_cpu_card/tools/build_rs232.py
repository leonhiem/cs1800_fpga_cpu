import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "rs232.kicad_sch")

max3232 = load("MAX3232.kicad_sym", "Interface_UART")
max232_base = load("MAX232.kicad_sym", "Interface_UART")
de9 = load("DE9_Pins.kicad_sym", "Connector")
c = load("C.kicad_sym", "Device")
gnd = load("GND.kicad_sym", "power")
v33 = load("+3V3.kicad_sym", "power")

sheet = Sheet("RS232 Transceiver (MAX3232) + DB9", paper="A3")
FP_MAX = "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_DB9 = "Connector_Dsub:DSUB-9_Pins_Horizontal_P2.77x2.54mm_EdgePinOffset9.40mm"

U1 = Component(max3232, "U1", "MAX3232EIDR", FP_MAX, 100, 60, 0, base_sym=max232_base)
U1.pin(1, net="MAX_C1P")
U1.pin(3, net="MAX_C1N")
U1.pin(4, net="MAX_C2P")
U1.pin(5, net="MAX_C2N")
U1.pin(2, net="MAX_VS+")   # VS+, needs its own 0.1uF to GND
U1.pin(6, net="MAX_VS-")   # VS-, needs its own 0.1uF to GND
U1.pin(16, power=v33)
U1.pin(15, power=gnd)
U1.pin(11, net="PICO_UART1_TX")   # T1IN <- Pico UART1 TX
U1.pin(12, net="PICO_UART1_RX")   # R1OUT -> Pico UART1 RX
U1.pin(14, net="RS232_TXD")       # T1OUT -> DB9 pin3
U1.pin(13, net="RS232_RXD")       # R1IN <- DB9 pin2
for p in (7, 8, 9, 10):           # channel 2 unused
    U1.pin(p, nc=True)
sheet.add(U1)

def cap(ref, x, y, net1, net2=None, power2=None):
    cc = Component(c, ref, "0.1uF", FP_C, x, y, 0)
    cc.pin(1, net=net1)
    if power2:
        cc.pin(2, power=power2)
    else:
        cc.pin(2, net=net2)
    sheet.add(cc)

cap("C1", 60, 30, "MAX_C1P", "MAX_C1N")
cap("C2", 140, 30, "MAX_C2P", "MAX_C2N")
cap("C3", 60, 90, "MAX_VS+", power2=gnd)
cap("C4", 140, 90, "MAX_VS-", power2=gnd)

J1 = Component(de9, "J1", "DB9_RS232", FP_DB9, 220, 60, 0)
J1.pin(2, net="RS232_RXD")
J1.pin(3, net="RS232_TXD")
J1.pin(5, power=gnd)
for p in (1, 4, 6, 7, 8, 9):
    J1.pin(p, nc=True)
sheet.add(J1)

with open(OUT, "w") as f:
    f.write(sheet.render())
print("wrote", OUT)
