#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
import atexit
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if, snap_config
import numpy as np
import sys
import time
import glob

from pathlib import Path

import argparse
import logging

import os


def mv_utc_antlo_to_ant(utc):
    CFG = snap_config.get_ata_cfg()
    obsdir = CFG['OBSDIR']
    g = glob.glob(os.path.join(obsdir, utc, "*"))
    for eachDir in g:
        bname = os.path.basename(eachDir)
        t = bname[0]
        e = bname[-1]
        if (t.isnumeric()) and (e.lower() in ["a","b","c","d"]):
            os.rename(eachDir, eachDir[:-1]) #remove LO
    return


def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # FRB observation
    ant_list = ["1c", "1e", "1g", "1h", "1k", "2a", "2b", "2c",
            "2e", "2h", "2j", "2l", "2m", "3c", "3d",
            "3l", "4j", "5b", "4g"] #no 2k yet

    lo = "B"
    antlo_list = [ant+lo for ant in ant_list]

    freqs = [1500]*len(ant_list)


    ata_control.reserve_antennas(list(set(ant_list)))
    atexit.register(ata_control.release_antennas, list(set(ant_list)), True)

    ata_control.set_freq(freqs, ant_list, lo='b')

    time.sleep(30)

    source = "J1934+2153"
    ata_control.make_and_track_ephems(source, list(set(ant_list)))


    ata_control.autotune(ant_list, power_level=-15)

    obs_time = 1200
    
    #Note - ncycles should not be less than nhours, to ensure that the backend
    #can catch up and process the files before filling up disk space
    nhours = 1
    ncycles = 7

    for icycle in range(ncycles):
        for i in range(nhours*3):
            snap_if.tune_if_antslo(antlo_list)
            utc = snap_dada.start_recording(antlo_list, obs_time, 
                    npolout=1, acclen=120, disable_rfi=True)
            mv_utc_antlo_to_ant(utc)
            Path('/mnt/buf0/obs/%s/obs.sumall' %utc).touch()
            snap_dada.mark_obs_for_heimdall(utc)


        time.sleep(300)


if __name__ == "__main__":
    main()
