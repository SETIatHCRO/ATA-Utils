#!/home/sonata/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
import time
import atexit
from SNAPobs import snap_dada
import numpy as np
import sys

import argparse
import logging

import os

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)
    
    # Magnetar observation
    ant_list = ["3c"]
    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, 
            ant_list, True)

    """
    goes_az = 60
    goes_el = 60
    step = 1

    az_list = np.arange(goes_az - 10, goes_az + 10, step)
    el_list = np.arange(goes_el - 10, goes_el + 10, step)

    for az in az_list:
        for el in el_list:
            t1 = time.time()
            print(az,el)
            #ata_control.set_az_el(ant_list, az, el)
            ata_control.set_ra_dec(ant_list, ra, dec)
            t2 = time.time()
            print(t1-t2)
            print("Waiting for some 'backend'")
            time.sleep(3)
    """


    ra  = 23.386
    dec = 40
    step = 3

    dec_list = np.arange(dec - 12, dec + 12, step)
    ra_list = np.array([ra]*len(dec_list))

    for ra in ra_list:
        for dec in dec_list:
            t1 = time.time()
            print(ra,dec)
            ata_control.make_and_track_ra_dec(ra, dec, ant_list)
            t2 = time.time()
            print(t1-t2)
            print("Waiting for some 'backend'")
            time.sleep(3)


if __name__ == "__main__":
    main()
