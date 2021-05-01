#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
import atexit
from SNAPobs import snap_dada, snap_if
from sigpyproc.Readers import FilReader
import numpy as np
import sys
import time

import argparse
import logging

import os
import glob
OBSDIR = '/mnt/buf0/obs'


def get_power(utc, ant):
    filfile = glob.glob(os.path.join(OBSDIR, utc, ant, "*x.fil"))[0]
    fil = FilReader(filfile)

    chans = np.linspace(fil.header.ftop, fil.header.fbottom, fil.header.nchans)
    block = fil.readBlock(0, fil.header.nsamples)
    bp = block.mean(axis=1)

    args = (chans > 1678) & (chans < 1696)

    power_inband = (bp[args]).sum()
    return power_inband


def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)
    
    ant_list = ['3c']

    snap_if.setatten({ant+pol:27 for ant in ant_list for pol in ["x","y"]})
    snap_dada.set_freq_auto([1600]*len(ant_list), ant_list)

    obs_time = 10

    goes_az = 121.96
    goes_el = 23.63

    # point at goes16
    ata_control.set_az_el(ant_list, goes_az, goes_el)
    utcs = []
    while True:
        utc = snap_dada.start_recording(ant_list, obs_time, acclen=120*16,
                disable_rfi=True)
        utcs.append(utc)
        time.sleep(2)
        print("")
        print("="*79)
        for ant in ant_list:
            p = get_power(utc, ant)
            print(ant, p, 10*np.log10(p), "dB")
        print("="*79)
        print("")
        _ = input("measure again?")



if __name__ == "__main__":
    main()
