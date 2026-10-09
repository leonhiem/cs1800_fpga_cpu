import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "pico_w_bridge.kicad_sch")

pico = load("RaspberryPi_Pico_W.kicad_sym", "MCU_Module")
pico_base = load("RaspberryPi_Pico.kicad_sym", "MCU_Module")
r = load("R.kicad_sym", "Device")
c = load("C.kicad_sym", "Device")
d = load("D_Schottky.kicad_sym", "Device")
gnd = load("GND.kicad_sym", "power")
v33 = load("+3V3.kicad_sym", "power")
v5 = load("+5V.kicad_sym", "power")
pwrflag = load("PWR_FLAG.kicad_sym", "power")

sheet = Sheet("UART Bridge (Raspberry Pi Pico-W)", paper="A3")
FP_PICO = "cs1800:RaspberryPi_Pico_W_SocketHeaders_2x1x20_P2.54mm"  # mounted on
# sockets (removable), not soldered direct -- see tools/gen_pico_socket_fp.py.
# Needed so the Pico-W's own micro-USB port has clearance for a cable once
# the module is elevated above this board.
FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_C_BULK = "Capacitor_SMD:C_1210_3225Metric"
FP_D = "Diode_SMD:D_SMA"

A1 = Component(pico, "A1", "RaspberryPi_Pico_W", FP_PICO, 100, 60, 0, base_sym=pico_base)
A1.pin(1, net="UART0_RXD")    # GPIO0, native UART0_TX -> drives the net the FPGA calls its RXD
A1.pin(2, net="UART0_TXD")    # GPIO1, native UART0_RX <- driven by the net the FPGA calls its TXD
for p in (3, 8, 13, 18, 23, 28, 33, 38):
    A1.pin(p, power=gnd)
A1.pin(6, net="PICO_UART1_TX")   # GPIO4, UART1 TX -> MAX3232 T1IN
A1.pin(7, net="PICO_UART1_RX")   # GPIO5, UART1 RX <- MAX3232 R1OUT
PICO_GPIO = {19: 0, 20: 1, 21: 2, 22: 3, 24: 4, 25: 5, 26: 6, 27: 7}
for pin, idx in PICO_GPIO.items():
    A1.pin(pin, net=f"PICO[{idx}]")
A1.pin(30, net="PICO_RUN")        # RUN, pulled up externally
A1.pin(39, net="PICO_VSYS")       # VSYS, fed via Schottky diode from board +5V
A1.pin(33, nc=True)               # AGND -- left floating, ADC unused in this design
for p in (4, 5, 9, 10, 11, 12, 14, 15, 16, 17, 29, 31, 32, 34, 35, 36, 37, 40):
    A1.pin(p, nc=True)
sheet.add(A1)

# RUN pull-up (normal run state)
rrun = Component(r, "R1", "10k", FP_R, 140, 20, 0)
rrun.pin(1, power=v33)
rrun.pin(2, net="PICO_RUN")
sheet.add(rrun)

# Low-ESR bulk cap on VSYS feed (board side, before the diode)
cbulk = Component(c, "C1", "10uF_LowESR", FP_C_BULK, 60, 20, 0)
cbulk.pin(1, power=v5)
cbulk.pin(2, power=gnd)
sheet.add(cbulk)

# Back-feed protection: Schottky diode, anode on board +5V, cathode on Pico VSYS
d1 = Component(d, "D1", "1N5817", FP_D, 60, 100, 0)
d1.pin(2, power=v5)          # A (anode)
d1.pin(1, net="PICO_VSYS")   # K (cathode)
sheet.add(d1)

# PICO_VSYS has no power_out-type source in this model (the diode is passive),
# even though it's genuinely driven (through the diode) from +5V -- flag it so.
pf = Component(pwrflag, "PF1", "PWR_FLAG", "", 80, 100, 0)
pf.pin(1, net="PICO_VSYS")
sheet.add(pf)

with open(OUT, "w") as f:
    f.write(sheet.render())
print("wrote", OUT)
