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

    # pulsar observation
    ant_list = ["1c", "1g", "1h", "1k", "1e", "2a", "2b", "2c",
                "2e", "2h", "2j", "2k", "2l", "2m", "3c", "3d",
                "3l", "4j", "5b", "4g"]

    lo = "c"
    antlo_list = [ant+lo.upper() for ant in ant_list]
    
    #antlo_list += [ant+"C" for ant in ant_list]
    
    #los = list(set([antlo[-1] for antlo in antlo_list]))

    freqs   = [3000]*len(ant_list)
    freqs_c = [1400+800]*len(ant_list)


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    ata_control.set_freq(freqs, ant_list, lo='b')
    time.sleep(20)
    ata_control.set_freq(freqs_c, ant_list, lo='c', nofocus=True)
    time.sleep(30)
    

    source = "3c138"
    ata_control.make_and_track_ephems(source, ant_list)


    #ata_control.autotune(ant_list)
    #snap_if.tune_if_antslo(antlo_list)
    #obs_time = 300

    #utc = snap_dada.start_recording(antlo_list, obs_time, 
    #        disable_rfi=True, npolout=1, acclen=120)


if __name__ == "__main__":
    main()
