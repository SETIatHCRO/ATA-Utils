#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 2019

@author: jkulpa
"""

import OnOffCalc.misc
import numpy

import pdb

def simple(onArray, offArray):
    """
    a simple data filter for On and Off data set
    
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
    
    Larray = len(onArray)
    Larray2 = len(offArray)
    
    assert Larray == Larray2, "both arrays should have the same size"
    
    #onFiltered = numpy.array(onArray)[:,OnOff.misc.constants.dataRange]
    #offFiltered = numpy.array(offArray)[:,OnOff.misc.constants.dataRange]
    
    #return onFiltered,offFiltered,OnOff.misc.constants.dataRange
    
    dataMask = numpy.ones(onArray.shape)
    dataMask[:,OnOffCalc.misc.constants.dataRange] = 0
    
    return dataMask
    
