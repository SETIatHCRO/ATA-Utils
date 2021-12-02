#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
import atexit
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
from ATATools import ata_sources

import numpy as np
import sys
import time

import argparse
import logging

import os

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # multiple source observation
    ant_list = ["1c", "1e", "1g", "1h", "1k", "2a", "2b", "2c",
                "2e", "2h", "2j", "2l", "2m", "3c", "3d",
                "3l", "4j", "5b", "4g"] #2k left out 
                                        
    antlo_list = [ant+"B" for ant in ant_list]
    
    
    freqs = [1500]*len(ant_list)


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    ata_control.set_freq(freqs, ant_list, lo='b')

    #time.sleep(30)
    
    print("Aquiring source list")
    
    lista = []
    
    with open("source_radec.txt") as f:
        source_list = f.readlines()[1:]

        for x in source_list:
            lista.append(x.split(' ')[0])

    source_name = lista

    print(source_name)
    
    #source_name = source_name[1]   #if you want to just observe one of the sources

    print("source list aquired") 
    
    for i, source in enumerate(source_name):
        print(i, source)

        if ata_sources.check_source(source)['el'] > 17:

            ata_control.make_and_track_ephems(source, ant_list)


            ata_control.autotune(ant_list)
            snap_if.tune_if_antslo(antlo_list)
            
            obs_time = 30
        
            #_ = input("press enter to continue")
            
            utc = snap_dada.start_recording(antlo_list, obs_time, 
                    disable_rfi=True, npolout=1, acclen=120)
        else:
            continue

if __name__ == "__main__":
    main()
