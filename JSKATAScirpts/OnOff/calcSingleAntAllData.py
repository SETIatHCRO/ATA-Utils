#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Thu Jul 22 2019

@author: jkulpa
"""

import OnOff.flux
import OnOff.misc
import OnOff.yFactor
import numpy

import pdb
import matplotlib.pyplot as plt

def calcSingleAntAllData(source, frequency, measdate, onArray, offArray):
    """
    Calculates system temperature based on On-Off data

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
        sytem temp in Kelvin
        
    Raises
    -------------
        AssertionError     
    """    

    doDebug = 1

    flx = OnOff.flux.sourceFlux(source,frequency,measdate)
    TSrc = OnOff.misc.calcSourceTemp(flx)
    
    Larray = len(onArray)
    Larray2 = len(offArray)
    
    assert Larray == Larray2, "both arrays should have the same size"
    
    assert len(onArray[0]) == len(offArray[0]), "both arrays should have the same size"
    
    #temps = numpy.zeros(Larray,dtype=float)
    
    cOn = numpy.sum(onArray,axis=0,dtype='float')

    #pdb.set_trace()
        
    if doDebug:
        cOn[0] = 0.0
        plt.plot(cOn)
        plt.show()
        
    cOff = numpy.sum(offArray,axis=0,dtype='float')
        
    if doDebug:
        cOff[0] = 0.0
        plt.plot(cOff)
        plt.show()
        

    yFac = OnOff.yFactor.simple(cOn,cOff)
    temp = OnOff.misc.calcAntennaTemp(yFac,TSrc)
        

    if doDebug:    
        print(temp)
        #pdb.set_trace()
        
    return temp
    
    
    