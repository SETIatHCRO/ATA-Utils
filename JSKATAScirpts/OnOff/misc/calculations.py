#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 2019

@author: jkulpa
"""

import constants
import numpy


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