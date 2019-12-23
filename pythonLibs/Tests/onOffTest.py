#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Thu Jul 22 2019

@author: jkulpa
"""

import sys

sys.path.append("..")

#import OnOff.flux
#import OnOff.misc
#import OnOff.yFactor
import OnOff
import datetime
import pickle

#onFileName = '/home/jkulpa/Desktop/onoff_20190125_1548375694_rf10000.00_n16_casa_on_001_ant_2f_10000.00_obsid2871.pkl'
#offFileName = '/home/jkulpa/Desktop/onoff_20190125_1548375641_rf10000.00_n16_casa_off_000_ant_2f_10000.00_obsid2871.pkl'

#onFileName = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548378095_rf1000.00_n16_casa_on_000_ant_1a_1000.00_obsid2872.pkl'
#offFileName = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548378147_rf1000.00_n16_casa_off_000_ant_1a_1000.00_obsid2872.pkl'

#onFileName = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385298_rf3000.00_n16_casa_on_000_ant_2b_3000.00_obsid2874.pkl'
#offFileName = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385354_rf3000.00_n16_casa_off_000_ant_2b_3000.00_obsid2874.pkl'

onFileName = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385406_rf3000.00_n16_casa_on_001_ant_2b_3000.00_obsid2874.pkl'
offFileName = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385459_rf3000.00_n16_casa_off_001_ant_2b_3000.00_obsid2874.pkl'

#onFileName = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385522_rf3000.00_n16_casa_on_002_ant_2b_3000.00_obsid2874.pkl'
#offFileName = '/home/jkulpa/Desktop/onoffdata/onoff_20190125_1548385571_rf3000.00_n16_casa_off_002_ant_2b_3000.00_obsid2874.pkl'


onDict = pickle.load( open( onFileName, "rb" )  )
offDict = pickle.load( open( offFileName, "rb" ) )


freq=offDict['rfc']
freqtest=onDict['rfc']

assert freq == freqtest, "file mismatch"

ant = onDict['ant'];
meastime = int(onDict['auto0_timestamp'][0])
datetime_stamp = datetime.datetime.utcfromtimestamp(meastime)
source= onDict['source']

#TsysX,TsysstdX = OnOff.calcSingleAnt(source, freq, datetime_stamp, onDict['auto0'], offDict['auto0'])
#TsysY,TsysstdY = OnOff.calcSingleAnt(source, freq, datetime_stamp, onDict['auto1'], offDict['auto1'])

#print('TsysX = %f +- %f K',TsysX, TsysstdX)
#print('TsysY = %f +- %f K',TsysY, TsysstdY)

#TsysX = OnOff.calcSingleAntAllData(source, freq, datetime_stamp, onDict['auto0'], offDict['auto0'])
#TsysY = OnOff.calcSingleAntAllData(source, freq, datetime_stamp, onDict['auto1'], offDict['auto1'])

#print('TsysX = %f K',TsysX)
#print('TsysY = %f K',TsysY)

SEFD_X = OnOff.calcSEFDSingleAnt(source, freq, datetime_stamp, onDict['auto0'], offDict['auto0'])
SEFD_Y = OnOff.calcSEFDSingleAnt(source, freq, datetime_stamp, onDict['auto1'], offDict['auto1'])
            
print('SEFD_X = %f Jy',SEFD_X)
print('SEFD_Y = %f Jy',SEFD_Y)
