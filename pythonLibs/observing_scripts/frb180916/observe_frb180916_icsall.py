#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
from pathlib import Path

import numpy as np
import sys
import atexit

import argparse
import logging

import time
import os

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # pulsar observation
    #ant_list = ["1a", "1k", "5c", "1h", "4j", "3d", "4g", "2h", "2a", "2b", "1c"]
    #ant_list = ["1a", "1f", "2a", "2h", "3d", "4g", "1k", "5c", "1h", "2b"]
    ant_list = ['1a', '1f', '1c', '1h', '2a', '4j', '2h', '3d', '4g', '5c', '2b']

    freqs = [1500]*len(ant_list)

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, True)

    # observe a pulsar
    #source = "J1935+1616"
    #source = "J0332+5434"
    #ata_control.make_and_track_ephems(source, ant_list)
    #ata_control.autotune(ant_list, power_level=-15)
    #snap_dada.set_freq_auto(freqs, ant_list)
    #snap_if.tune_if_ants(ant_list)
    #utc = snap_dada.start_recording(ant_list, 600,
    #                    npolout=1, acclen=120, disable_rfi=True)


    # now to FRB source
    source = "frb180916"
    ata_control.make_and_track_ephems(source, ant_list)
    ata_control.autotune(ant_list, power_level=-15)
    snap_dada.set_freq_auto(freqs, ant_list)
    snap_if.tune_if_ants(ant_list)
    obs_time = 1200
    nhours = 1
    ncycles = 3

    for icycle in range(ncycles):
        for i in range(nhours*3):
            snap_if.tune_if_ants(ant_list)
            utc = snap_dada.start_recording(ant_list, obs_time, 
                    npolout=1, acclen=120, disable_rfi=True)
            Path('/mnt/buf0/obs/%s/obs.sumall' %utc).touch()
            snap_dada.mark_obs_for_heimdall(utc)


        time.sleep(300)

if __name__ == "__main__":
    main()
