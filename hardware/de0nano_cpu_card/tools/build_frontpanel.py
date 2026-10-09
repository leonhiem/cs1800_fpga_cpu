import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import load, Component, Sheet

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sheets", "frontpanel_io.kicad_sch")

led = load("LED.kicad_sym", "Device")
r = load("R.kicad_sym", "Device")
conn02 = load("Conn_01x02.kicad_sym", "Connector_Generic")
gnd = load("GND.kicad_sym", "power")
v33 = load("+3V3.kicad_sym", "power")

sheet = Sheet("Front Panel I/O", paper="A3")
FP_LED = "LED_THT:LED_D3.0mm"
FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_HDR2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"

LEDS = [
    ("D1", "LED1_fetch", "LED_Green"),
    ("D2", "LED2_execute", "LED_Yellow"),
    ("D3", "LED3_interrupt", "LED_Red"),
    ("D4", "LED4_Q", "LED_Red"),
]
x = 30
for ref, net, color in LEDS:
    d = Component(led, ref, color, FP_LED, x, 30, 0)
    d.pin(1, power=gnd)                 # K -> GND
    d.pin(2, net=f"{net}_A")            # A -> series resistor
    sheet.add(d)
    rr = Component(r, f"R_{ref}", "220", FP_R, x, 60, 90)
    rr.pin(1, net=f"{net}_A")
    rr.pin(2, net=net)
    sheet.add(rr)
    x += 30

SWITCHES = [
    ("SW1", "SW_halt", "Rocker_run/halt"),
    ("SW2", "SW_dog", "Rocker_dog_off"),
    ("SW3", "SW_LC_off", "Rocker_LC_off"),
    ("SW4", "BUT_step", "Button_step"),
    ("SW5", "BUT_reset", "Button_reset"),
    ("SW6", "BUT_qef4", "Button_qef4"),
]
x = 30
for ref, net, label in SWITCHES:
    j = Component(conn02, ref, label, FP_HDR2, x, 120, 0)
    j.pin(1, net=net)
    j.pin(2, power=gnd)
    sheet.add(j)
    rr = Component(r, f"R_{ref}", "10k", FP_R, x, 150, 90)
    rr.pin(1, power=v33)
    rr.pin(2, net=net)
    sheet.add(rr)
    x += 30

with open(OUT, "w") as f:
    f.write(sheet.render())
print("wrote", OUT)
