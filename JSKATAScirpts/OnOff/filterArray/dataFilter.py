#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 3 2019

@author: jkulpa
"""

import simple
import MADSEFD


filterType = 'MADall'
doUseCFAR = True

def useCFAR(val):
    global doUseCFAR
    doUseCFAR = val

def setSimple():
    """
    Sets filter type to simple filter
    """
    global filterType
    filterType = 'simple'

def setMADall():
    """
    Sets filter type to MADall filter
    """
    global filterType
    filterType = 'MADall'

def setMAD():
    """
    Sets filter type to MADall filter
    """
    global filterType
    filterType = 'MAD'
    
def getFilterType():
    """
    returns the string corresponding to current filter used
    """
    
    return filterType

def filterFun(onArray, offArray):
    """
    Filter choosing function - based on filterType, it will run given filter function
    Defatult is MADSEFDAll
    
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
    
    switcher = {
            'MAD': MADSEFD.MADSEFD,
            'MADall': MADSEFD.MADSEFDAll,
            'simple': simple.simple,
                }
    
    func = switcher.get(filterType)
    
    assert func is not None, "unknown filter call"
    
    maksedArray = func(onArray, offArray)
    
    return maksedArray
