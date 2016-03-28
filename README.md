# Mini_2016
Implementation of the digital back-end using ROACH technology into the MINI- Radio Telescope. In this commit we incorporatie an async reset signal, in order to trigger a new accumulation using the gpio in the ROACH.

Several scripts have been written, the latest version are online here in the repository. Three folders contains all necessary files to test this project.

#1) espectrometro : 
This folder contain the python script spec12_32b_2bram.py, to perform two spectrometers with one bram per band.

How to run this script?:

./spec12_32b_2bram.py 192.168.1.11 -g 262143 -l 65536

Gain = 2^{18} - 1 = 262143

Accumulation length = 65536 very long!

#2) Calibration :

to run it:

./spectrometer_64bits_float_s12_dif_ed_sin_acc_data_upper_low2_dctrl.py 192.168.1.11  -g 0x0080000 -b cal_spectrometer_2048ch_2014_Jul_15_0203.bof

Gain = 0x0080000 (hex) = 524288 (Decimal).

#3) DSSS :

To run this script:

./spectrometer_32bits_1brampsb_s12_SRR_measurement.py 192.168.1.11 -g 262143 
-l 65536 -b minispec_1ghz_1bram_u_2015_Sep_04_1658.bof

Gain = 2^{18} - 1 = 262143

Accumulation length = 65536 very long!

