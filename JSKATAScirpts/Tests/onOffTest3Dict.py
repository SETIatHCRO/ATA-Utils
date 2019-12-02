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
import matplotlib.pyplot as plt
import re

outputDir = '../'

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

OnOff.filterArray.setMADall()
#OnOff.filterArray.setSimple()
SEFD_X,SEFD_var_X,SEFD_Y,SEFD_var_Y,timeStamps,powerX,powerY,idx,idy = OnOff.calcSEFDThreeDict(Dict0On, Dict0Off,Dict1On, Dict1Off,Dict2On, Dict2Off)

outDict={}
outDict['SEFD_X']=SEFD_X
outDict['SEFD_var_X']=SEFD_var_X
outDict['SEFD_Y']=SEFD_Y
outDict['SEFD_var_Y']=SEFD_var_Y
outDict['timeStamps']=timeStamps
outDict['powerX']=powerX
outDict['powerY']=powerY

obsname = offKey=re.sub('_on_000_','_',Dict0On['comment'])

fileName =  outputDir + 'processed_'+obsname+'.pkl'

file_out = open(fileName, 'w') 
pickle.dump(outDict, file_out)
file_out.close()

filepownameX = outputDir + 'pow_'+obsname+'.png'
plt.plot(timeStamps,powerX,'.',label='powerX')
plt.plot(timeStamps,powerY,'.',label='powerY')
plt.legend(['X','Y'])
plt.title(obsname)
plt.xlabel('time [s]')
plt.ylabel('power [arbitrary]')
plt.savefig(filepownameX)