#!/home/sonata/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada
import numpy as np
import sys

import argparse
import logging

import os

ATTEMP_SCRIPT = "/home/sonata/psrdada/ata/scripts/attemp.py"

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # pulsar observation
    ant_list = ["1c", "2a", "2b", "2h"]
    ata_control.reserve_antennas(ant_list)
    freq = 1500
    ata_control.set_freq(freq, ant_list)

    source = "J0534+2200"
    ata_control.make_and_track_ephems(source, ant_list)
    obs_time = 3600
    os.system(ATTEMP_SCRIPT)
    ata_control.release_antennas(ant_list, True)


if __name__ == "__main__":
    main()
