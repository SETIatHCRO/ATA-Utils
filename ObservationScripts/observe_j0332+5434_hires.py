#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
import atexit
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
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
    ant_list = ["1f", "1h", "1c"]#, "1k", "5c"]
    freqs =    [950, 1300, 1650]#, 1600, 950]


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    source = "J0332+5434"
    ata_control.make_and_track_ephems(source, ant_list)

    #ata_control.set_freq(freqs, ant_list)
    snap_dada.set_freq_auto(freqs, ant_list)

    ata_control.autotune(ant_list)
    snap_if.tune_if_ants(ant_list)
    obs_time = 300

    utc = snap_dada.start_recording(ant_list, obs_time,
            npolout=1, acclen=24, disable_rfi=True)



if __name__ == "__main__":
    main()
