#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
operations on observator (obs) list

Created Feb 2020

@author: jkulpa
"""

from ATATools import logger_defaults
from . import obs_common

def print_ant_recording_list(rec_list,headers=None,printHeaderNames=True):
    """
    Print the content of recordingAntennaList(rec_list)
    if headers=None, prints all fields
    if printHeaderNames is true, prints the first line with header description
    """

    logger= logger_defaults.getModuleLogger(__name__)

    avalHeaders = 'setid,recid,ant,freq,description,tstart,tstop,type,source,az,el'
    if not headers:
        htoprint = avalHeaders.split(',')
    else:
        htoprint = headers.split(',')

    if printHeaderNames:
        print('\t'.join(htoprint))

    for crow in rec_list:
        slist = []
        for cheader in htoprint:
            if cheader == 'setid':
                slist.append('{0:d}'.format(crow['setid']))
            elif cheader == 'recid': 
                slist.append('{0:d}'.format(crow['recid']))
            elif cheader == 'ant':
                slist.append('{0:s}'.format(crow['ant']))
            elif cheader == 'freq': 
                slist.append('{0:.2f}'.format(crow['freq']))
            elif cheader == 'description':
                slist.append('{0:s}'.format(crow['desc']))
            elif cheader == 'tstart':
                slist.append('{}'.format(crow['tstart']))
            elif cheader == 'tstop':
                slist.append('{}'.format(crow['tstop']))
            elif cheader == 'type':
                slist.append('{0:s}'.format(crow['type']))
            elif cheader == 'source':
                slist.append('{0:s}'.format(crow['source']))
            elif cheader == 'az':
                slist.append('{0:.2f}'.format(crow['az']))
            elif cheader == 'el':
                slist.append('{0:.2f}'.format(crow['el']))
            else:
                logger.error('unknown header') 
                raise KeyError('unknown header')

        print('\t'.join(slist))

        
def filter_ant_recording_list(rec_list,r_type,freq_filter=None,ant_filter=None):
    """
    Filters rec_list and creates a new list with copied entities. Only copies the
    rows that matches r_type. 
    optionally, filters by antennas and frequencies
    """
    
    logger= logger_defaults.getModuleLogger(__name__)

    prop_r_type = obs_common.getRecType(r_type)
    
    retList = []


    if not freq_filter and not ant_filter:
        #filtering just types
        logger.info('filtering for {}'.format(prop_r_type))
        for row in rec_list:
            if row['type'] == prop_r_type:
                retList.append(row)

        return retList

    elif not freq_filter:
        #filtering types and antennas
        logger.info('filtering for {}, antennas {}'.format(prop_r_type,','.join(ant_filter)))
        for row in rec_list:
            if row['type'] == prop_r_type and row['ant'] in ant_filter:
                retList.append(row)

        return retList

    elif not ant_filter:
        #filtering types and frequencies
        logger.info('filtering for {}, freqs {}'.format(prop_r_type,','.join(map(str,freq_filter))))
        for row in rec_list:
            if row['type'] == prop_r_type and row['freq'] in freq_filter:
                retList.append(row)

        return retList

    else:
        logger.info('filtering for {}, antennas {}, freqs {}'.format(prop_r_type, ','.join(ant_filter), ','.join(map(str,freq_filter))))
        for row in rec_list:
            if row['type'] == prop_r_type and row['freq'] in freq_filter and row['ant'] in ant_filter:
                retList.append(row)

        return retList

    logger.error("something went wrong?")
    raise RuntimeError('this part shouldn\'t be reachable')

def split_ant_recording_list(rec_list,freq_filter=None,ant_filter=None):
    """
    Filters rec_list and creates a new list with copied entities. 
    First list is created by matching antennas, frequencies or both. 
    Second list is what remains
    
    Returns
    -------------
        list (of dictionaries)
            list of 'matching' entries
        list (of dictionaries)
            list of 'remaining' entries

    
    """
    
    logger= logger_defaults.getModuleLogger(__name__)

    retList = []
    retOther = []

    if not freq_filter and not ant_filter:
        logger.error('at least one filter must be provided')
        raise RuntimeError('at least one filter must be non-empty') 

    elif not freq_filter:
        #filtering antennas
        logger.info('filtering antennas {}'.format(','.join(ant_filter)))
        for row in rec_list:
            if row['ant'] in ant_filter:
                retList.append(row)
            else:
                retOther.append(row)

        return retList,retOther

    elif not ant_filter:
        #filtering frequencies
        logger.info('filtering freqs {}'.format(','.join(map(str,freq_filter))))
        for row in rec_list:
            if row['freq'] in freq_filter:
                retList.append(row)
            else:
                retOther.append(row)

        return retList,retOther

    else:
        logger.info('filtering  antennas {}, freqs {}'.format(','.join(ant_filter), ','.join(map(str,freq_filter))))
        for row in rec_list:
            if row['freq'] in freq_filter and row['ant'] in ant_filter:
                retList.append(row)
            else:
                retOther.append(row)

        return retList,retOther

    logger.error("something went wrong?")
    raise RuntimeError('this part shouldn\'t be reachable')
