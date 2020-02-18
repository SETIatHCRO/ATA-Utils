#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 2019

@author: jkulpa
"""

import OnOffCalc.misc
import numpy
import os

aof_default_stategy = os.path.expanduser('~/aoflagger/aoflagger-code/teststrategies/default-2.14.0.rfis')

def simple(onArray, offArray):
    """
    simple approach to aoflagger
    
    Parameters
    -------------
    onArray : numpy.array
        Data array for ON measurement
    offArray : numpy.array
        Data array for OFF measurement
        
    Returns
    -------------
    numpy.array
        mask of invalid frequency bins (contaminated by RFI)
        
    Raises
    -------------
         AssertionError     
    """
    
    import aoflagger as aof

    drange = OnOffCalc.misc.getDatarange(onArray.shape[1])
    dataMask = numpy.ones(onArray.shape)
    
    validfreq = len(drange)
    validtimes = onArray.shape[0]

    onData = numpy.zeros([validfreq,validtimes],dtype=numpy.float64)
    offData = numpy.zeros([validfreq,validtimes],dtype=numpy.float64)

    onData[:,:] = numpy.transpose(onArray[:,drange])
    offData[:,:] = numpy.transpose(offArray[:,drange])

    aoflagger = aof.AOFlagger()
    strategy = aoflagger.load_strategy(aof_default_stategy)

    data = aoflagger.make_image_set(validtimes, validfreq, 2)
    data.set_image_buffer(0, onData)
    data.set_image_buffer(1, offData)
    
    flags = aoflagger.run(strategy, data)
    flagvalues = flags.get_buffer()

    dataMask[:,drange] = numpy.transpose(flagvalues)
    
    #return onFiltered,offFiltered,OnOff.misc.constants.dataRange[uniqueIdList]
    return dataMask

