#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
helpers for observator (obs) database

Created Feb 2020

@author: jkulpa
"""

def getRecType(string):
    """
    supported types: frb, calibration, on-off, pulsar, other        
    """
    lstring = string.lower()
    if lstring in ['frb']:
        return 'FRB'
    elif lstring in ['calibration','cal']:
        return 'CALIBRATION'
    elif lstring in ['onoff','on-off']:
        return 'ON-OFF'
    elif lstring in ['pulsar']:
        return 'PULSAR'
    else:
        return 'OTHER'

def getRecBackend(string):
    """
    supported backends: frb, beamformer, correlator, snap
    """
    lstring = string.lower()
    if lstring in ['bf','beamformer']:
        return 'BEAMFORMER'
    elif lstring in ['frb']:
        return 'FRB'
    elif lstring in ['correlator']:
        return 'CORRELATOR'
    elif lstring in ['snap']:
        return 'SNAP'
    else:
        raise KeyError('Unknown backend')

