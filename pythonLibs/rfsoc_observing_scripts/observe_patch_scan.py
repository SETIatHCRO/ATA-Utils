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
                "2e", "2h", "2j", "2l", "2m", "3c", "3d",
                "3l", "4j", "5b", "4g", "2k"]

    antlo_list = [ant+"B" for ant in ant_list]
    
    #antlo_list += [ant+"C" for ant in ant_list]
    

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)


    time.sleep(30)
    
    freqs = np.arange(2250, 11200, 550)

    obs_time = 20
    
    start_az = 20
    start_el = 0
    end_az = 360
    end_el = 90
    step = 10

    az_list = np.arange(start_az, end_az, step)
    el_list = np.arange(start_el, end_el, step)

    for freq in freqs:
    
        ata_control.set_freq(freq, ant_list, lo='b')
        ata_control.autotune(ant_list)
        snap_if.tune_if_antslo(antlo_list)

        for az in az_list:
            for el in el_list:

                print("az: %.2f, el: %.2f" %(az, el))
                os.system("killall ata_udpdb")
                ata_control.set_az_el(ant_list, az, el)
                utc = snap_dada.start_recording(antlo_list, obs_time, acclen=120*16,
                        disable_rfi=True)
            time.sleep(10)


if __name__ == "__main__":
    main()
