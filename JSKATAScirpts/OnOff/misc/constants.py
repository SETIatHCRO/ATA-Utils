#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy

"""
Created on Thu Jul 18 2019

@author: jkulpa
"""

"""Antenna radius [m]"""
antR = 3;
"""antenna efficency, 1 is max"""
antEff = 0.6;
"""Boltzman constant"""
kBoltzman = 1.38064852;
"""Cold outer space temperature, K"""
TCold = 3
"""the valid data range for the array"""
#dataRange = range(768,1700)
dataRange = numpy.array(range(700,1800))
