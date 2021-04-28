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
    ant_list = ["2h"]

    obs_time = 600
    os.system(ATTEMP_SCRIPT)
    utc = snap_dada.start_recording(ant_list, obs_time, acclen=160)


if __name__ == "__main__":
    main()
