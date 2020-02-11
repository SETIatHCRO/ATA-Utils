#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
calculations of H5 on-off measurement sets for SEFD

Created Feb 2020

@author: jkulpa
"""

from optparse import OptionParser
import logging
import OnOffCalc
from SNAPobs import snap_dirs
from ATATools import logger_defaults
from ATAobs import obs_db,obs_list,obs_h5
import sys
import pyuvdata

def sortOnOff(cList):
    logger = logger_defaults.getModuleLogger(__name__)
    onList = []
    offList = []
    for cc in cList:
        #checking if both az and el is 0 (on source)
        if cc['az'] == 0.0 and cc['el'] == 0.0:
            onList.append(cc)
        else:
            offList.append(cc)

    #sorting by start time
    onList.sort(key=lambda sd: sd['tstart'])
    offList.sort(key=lambda sd: sd['tstart'])

    return onList,offList

def processSignleAntFreqSEFDfiles(datadir,cList,method,compareflag,uploadflag):
    logger = logger_defaults.getModuleLogger(__name__)

    cant = cList[0]['ant']
    cfreq = cList[0]['freq']
    #TODO: check if all data is from cant and cfreq

    onList,offList = sortOnOff(cList)
    onData=[]
    offData=[]
    for cdat in onList:
        try:
            cpyuv = obs_h5.getUVData(datadir,cdat)
            if (obs_h5.checkIfWaterfall(cpyuv,cfreq*1e6,cant)):
                onData.append(cpyuv)
            else:
                logger.warning('file {} does not seem to have h5 waterfall data'.format(cdat))
        except:
            logger.warning('unable to get the file corresponding to {}'.format(cdat))
            raise
            #pass
    for cdat in offList:
        try:
            cpyuv = obs_h5.getUVData(datadir,cdat)
            if (obs_h5.checkIfWaterfall(cpyuv,cfreq*1e6,cant)):
                offData.append(cpyuv)
            else:
                logger.warning('file {} does not seem to have h5 waterfall data'.format(cdat))
        except:
            logger.warning('unable to get the file corresponding to {}'.format(cdat))
            raise
            #pass

    if len(onData) != len(offData):
        logger.error('unable to get the same number of files for on and off observations ({} vs {})'.format( len(onData), len(offData)  ))
        raise RuntimeError("number of On files does not match number of Off files")

    import pdb
    pdb.set_trace()

def processSEFDfiles(datadir,rec_list,method=OnOffCalc.defaultFilterType,compareflag=False,uploadflag=False):
    logger = logger_defaults.getModuleLogger(__name__)

    if not len(rec_list):
        logger.error('Rec list is empty')
        raise RuntimeError('List is empty')

    retlist = []
    while(rec_list):
        cant = rec_list[0]['ant']
        cfreq = rec_list[0]['freq']
        cList,rec_list = obs_list.split_ant_recording_list(rec_list,[cfreq],[cant])
        #this part can be executed by calling in separate threads/processes
        try:
            rval = processSignleAntFreqSEFDfiles(datadir,cList,method,compareflag,uploadflag)
            retlist.append(rval)
        except Exception, e:
            logger.error("error while processing antena {} freq {} : {}".format(cant,cfreq,e))
            raise
            #pass

def main():
    # Define the argumants
    parser = OptionParser(usage= 'Usage %prog options',
                        description='process the observation set for On-Off observations'
                                    'calling:'
                                    '        %prog --all --upload --compare'
                                    'will process all data from latest on-off observation and create png comparision file')

    parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
            help ="More on-screen information")
    parser.add_option('-f','--freqs',dest='freqs', type=str, action="store", default=None,
            help ='Comma separated list of sky tuning frequencies, in MHz. Only one set of frequencies, eg: \"2000,3000,4000\. If none, all frequencies will be processed"')
    parser.add_option('-a','--ants', dest='ants', type=str, action="store", default=None,
            help ='Comma separated array list of ATA antennas, eg: \"2j,2d,4k\". If none, all antennas will be processed')
    parser.add_option('--all', dest='all', action="store_true", default=False,
            help ="Process all avaliable antennas and frequencies")
    parser.add_option('-l','--list', dest='do_list', action="store_true", default=False,
            help ="List avaliable antenna and frequencies. Then exit.")
    parser.add_option('-i', dest='obs_set', type=int, action="store", default=None,
            help ='Observation set ID. If not present, the last on-off measurement set will be processed')
    #probably should add a -d, --dir option to specify the dir directly. Different way of file fetching would be necessary. 
    parser.add_option('-u', '--upload', dest='upload', action="store_true", default=False,
            help ="Create and upload images")
    parser.add_option('-c', '--compare', dest='compare', action="store_true", default=False,
            help ="Make comparison between choosen/default method and 'simple' method")
    parser.add_option('-m', '--method', dest='method', type=str, action="store", default=OnOffCalc.defaultFilterType,
            help ='method to be used in rfi rejection. Possible methods: \"{}\"'.format('\", \"'.join( OnOffCalc.filterTypes )))
    
    
    (options,args) = parser.parse_args()

    if(options.verbose):
        logger = logger_defaults.getProgramLogger("ON_OFF_CALC",loglevel=logging.INFO)
    else:
        logger = logger_defaults.getProgramLogger("ON_OFF_CALC",loglevel=logging.WARNING)

    if (len(sys.argv) <= 1):
        logger.warning("no options provided")
        parser.print_help()
        sys.exit(1)

    #TODO: probably the whole next section should be conditional
    #and the directory-related way of creating rec_list should
    #be implemented
    if options.obs_set:
        try:
            obs_set_id = options.obs_set
            obs_db.getSetData(obs_set_id)
        except:
            logger.error("Data set id {} does not exist".format(obs_set_id))
            sys.exit(1)
    else:
        obs_set_id = obs_db.getLatestSetID("ON-OFF")

    if options.all and (options.ants or options.freqs):
        logger.error("option --all cannot be specified together with --ants or --freqs")
        sys.exit(1)

    if options.freqs:
        freq_filter = map(float,options.freqs.split(','))
    else:
        freq_filter = None
    if options.ants:
        ant_filter = options.ants.split(',')
    else:
        ant_filter = None

    rec_list = obs_db.getAntRecordings(obs_set_id)
    rec_list = obs_list.filter_ant_recording_list(rec_list,"ON-OFF",freq_filter,ant_filter)

    if options.do_list:
        obs_list.print_ant_recording_list(rec_list,headers=None)
        sys.exit(1)

    method = options.method
    compareflag = options.compare
    uploadflag = options.upload

    datadir = snap_dirs.get_dir_obsid(obs_set_id)

    logger.info('processing {} data files'.format(len(rec_list)))
    processSEFDfiles(datadir,rec_list,method,compareflag,uploadflag)

if __name__== "__main__":
    main()

