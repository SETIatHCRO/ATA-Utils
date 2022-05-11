#!/home/sonata/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada
import numpy as np
import sys

import argparse
import logging

import os

ATTEMP_SCRIPT = "/home/sonata/psrdada/ata/scripts/attemp.py"

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    """
    # moon observation
    az_offset = 0
    el_offset = 20
    freqs = np.arange(1000, 11000, 500)
    ant_list = ['1a', '1c', '1f', '2a', '2b', '2h', '4g', '5c']
    ata_control.reserve_antennas(ant_list)
    obs_time = 30
    source = "moon"
    ata_control.create_ephems2(source, az_offset, el_offset)
    for i in range(1):
        for freq in freqs:
            print (freq)
            ata_control.set_freq(freq, ant_list)
            os.system(ATTEMP_SCRIPT)

            # record on
            ata_control.point_ants2(source, "on", ant_list)
            ant_list.append('rfi')
            utc = snap_dada.start_recording(ant_list, obs_time, 
                    acclen=160*80)
            ant_list.remove('rfi')

            # record off
            ata_control.point_ants2(source, "off", ant_list)
            ant_list.append('rfi')
            utc = snap_dada.start_recording(ant_list, obs_time,
                    acclen=160*80)
            ant_list.remove('rfi')
    """

    # Casa observation
    az_offset = 0
    el_offset = 10
    freqs = np.arange(1000, 11000, 500)
    ant_list = ['1a', '1c', '2a', '2b', '2h', '4g']
    ata_control.reserve_antennas(ant_list)
    """
    obs_time = 30
    source = "casa"
    ata_control.create_ephems2(source, az_offset, el_offset)
    for i in range(1):
        for freq in freqs:
            print (freq)
            ata_control.set_freq(freq, ant_list)
            os.system(ATTEMP_SCRIPT)

            # record on
            ata_control.point_ants2(source, "on", ant_list)
            #ant_list.append('rfi')
            utc = snap_dada.start_recording(ant_list, obs_time, 
                    acclen=160*80)
            #ant_list.remove('rfi')

            # record off
            ata_control.point_ants2(source, "off", ant_list)
            #ant_list.append('rfi')
            utc = snap_dada.start_recording(ant_list, obs_time,
                    acclen=160*80)
            #ant_list.remove('rfi')
    """

    
    # Magnetar observation
    ant_list = ["1c", "2a", "2b", "2h"]
    freq = 1600
    ata_control.set_freq(freq, ant_list)

    source = "J1934+2153"
    ata_control.make_and_track_ephems(source, ant_list)
    obs_time = 3600
    os.system(ATTEMP_SCRIPT)

    for i in range(7):
        ata_control.make_and_track_ephems(source, ant_list)
        utc = snap_dada.start_recording(ant_list, obs_time)
        print (utc)


    # casa observation
    az_offset = 0
    el_offset = 10
    freqs = np.arange(1000, 11000, 500)
    ant_list = ['1a',  '1c', '2a', '2b', '2h', '4g']
    obs_time = 30
    source = "casa"
    ata_control.create_ephems2(source, az_offset, el_offset)
    for i in range(1):
        for freq in freqs:
            print (freq)
            ata_control.set_freq(freq, ant_list)
            os.system(ATTEMP_SCRIPT)

            # record on
            ata_control.point_ants2(source, "on", ant_list)
            #ant_list.append('rfi')
            utc = snap_dada.start_recording(ant_list, obs_time, 
                    acclen=160*80)
            #ant_list.remove('rfi')

            # record off
            ata_control.point_ants2(source, "off", ant_list)
            #ant_list.append('rfi')
            utc = snap_dada.start_recording(ant_list, obs_time,
                    acclen=160*80)
            #ant_list.remove('rfi')
    ant_list = ['1a',  '1c', '2a', '2b', '2h', '4g']
    ata_control.release_antennas(ant_list, True)

if __name__ == "__main__":
    main()
