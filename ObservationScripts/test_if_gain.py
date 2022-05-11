#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
import time
import atexit
import numpy as np
import sys

import argparse
import logging

import os

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    ant_list = ["1a", "1f", "1c", "2a", "2b", "2h",
            "3c", "4g", "1k", "5c", "1h", "4j"]

    #ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, False)

    ata_control.set_az_el(ant_list, 180, 75)

    ata_control.autotune(ant_list)

    freqs = np.arange(2250, 11200, 550)

    snap_dada.set_freq_auto([freqs[0]]*len(ant_list), ant_list)
    time.sleep(30)
    
    o = open("output_snap_if.txt","w")

    for ifreq, freq in enumerate(freqs):
        time.sleep(10)
        snap_dada.set_freq_auto([freq]*len(ant_list), ant_list)
        snap_if.tune_if_ants(ant_list)
        o.write(str(freq))
        o.write(str(snap_if.getatten(ant_list)))

    o.close()


if __name__ == "__main__":
    main()
