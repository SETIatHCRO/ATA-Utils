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

    ant_list = ["1c", "1e", "1g", "1h", "1k", "2a", "2b", "2c",
                "2e", "2h", "2j", "2k", "2l", "2m", "3c", "3d",
                "3l", "4j", "5b", "4g"] #2a? 1k? 

    lo = "b"
    antlo_list = [ant+lo.upper() for ant in ant_list]
    
    #antlo_list += [ant+"C" for ant in ant_list]
    
    #los = list(set([antlo[-1] for antlo in antlo_list]))

    freqs   = [4000]*len(ant_list)


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    ata_control.set_freq(freqs, ant_list, lo='b')
    #time.sleep(20)
    #ata_control.set_freq(freqs_c, ant_list, lo='c')
    #time.sleep(30)

    cal_source = '3c273'
    source = "virgo"

    ata_control.make_and_track_ephems(source, ant_list)
    ata_control.autotune(ant_list)
    snap_if.tune_if_antslo(antlo_list) 

    os.system("start_record_in_x.py -H 1 2 3 4 -i 5 -n 3600")
    time.sleep(3600)

    ata_control.make_and_track_ephems(cal_source, ant_list)
    os.system("start_record_in_x.py -H 1 2 3 4 -i 5 -n 180")
    time.sleep(180)

    for i in range(10):
        ata_control.make_and_track_ephems(source, ant_list)
        os.system("start_record_in_x.py -H 1 2 3 4 -i 5 -n 1800")
        time.sleep(1800)

        ata_control.make_and_track_ephems(cal_source, ant_list)
        os.system("start_record_in_x.py -H 1 2 3 4 -i 5 -n 180")
        time.sleep(180)




    #obs_time = 300

    #utc = snap_dada.start_recording(antlo_list, obs_time, 
    #        disable_rfi=True, npolout=1, acclen=120)


if __name__ == "__main__":
    main()
