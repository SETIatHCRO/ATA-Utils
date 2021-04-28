#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
import time
import atexit
import numpy as np
import sys

import argparse
import logging

import os

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    az_offset = 20.
    el_offset = 0.

    ant_list = ["2b"]
    source = "casa"
    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, False)

    ata_control.create_ephems2(source, az_offset, el_offset)

    ata_control.point_ants2(source, "off", ant_list)
    ata_control.autotune(ant_list)

    _ = input("Press any key to switch to on source")
    ata_control.point_ants2(source, "on", ant_list)
    print("on source acquired")


if __name__ == "__main__":
    main()
