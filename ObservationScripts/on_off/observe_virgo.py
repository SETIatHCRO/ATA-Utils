#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
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

    # moon observation
    az_offset = 20
    el_offset = 0

    #ant_list = ["1a", "1f", "1c", "2a", "2b", "2h",
    #        "3c", "4g", "1k", "5c", "1h", "4j"]
    ant_list = ["1c", "2a", "2b", "2h",
            "3c", "4g", "1k", "1h", "4j"]
    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, False)

    obs_time = 30

    source = "virgo"
    ata_control.create_ephems2(source, az_offset, el_offset)

    ata_control.point_ants2(source, "on", ant_list)
    ata_control.autotune(ant_list)

    freqs = np.arange(1200, 10500, 350)
    #freqs = np.arange(1200, 1900, 350)

    utcs_all = []
    for freq in freqs:
        utcs_this_freq = []
        snap_dada.set_freq_auto([freq]*len(ant_list), ant_list)
        snap_if.tune_if_ants(ant_list)

        for i in range(3):
            # record on
            ata_control.point_ants2(source, "on", ant_list)

            i = 0
            while i < 3:
                try:
                    utc = snap_dada.start_recording(ant_list, obs_time, 
                            npolout=2, acclen=120*16, disable_rfi=True)
                    break
                except:
                    i += 1

            utcs_this_freq.append(utc)

            #record off
            ata_control.point_ants2(source, "off", ant_list)

            i = 0
            while i < 3:
                try:
                    utc = snap_dada.start_recording(ant_list, obs_time, 
                            npolout=2, acclen=120*16, disable_rfi=True)
                    break
                except:
                    i += 1

            utcs_this_freq.append(utc)

        utcs_all.append(utcs_this_freq)

    initial_utc = utcs_all[0][0]

    os.system("mkdir /mnt/datax-netStorage-40G/calibration/"+initial_utc)
    for freq, utcs in zip(freqs, utcs_all):
        os.system("mkdir /mnt/datax-netStorage-40G/calibration/%s/freq_%i"
                %(initial_utc, freq))
        for utc in utcs:
            os.system("mv /mnt/buf0/obs/%s /mnt/datax-netStorage-40G/calibration/%s/freq_%i"
                    %(utc, initial_utc, freq))


if __name__ == "__main__":
    main()
