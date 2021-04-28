#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if

import atexit

import numpy as np
import sys

import argparse
import logging

import os

ATTEMP_SCRIPT = "/home/obsuser/src/psrdada/ata/scripts/attemp_new.py"

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # pulsar observation
    #ant_list = ["1f", "1h"]#, "1k", "5c"]
    #freqs =    [950, 1600]#, 1600, 950]

    #ant_list = ["1a",    "4j",    "1k"]
    #freqs = [950] + [1600] + [2250]
    ant_list = ["1f", "5c", "1a",   "1c", "2a", "4j",    "2h", "1k", "1h"]
    #freqs = [950]*3 + [1600]*3 + [2250]*3
    freqs = [1400]*len(ant_list)

    #ant_list = ["1f", "1k"]
    #freqs = [950, 1600]
    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    source = "j0534+2200"
    ata_control.make_and_track_ephems(source, ant_list)
    ata_control.autotune(ant_list)
    snap_dada.set_freq_auto(freqs, ant_list)
    snap_if.tune_if_ants(ant_list)
    obs_time = 1800

    #for i in range(3):
    utc = snap_dada.start_recording(ant_list, obs_time, 
            npolout=1, acclen=40, disable_rfi=True)


if __name__ == "__main__":
    main()
