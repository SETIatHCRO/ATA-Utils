#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
calculations of H5 on-off measurement sets for SEFD

Created Feb 2020

@author: jkulpa
"""

import sefd_graphs
from optparse import OptionParser
import logging
import OnOffCalc
from SNAPobs import snap_dirs
from ATATools import logger_defaults
from ATAobs import obs_db,obs_list,obs_h5
import sys
import pyuvdata
import numpy
import sefd_db

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

def processSignleAntFreqSEFDfiles(datadir,cList,method,compareflag,uploadflag,dbflag):
    logger = logger_defaults.getModuleLogger(__name__)

    cant = cList[0]['ant']
    cfreq = cList[0]['freq']
    csetid = cList[0]['setid']
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

    if compareflag:
        retsimple = OnOffCalc.calcSEFDpyuv(onData, offData, 'simple', updateFlags=False)
        retsimple['ant'] = cant
        retsimple['freq'] = cfreq
        retsimple['setid'] = csetid
        retsimple['method'] = 'simple'
    else:
        retsimple = None

    ret = OnOffCalc.calcSEFDpyuv(onData, offData, method, updateFlags=True)
    ret['ant'] = cant
    ret['freq'] = cfreq
    ret['setid'] = csetid
    ret['method'] = method

    if dbflag:
        sefd_db.insertSEFDs(cant,cfreq,csetid,method,ret['sefd_ts'],ret['sefd_x'],ret['sefd_x_var'],ret['sefd_y'],ret['sefd_y_var'])

        if compareflag:
            sefd_db.insertSEFDs(cant,cfreq,csetid,'simple',retsimple['sefd_ts'],retsimple['sefd_x'],retsimple['sefd_x_var'],retsimple['sefd_y'],retsimple['sefd_y_var'])

    if uploadflag:
        imgdir = snap_dirs.get_imgdir_obsid(csetid)
        powerplotnames,spectrogramplotnames = sefd_graphs.genImages(onData, offData, ret, comparedict=retsimple, upload=True, genspectrograms=True, directory=imgdir)
        ret['powerplots'] = powerplotnames
        ret['specplots'] = spectrogramplotnames
    else:
        ret['powerplots'] = None
        ret['specplots'] = None

    #{'sefd_x', 'sefd_y', 'sefd_x_var', 'sefd_y_var','sefd_ts', 'power_x', 'power_y', 'ts', 'source','ant','freq','setid','powerplots','specplots','method'}
    return ret

def processSEFDfiles(datadir,rec_list,method=OnOffCalc.defaultFilterType,compareflag=False,uploadflag=False, dbflag = True):
    import concurrent.futures
    logger = logger_defaults.getModuleLogger(__name__)

    if not len(rec_list):
        logger.error('Rec list is empty')
        raise RuntimeError('List is empty')

    retlist = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        threads = []
        while(rec_list):
            cant = rec_list[0]['ant']
            cfreq = rec_list[0]['freq']
            cList,rec_list = obs_list.split_ant_recording_list(rec_list,[cfreq],[cant])
            #this part can be executed by calling in separate threads/processes
            t = executor.submit(processSignleAntFreqSEFDfiles,datadir,cList,method,compareflag,uploadflag,dbflag)
            threads.append(t)


        for t in concurrent.futures.as_completed(threads):
            try:
                rval = t.result()
                #preparation for multicore
                cant = rval['ant']
                cfreq = rval['freq']
                #if this is the first freq for that antenna
                if cant not in retlist:
                    retlist[cant] = {}
                if cfreq in retlist[cant]:
                    logger.warning("for some reason, we already have a data in {}:{}".format(cant,cfreq))
                retlist[cant][cfreq] = rval
                
            except Exception as e:
                logger.error("error while processing antena {} freq {} : {}".format(cant,cfreq,e))
                raise
                #pass
    
    if uploadflag:
        sefd_graphs.makeHtml(retlist)
        sefd_graphs.makeJson(retlist)

    return retlist

def processSEFDfiles_single(datadir,rec_list,method=OnOffCalc.defaultFilterType,compareflag=False,uploadflag=False, dbflag = True):
    logger = logger_defaults.getModuleLogger(__name__)

    if not len(rec_list):
        logger.error('Rec list is empty')
        raise RuntimeError('List is empty')

    retlist = {}
    while(rec_list):
        cant = rec_list[0]['ant']
        cfreq = rec_list[0]['freq']
        cList,rec_list = obs_list.split_ant_recording_list(rec_list,[cfreq],[cant])
        #this part can be executed by calling in separate threads/processes
        try:
            rval = processSignleAntFreqSEFDfiles(datadir,cList,method,compareflag,uploadflag,dbflag)
            #preparation for multicore
            cant = rval['ant']
            cfreq = rval['freq']
            #if this is the first freq for that antenna
            if cant not in retlist:
                retlist[cant] = {}
            if cfreq in retlist[cant]:
                logger.warning("for some reason, we already have a data in {}:{}".format(cant,cfreq))
            retlist[cant][cfreq] = rval
            
        except Exception as e:
            logger.error("error while processing antena {} freq {} : {}".format(cant,cfreq,e))
            raise
            #pass
    
    if uploadflag:
        sefd_graphs.makeHtml(retlist)
        sefd_graphs.makeJson(retlist)

    return retlist

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
    dbflag = True

    datadir = snap_dirs.get_dir_obsid(obs_set_id)

    logger.info('processing {} data files'.format(len(rec_list)))
    processSEFDfiles(datadir,rec_list,method,compareflag,uploadflag,dbflag)

if __name__== "__main__":
    main()

