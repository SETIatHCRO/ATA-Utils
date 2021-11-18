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
    #ant_list = ["1a", "1f", "5c",     "1c", "2a", "4j",     "2h", "1k", "1h"]
    #ant_list = ["3c", "2b"]
    ant_list = ["1a", "1f", "1c", "2b",
            "1k", "5c", "1h", "4j", "2a", "3d", "4g", "2h"]
    ant_list = ["1a", "1f", "1k", "5c", "1h", "4j", "3d", "4g", "2h", "2a", "1c", "2b"]
    #ant_list = ["1a", "1f", "5c", "4g"]
    
    #freqs = [950]*3 + [1600]*3 + [2250]*3
    #ant_list = ["1f"]
    #freqs = [1500]*len(ant_list)
    freqs = [750]*len(ant_list)


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, True)

    ata_control.set_freq(freqs, ant_list)
    snap_dada.set_freq_auto(freqs, ant_list)
    print("Done")
    time.sleep(30)

    source = "J0332+5434"
    ata_control.make_and_track_ephems(source, ant_list)


    ata_control.autotune(ant_list, power_level=-15)
    snap_if.tune_if_ants(ant_list)
    obs_time = 600 * 2

    utc = snap_dada.start_recording(ant_list, obs_time, 
            disable_rfi=True, npolout=1, acclen=120)


if __name__ == "__main__":
    main()
