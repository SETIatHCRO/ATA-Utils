#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
main functions for snap observations
"""

from ATATools import logger_defaults,obs_db,ata_control
import snap_defaults
import snap_dirs
from threading import Thread
#from subprocess import Popen, PIPE

def single_snap_observe():
    logger = logger_defaults.getModuleLogger(__name__)


def observe_same(ant_dict,freq,source,ncaptures,obstype,obsuser,desc,filefragment,rms=None,
        az_offset=0,el_offset=0,fpga_file=snap_defaults.spectra_snap_file,obs_set_id=None):
    """


    """

    logger = logger_defaults.getModuleLogger(__name__)
    #setting up the observation and starting it

    obsid = obs_db.initObservation(freq,obstype,"SNAP",desc,obsuser,obs_set_id)

    logger.info("got obs id {}".format(obsid))

    snap_dirs.set_output_dir_obsid(obsid) 

    ant_list = ant_dict.values()
    logger.info("updating database with antennas {}".format(", ".join(ant_list)))
    obs_db.initAntennasTable(obsid,ant_list,source,az_offset,el_offset,True)

    if rms:
        logger.info("starting observation {}. Target RMS {}".format(obsid,rms))
    else:
        logger.info("starting observation {}. No RMS provided".format(obsid))
    obs_db.startObservation(obsid)

    #import pdb
    #pdb.set_trace()

    snaps = ant_dict.keys()
    threads = []
    for snap in snaps:
        t = Thread(target=single_snap_observe,
                args=())

        t.start()
        #time.sleep(1)
        threads.append(t)


    for t in threads:
        t.join()

    obs_db.stopObservation(obsid)

    return obsid


if __name__== "__main__":
    
    ant_list = ['2j','2a','1c']
    ant_dict = {'snap1': '2j', 'snap0': '2a', 'snap2': '1c'}
    freq = 1400.0
    source = 'casa'
    ncaptures = 16
    obstype='ON-OFF'
    obsuser='ataonoff'
    desc='ON rep 0'
    filefragment = 'on_000'
    rms=None
    az_offset=0
    el_offset=0
    fpga_file=snap_defaults.spectra_snap_file
    obs_set_id=None
    
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logger_defaults.getModuleLogger('snap_obs_test')
    ata_control.reserve_antennas(ant_list)

    try:
        obsid = observe_same(ant_dict,freq,source,ncaptures,obstype,obsuser,desc,filefragment,rms,
                        az_offset,el_offset,fpga_file,obs_set_id)
        logger.info("ID: {}".format(obsid))
    except:
        logger.exception('Top level test')
        raise
    finally:
        ata_control.release_antennas(ant_list, True)

