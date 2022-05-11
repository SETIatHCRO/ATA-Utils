#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
import atexit
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
import numpy as np
import sys
import time

import argparse
import logging

import os

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # pulsar observation
    antlo_list = ["1aA", "1cA", "2aA", "4jA", "2hA", "3dA", "4gA", "1kA", "5cA", "1hA", "2bA",
            "1eB", "1gB",
            "2cB",
            "2eB", "2jB"]
    ant_list = [antlo[:-1] for antlo in antlo_list]
    los = list(set([antlo[-1] for antlo in antlo_list]))
    
    #freqs = [950]*3 + [1600]*3 + [2250]*3
    #ant_list = ["1f"]
    freqs = [1500]*len(ant_list)


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    #ata_control.set_freq(freqs, ant_list, lo='a')
    #ata_control.set_freq(freqs, ant_list, lo='b')

    #time.sleep(30)

    source = "J0332+5434"
    ata_control.make_and_track_ephems(source, ant_list)


    ata_control.autotune(ant_list, power_level=-15)
    #snap_if.tune_if_ants(ant_list)
    snap_if.tune_if_antslo(antlo_list)
    obs_time = 600

    utc = snap_dada.start_recording(antlo_list, obs_time, 
            disable_rfi=True, npolout=1, acclen=120)


if __name__ == "__main__":
    main()
