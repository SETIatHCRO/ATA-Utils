#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
file access on observator (obs) list

Created Feb 2020

@author: jkulpa
"""

from ATATools import logger_defaults
from . import obs_common
import pyuvdata
import glob
import os
import numpy

def getUVData(directory,datdictionary):
    '''
    searches the directory for a file that matches file pattern (recid and ant from datdictionary)
    returns pyuvdata object
    '''
    logger = logger_defaults.getModuleLogger(__name__)

    rec = datdictionary['recid']
    ant = datdictionary['ant']

    fnamepattern = os.path.expanduser(os.path.join(directory,'*_' + str(rec) + '_*_' + ant + '.h5'))
    fnamelist = glob.glob(fnamepattern)
    if len(fnamelist) != 1:
        logger.error('there is not exactly 1 file matching the pattern. Got {}'.format(fnamelist))
        raise RuntimeError('not 1 filename matching the patter')

    fname = fnamelist[0]

    UV = pyuvdata.UVData()
    UV.read_uvh5(fname)

    return UV

def checkIfWaterfall(dat,freq=None,ant=None):
    #is the data format right
    if not isinstance(dat,pyuvdata.uvdata.UVData):
        return False
    #data from only 1 antenna, all indexes equal and all uvw == 0
    cc = dat.Nants_data == 1 and all(dat.ant_1_array == dat.ant_2_array ) and not numpy.any(dat.uvw_array)
    if freq:
        cc = cc and dat.freq_array[0,0] <= freq and dat.freq_array[0,-1] >= freq 

    if ant:
        cc = cc and dat.antenna_names[dat.ant_1_array[0]] == ant

    return cc




