#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
main functions for snap observations
"""

from ATATools import logger_defaults,obs_db,ata_control
import snap_defaults
import snap_dirs
import concurrent.futures
import snap_recorder

def single_snap_recording():
    logger = logger_defaults.getModuleLogger(__name__)
    raise NotImplementedError


def getRMS(ant_dict,fpga_file=snap_defaults.spectra_snap_file,srate=snap_defaults.srate):
    """
    for debug only - reading current RMS values of the snap
    """
    logger = logger_defaults.getModuleLogger(__name__)

    ant_list = ant_dict.values()

    snaps = ant_dict.keys()
    nsnaps = len(snaps)

    rdict = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=nsnaps) as executor:
        threads = []
        for snap in snaps:
            t = executor.submit(snap_recorder.getSnapRMS,snap,ant_dict[snap],fpga_file)
            threads.append(t)

        for t in threads:
            retval = t.result()
            rdict[retval['ant']] = retval
            retval.pop('ant')

    return rdict

def setRMS(ant_dict,fpga_file=snap_defaults.spectra_snap_file,rms=snap_defaults.rms,srate=snap_defaults.srate):
    """
    set attenuators values for SNAP observation
    """

    logger = logger_defaults.getModuleLogger(__name__)

    ant_list = ant_dict.values()

    snaps = ant_dict.keys()
    nsnaps = len(snaps)

    rdict = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=nsnaps) as executor:
        threads = []
        for snap in snaps:
            t = executor.submit(snap_recorder.setSnapRMS,snap,ant_dict[snap],fpga_file,rms)
            threads.append(t)

        for t in threads:
            retval = t.result()
            rdict[retval['ant']] = retval
            retval.pop('ant')

    return rdict


def record_same(ant_dict,freq,source,ncaptures,obstype,obsuser,desc,filefragment,backend="SNAP",
        az_offset=0,el_offset=0,fpga_file=snap_defaults.spectra_snap_file,obs_set_id=None):
    """
    basic recording scripts, where all antennas are pointed on in the same position
    NOTE:
    the frequency, antenna pointing and source has to be set up earlier. This function only 
    records data and populates the database with given information. 

    Parameters
    -------------
    ant_dict : dict
        the snap to antenna mapping for the recording. e.g. {'snap2': '2a','snap1': '2j'}
    freq : float
        the frequency
    
    Returns
    -------------
    long
        observation (recording) id
    
    Raises
    -------------


    """

    logger = logger_defaults.getModuleLogger(__name__)
    #setting up the observation and starting it

    obsid = obs_db.initRecording(freq,obstype,backend,desc,obsuser,obs_set_id)

    logger.info("got obs id {}".format(obsid))

    snap_dirs.set_output_dir_obsid(obs_set_id) 

    ant_list = ant_dict.values()
    logger.info("updating database with antennas {}".format(", ".join(ant_list)))
    obs_db.initAntennasTable(obsid,ant_list,source,az_offset,el_offset,True)

    logger.info("starting observation {}".format(obsid))
    obs_db.startRecording(obsid)

    #import pdb
    #pdb.set_trace()

    snaps = ant_dict.keys()
    nsnaps = len(snaps)

    with concurrent.futures.ProcessPoolExecutor(max_workers=nsnaps) as executor:
        threads = []
        for snap in snaps:
            t = executor.submit(single_snap_recording)
            threads.append(t)


        for t in threads:
            retval = t.result()

    obs_db.stopRecording(obsid)

    return obsid


if __name__== "__main__":
    
    ant_list = ['1a','2a','2j']
    ant_dict = {'snap2': '2a', 'snap0': '1a', 'snap1':'2j'}
    freq = 1400.0
    source = 'casa'
    ncaptures = 16
    obstype='ON-OFF'
    obsuser='ataonoff'
    desc='ON rep 0'
    filefragment = 'on_000'
    rms=16.0
    az_offset=0
    el_offset=0
    fpga_file=snap_defaults.spectra_snap_file
    obs_set_id=None
    
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logger_defaults.getModuleLogger('snap_obs_test')
    ata_control.reserve_antennas(ant_list)

    try:
        #obsid = record_same(ant_dict,freq,source,ncaptures,obstype,obsuser,desc,filefragment,
        #                az_offset,el_offset,fpga_file,obs_set_id)
        #logger.info("ID: {}".format(obsid))
        #retval = getRMS(ant_dict,fpga_file) 
        retval = setRMS(ant_dict,fpga_file,rms) 
        print(str(retval))
    except:
        logger.exception('Top level test')
        raise
    finally:
        ata_control.release_antennas(ant_list, True)

