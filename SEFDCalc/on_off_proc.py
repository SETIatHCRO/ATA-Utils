#! /usr/bin/python

import cPickle as pkl
import glob
import re
import numpy as np
import scipy.io
import pdb
import argparse

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(description='Process ATA ON/OFF measurements')
parser.add_argument('dataset', help='The data directory to process (i.e. /data/...)')
args = parser.parse_args()
dataDir = args.dataset

resultDir = 'sefdVals'
chanRange = np.arange(720,720+1024)

fileList = glob.glob(dataDir + '/*.pkl') 
antIDList = [];
obsIDList = [];
idx = 0
nFile = len(fileList)
for pklFile in fileList:
  obsID = re.search('obsid[0-9]{1,6}\.pkl',pklFile)
  antID = re.search('_ant_[0-9][a-z]_',pklFile)
  if (obsID is None) or (antID is None):
    continue
  obsID = obsID.group(0)[5:-4]
  antID = antID.group(0)[5:7]
  if not (obsID in obsIDList):
    obsIDList.append(obsID)
  if not (antID in antIDList):
    antIDList.append(antID)

antIDList = sorted(antIDList)
obsIDList = sorted(obsIDList)

for obsID in obsIDList:
  for antID in antIDList:
    firstFile = True
    fileList = sorted(glob.glob(dataDir + '/*_ant_' + antID + '_*_obsid' + obsID + '.pkl'))
    if (not fileList):
      continue
    for pklFile in fileList:
      pklData = pkl.load(open(pklFile,"rb"))
      autoXScan = np.single(np.median(np.reshape(np.concatenate(pklData['auto0']), \
        [len(pklData['auto0']),len(pklData['auto0'][0])]),axis=0)[chanRange])
      autoYScan = np.single(np.median(np.reshape(np.concatenate(pklData['auto1']), \
        [len(pklData['auto1']),len(pklData['auto1'][0])]),axis=0)[chanRange])
      if not firstFile:
        autoXData = np.vstack([autoXData,autoXScan])
        autoYData = np.vstack([autoYData,autoYScan])
        onSource = np.append(onSource,(re.search('_on_',pklFile) is not None))
        timeStamps = np.append(timeStamps,np.median(pklData['auto0_timestamp']))
      else:
        autoXData = autoXScan
        autoYData = autoYScan
        onSource = np.array((re.search('_on_',pklFile) is not None))
        timeStamps = np.median(pklData['auto0_timestamp'])
        firstFile = False

    freqRange = pklData['frange']
    if (len(freqRange) == 4096):
      freqRange = freqRange[np.arange(1,4096,2)]
    freqRange = freqRange[chanRange]
    midFreq = np.median(freqRange)
    souName = pklData['source']
    
    onOffXVals = np.divide(autoXData[np.where(onSource == True)],autoXData[np.where(onSource == False)])
    yFactorXVals = np.array(np.percentile(onOffXVals,[30.8538, 50.0, 69.146],axis=1))
    yFactorXVals = np.transpose(np.array([yFactorXVals[1,:],yFactorXVals[2,:]-yFactorXVals[0,:]]))

    onOffYVals = np.divide(autoYData[np.where(onSource == True)],autoYData[np.where(onSource == False)])
    yFactorYVals = np.array(np.percentile(onOffYVals,[30.8538, 50.0, 69.146],axis=1))
    yFactorYVals = np.transpose(np.array([yFactorYVals[1,:],yFactorYVals[2,:]-yFactorYVals[0,:]]))

    dataDict = {
      'autoXData':    autoXData,
      'autoYData':    autoYData,
      'freqRange':    freqRange,
      'midFreq':      midFreq,
      'souName':      souName,
      'onSource':     onSource,
      'timeStamps':   timeStamps,
      'obsID':        obsID,
      'antID':        antID,
      'yFactorXVals': yFactorXVals,
      'yFactorYVals': yFactorYVals
    }
    scipy.io.savemat(resultDir + '/' + obsID + '-' + antID + '.mat',dataDict,oned_as='row')
  print(obsID + " is done!")

