#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 2019

@author: jkulpa
"""

import numpy

def casaFlux(freqMHz,date):
    """
    a flux calculation of Cassiopea A
    
    based on Baars et al 1977

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
        AssertionError
    """   
    
    assert freqMHz >= 500, "Frequency out of predictable range (0.5-30 GHz)"
    assert freqMHz <= 30000, "Frequency out of predictable range (0.5-30 GHz)"
    
    snu = 10**(5.745 - 0.770 * numpy.log10(freqMHz));
    """fadeout per year"""
    dnu = (0.97 - 0.30*numpy.log10(freqMHz/1000))/100;
    loss = (1-dnu) ** (date - 1980);

    flux = loss * snu;
    return flux
    
