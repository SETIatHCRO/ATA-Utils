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

    # moon observation
    az_offset = 20.
    el_offset = 0.

    #ant_list = ["1a", "1f", "1c", "2a", "2b", "3d",
    #        "4g", "1k", "5c", "1h", "4j", "2h"]
    ant_list = ["1a", "1c", "2a", "4j", "2h",
            "3d", "4g", "1k", "5c", "1h", "2b"]
    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, True)

    obs_time = 30
    n_on_off = 1

    source = "moon"
    ata_control.create_ephems2(source, az_offset, el_offset)

    ata_control.point_ants2(source, "off", ant_list)
    ata_control.autotune(ant_list)

    #freqs = np.arange(1200, 9500, 350)
    #freqs = np.arange(1200, 11200, 350)
    #freqs = np.arange(1200, 1900, 350)
    freqs = np.arange(2250, 11200, 550)

    snap_dada.set_freq_auto([freqs[0]]*len(ant_list), ant_list)
    time.sleep(30)

    utcs_all = []
    for ifreq, freq in enumerate(freqs):
        utcs_this_freq = []
        if ifreq != 0:
            snap_dada.set_freq_auto([freq]*len(ant_list), ant_list)
            snap_if.tune_if_ants(ant_list)

        for i in range(n_on_off):
            # record on
            ata_control.point_ants2(source, "on", ant_list)

            utc = snap_dada.start_recording(ant_list, obs_time, 
                    npolout=2, acclen=120*16, disable_rfi=True)

            utcs_this_freq.append(utc)
            os.system("killall ata_udpdb")

            #record off
            ata_control.point_ants2(source, "off", ant_list)

            utc = snap_dada.start_recording(ant_list, obs_time, 
                    npolout=2, acclen=120*16, disable_rfi=True)

            utcs_this_freq.append(utc)
            os.system("killall ata_udpdb")

        utcs_all.append(utcs_this_freq)

    initial_utc = utcs_all[0][0]


    os.system("mkdir /mnt/datax-netStorage-40G/calibration/"+initial_utc)
    for freq, utcs in zip(freqs, utcs_all):
        os.system("mkdir /mnt/datax-netStorage-40G/calibration/%s/freq_%i"
                %(initial_utc, freq))
        for utc in utcs:
            os.system("mv /mnt/buf0/obs/%s /mnt/datax-netStorage-40G/calibration/%s/freq_%i"
                    %(utc, initial_utc, freq))

    os.system("/home/obsuser/scripts/fil2csv.py /mnt/datax-netStorage-40G/calibration/%s/*/*/*/*.fil" %(initial_utc))

    """
    os.system("mkdir /mnt/datax-netStorage-40G/calibration/"+initial_utc)
    for freq, utcs in zip(freqs, utcs_all):
        for utc in utcs:
            os.system("mv /mnt/buf0/obs/%s /mnt/datax-netStorage-40G/calibration/%s"
                    %(utc, initial_utc))
    """

    o = open("/mnt/datax-netStorage-40G/calibration/obs.dat", "a")
    o.write("%s %s %i\n" %(initial_utc, source, n_on_off))
    o.close()


if __name__ == "__main__":
    main()
