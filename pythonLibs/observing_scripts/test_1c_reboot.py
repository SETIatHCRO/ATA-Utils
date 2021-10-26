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

def main():
    ant_list = ["1a", "1c", "2a", "2h", "3d", "1k", "5c", "2b", "1h", "4g", "4j"]

    logger = logger_defaults.getProgramLogger("observe",
                        loglevel=logging.INFO)

    #ata_control.reserve_antennas(ant_list)
    #atexit.register(ata_control.release_antennas, ant_list, True)

    obs_time = 30

    utc = snap_dada.start_recording(ant_list, obs_time, 
            npolout=1, acclen=120, disable_rfi=True)


if __name__ == "__main__":
    main()
