#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if

import numpy as np
import sys
import atexit

import argparse
import logging

import time
import os

ATTEMP_SCRIPT = "/home/obsuser/src/psrdada/ata/scripts/attemp_new.py"

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # pulsar observation
    #ant_list = ["1a", "1f", "1c", "2a", "2h", "1k", "5c", "4g", "4j"]
    #freqs = [950, 950, 1600, 1600, 1600, 1600, 950, 950, 1600]

    #ant_list = ["1a", "1f", "1c", "2a", "2h", "1k", "5c", "4g", "4j", "1h"]
    #freqs = [950, 950, 1600, 1600, 1600, 1600, 950, 950, 1600, 1600]

    ant_list = ["1a", "1f", "5c",   "1c", "2a", "4j",    "2h", "1k", "1h"]
    freqs = [950]*3 + [1600]*3 + [2250]*3

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, True)

    # observe a pulsar
    #source = "J1935+1616"
    source = "J0332+5434"
    ata_control.make_and_track_ephems(source, ant_list)

    ata_control.autotune(ant_list)
    snap_dada.set_freq_auto(freqs, ant_list)
    snap_if.tune_if_ants(ant_list)
    utc = snap_dada.start_recording(ant_list, 600,
                        npolout=1, acclen=120, disable_rfi=True)

    # now to FRB source
    source = "frb20201124a"
    ata_control.make_and_track_ephems(source, ant_list)
    ata_control.autotune(ant_list)
    obs_time = 1200
    nhours = 3
    ncycles = 2

    for icycle in range(ncycles):
        for i in range(nhours*3):
            snap_if.tune_if_ants(ant_list)
            utc = snap_dada.start_recording(ant_list, obs_time, 
                    npolout=1, acclen=120, disable_rfi=True)
            snap_dada.mark_obs_for_heimdall(utc)

        time.sleep(1200)

if __name__ == "__main__":
    main()
