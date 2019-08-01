#!/usr/bin/env python2
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
import numpy as np

#onFileName = '/home/jkulpa/Desktop/onoff_20190125_1548375694_rf10000.00_n16_casa_on_001_ant_2f_10000.00_obsid2871.pkl'
#offFileName = '/home/jkulpa/Desktop/onoff_20190125_1548375641_rf10000.00_n16_casa_off_000_ant_2f_10000.00_obsid2871.pkl'

onFileName = '/home/jkulpa/Desktop/onoff_20190125_1548378095_rf1000.00_n16_casa_on_000_ant_1a_1000.00_obsid2872.pkl'
offFileName = '/home/jkulpa/Desktop/onoff_20190125_1548378147_rf1000.00_n16_casa_off_000_ant_1a_1000.00_obsid2872.pkl'

dataon = pickle.load( open( onFileName, "rb" )  )
dataoff = pickle.load( open( offFileName, "rb" ) )

source = 'casa'
tuning=dataon['rfc']
antenna = dataon['ant'];

power0 = np.zeros(1);
power1 = np.zeros(1);
ratio0 = 0.0
ratio1 = 0.0
goodcnt0 = 0;
goodcnt1 = 0;
                        
if dataon['adc0_stats']['dev'] >= 2.:
    frange = dataon['frange'][768:1700]
    specon = np.mean(dataon['auto0'], axis=0)[768:1700]
    specoff = np.mean(dataoff['auto0'], axis=0)[768:1700]

    power0 = np.append(power0, np.mean(np.array(dataon['auto0'])[:,768:1700], axis=1))
    power0 = np.append(power0, np.mean(np.array(dataoff['auto0'])[:,768:1700], axis=1))   
    onpower = np.mean(np.array(dataon['auto0'])[:,768:1700])
    offpower = np.mean(np.array(dataoff['auto0'])[:,768:1700])
    #print onpower
    #print offpower
    ratio0 += (onpower / offpower - 1.0)
    goodcnt0 += 1

if dataon['adc1_stats']['dev'] >= 2.:
    frange = dataon['frange'][768:1700]
    specon = np.mean(dataon['auto1'], axis=0)[768:1700]
    specoff = np.mean(dataoff['auto1'], axis=0)[768:1700]

    power1 = np.append(power1, np.mean(np.array(dataon['auto1'])[:,768:1700], axis=1))
    power1 = np.append(power1, np.mean(np.array(dataoff['auto1'])[:,768:1700], axis=1))


    onpower = np.mean(np.array(dataon['auto1'])[:,768:1700])
    offpower = np.mean(np.array(dataoff['auto1'])[:,768:1700])
    #print onpower
    #print offpower
    ratio1 += (onpower / offpower - 1.0)
    goodcnt1 += 1


        # We have on and off data for this antenna. Plot a spectrum at 3 GHz with the ratio.
#plt.figure()
#plt.plot(frange, specon / specoff)
#plt.title(mylist[i])
#plt.show()
#print len(power0)
#print len(power1)
if source == "moon":
    sourceflux = 1.38 * 10**-23 * 270 / ((3 * 10**8) / (float(tuning) * 10**6))**2 * (6.67*10**-5)/ (10**-26)
if source == "casa":
    sourceflux = 250034 * float(tuning)**-0.667
if source == "vira":
    sourceflux = 39810.7 * float(tuning)**-0.75
if source == "taua":
    sourceflux = 6309.6 * float(tuning)**-0.25
#print sourceflux

if len(power0) > 2:
    #print ratio0
        ratio = 1/(ratio0 / (float(goodcnt0)))
        #print ratio
        if 1/ratio < 0.01:
            ratio = 0.0
        
        """ 
        plt.figure()
        plt.plot(power0)
        
        ptitle = "Antenna: "+ antenna+ "X Frequency: "+ tuning+ " MHz SEFD: "+ str(ratio * sourceflux)+ " Jy"
        plt.title(ptitle)
        """ 
        
        #print "Antenna: ", antenna, "X Frequency: ", tuning, " MHz SEFD: ", ratio * sourceflux, " Jy", "ratio: ", ratio
        #print source,antenna,tuning,ratio * sourceflux,ratio
        #print source,",",antenna,",x,",tuning,",",ratio * sourceflux,",",ratio
        print("%s,%s,x,%s,%f,%f" % (source, antenna, tuning, ratio * sourceflux, ratio));
        
        """
        plt.savefig(antenna+"X"+tuning+".png")
        plt.close()				
        """
       
        #freqlist.append(float(tuning))
        #antennalist.append(colors[antennas.index(antenna) * 2 + 0])
        #sefdlist.append(ratio * sourceflux)

if len(power1) > 2:
    #print ratio1
        ratio = 1/(ratio1 / (float(goodcnt1)))
        #print ratio
        if 1/ratio < 0.01:
            ratio = 0.0
        
        """ 
        plt.figure()
        plt.plot(power1)
        
        ptitle = "Antenna: "+ antenna+ "Y Frequency: "+ tuning+ " MHz SEFD: "+ str(ratio * sourceflux)+ " Jy"
        
        plt.title(ptitle)
        """ 
        
        #print "Antenna: ", antenna, "Y Frequency: ", tuning, " MHz SEFD: ", ratio * sourceflux, " Jy", "ratio: ", ratio
        print("%s,%s,y,%s,%f,%f" % (source, antenna, tuning, ratio * sourceflux, ratio));
        #print source,",",antenna,",y,",tuning,ratio * sourceflux,",",ratio
        
        """ 
        plt.savefig(antenna+"Y"+tuning+".png")
        plt.close()				
        """ 
        
        #freqlist.append(float(tuning))
        #antennalist.append(colors[antennas.index(antenna) * 2 + 1])
        #sefdlist.append(ratio * sourceflux)