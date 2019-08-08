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
import pickle
import re
from google.cloud import storage
import matplotlib.pyplot as plt
#import pdb

outputDir = '../'

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
    if re.search('_on_000', key):
    #if re.search('_on_000_ant_2b_3000.00', key):
        if re.search(searchsrc, key):
            offKey=re.sub('_on_000_','_off_000_',key)
            key1=re.sub('_on_000_','_on_001_',key)
            offKey1=re.sub('_on_000_','_off_001_',key)
            key2=re.sub('_on_000_','_on_002_',key)
            offKey2=re.sub('_on_000_','_off_002_',key)
            
            Dict0On = pickle.loads(bucketDict[key].download_as_string())
            Dict0Off = pickle.loads(bucketDict[offKey].download_as_string())
            Dict1On = pickle.loads(bucketDict[key1].download_as_string())
            Dict1Off = pickle.loads(bucketDict[offKey1].download_as_string())
            Dict2On = pickle.loads(bucketDict[key2].download_as_string())
            Dict2Off = pickle.loads(bucketDict[offKey2].download_as_string())
            
            SEFD_X,SEFD_var_X,SEFD_Y,SEFD_var_Y,timeStamps,powerX,powerY = OnOff.calcSEFDThreeDict(Dict0On, Dict0Off,Dict1On, Dict1Off,Dict2On, Dict2Off)

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
            plt.clf()
            plt.plot(timeStamps,powerX,'.',label='powerX')
            plt.plot(timeStamps,powerY,'.',label='powerY')
            plt.legend(['X','Y'])
            plt.title(obsname)
            plt.xlabel('time [s]')
            plt.ylabel('power [arbitrary]')
            plt.savefig(filepownameX)
