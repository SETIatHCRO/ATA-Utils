#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Thu Jul 31 2019

@author: jkulpa
"""

import OnOff.flux
import OnOff.misc
import numpy
import datetime

import pdb
import matplotlib.pyplot as plt

def calcSEFDThreeDict(Dict0On, Dict0Off,Dict1On, Dict1Off,Dict2On, Dict2Off):
    """
    Calculates system SEFD based on On-Off data for 3 consecutive measurements

    averages the measurements (assuming ergodicity)

    Parameters
    -------------
    Dict0On : dict
        dictionary containing 000 On data
    Dict0Off : dict
        dictionary containing 000 Off data
    Dict1On : dict
        dictionary containing 001 On data
    Dict1Off : dict
        dictionary containing 001 Off data
    Dict2On : dict
        dictionary containing 002 On data
    Dict2Off : dict
        dictionary containing 002 Off data
        
    Returns
    -------------
    array_like
        SEFD X in Jy, for all 3 measurements
    array_like
        SEFD_var X in Jy, for all 3 measurements        
    array_like
        SEFD Y in Jy, for all 3 measurements
    array_like
        SEFD_var Y in Jy, for all 3 measurements   
    array_like
        time vector for power
    array_like
        power for X meas
    array_like
        power for Y meas
        
    Raises
    -------------
        AssertionError     
    """    

    len00 = len(Dict0On['auto0'])
    len01 = len(Dict0On['auto1'])

    len10 = len(Dict1On['auto0'])
    len11 = len(Dict1On['auto1'])
    
    len20 = len(Dict2On['auto0'])
    len21 = len(Dict2On['auto1'])

    assert len00 == len01, "array size mismatch"
    assert len00 == len(Dict0Off['auto0']), "array size mismatch"
    assert len00 == len(Dict0Off['auto1']), "array size mismatch"

    assert len10 == len11, "array size mismatch"
    assert len10 == len(Dict1Off['auto0']), "array size mismatch"
    assert len10 == len(Dict1Off['auto1']), "array size mismatch"

    assert len20 == len21, "array size mismatch"
    assert len20 == len(Dict2Off['auto0']), "array size mismatch"
    assert len20 == len(Dict2Off['auto1']), "array size mismatch"

    #we assume that the flux does not change that rapidly
    meastime = int(Dict0On['auto0_timestamp'][0])
    datetime_stamp = datetime.datetime.utcfromtimestamp(meastime) 
    
    
    freq=Dict0On['rfc']    
    assert freq == Dict0Off['rfc'], "freq mismatch"
    assert freq == Dict1On['rfc'], "freq mismatch"
    assert freq == Dict1Off['rfc'], "freq mismatch"
    assert freq == Dict2On['rfc'], "freq mismatch"
    assert freq == Dict2Off['rfc'], "freq mismatch"

    source= Dict0On['source']
    assert source == Dict0Off['source'], "source mismatch"
    assert source == Dict1On['source'], "source mismatch"
    assert source == Dict1Off['source'], "source mismatch"
    assert source == Dict2On['source'], "source mismatch"
    assert source == Dict2Off['source'], "source mismatch"
    
    assert Dict0On['auto0_timestamp'] == Dict0On['auto1_timestamp'], "timestamp error"
    assert Dict0Off['auto0_timestamp'] == Dict0Off['auto1_timestamp'], "timestamp error"
    assert Dict1On['auto0_timestamp'] == Dict1On['auto1_timestamp'], "timestamp error"
    assert Dict1Off['auto0_timestamp'] == Dict1Off['auto1_timestamp'], "timestamp error"
    assert Dict2On['auto0_timestamp'] == Dict2On['auto1_timestamp'], "timestamp error"
    assert Dict2Off['auto0_timestamp'] == Dict2Off['auto1_timestamp'], "timestamp error"

    #calculating flux based on the time. If needed, various timestamps may be used
    flx = OnOff.flux.sourceFlux(source,freq,datetime_stamp)
    
    SEFD_X = numpy.zeros(3,dtype='float')
    SEFD_var_X = numpy.zeros(3,dtype='float')
    SEFD_Y = numpy.zeros(3,dtype='float')
    SEFD_var_Y = numpy.zeros(3,dtype='float')
    
    SEFD_X[0],SEFD_var_X[0],powOn0X,powOff0X = OnOff.misc.calcSEFD(Dict0On['auto0'],Dict0Off['auto0'],flx)
    SEFD_X[1],SEFD_var_X[1],powOn1X,powOff1X = OnOff.misc.calcSEFD(Dict1On['auto0'],Dict1Off['auto0'],flx)
    SEFD_X[2],SEFD_var_X[2],powOn2X,powOff2X = OnOff.misc.calcSEFD(Dict2On['auto0'],Dict2Off['auto0'],flx)
    
    SEFD_Y[0],SEFD_var_Y[0],powOn0Y,powOff0Y = OnOff.misc.calcSEFD(Dict0On['auto1'],Dict0Off['auto1'],flx)
    SEFD_Y[1],SEFD_var_Y[1],powOn1Y,powOff1Y = OnOff.misc.calcSEFD(Dict1On['auto1'],Dict1Off['auto1'],flx)
    SEFD_Y[2],SEFD_var_Y[2],powOn2Y,powOff2Y = OnOff.misc.calcSEFD(Dict2On['auto1'],Dict2Off['auto1'],flx)
    
    powerX = numpy.concatenate( (powOn0X,powOff0X,powOn1X,powOff1X,powOn2X,powOff2X) )
    powerY = numpy.concatenate( (powOn0Y,powOff0Y,powOn1Y,powOff1Y,powOn2Y,powOff2Y) )

    timeStamps = numpy.concatenate( (Dict0On['auto0_timestamp'],Dict0Off['auto0_timestamp'],Dict1On['auto0_timestamp'],Dict1Off['auto0_timestamp'],Dict2On['auto0_timestamp'],Dict2Off['auto0_timestamp']) )
 
    #pdb.set_trace()
    
    return SEFD_X,SEFD_var_X,SEFD_Y,SEFD_var_Y,timeStamps,powerX,powerY