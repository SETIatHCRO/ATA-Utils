#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Thu Jul 22 2019

@author: jkulpa
"""

import OnOffCalc.flux
import OnOffCalc.misc
import OnOffCalc.yFactor
import numpy

import pdb
import matplotlib.pyplot as plt

def calcSingleAnt(source, frequency, measdate, onArray, offArray):
    """
    Calculates system temperature based on On-Off data

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
    float
        std of system temp
        
    Raises
    -------------
        AssertionError     
    """    

    doDebug = 0

    flx = OnOffCalc.flux.sourceFlux(source,frequency,measdate)
    TSrc = OnOffCalc.misc.calcSourceTemp(flx)
    
    Larray = len(onArray)
    Larray2 = len(offArray)
    
    assert Larray == Larray2, "both arrays should have the same size"
    
    assert len(onArray[0]) == len(offArray[0]), "both arrays should have the same size"
    
    temps = numpy.zeros(Larray,dtype=float)
    
    
    for iK in range(Larray):
        cOn = onArray[iK]
        
        if doDebug:
            cOn[0] = 0.0
            plt.plot(cOn)
            plt.show()
        
        cOff = offArray[iK]
        
        if doDebug:
            cOff[0] = 0.0
            plt.plot(cOff)
            plt.show()
        
        #pdb.set_trace()
        yFac = OnOffCalc.yFactor.simple(cOn,cOff)
        temps[iK] = OnOffCalc.misc.calcAntennaTemp(yFac,TSrc)
        

    avgTemp = numpy.mean(temps)
    stdTemp = numpy.std(temps)

    if doDebug:    
        print(temps)
        #pdb.set_trace()
        
    return avgTemp,stdTemp
    
    
    
