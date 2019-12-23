#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 2019

@author: jkulpa
"""

import numpy

def simple(vectorOn,vectorOff,guardAreaPercent = 0.1):
    """
    Simple method of calculation of Y-Factor
    
    the method neglects the outer guardAreaPercent band of the samples at low, 
    and the same amoutnt at high frequency.
        
    Parameters
    -------------
    vectorOn : array_like
        The spectrum vector from the "on" part of the measurements
    vectorOff : array_like
        The spectrum vector from the "off" part of the measurements
    guardAreaPercent : float
        percentage of outer band zeroing area
        
    Returns
    -------------
    float
        calculated Y-factor
        
    Raises
    -------------
        AssertionError     
    """  
    
    dataONLen = len(vectorOn);
    dataOFFLen = len(vectorOff);
    
    assert dataONLen == dataOFFLen, "two vectors must have the same size"
    assert guardAreaPercent <= 0.45, "guard area cannot exceed 2*45% of the data"
    
    guardSamplesOneSide = numpy.int(numpy.floor(guardAreaPercent * dataONLen))

    
    powerOn = numpy.sum(vectorOn[guardSamplesOneSide:dataONLen-guardSamplesOneSide],dtype=float)
    powerOff = numpy.sum(vectorOff[guardSamplesOneSide:dataONLen-guardSamplesOneSide],dtype=float)
    
    yFactor = powerOn/powerOff

    return yFactor
    
    

    
