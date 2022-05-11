#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada
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
    #ant_list = ["1a", "1f", "1c", "2a", "2b"]
    ant_list = ["1a", "1f", "1c", "2a", "2b",
            "2h", "3c", "4g", "1k", "5c"]
    #ata_control.reserve_antennas(ant_list)
    #atexit.register(ata_control.release_antennas, ant_list, True)

    sources = ["J2022+5154", "J2022+2854", "J2018+2839", "J1935+1616",
            "J1932+1059"]
    sources = ["J0953+0755"]
    #sources = ["J1935+1616"]
    sources = ["J0332+5434"]
    #sources = ["J1239+2453"]

    #ata_control.set_freq(2000, ant_list)
    obs_time = 1800

    for source in sources:
        #ata_control.make_and_track_ephems(source, ant_list)
        #ata_control.autotune(ant_list)
        os.system(ATTEMP_SCRIPT)

        utc = snap_dada.start_recording(ant_list, obs_time, 
                npolout=2, acclen=160*2, disable_rfi=True)


if __name__ == "__main__":
    main()
