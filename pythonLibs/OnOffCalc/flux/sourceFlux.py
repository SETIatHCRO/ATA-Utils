#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 2019

@author: jkulpa
"""

import casaFlux
import moonFlux
import datetime
import pdb

def sourceFlux(source,freqMHz,date):
    """
    a flux calculation of astronomical source

    Parameters
    -------------
    source : string
        indication of a source name. Currently implemented: casa, moon
    freqMHz : float
        center frequency in MHz used for calculation
    date : datetime
        the date of the mearusements
        
    Returns
    -------------
    float
        flux in Jy of the object
        
    Raises
    -------------
        AssertionError     
    """    
        
    switcher = {
            'casa': casaFlux.casaFlux,
            'Casa': casaFlux.casaFlux,
            'moon': moonFlux.moonFlux,
            'Moon': moonFlux.moonFlux
                }
    
    func = switcher.get(source)
    
    assert func is not None, "unknown source"
    
    """this is approximation, but should be sufficient"""
    yearFrac = float(date.year) + float(date.month)/12 + float(date.day)/(30*12)
    
    #pdb.set_trace()
    
    
    
    flux = func(freqMHz,yearFrac)
    return flux
