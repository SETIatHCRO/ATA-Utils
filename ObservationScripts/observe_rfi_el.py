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
    az_ants = [0, 45, 90, 135, 180, 225, 270, 315, 360]

    el_inc = [20,30,40,50,60,70,80,85]

    #ata_control.autotune(ant_list)
    #ata_control.set_freq(1400, ant_list)
    #os.system(ATTEMP_SCRIPT)

    obs_time = 600

    for el in el_inc:
        for iant, ant in enumerate(ant_list):
            ata_control.set_az_el(ant_list[iant], az_ants[iant], el)

        utc = snap_dada.start_recording(ant_list, obs_time, 
                npolout=2, acclen=160*8, disable_rfi=True)
        


if __name__ == "__main__":
    main()
