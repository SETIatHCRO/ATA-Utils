#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
# Atel #14089
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada
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

    ant_list = ["1a", "1f", "1h", "1c", "2a", "2h", "1k", "5c", "4j", "4g"]
    freqs = [950, 950, 1600, 1600, 1600, 1600, 1600, 950, 1600, 950]

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, True)

    source = "J0008+6829"
    ata_control.make_and_track_ephems(source, ant_list)

    snap_dada.set_freq_auto(freqs, ant_list)
    ata_control.autotune(ant_list)
    os.system(ATTEMP_SCRIPT)
    obs_time = 1200
    nhours = 3

    for i in range(int(nhours*3)):
        utc = snap_dada.start_recording(ant_list, obs_time, 
                npolout=1, acclen=120, disable_rfi=True)


if __name__ == "__main__":
    main()
