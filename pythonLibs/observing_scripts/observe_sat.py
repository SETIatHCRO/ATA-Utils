#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults, ata_coords

from SNAPobs import snap_dada, snap_if
import atexit
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

    ant_list = ["1a","1f"]

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)
    dump_thread = ata_coords.CoordDumpThread(ant_list, 
            "/mnt/buf0/obs/coords_dump.txt")
    dump_thread.start()
    atexit.register(dump_thread.stop)

    #source = "GPS-BIIRM-3--PRN-12-"
    source = "GPS-BIIF-6---PRN-06-"

    ata_control.create_ephem(source, **{'duration': 2, 'interval': 0.1})

    freqs = [1575]*len(ant_list)

    snap_dada.set_freq_auto(freqs, ant_list)
    antpols = ["%s%s" %(ant, pol) for ant in ant_list for pol in ["x", "y"]]
    if_atten = {antpol:10 for antpol in antpols}
    snap_if.setatten(if_atten)

    pbfwhm = (3.5 / freqs[0] * 1000.0);
    delta = pbfwhm / 2.0
    obs_time = 30

    offsets = [
            [0., 4*delta],
            [0., delta],
            [0., 0.],
            [0., -delta],
            [0., -4*delta],
            [-4*delta, 0.],
            [-delta, 0.],
            [0., 0.],
            [delta, 0.],
            [4*delta, 0.]
            ]


    # offsets = az/el
    for offset in offsets:
        print(offset)
        ata_control.track_and_offset(source, ant_list, offset=offset)
        utc = snap_dada.start_recording(ant_list, obs_time, acclen=120*16,
                    disable_rfi=True)


if __name__ == "__main__":
    main()
