#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 2019

@author: jkulpa
"""

import OnOff.misc
import numpy

import pdb

def simple(onArray, offArray):
    """
    a simple data filter for On and Off data set
    
    Parameters
    -------------
    onArray : array_like
        Data array for ON measurement
    offArray : array_like
        Data array for OFF measurement
        
    Returns
    -------------
    array_like
        filtered data for ON measurement, number of columns in each row may vary
    array_like
        filtered data for OFF measurement, number of columns in each row may vary
        
    Raises
    -------------
         AssertionError     
    """
    
    Larray = len(onArray)
    Larray2 = len(offArray)
    
    assert Larray == Larray2, "both arrays should have the same size"
    
    onFiltered = numpy.array(onArray)[:,OnOff.misc.constants.dataRange]
    offFiltered = numpy.array(offArray)[:,OnOff.misc.constants.dataRange]
    
    return onFiltered,offFiltered