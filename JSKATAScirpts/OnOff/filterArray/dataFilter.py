#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 3 2019

@author: jkulpa
"""

import simple
import MADSEFD

filterType = 'MADall'


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
    
    switcher = {
            'MAD': MADSEFD.MADSEFD,
            'MADall': MADSEFD.MADSEFDAll,
            'simple': simple.simple,
                }
    
    func = switcher.get(filterType)
    
    assert func is not None, "unknown filter call"
    
    onFiltered,offFiltered = func(onArray, offArray)
    
    return onFiltered,offFiltered
