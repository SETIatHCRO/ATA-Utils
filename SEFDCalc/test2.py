# Script to test antenna performance at the ATA, by Christiaan Brinkerink, 22-06-2018.
# A run has been performed last night (Thu 21 to Fri 22 June 2018) with 12 telescopes (only 8 actually connected, so there are duplicates in the data), at 3 different frequencies (1 GHz, 2 GHz, 3 GHz).
# This script is meant to be a sandbox for investigating antenna Tsys, SEFD and other metrics that may be useful.

# We work with python pickle files, each of which stores the results of one scan (180 integrations of ~1 s each) on one target with one frequency setting (on or off source).

import pickle
import numpy as np
import matplotlib.pyplot as plt

# The following ranges of parameters have simply been glanced from the data file names available on 10.1.49.174 (user: sonata, dir: ~/data/ ).
# A future version of this script might incorporate a more advanced function that determines the parameter ranges from the data encountered in the fiiles themselves.

# Antenna names:
antennas = ["1e",
            "1h",
            "1k",
            "2a",
            "2b",
            "2e",
            "2h",
            "2j",
            "2m",
            "3d",
            "3l",
            "4j"]

# Tunings (in MHz):
tunings = ["1000.00",
           "2000.00",
           "3000.00"]

# Bandwidth at 1000 MHz: 450 MHz (2048 channels)
# Bandwidth at 2000 MHz: 450 MHz (2048 channels)
# Bandwidth at 3000 MHz: 450 MHz (2048 channels)

# Sources:
sources = ["moon"] # VLA calibrator source, ~10 Jy at 3 GHz

# States:
states = ["on", "off"] # on-source and off-source. NOTE: time intervals between on- and off-source are long for this observation! May explain why we see flux density offsets of ~1.5% between the two states. This difference is too large to be explained by source flux density, as it would require an SEFD per antenna of around 650 Jy. SEFD from design is more like 6500 Jy. New observations are being recorded at the moment with a different scan structure.

# Filename format: rf1000.00_n180_3C295_off_ant_1e_1000.00.pkl

# Pickle data structure is a dictionary with the following entries:
# comment
# ncaptures
# fft_shift
# adc1_stats
# auto0
# auto1
# adc1_bitsnaps
# srate
# fpga_clk
# frange
# adc0_stats
# auto0_timestamp
# fft_of1
# fft_of0
# auto1_timestamp
# auto1_of_count
# host
# path
# auto0_of_count
# adc0_bitsnaps
# rfc
# ata_status
# ifc
# fpgfile

resimgdev = np.zeros((6, 12))
resimgmean = np.zeros((6, 12))

specon = 0.
specoff = 0.
frange = 0.

#plt.figure()

for antenna in antennas:
  for tuning in tunings:
    for source in sources:
      for state in states:
        x = antennas.index(antenna)
        y1 = tunings.index(tuning)
        y2 = states.index(state)
        y = 2 * y1 + y2
        fname = "rf" + tuning + "_" + "n180" + "_" + source + "_" + state + "_ant_" + antenna + "_" + tuning + ".pkl"
        data = 0.
        try:
          data = pickle.load(open(fname,'r'))
          resimgdev[y,x] = data['adc0_stats']['dev']
          resimgmean[y,x] = data['adc0_stats']['mean']
          if (tuning == '1000.00'):
              if (state == 'on'):
                frange = data['frange']
                specon = np.mean(data['auto0'], axis=0)
              if (state == 'off'):
                specoff = np.mean(data['auto0'], axis=0)
                # We have on and off data for this antenna. Plot a spectrum at 3 GHz with the ratio.
                plt.figure()
                plt.plot(frange, specon / specoff)
                plt.title(antenna)
                #plt.figure()
                #plt.plot(frange, specon, label=antenna)
              #plt.plot(data['frange'], np.mean(data['auto0'], axis=0))
          # The following boundary values for the ADC standard deviations are simple estimates
          if (data['adc0_stats']['dev'] <= 20. and data['adc0_stats']['dev'] >= 5.):
              print "Good stddev for adc0: ", fname, data['adc0_stats']
          else:
              print "Bad stddev for adc0: ", fname, data['adc0_stats']
        except:
          print "File not found: ", fname

#plt.legend(loc='best')

#plt.figure()
#plt.imshow(resimgdev)
#plt.axis('auto')
#plt.title("dev of adc0")
#plt.yticks(range(0,6),['1GHz-on','1GHz-off','2GHz-on','2GHz-off','3GHz-on','3GHz-off'])
#plt.xticks(range(0,12), antennas)
#plt.colorbar()
#
#plt.figure()
#plt.imshow(resimgmean)
#plt.axis('auto')
#plt.title("mean of adc0")
#plt.yticks(range(0,6),['1GHz-on','1GHz-off','2GHz-on','2GHz-off','3GHz-on','3GHz-off'])
#plt.xticks(range(0,12), antennas)
#plt.colorbar()
