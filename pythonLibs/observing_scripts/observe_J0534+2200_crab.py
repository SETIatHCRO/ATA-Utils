#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
import SNAPobs
import atexit
import numpy as np
import sys
import time
from pathlib import Path


import argparse
import logging

import os

#ATTEMP_SCRIPT = "/home/obsuser/src/psrdada/ata/scripts/attemp_new.py"

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # pulsar observation
    #ant_list = ["1a",  "1c", "2a", 
    #        "2h",  "4g", "1k", "5c"]

    # 4g and 1h for GNURADIO
    #ant_list = ["1a", "1f", "1c", "1h", "2a",  "1k", "5c", "4g"]
    #freqs = [950, 950, 1600, 1600, 1600, 1600, 950, 950]

    # LO b
    #sub1  = ["1f", "5c"]
    #freq1 = [950]

    # LO c
    #sub2  = ["2h", "1k", "1h"]
    #freq2 = [1300]

    # LO a
    #sub3  = ["1c", "2a", "4j"]
    #freq3 = [1650]

    #ant_list = sub1 + sub2 + sub3
    #freqs = freq1*len(sub1) + freq2*len(sub2) + freq3*len(sub3)

    #ant_list = ["1f", "5c", "1a",    "1c", "2a", "4j",    "2h", "1k", "1h"]
    #freqs = [950]*3 + [1600]*3 + [2250]*3

    #ant_list = ["1a", "1k", "5c", "1h", "4j", "3d", "4g", "2h", "2a", "1c", "2b"]
    ant_list = ["1a", "1f", "1c", "2a", "2h", "3d", "1k", "5c", "2b", "4g", "4j"]
    freqs = [1500]*len(ant_list)
  

    #ant_list = ["1f", "2a", "1k", "5c"]
    #freqs = [950, 1600, 1600, 950]

    snap_dada.set_freq_auto(freqs, ant_list)

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, True)


    #source = "J1935+1616"
    #ata_control.make_and_track_ephems(source, ant_list)

    #ata_control.autotune(ant_list)
    #snap_if.tune_if_ants(ant_list)
    #utc = snap_dada.start_recording(ant_list, 600,
    #                    npolout=1, acclen=120, disable_rfi=True)


    source = "J0534+2200"
    ata_control.make_and_track_ephems(source, ant_list)
    ata_control.autotune(ant_list, power_level=-15)

    obs_time = 1200

    
    snap_if.tune_if_ants(ant_list)
    utc = snap_dada.start_recording(ant_list, obs_time, npolout=1, acclen=120, disable_rfi=True)
    snap_dada.mark_obs_for_heimdall(utc)
    Path('/mnt/buf0/obs/%s/obs.sumall' %utc).touch()
                                        



if __name__ == "__main__":
    main()
