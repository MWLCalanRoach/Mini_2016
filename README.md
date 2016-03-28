# Mini_2016

Implementation of the digital back-end using ROACH technology into the MINI- Radio Telescope. In this contribution we incorporate an async reset signal, in order to trigger a new accumulation using the gpio in the ROACH. 

In the ROACH-I for cabling convenience, two of the GPIO pins are also wired to SMA connectors. We are using the J11 sma connector. The GPIO input takes 0-3.3V, ranging from DC to ~10MHz.


Several scripts have been written, the latest version are online here in the repository. Three python scripts are necessary for test this project: spectrometer_mini.py to perform two spectrometers with one bram per band. The calibration.py to compute the complex constants and the 2sb_mini.py to test the SRR measurement.

Hint for the SRR measurement: Mode 1: calibrated (complex constants), Mode 2: Ideal (1 & 0), Mode 3: spectrometer (0).

1) spectrometer_mini.py

2) calibration.py

3) 2sb_mini.py 

The boffiles are available in the bof folder.
