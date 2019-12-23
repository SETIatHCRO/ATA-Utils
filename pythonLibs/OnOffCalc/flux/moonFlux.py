#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 2019

@author: jkulpa
"""

#import numpy

def moonFlux(freqMHz,date):
    """
    a flux calculation of a moon
    
        Parameters
    -------------
    freqMHz : float
        center frequency in MHz used for calculation
    date : float
        the date of the mearusements (in fractional year e.g. 2019.21)
        
    Returns
    -------------
    float
        flux in Jy of the object
           
    Raises
    -------------
        
    """
    
    """Based on Jon's code"""
    flux = 1.38 * 10**-23 * 270 / ((3 * 10**8) / (float(freqMHz) * 10**6))**2 * (6.67*10**-5)/ (10**-26)
    
    return flux
