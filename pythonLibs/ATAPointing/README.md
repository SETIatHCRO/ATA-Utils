# ATA pointing

This directory contains a few python scripts to help visualize the results of the pointing calibration and raster observations.

1. `pointing_azel_table.py` - This script displays the mean, median, standard deviation and MAD of the offsets in elevation and x-elevation in the form of a matplotlib table, for each antenna. The table is displayed as a pop-up, external to the screen. It is also saved as a pandas dataframe.

2. `pointing_azel_print.py` - This script simply prints the above values for each antena

3. `pointing_elxel_plot.py` - This script plots the elevation and x-el offsets against elevation and x-el for all antennas. 

4. `pointing_elxel_plot_all.py` - The above script with command line arguments to adjsut the plot settings. 

5. `multiants_beam.py` - This script displays the beam pattern of the raster scan observation with multiple antennas. The range and step size can be changed accordingly 

6. `2k_beam.py` - Simply displays the raster scan of 2k (can change the antenna)

7. `raster_swivel.py` - Displays the ephemeris tracking raster swivel 
