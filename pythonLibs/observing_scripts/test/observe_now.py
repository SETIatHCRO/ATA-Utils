#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
import atexit
from SNAPobs import snap_dada, snap_if
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

    
    #ant_list = ["1c"]
    #ant_list = ["1a", "1f", "1c", "2a", "2b", "2h", "3c", "4g", "1k", "5c", "1h", "4j"]
    #ant_list = ["1f", "5c", "1a",    "1c", "2a", "4j",    "2h", "1k", "1h"]
    #ant_list = ["1a", "1f"]
    ant_list = ["2b", "1f"]
    #ant_list = ["3c"]
    #snap_if.tune_if_ants(ant_list)
    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)
    #az,el = 60,60

    #ata_control.set_az_el(ant_list, az, el)
    obs_time = 30

    utc = snap_dada.start_recording(ant_list, obs_time, acclen=120*16,
            npolout=2, disable_rfi=True)
    #snap_dada.mark_obs_for_heimdall(utc)
    #_ = input("Press any key to record again")
    #utc = snap_dada.start_recording(ant_list, obs_time, acclen=120*16,
    #        npolout=2, disable_rfi=True)

if __name__ == "__main__":
    main()
