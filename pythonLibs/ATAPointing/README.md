# ATA pointing

This directory contains a few python scripts to help visualize the results of the pointing calibration observations.

1. `pointing_azel_table.py` - This script displays the mean, median, standard deviation and MAD of the offsets in elevation and x-elevation in the form of a matplotlib table, for each antenna. The table is displayed as a pop-up, external to the screen. It is also saved as a pandas dataframe.

2. `pointing_azel_print.py` - This script simply prints the above values for each antena

3. `pointing_elxel_plot.py` - This script plots the elevation and x-el offsets against elevation and x-el for all antennas. 