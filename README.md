# Mini_2016
Implementation of the digital back-end using ROACH technology into the MINI- Radio Telescope. In this contribution we incorporate an async reset signal, in order to trigger a new accumulation using the gpio in the ROACH. 
In the ROACH-I for cabling convenience, two of the GPIO pins are also wired to SMA connectors. We are using the J11 sma connector. The GPIO input takes 0-3.3V, ranging from DC to ~10MHz.
This folder contain the python script spec12_32b_2bram.py, to perform two spectrometers with one bram per band.

Several scripts have been written, the latest version are online here in the repository. Three python scripts are necessary for test this project:

1) spectrometer_mini.py 
2) calibration.py
3) 2sb_mini.py 

The boffiles are available in the bof folder.
