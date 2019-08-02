#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Thu Jul 31 2019

@author: jkulpa
"""

import sys

sys.path.append("..")

import OnOff
import pickle

onFileName0 = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385298_rf3000.00_n16_casa_on_000_ant_2b_3000.00_obsid2874.pkl'
offFileName0 = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385354_rf3000.00_n16_casa_off_000_ant_2b_3000.00_obsid2874.pkl'

onFileName1 = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385406_rf3000.00_n16_casa_on_001_ant_2b_3000.00_obsid2874.pkl'
offFileName1 = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385459_rf3000.00_n16_casa_off_001_ant_2b_3000.00_obsid2874.pkl'

onFileName2 = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385522_rf3000.00_n16_casa_on_002_ant_2b_3000.00_obsid2874.pkl'
offFileName2 = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385571_rf3000.00_n16_casa_off_002_ant_2b_3000.00_obsid2874.pkl'


Dict0On = pickle.load( open( onFileName0, "rb" )  )
Dict0Off = pickle.load( open( offFileName0, "rb" ) )

Dict1On = pickle.load( open( onFileName1, "rb" )  )
Dict1Off = pickle.load( open( offFileName1, "rb" ) )

Dict2On = pickle.load( open( onFileName2, "rb" )  )
Dict2Off = pickle.load( open( offFileName2, "rb" ) )

SEFD_X,SEFD_var_X,SEFD_Y,SEFD_var_Y,timeStamps,powerX,powerY = OnOff.calcSEFDThreeDict(Dict0On, Dict0Off,Dict1On, Dict1Off,Dict2On, Dict2Off)
