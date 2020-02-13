#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 2019

@author: jkulpa
"""

from . import constants
import numpy
import OnOffCalc.filterArray

import pdb
import matplotlib.pyplot as plt

def getDatarange(veclen):
    if veclen == 2048:
        return numpy.array(range(constants.lowerval,constants.upperval))
    else:
        lv =  int(numpy.floor(constants.lowerval/2048.0*veclen))
        uv =  int(numpy.floor(constants.upperval/2048.0*veclen))
        return numpy.array(range(lv,uv))

def calcOnOffParamVec(onVectIn, offVectIn, maskedVect):
    """
    Calculation of vector of SFED values
        
    Parameters
    -------------
    onVect : array_like
        vector of On data
    offVect : array_like
        vector of Off data
        
    Returns
    -------------
    float
        the SEFD value
    float
        power on    
    float
        power off
        
    """   
    
    assert len(onVectIn) == len(offVectIn), "both vectors should have the same size"
    assert len(onVectIn) == len(maskedVect), "mask vector should have the same size as the others"
    
    
    onVect = onVectIn[maskedVect == 0]
    offVect = offVectIn[maskedVect == 0]
    
    #pdb.set_trace()
    
    tmpVect = numpy.divide(offVect,(onVect - offVect))

    onoffparam = numpy.median(tmpVect)

    #powOn = numpy.divide(numpy.sum(onVect),len(onVect))
    #powOff =  numpy.divide(numpy.sum(offVect),len(offVect))
    
    powOn  =  numpy.divide(numpy.sqrt(numpy.sum(numpy.square(onVect))),len(onVect))
    powOff = numpy.divide(numpy.sqrt(numpy.sum(numpy.square(offVect))),len(offVect))
    
    #plt.plot(tmpVect[indexList])
    #plt.show()
    return onoffparam,powOn,powOff

def calcSEFD(onArrayM, offArrayM, srcFlux, method=OnOffCalc.filterArray.defaultFilterType):
    """
    Calculation of SFED for signle frequency
        
    Parameters
    -------------
    onArray : array_like
        vector of On data
    offArray : array_like
        vector of Off data
    srcFlux : float
        flux of the source
        
    Returns
    -------------
    float
        SEFD value
    float
        SEFD variance in time
    array_like 
        On power in time
    array_like 
        On power in time
    array_like
        indexes used for calculation
           
    """
    
    maskedBinsArray = OnOffCalc.filterArray.filterFun(onArrayM,offArrayM,method)
    
    #plt.imshow(offArrayM[:,OnOffCalc.misc.constants.dataRange],aspect='auto', interpolation='none')
    #plt.show()
    #plt.clf()
    #plt.imshow(maskedBinsArray[:,OnOffCalc.misc.constants.dataRange],aspect='auto', interpolation='none')
    #plt.show()
    #numpy.sum(maskedBinsArray)
    #pdb.set_trace()
    
    Larray = len(onArrayM)
    
    SEFDs = numpy.zeros(Larray,dtype=float)
    powOn = numpy.zeros(Larray,dtype=float)
    powOff = numpy.zeros(Larray,dtype=float)
    
    for iK in range(Larray):
        SEFDs[iK],powOn[iK],powOff[iK] = calcOnOffParamVec(onArrayM[iK],offArrayM[iK],maskedBinsArray[iK])
        
    #normalization towars 0?
    mean_off = numpy.mean(powOff)
    powOn = powOn - mean_off
    powOff = powOff - mean_off

    SEFD = srcFlux * numpy.median(SEFDs)
    SEFD_var = srcFlux * numpy.std(SEFDs)
    
    #pdb.set_trace()
    
    return SEFD,SEFD_var,powOn,powOff,maskedBinsArray
    

def calcAntennaTemp(yFactor, TSrc, localTCold = constants.TCold):
    """
    Calculation of source temperature based on source flux and antenna size
        
    Parameters
    -------------
    yFactor : float
        Y-Factor based on On and Off power
    TSrc : float
        Astronomical source temperature
    localTCold : float
        Temperature of outer space. The default value is defined in OnOff.misc.contsants.TCold
        
    Returns
    -------------
    float
        Temperature of the antenna, in Kelvin
           
    """   
    
    if yFactor == 1:
        return numpy.inf
    
    numerator = (TSrc + localTCold ) - yFactor * localTCold 
    denominator = yFactor - 1;
    
    TAnt = numerator/denominator
    return TAnt
    

def calcSourceTemp(srcFlux):
    """
    Calculation of source temperature based on source flux and antenna size
    
    The function uses the antenna size defined in OnOff.misc.constants
    
    Parameters
    -------------
    srcFlux : float
        flux of the source
        
    Returns
    -------------
    float
        Temperature of the source, in Kelvin
           
    """   
    
    antennaEffArea = calcEffAntennaArea()
    
    TSrc = srcFlux * antennaEffArea / constants.kBoltzman * 1e-3;
    return TSrc
    


def calcEffAntennaArea():
    antennaEffArea = constants.antEff * numpy.pi * constants.antR * constants.antR;

    return antennaEffArea
