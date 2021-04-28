#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults

from SNAPobs import snap_dada, snap_if
import atexit
import numpy as np
import sys
import time

import argparse
import logging

import os

ATTEMP_SCRIPT = "/home/obsuser/src/psrdada/ata/scripts/attemp_new.py"

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # pulsar observation

    ant_list = ["1a","1f","5c"]
    freqs = [950]*3

    ant_list += ["2h", "1k", "1h"]
    freqs += [1300]*3

    ant_list += ["1c", "2a", "4j"]
    freqs += [1650]*3

    #ant_list = ["1f", "2a", "1k", "5c"]
    #freqs = [950, 1600, 1600, 950]
    #ant_list = ["1a", "1f", "1c", "2a", "2b", "2h", "3c", 
    #        "1k", "5c", "4g", "4j", "1h"]
    #freqs = [1400]*len(ant_list)

    ant_list = ["1f", "5c", "1a",   "1c", "2a", "4j",    "2h", "1k", "1h"]
    freqs = [950]*3 + [1600]*3 + [2250]*3


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    source = "J1935+1616"
    ata_control.make_and_track_ephems(source, ant_list)
    ata_control.autotune(ant_list)
    snap_dada.set_freq_auto(freqs, ant_list)
    time.sleep(30)

    snap_if.tune_if_ants(ant_list)
    obs_time = 600

    utc = snap_dada.start_recording(ant_list, obs_time, 
            npolout=1, acclen=120, disable_rfi=True)


if __name__ == "__main__":
    main()
