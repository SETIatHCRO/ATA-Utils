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
import csv
import os

from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults
from SNAPobs.snap_hpguppi import record_in as hpguppi_record
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary

from recons10_utils import get_source_names
from recons10_utils import is_observed
from recons10_utils import mark_as_observed


def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # multiple source observation
    ant_list = ["1c", "1e", "1g", "1h", "1k", "2a", "2b", "2c",
                "2e", "2h", "2j", "2l", "2k", "2m", "4e", "3d",
                "3l", "4j", "5b", "4g"] 
                                        
    antlo_list = [ant+lo for ant in ant_list for lo in ['B', 'C']]
    
    
    #Define observing frequencies - outside loop
    freqs = [4750]*len(ant_list)
    freqs_c = [5450]*len(ant_list)

    #freqs = [7550]*len(ant_list)
    #freqs_c = [8250]*len(ant_list)


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    #ata_control.set_freq(freqs, ant_list, lo='b', nofocus=True)
    #ata_control.set_freq(freqs_c, ant_list, lo='c')

    time.sleep(30)
    
    print("Aquiring source list")
    
    lista = []
    
    csv_name = 'sources_observed.csv'

    source_names = get_source_names(csv_name)
    
    print(source_names)

    
    d = hpguppi_defaults.hashpipe_targets_LoB.copy()
    d.update(hpguppi_defaults.hashpipe_targets_LoC)
    
    
    do_autotune = False
    
    
    while True:
        #loop through source list
        for i, source in enumerate(source_names):
            print(i, source)

            #make sure source is not observed
            if is_observed(csv_name, source, freqs[0]) == 0 and\
                    is_observed(csv_name, source, freqs_c[0]) == 0:
                #place elevation limits
                if 85 > ata_sources.check_source(source)['el'] > 21:
                
                    ata_control.make_and_track_ephems(source, ant_list)
                    
                    if do_autotune:
                        ata_control.autotune(ant_list)
                        snap_if.tune_if_antslo(antlo_list)
                        do_autotune = False

                    print("Tuning complete")

                    #time.sleep(20)

                    obs_time = 300 #610 #925 #seconds
                    obs_start_in = 5

                    
                    hpguppi_record.block_until_post_processing_waiting(d)
                    print('Post proc is done for\n', d)

                    print("Starting new obs")
                    
                    if 85 < ata_sources.check_source(source)['el'] < 21:
                        continue

                    # Start recording -- record_in does NOT block
                    hpguppi_record.record_in(obs_start_in, obs_time,
                                hashpipe_targets = d)
                    print("Recording for %.2f seconds started..." %obs_time)
                    
                    time.sleep(obs_time + obs_start_in + 5)

                    print("Obs completed")
                    print("Marking as observed")
                    
                    mark_as_observed(csv_name, source, freqs[0])
                    mark_as_observed(csv_name, source, freqs_c[0])

                    print(str(source) + " has been successfully observed at " + str(freqs[0]) + "MHz and " + str(freqs_c[0]) + "MHz")
                    
                else:
                    print(str(source) + " is not high (or low) enough to observe, trying again once all others are targeted")

            else:
                print(str(source) + " has been observed at " + str(freqs[0]) + "MHz and " + str(freqs_c[0]) + "MHz, moving to the next source") 

if __name__ == "__main__":
    main()
