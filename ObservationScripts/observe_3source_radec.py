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
                "2e", "2h", "2j", "2l", "2k", "2m", "3c", "3d",
                "3l", "4j", "5b", "4g"] 
                                        
    antlo_list = [ant+"B" for ant in ant_list]
    
    
    freqs = [3000]*len(ant_list)


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    ata_control.set_freq(freqs, ant_list, lo='b')

    #time.sleep(30)
    
    source_name = ['3c273', '3c286', '3c295'] 

    do_autotune = True

    while True:
        for i, source in enumerate(source_name):
            print(i, source)

            if 85 > ata_sources.check_source(source)['el'] > 21:
      
                ata_control.make_and_track_ephems(source, ant_list)

                if do_autotune:
                    ata_control.autotune(ant_list)
                    snap_if.tune_if_antslo(antlo_list)
                    do_autotune = False
                

                print("Tuning complete")

                #time.sleep(20)

                obs_time = 610 #925 #seconds

                print("="*79)
                print("Starting new obs")
                print("start_record_in_x.py -H 1 2 3 4 -i 10 -n %i" %obs_time)
                os.system("start_record_in_x.py -H 1 2 3 4 -i 10 -n %i" %obs_time)
                print("Recording on sky source %s..." %source)
                time.sleep(obs_time+20)

                print("="*79)
                print("Obs completed")
            
            else:
                print(str(source) + " is not high (or low) enough to observe, trying again once all others are targeted")

if __name__ == "__main__":
    main()
