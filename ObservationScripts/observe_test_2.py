#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
import time
import atexit
import numpy as np
import sys

import argparse
import logging

import os,sys
import glob

from SNAPobs import snap_config

CFG = snap_config.get_ata_cfg()


def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)


    antlo_list = [
		"1cB", "1eB", "1gB", "1hB","1kB",
		 "2aB", "2cB",
		"2eB", "2hB", "2jB",
		"2mB", "3cB", "3dB",
		"3lB", "4jB", "5bB", "4gB"]

    ant_list = ["1c", "1e", "1g", "1h", "1k", "2a", "2b", "2c",
                "2e", "2h", "2j", "2k", "2l", "2m", "3c", "3d",
                "3l", "4j", "5b", "4g"]

    #ant_list = ["2e", "2h", "2j", "2k", "2l", "2m", "3c", "3d",
    #            "1c", "1e", "1g", "1h", "1k", "2a", "2b", "2c"]

    #ant_list = ["2j", "2m", "2k", "3d", "2e"]


    antlo_list = [ant+"B" for ant in ant_list]

    obs_time = 10

    #snap_if.tune_if_antslo(antlo_list)
    for i in range(50):
        utc = snap_dada.start_recording(antlo_list, obs_time, 
                npolout=2, acclen=120*16, disable_rfi=True)


if __name__ == "__main__":
    main()
