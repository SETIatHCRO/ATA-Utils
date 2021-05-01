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

    ant_list = ["3c"] 

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    source = "J1935+1616"
    ata_control.make_and_track_ephems(source, ant_list)
    ata_control.autotune(ant_list)
    snap_if.tune_if_ants(ant_list)

    obs_time = 600

    utc = snap_dada.start_recording(ant_list, obs_time, 
            npolout=1, acclen=120, disable_rfi=True)


if __name__ == "__main__":
    main()
