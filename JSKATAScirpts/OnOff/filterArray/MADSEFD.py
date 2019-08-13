#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 2019

@author: jkulpa
"""

import OnOff.misc
import numpy

import pdb

def MADSEFD(onArray, offArray):
    """
    a MAD based data filter for On and Off data set
    
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
    
    onFiltered = []
    offFiltered = []
    
    for iK in range(Larray):
        onVectSel = onArray[iK][OnOff.misc.constants.dataRange]
        offVectSel = offArray[iK][OnOff.misc.constants.dataRange]
        tmpVect = numpy.divide(offVectSel,(onVectSel - offVectSel),dtype='float')
    
        xMed = numpy.median(tmpVect);
        xMAD = numpy.median(numpy.abs(tmpVect - xMed))
    
        # extracting indexes of values in tmpVect being median +/- 3*MAD
        indexList = numpy.asarray( (tmpVect < (xMed + 1.48*xMAD)) * (tmpVect > (xMed - 1.48*xMAD)) ).nonzero()[0]
        
        onFiltered.append(onVectSel[indexList])
        offFiltered.append(offVectSel[indexList])
    
    return onFiltered,offFiltered

def MADSEFDAll(onArray, offArray):
    """
    a MAD based data filter for On and Off data set, index selection based on the whole array
    
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
    
    onSum = numpy.sum(numpy.array(onArray)[:,OnOff.misc.constants.dataRange],axis=0)
    offSum = numpy.sum(numpy.array(offArray)[:,OnOff.misc.constants.dataRange],axis=0)
    
    tmpVect = numpy.divide(offSum,(onSum - offSum),dtype='float')
    
    xMed = numpy.median(tmpVect);
    xMAD = numpy.median(numpy.abs(tmpVect - xMed))

    # extracting indexes of values in tmpVect being median +/- 3*MAD
    indexList = numpy.asarray( (tmpVect < (xMed + 3*xMAD)) * (tmpVect > (xMed - 3*xMAD)) ).nonzero()[0]
    
    #pdb.set_trace()
    
    onFiltered = []
    offFiltered = []
    
    for iK in range(Larray):
        onVectSel = onArray[iK][OnOff.misc.constants.dataRange]
        offVectSel = offArray[iK][OnOff.misc.constants.dataRange]
        
        onFiltered.append(onVectSel[indexList])
        offFiltered.append(offVectSel[indexList])
    
    return onFiltered,offFiltered