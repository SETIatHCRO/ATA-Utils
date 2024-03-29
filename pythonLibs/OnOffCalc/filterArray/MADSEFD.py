#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 2019

@author: jkulpa
"""

import OnOffCalc.misc
import numpy

import pdb

MADMultiplier = 1.48

def MADSEFD(onArray, offArray):
    """
    a MAD based data filter for On and Off data set
    
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
    
    #onFiltered = []
    #offFiltered = []
    drange = OnOffCalc.misc.getDatarange(onArray.shape[1])
    dataMask = numpy.ones(onArray.shape)
    
    for iK in range(Larray):
        onVectSel = onArray[iK,drange]
        offVectSel = offArray[iK,drange]
        tmpVect = numpy.divide(offVectSel,(onVectSel - offVectSel),dtype='float')
    
        xMed = numpy.median(tmpVect);
        xMAD = numpy.median(numpy.abs(tmpVect - xMed))
    
        # extracting indexes of values in tmpVect being median +/- 3*MAD
        indexList = numpy.asarray( (tmpVect < (xMed + MADMultiplier*xMAD)) * (tmpVect > (xMed - MADMultiplier*xMAD)) ).nonzero()[0]
        
        #onFiltered.append(onVectSel[indexList])
        #offFiltered.append(offVectSel[indexList])
        
        #uniqueIdList = list(set(uniqueIdList.append(indexList)))
        dataMask[iK,drange[indexList]] = 0
    
    #return onFiltered,offFiltered,OnOff.misc.constants.dataRange[uniqueIdList]
    return dataMask

def MADSEFDAll(onArray, offArray):
    """
    a MAD based data filter for On and Off data set, index selection based on the whole array
    
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
    
    drange = OnOffCalc.misc.getDatarange(onArray.shape[1])
    dataMask = numpy.ones(onArray.shape)
    
    onSum = numpy.sum(onArray[:,drange],axis=0)
    offSum = numpy.sum(offArray[:,drange],axis=0)
    
    tmpVect = numpy.divide(offSum,(onSum - offSum),dtype='float')
    
    xMed = numpy.median(tmpVect);
    xMAD = numpy.median(numpy.abs(tmpVect - xMed))

    # extracting indexes of values in tmpVect being median +/- 3*MAD
    indexList = numpy.asarray( (tmpVect < (xMed + MADMultiplier*xMAD)) * (tmpVect > (xMed - MADMultiplier*xMAD)) ).nonzero()[0]
    
    dataMask[:,drange[indexList]] = 0
    
    #pdb.set_trace()
    
    #onFiltered = []
    #offFiltered = []
    
    #for iK in range(Larray):
    #    onVectSel = onArray[iK][OnOff.misc.constants.dataRange]
    #    offVectSel = offArray[iK][OnOff.misc.constants.dataRange]
        
    #    onFiltered.append(onVectSel[indexList])
    #    offFiltered.append(offVectSel[indexList])
    
    #pdb.set_trace()
    
    #return onFiltered,offFiltered,OnOff.misc.constants.dataRange[indexList]
    return dataMask
