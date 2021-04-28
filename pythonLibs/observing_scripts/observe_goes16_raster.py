#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
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
    
    #ant_list = ["3c", "2b"]
    #ant_list = ['1a', '1f', '1c', '2a', '2b', '2h', 
    #        '4g', '1k', '5c', '1h', '4j']
    ant_list = ['3c']
    #snap_if.setatten({'3cx': 27, '3cy': 27, '2bx': 27, '2by': 27})
    snap_if.setatten({ant+pol:27 for ant in ant_list for pol in ["x","y"]})
    snap_dada.set_freq_auto([1600]*len(ant_list), ant_list)
    #snap_if.tune_if_ants(ant_list)
    obs_time = 10

    goes_az = 121.96
    goes_el = 23.63
    step = 0.1

    az_list = np.arange(goes_az - 1, goes_az + 1, step)
    el_list = np.arange(goes_el - 1, goes_el + 1, step)

    for az in az_list:
        os.system("killall ata_udpdb")
        for el in el_list:
            print("az: %.2f, el: %.2f" %(az, el))
            ata_control.set_az_el(ant_list, az, el)
            utc = snap_dada.start_recording(ant_list, obs_time, acclen=120*16,
                    disable_rfi=True)
        time.sleep(10)

if __name__ == "__main__":
    main()
