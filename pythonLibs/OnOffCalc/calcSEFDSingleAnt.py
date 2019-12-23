#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Thu Jul 22 2019

@author: jkulpa
"""

import OnOff.flux
import OnOff.misc
import numpy

import pdb
import matplotlib.pyplot as plt

def calcSEFDSingleAnt(source, frequency, measdate, onArray, offArray):
    """
    Calculates system SEFD based on On-Off data

    averages the measurements (assuming ergodicity)

    Parameters
    -------------
    source : string
        indication of a source name
    frequency : float
        center frequency in MHz of the measurement
    measdate : datetime
        the date of the mearusements
    onArray : list
        the list of the arrays with On data
    offArray : list
        the list of the arrays with Off data
        
    Returns
    -------------
    float
        SEFD in Jy
        
    Raises
    -------------
        AssertionError     
    """    

    flx = OnOff.flux.sourceFlux(source,frequency,measdate)
    
    SEFD,SEFD_var = OnOff.misc.calcSEFD(onArray,offArray,flx)
    
    return SEFD,SEFD_var
