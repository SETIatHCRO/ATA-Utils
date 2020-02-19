#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calculation of SEFD using pyuvdata UVData
Created on Feb 2020

@author: jkulpa
"""

import OnOffCalc.flux
import OnOffCalc.misc
import numpy
from astropy.time import Time
import datetime

def calcSEFDpyuv(onList, offList, method, updateFlags=False):
    """

    Parameters
    -------------
    onList : list
        list of UVData objects for "on" measurements
    offList : list
        list of UVData objects for "off" measurements
    method : str
        string describing the method See OnOffCalc.filterArray.filterTypes
    updateFlags : bool

    Returns
    -------------
    dict : 
        dictionary with calculated results
    """

    nTries = len(onList)
    assert(nTries > 0), "empty list"
    assert(len(onList) == len(offList)), "list len mismatch"

    freqLen = onList[0].Nfreqs
    freq = onList[0].freq_array[0,freqLen//2]/1e6
    source = onList[0].object_name

    datetime_stamp = datetime.datetime.utcfromtimestamp(Time(onList[0].time_array[0],format='mjd').unix)

    flx = OnOffCalc.flux.sourceFlux(source,freq,datetime_stamp)
        
    SEFD_X = numpy.zeros(nTries,dtype='float')
    SEFD_var_X = numpy.zeros(nTries,dtype='float')
    SEFD_Y = numpy.zeros(nTries,dtype='float')
    SEFD_var_Y = numpy.zeros(nTries,dtype='float')
    SEFD_ts = [] 
    powerX = numpy.zeros(0,dtype='float')
    powerY = numpy.zeros(0,dtype='float')
    sefd_vec_X = numpy.zeros(0,dtype='float')
    sefd_vec_Y = numpy.zeros(0,dtype='float')
    timestamps = numpy.zeros(0,dtype='float')

    for nn in range(nTries):
        SEFD_X[nn],SEFD_var_X[nn],powOn0X,powOff0X,indexesX,sefdvx = OnOffCalc.misc.calcSEFD(onList[nn].data_array[:,0,:,0].real, offList[nn].data_array[:,0,:,0].real,flx,method)
        SEFD_Y[nn],SEFD_var_Y[nn],powOn0Y,powOff0Y,indexesY,sefdvy = OnOffCalc.misc.calcSEFD(onList[nn].data_array[:,0,:,1].real, offList[nn].data_array[:,0,:,1].real,flx,method)
        SEFD_ts.append( datetime.datetime.utcfromtimestamp(Time(onList[nn].time_array[0],format='mjd').unix) )

        powerX = numpy.concatenate( (powerX,powOn0X,powOff0X) )
        powerY = numpy.concatenate( (powerY,powOn0Y,powOff0Y) )
        sefd_vec_X = numpy.concatenate( (sefd_vec_X,sefdvx) )
        sefd_vec_Y = numpy.concatenate( (sefd_vec_Y,sefdvy) )
        timestamps = numpy.concatenate( (timestamps,onList[nn].time_array,offList[nn].time_array) )

        if updateFlags:
            onList[nn].flag_array[:,0,:,0] = indexesX
            offList[nn].flag_array[:,0,:,0] = indexesX
            onList[nn].flag_array[:,0,:,1] = indexesY
            offList[nn].flag_array[:,0,:,1] = indexesY


    #import pdb
    #pdb.set_trace()
    return {'sefd_x' : SEFD_X, 'sefd_y' : SEFD_Y, 'sefd_x_var': SEFD_var_X, 'sefd_y_var': SEFD_var_Y, 'sefd_ts': SEFD_ts, 'power_x': powerX, 'power_y': powerY, 'ts': timestamps, 'source':source, 'sefd_vec_x':sefd_vec_X, 'sefd_vec_y': sefd_vec_Y}

