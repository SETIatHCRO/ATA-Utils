#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada
import numpy as np
import sys

import atexit

import argparse
import logging

import os

ATTEMP_SCRIPT = "/home/obsuser/src/psrdada/ata/scripts/attemp_new.py"


def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # moon observation
    az_offset = 20
    el_offset = 0
    #freqs = np.arange(1000, 11000, 500)
    #freq = 1600 #+ 2*300
    #freq = 1600 + 700 #+ 2*300

    ant_list = ["2b", "2a"]
    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, True)

    obs_time = 30
    source = "NCP"
    ata_control.set_az_el(ant_list, 0, 40.723)
    ata_control.autotune(ant_list)

    freqs = np.arange(1250, 11200, 450)

    snap_dada.set_freq_auto([freqs[0]]*len(ant_list), ant_list)
    time.sleep(30)

    for ifreq, freq in enumerate(freqs):
        snap_dada.set_freq_auto([freq]*len(ant_list), ant_list)
        snap_if.tune_if_ants(ant_list)

        utc = snap_dada.start_recording(ant_list, obs_time, npolout=2,
                acclen=120*2, source="NCP", disable_rfi=True)


if __name__ == "__main__":
    main()
