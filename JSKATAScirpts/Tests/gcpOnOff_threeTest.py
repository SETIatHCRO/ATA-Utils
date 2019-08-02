#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
testing flux functions
Created on Thu Jul 31 2019

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
import re
from google.cloud import storage

bucket_name = 'ata_test_data'
sClient = storage.Client()
prefix_name = 'onoff/20190125'
searchsrc = '_casa_'

llist = sClient.list_blobs(bucket_name,prefix=prefix_name)

bucketDict = {}

for cBckt in llist:
    cstr = str(cBckt.name);
    if cstr.lower().endswith('pkl'):
        cstrNew = re.sub('^.*?_','',cstr)
        bucketDict[cstrNew] = cBckt
        
for key in bucketDict.keys():
    #if re.search('_on_000', key):
    if re.search('_on_000_ant_2b_3000.00', key):
        if re.search(searchsrc, key):
            offKey=re.sub('_on_000_','_off_000_',key)
            key1=re.sub('_on_000_','_off_001_',key)
            offKey1=re.sub('_on_000_','_off_001_',key)
            key2=re.sub('_on_000_','_off_002_',key)
            offKey2=re.sub('_on_000_','_off_002_',key)
            
            onDict = pickle.loads(bucketDict[key].download_as_string())
            offDict = pickle.loads(bucketDict[offKey].download_as_string())
            onDict1 = pickle.loads(bucketDict[key].download_as_string())
            offDict1 = pickle.loads(bucketDict[offKey].download_as_string())
            onDict2 = pickle.loads(bucketDict[key].download_as_string())
            offDict2 = pickle.loads(bucketDict[offKey].download_as_string())
            
            freq=offDict['rfc']
            freqtest=onDict['rfc']

            assert freq == freqtest, "file mismatch"

            ant = onDict['ant'];
            meastime = int(onDict['auto0_timestamp'][0])
            datetime_stamp = datetime.datetime.utcfromtimestamp(meastime)
            source= onDict['source']

            print(key)
            
            #TsysX,TsysstdX = OnOff.calcSingleAnt(source, freq, datetime_stamp, onDict['auto0'], offDict['auto0'])
            #TsysX,TsysstdX = OnOff.calcSingleAnt(source, freq, datetime_stamp, onDict['auto0'], offDict['auto0'])
            #TsysY,TsysstdY = OnOff.calcSingleAnt(source, freq, datetime_stamp, onDict['auto1'], offDict['auto1'])
            #TsysY,TsysstdY = OnOff.calcSingleAnt(source, freq, datetime_stamp, onDict['auto1'], offDict['auto1'])

            #print('TsysX = %f +- %f K',TsysX, TsysstdX)
            #print('TsysY = %f +- %f K',TsysY, TsysstdY)

            SEFD_X,SEFD_X_STD = OnOff.calcSEFDSingleAnt(source, freq, datetime_stamp, onDict['auto0'], offDict['auto0'])
            SEFD_Y,SEFD_Y_STD = OnOff.calcSEFDSingleAnt(source, freq, datetime_stamp, onDict['auto1'], offDict['auto1'])
            
            print('SEFD_X = ' + repr(SEFD_X) + ' +/- ' + repr(SEFD_X_STD) + ' Jy')
            print('SEFD_Y = ' + repr(SEFD_Y) + ' +/- ' + repr(SEFD_Y_STD) + ' Jy')
