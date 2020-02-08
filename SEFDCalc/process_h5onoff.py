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
from ATATools import obs_db
import sys

def main():
    # Define the argumants
    parser = OptionParser(usage= 'Usage %prog options',
                        description='process the observation set for On-Off observations'
                                    'calling:'
                                    '        %prog --all --upload --compare'
                                    'will process all data from latest on-off observation and create png comparision file')

    parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
            help ="More on-screen information")
    parser.add_option('-f', dest='freqs', type=str, action="store", default=None,
            help ='Comma separated list of sky tuning frequencies, in MHz. Only one set of frequencies, eg: \"2000,3000,4000\. If none, all frequencies will be processed"')
    parser.add_option('-a', dest='ants', type=str, action="store", default=None,
            help ='Comma separated array list of ATA antennas, eg: \"2j,2d,4k\". If none, all antennas will be processed')
    parser.add_option('--all', dest='all', action="store_true", default=False,
            help ="Process all avaliable antennas and frequencies")
    parser.add_option('-l','--list', dest='do_list', action="store_true", default=False,
            help ="List avaliable antenna and frequencies. Then exit. Ignores -a and -f flags")
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

if __name__== "__main__":
    main()

