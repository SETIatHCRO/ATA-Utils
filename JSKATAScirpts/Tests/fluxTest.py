#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Thu Jul 18 2019

@author: jkulpa
"""

import sys

sys.path.append("..")

import OnOff.flux
import OnOff.misc
import OnOff.yFactor
import datetime


currDate = datetime.datetime.now()

flx = OnOff.flux.sourceFlux('casa',1000,currDate)

print(flx)

TSrc = OnOff.misc.calcSourceTemp(flx)

print(TSrc)

