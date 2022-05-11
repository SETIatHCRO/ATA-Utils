#!/home/obsuser/miniconda3/envs/rfsoc_test/bin/python
from ATATools import ata_control, logger_defaults
import atexit
from SNAPobs import snap_dada, snap_if
import numpy as np
import sys
import time

import argparse
import logging

import os


def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    #ant_list = ["1cB", "1eB", "1hB",
    #            "1kB", "2aB", "2bB", "2cB",
    #            "2eB", "2hB", "2jB"]
    #ant_list = ["1cB"]
    #ant_list = ["1aA", "1cA", "2aA", "4jA", "2hA", "3dA", "4gA", "1kA", "5cA", "1hA", "2bA",
    #        "1eB", "1gB",
    #        "2cB",
    #        "2eB", "2jB"]
    """

    antlo_list = ["1aA", "1fA", "1cA", "2aA", "4jA", "2hA", "3dA", "4gA", "1kA", "5cA", "1hA", "2bA",
            "1cB", "1eB", "1gB", "1hB", #rfsoc1
            "1kB", "2aB", "2bB", "2cB", #rfsoc2
            "2eB", "2hB", "2jB", #"2kB", #rfsoc3
            "2lB", "2mB", "3cB", "3dB", #rfsoc4
            "3lB", "4jB", "5bB", "4gB", #rfsoc5
            ]

            ]
    """

    antlo_list = [
		    "1cB", "1eB", "1gB", "1hB",
		    "1kB", "2aB", "2cB", "2bB",
		    "2eB", "2hB", "2jB", "2kB",
		    "2mB", "2lB", "3cB", "3dB",
		    "4jB", "5bB", "4gB"]

    antlo_list = [
		    "1cB", "1eB", "1gB", "1hB",
		    "1kB", "2aB", "2cB", "2bB",
		    "2eB", "2hB", "2kB",
		    "2mB", "2lB", "3cB", "3dB",
		    "4jB", "5bB", "4gB"]

    #antlo_list = ["3lB", "4jB", "5bB", "4gB",] #rfsoc5

    #snap_if.tune_if_antslo(ant_list)
    #ata_control.reserve_antennas(ant_list)
    #atexit.register(ata_control.release_antennas, ant_list, False)
    #az,el = 60,60

    #ata_control.set_az_el(ant_list, az, el)
    obs_time = 30

    #utc = snap_dada.start_recording(antlo_list, obs_time, acclen=120*16,
    #        npolout=2, disable_rfi=True)

    utc = snap_dada.start_recording(antlo_list, obs_time, acclen=120,
            npolout=2, disable_rfi=True)

if __name__ == "__main__":
    main()
