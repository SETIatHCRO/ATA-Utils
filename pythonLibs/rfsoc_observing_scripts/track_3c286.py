#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
import atexit
from ATATools import ata_control, logger_defaults
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

    antlo_list = [
            "1cB", "1eB", "1gB", "1hB",
            "1kB", "2aB", "2bB", "2cB",
            "2eB", "2hB", "2jB",
            "2lB", "2mB", "3cB", "3dB",
            "3lB", "4jB", "5bB", "4gB"]

    ant_list = list(set([antlo[:-1] for antlo in antlo_list]))
    los = list(set([antlo[-1] for antlo in antlo_list]))

    
    #freqs = [950]*3 + [1600]*3 + [2250]*3
    #ant_list = ["1f"]
    freqs = [3000]*len(ant_list)
    freqs = [6000]*len(ant_list)
    #freqs = [8450]*len(ant_list)


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    #ata_control.set_freq(freqs, ant_list, lo='a')
    ata_control.set_freq(freqs, ant_list, lo='b')

    time.sleep(30)

    source = "3c286"
    ata_control.make_and_track_ephems(source, ant_list)


    ata_control.autotune(ant_list)
    snap_if.tune_if_antslo(antlo_list)


if __name__ == "__main__":
    main()
