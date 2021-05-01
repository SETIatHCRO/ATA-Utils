#!/home/sonata/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada
import numpy as np
import sys

import argparse
import logging

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)
    #parser = argparse.ArgumentParser(description="Observing script")
    #parser.add_argument("ants", nargs="+", help="ant names")
    #args = parser.parse_args()
    #ants = args.ants
    nbatches = 15
    ant_list = ["1a","1c","1f","2a","2b","2h","4g","5c"]
    az_offset = 0
    el_offset = 10
    obs_time = 30
    source = "casa"
    #source = "moon"

    ata_control.try_on_lnas(ant_list)

    #ata_control.make_and_track_ephems(source, ant_list)
    ata_control.create_ephems2(source, az_offset, el_offset)


    #freqs = np.arange(1200, 8000, 400)
    freqs = np.arange(1000, 11000, 500)

    for freq in freqs:
        print (freq)
        ata_control.set_freq(freq, ant_list)

        # record on
        ata_control.point_ants2(source, "on", ant_list)
        ant_list.append('rfi')
        utc = snap_dada.start_recording(ant_list, obs_time)
        ant_list.remove('rfi')

        # record off
        ata_control.point_ants2(source, "off", ant_list)
        ant_list.append('rfi')
        utc = snap_dada.start_recording(ant_list, obs_time)
        ant_list.remove('rfi')
    ata_control.release_antennas(ant_list, True)


if __name__ == "__main__":
    main()
