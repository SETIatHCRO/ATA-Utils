#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 3 2019

@author: jkulpa
"""

from . import simple,MADSEFD,ata_aoflag


def filterFun(onArray, offArray, method):
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
            'aoflagger': ata_aoflag.simple,
                }
    
    func = switcher.get(method)
    
    assert func is not None, "unknown filter call"
    
    maksedArray = func(onArray, offArray)
    
    return maksedArray
