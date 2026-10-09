# DE0-Nano 40-pin GPIO Header

GDE0-Nano has two 2x20 headers; GPIO_0 and GPIO_1 

The QSF is here: cs1800.qsf

GPIO_0 is used for the backplane. Notes:
- pins 12 and 30 are GND
- pin 29 is VCC3P3 (output from DE0-nano, 3.3 Volt)
- pin 11 is VCC_SYS (output from DE0-nano 5 Volt)
- cs1800.qsf starting on line 129



GPIO_1 is used locally on the Eurocard. Notes:
- pins 12 and 30 are GND
- pin 29 is VCC3P3 (output from DE0-nano, 3.3 Volt)
- pin 11 is VCC_SYS (output from DE0-nano 5 Volt)
- cs1800.qsf starting on line 285


