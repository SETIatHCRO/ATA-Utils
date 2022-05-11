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

from SNAPobs.snap_hpguppi import record_in as hpguppi_record_in
from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary



def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    ant_list = ["1c", "1e", "1g", "1h", "1k", "2a", "2b", "2c",
                "2e", "2h", "2j", "2k", "2l", "2m", "4e", "3d",
                "3l", "4j", "5b", "4g"]  

    lo = "b"
    antlo_list = [ant+lo.upper() for ant in ant_list]
    
    antlo_list += [ant+"C" for ant in ant_list]
    
    #los = list(set([antlo[-1] for antlo in antlo_list]))

    #freqs   = [763]*len(ant_list)
    #freqs_c = [1960]*len(ant_list)

    #freqs   = [2000]*len(ant_list)
    #freqs_c = [3000]*len(ant_list)
    #freqs   = [4750]*len(ant_list)
    #freqs_c = [5450]*len(ant_list)
    #freqs   = [3350]*len(ant_list)
    #freqs_c = [4050]*len(ant_list)
    #freqs   = [7550]*len(ant_list)
    #freqs_c = [8250]*len(ant_list)
    freqs   = [8500]*len(ant_list)
    freqs_c = [6500.375]*len(ant_list)


    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    ata_control.set_freq(freqs, ant_list, lo='b', nofocus=True)
    time.sleep(20)
    ata_control.set_freq(freqs_c, ant_list, lo='c')
    time.sleep(20)
    

    source = "3c84"
    ata_control.make_and_track_ephems(source, ant_list)


    #ata_control.autotune(ant_list)
    #snap_if.tune_if_antslo(antlo_list)
    
    obs_time = 60
    obs_start_in = 10

    d = hpguppi_defaults.hashpipe_targets_LoB.copy()
    d.update(hpguppi_defaults.hashpipe_targets_LoC)
    
    keyval_dict = {'XTIMEINT':30}
    hpguppi_auxillary.publish_keyval_dict_to_redis(keyval_dict,
            d,
            postproc=False)

    # Start recording -- record_in does NOT block
    hpguppi_record_in.record_in(obs_start_in, obs_time,
            hashpipe_targets = d)
    print("Recording for %.2f seconds started..." %obs_time)
    time.sleep(obs_time + obs_start_in + 5)
    print("Done")

if __name__ == "__main__":
    main()
