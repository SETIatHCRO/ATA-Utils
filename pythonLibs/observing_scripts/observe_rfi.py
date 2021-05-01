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

    ant_list = ["1a", "1f", "1c", "2a",
            "2h", "3c", "4g", "1k", "5c"]
    az_incr = [0, 30, 60, 90, 120, 150, 180, 210,
            240, 270, 300, 330, 360]
    az_incr = [210, 240, 270, 300, 330, 360]
    el = 18
    #ata_control.autotune(ant_list)
    #ata_control.set_freq(1400, ant_list)
    #os.system(ATTEMP_SCRIPT)

    obs_time = 600

    for az in az_incr:
        ata_control.set_az_el(ant_list, az, el)

        utc = snap_dada.start_recording(ant_list, obs_time, 
                npolout=2, acclen=160*8, disable_rfi=True)
        


if __name__ == "__main__":
    main()
