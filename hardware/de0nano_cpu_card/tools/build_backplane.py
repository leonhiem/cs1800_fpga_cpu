import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "backplane_connector.kicad_sch")

conn31 = load("Conn_01x31.kicad_sym", "Connector_Generic")
r = load("R.kicad_sym", "Device")
c = load("C.kicad_sym", "Device")
gnd = load("GND.kicad_sym", "power")
v5 = load("+5V.kicad_sym", "power")

sheet = Sheet("Backplane Connector (DIN41617, 31p male)", paper="A2")
FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_CONN = "cs1800:DIN41617_31P_Male_Angled"  # see tools/gen_din41617_fp.py

J1 = Component(conn31, "J1", "DIN41617_31P", FP_CONN, 60, 140, 0)

PINS = {
    1: ("+5V", "power"),
    2: ("BP_LC", "pu"),
    3: ("BP_nINT", "pu100p"),
    4: ("BP_nMWR", None),
    5: ("BP_TPA", None),
    6: ("BP_nMRD", None),
    7: ("BP_TPB", None),
    8: ("BP_DATA[7]", "pu"),
    9: ("BP_ADDR[7]", None),
    10: ("BP_DATA[6]", "pu"),
    11: ("BP_ADDR[6]", None),
    12: ("BP_DATA[5]", "pu"),
    13: ("BP_ADDR[5]", None),
    14: ("BP_DATA[4]", "pu"),
    15: ("BP_ADDR[4]", None),
    16: ("BP_DATA[3]", "pu"),
    17: ("BP_ADDR[3]", None),
    18: ("BP_DATA[2]", "pu"),
    19: ("BP_ADDR[2]", None),
    20: ("BP_DATA[1]", "pu"),
    21: ("BP_ADDR[1]", None),
    22: ("BP_DATA[0]", "pu"),
    23: ("BP_ADDR[0]", None),
    24: ("BP_nEF[0]", "pu"),
    25: ("BP_N[2]", None),
    26: ("BP_nEF[1]", "pu"),
    27: ("BP_N[1]", None),
    28: ("BP_nEF[2]", "pu"),
    29: ("BP_N[0]", None),
    30: ("BP_Q", None),
    31: ("GND", "power"),
}

ry = 20
for pin, (net, kind) in PINS.items():
    if net == "+5V":
        J1.pin(pin, power=v5)
        continue
    if net == "GND":
        J1.pin(pin, power=gnd)
        continue
    J1.pin(pin, net=net)
    if kind == "pu":
        rr = Component(r, f"R{pin}", "10k", FP_R, 140, ry, 0)
        rr.pin(1, power=v5)
        rr.pin(2, net=net)
        sheet.add(rr)
        ry += 15
    elif kind == "pu100p":
        rr = Component(r, f"R{pin}", "10k", FP_R, 140, ry, 0)
        rr.pin(1, power=v5)
        rr.pin(2, net=net)
        sheet.add(rr)
        ry += 15
        cc = Component(c, f"C{pin}", "100pF", FP_C, 160, ry, 0)
        cc.pin(1, net=net)
        cc.pin(2, power=gnd)
        sheet.add(cc)
        ry += 15

sheet.add(J1)

with open(OUT, "w") as f:
    f.write(sheet.render())
print("wrote", OUT)
