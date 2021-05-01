#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
import atexit
from SNAPobs import snap_dada
import numpy as np
import sys

import argparse
import logging

import os

ATTEMP_SCRIPT = "/home/obsuser/src/psrdada/ata/scripts/attemp_new.py"


def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)
    
    # Magnetar observation
    #ant_list = ["1c"]
    #ant_list = ["1a", "1f", "1c", "2a", "2b", "2h", "3c", "4g", "1k", "5c", "1h", "4j"]
    ant_list = ["1a", "1f", "1c", "2a", "2b", "2h", "4g", "1k", "5c", "1h", "4j"]

    #ant_list = ["1f"]
    #freqs = [950, 950, 1600, 1600, 1600, 1600, 950, 950, 1600]
    #freqs = [3000]*len(ant_list)
    #ant_list = ["1f"]
    #ata_control.reserve_antennas(ant_list)
    #atexit.register(ata_control.release_antennas, 
    #        ant_list, True)

    #freq = 1600
    #freq = 800
    #ata_control.set_freq(freq, ant_list, lo='b')

    #source = "J0332+5434"
    #ata_control.make_and_track_ephems(source, ant_list)
    #snap_dada.set_freq_auto(freqs, ant_list)
    #ata_control.autotune(ant_list)
    #os.system(ATTEMP_SCRIPT)

    obs_time = 30

    #utc = snap_dada.start_recording(ant_list, obs_time, acclen=120,
    #        source="Testmode", npolout=2, disable_rfi=True)
    utc = snap_dada.start_recording(ant_list, obs_time, acclen=120,
            npolout=2, disable_rfi=True)

    #utc = snap_dada.start_recording(ant_list, obs_time, acclen=120*16,
    #        npolout=2, disable_rfi=True)

if __name__ == "__main__":
    main()
