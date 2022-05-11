#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if, snap_config

import atexit

import numpy as np
import sys

import argparse
import logging

import os

import time

CFG = snap_config.get_ata_cfg()

def mv_utc_antlo_to_ant(utc):
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

    # pulsar observation
    #ant_list = ["1f", "1h"]#, "1k", "5c"]
    #freqs =    [950, 1600]#, 1600, 950]

    #ant_list = ["1a",    "4j",    "1k"]
    #freqs = [950] + [1600] + [2250]
    ant_list = ["1f", "5c", "1a",   "1c", "2a", "4j",    "2h", "1k", "1h"]
    antlo_list = ["1aA", "1fA", "2aA", "2hA", "3dA", "4gA", "1kA", "5cA", "1hA", "2bA",
            "1cB", "1eB", "1gB", #rfsoc1
#            "2cB", #rfsoc2
            "2eB", "2jB", #"2kB", #rfsoc3
            "2mB", "3cB", #rfsoc4
            "3lB", "5bB", "4jB"  #rfsoc5
            ]

    freq = 1500
    ant_list = [antlo[:-1] for antlo in antlo_list]


    #ant_list = ["1f", "1k"]
    #freqs = [950, 1600]
    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    source = "j0534+2200"
    ata_control.make_and_track_ephems(source, ant_list)
    ata_control.autotune(ant_list)

    #snap_dada.set_freq_auto(freqs, ant_list)
    ata_control.set_freq([freq]*len(ant_list), ant_list, lo='a')
    time.sleep(20)
    ata_control.set_freq([freq]*len(ant_list), ant_list, lo='b')

    #snap_if.tune_if_ants(ant_list)
    snap_if.tune_if_antslo(antlo_list)
    obs_time = 1200

    #for i in range(3):
    utc = snap_dada.start_recording(antlo_list, obs_time, 
            npolout=1, acclen=120, disable_rfi=True)
    
    mv_utc_antlo_to_ant(utc)


if __name__ == "__main__":
    main()
