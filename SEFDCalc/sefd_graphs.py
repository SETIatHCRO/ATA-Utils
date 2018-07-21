#!/usr/bin/python

from __future__ import division

import sys
import numpy as np, scipy.io
import pickle
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
import plumbum
import math

#sefd_graphs.py
#code will read in data, calculate average SEFD, output one value for X and one value for Y
# and also the png filename. This CVS data is then appropriate for converting to JSON.
# The png files are scp'd to the server


antennas = ["1d",
        "1e",
        "1f",
        "1h",
        "1k",
        "2a",
        "2b",
        "2e",
        "2h",
        "2j",
        "2d",
        "2f",
        "2m",
        "3d",
        "3e",
        "3l",
        "3j",
        "4j",
        "4l",
        "4g",            
        "4k",            
        "5c",
        "5h"]

tunings = ["1000.00",
        "2000.00",
        "3000.00",
        "4000.00",
        "5000.00",                      
        "6000.00",
        "7000.00",
        "8000.00",
        "9000.00",
        "10000.00"]

sources = ["moon",
        "casa",
        "vira",
        "taua"]

fig = plt.subplots()

for antenna in antennas:

        for source in sources:



                for tuning in tunings:	

                        #print antenna
                        #print source
                        #print tuning


                        #mylist = sorted([f for f in glob.glob("*"+ source + "*" + antenna +"*" + tuning +"*obsid" + myObsid +".pkl")])
                        mylist = sorted([f for f in glob.glob("*"+source+"*" + antenna +"*" + tuning +"*.pkl")])		
                        #print mylist
                        z = range(len(mylist))
                        power0 = np.zeros(1);
                        power1 = np.zeros(1);
                        ratio0 = 0.0
                        ratio1 = 0.0
                        goodcnt0 = 0;
                        goodcnt1 = 0;

                        lastObsid = "-1"
                        thisObsid = "-1"
                        markers = [];


                        j = 0
                        for i in z[::2]:

                                try:
                                    if "_on_" not in mylist[j]:
                                        j = j + 1;
                                        print "skip1, %s,%s" % ( mylist[j],  mylist[j+1])
                                        continue
                                    if "_off_" not in mylist[j+1]:
                                        j = j + 1
                                        print "skip2, %s,%s" % ( mylist[j],  mylist[j+1])
                                        continue
                                    dataon = pickle.load(open(mylist[j],'r'))
                                    dataoff = pickle.load(open(mylist[j+1],'r'))

                                    #Keep track of the obsId for drawing the markers
                                    thisObsid = mylist[j+1].split("_")[-1].split(".")[0][5:]
                                    if(lastObsid == "-1"):
                                        lastObsid = thisObsid;
                                    #print mylist[j] 
                                    #print mylist[j+1]
                                    #print " "
                                except:

                                    continue

                                j = j + 2

                                """
                                if (dataon['adc0_stats']['dev'] <= 30. and dataon['adc0_stats']['dev'] >= 5.):
                                        print "Good stddev for adc0: ", mylist[i], dataon['adc0_stats']
                                else:
                                        print "Bad stddev for adc0: ", mylist[i], dataon['adc0_stats']		

                                if (dataoff['adc0_stats']['dev'] <= 30. and dataoff['adc0_stats']['dev'] >= 5.):
                                        print "Good stddev for adc0: ", mylist[i+1], dataoff['adc0_stats']
                                else:
                                        print "Bad stddev for adc0: ", mylist[i+1], dataoff['adc0_stats']		

                                if (dataon['adc1_stats']['dev'] <= 30. and dataon['adc1_stats']['dev'] >= 5.):
                                        print "Good stddev for adc1: ", mylist[i], dataon['adc1_stats']
                                else:
                                        print "Bad stddev for adc1: ", mylist[i], dataon['adc1_stats']		

                                if (dataoff['adc1_stats']['dev'] <= 30. and dataoff['adc1_stats']['dev'] >= 5.):
                                        print "Good stddev for adc1: ", mylist[i+1], dataoff['adc1_stats']
                                else:
                                        print "Bad stddev for adc1: ", mylist[i+1], dataoff['adc1_stats']		
                                """
                                """
                                if(antenna == '4l'):
                                    if (dataon['adc0_stats']['dev'] > 30. or dataon['adc0_stats']['dev'] < 5.):
                                        print "Bad stddev for adc0: ", mylist[i], dataon['adc0_stats']		

                                    if (dataoff['adc0_stats']['dev'] > 30. or dataoff['adc0_stats']['dev'] < 5.):
                                        print "Bad stddev for adc0: ", mylist[i+1], dataoff['adc0_stats']		

                                    if (dataon['adc1_stats']['dev'] > 30. or dataon['adc1_stats']['dev'] < 5.):
                                        print "Bad stddev for adc1: ", mylist[i], dataon['adc1_stats']

                                    if (dataoff['adc1_stats']['dev'] > 30. or dataoff['adc1_stats']['dev'] < 5.):
                                        print "Bad stddev for adc1: ", mylist[i+1], dataoff['adc1_stats']		
                                """

                                if dataon['adc0_stats']['dev'] >= 2.:
                                    frange = dataon['frange'][768:1700]
                                    specon = np.mean(dataon['auto0'], axis=0)[768:1700]
                                    specoff = np.mean(dataoff['auto0'], axis=0)[768:1700]

                                    if(lastObsid != thisObsid):
                                        markers.append([len(power0)-1, lastObsid])
                                        lastObsid = thisObsid

                                    power0 = np.append(power0, np.mean(np.array(dataon['auto0'])[:,768:1700], axis=1))
                                    power0 = np.append(power0, np.mean(np.array(dataoff['auto0'])[:,768:1700], axis=1))   
                                    onpower = np.mean(np.array(dataon['auto0'])[:,768:1700])
                                    offpower = np.mean(np.array(dataoff['auto0'])[:,768:1700])
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
                                    ratio1 += (onpower / offpower - 1.0)
                                    goodcnt1 += 1

                        markers.append([len(power0)-1, thisObsid])

                        if source == "moon":
                            sourceflux = 1.38 * 10**-23 * 270 / ((3 * 10**8) / (float(tuning) * 10**6))**2 * (6.67*10**-5)/ (10**-26)
                        if source == "casa":
                            sourceflux = 250034 * float(tuning)**-0.667
                        if source == "vira":
                            sourceflux = 39810.7 * float(tuning)**-0.75
                        if source == "taua":
                            sourceflux = 6309.6 * float(tuning)**-0.25

                        if len(power0) > 2:
                                ratio = 1/(ratio0 / (float(goodcnt0)))
                                ratio = math.fabs(ratio);
                                if 1/ratio < 0.01:
                                    ratio = 0.0
                                
                                # Finish up the plot
                                plt.figure()
                                plt.plot(power0)
                                ptitle = "Antenna: "+ antenna+ "X Frequency: "+ tuning+ " MHz SEFD: "+ str(ratio * sourceflux)+ " Jy"
                                plt.title(ptitle)
                                for m in markers:
                                  plt.axvline(x=m[0], color='grey', linestyle='--')
                                  plt.text(m[0]-1, 0, m[1], horizontalalignment='right');
                                fname = antenna+"x_"+tuning+"_"+source+".png"
                                plt.savefig(fname)
                                plt.close()				

                                #Output CSV line
                                print("%s,%s,x,%s,%f,%f,%s" % (source, antenna, tuning, ratio * sourceflux, ratio, fname));
                                # SSH to server
                                """
                                r = plumbum.machines.SshMachine("antfeeds.setiquest.info")
                                fro = plumbum.local.path(fname)
                                to =  r.path("www/sefd")
                                plumbum.path.utils.copy(fro, to);
                                """
                               

                        if len(power1) > 2:
                                ratio = 1/(ratio1 / (float(goodcnt1)))
                                ratio = math.fabs(ratio);
                                if 1/ratio < 0.01:
                                    ratio = 0.0
                                
                                # Finish up the plot
                                plt.figure()
                                plt.plot(power1)
                                ptitle = "Antenna: "+ antenna+ "Y Frequency: "+ tuning+ " MHz SEFD: "+ str(ratio * sourceflux)+ " Jy"
                                plt.title(ptitle)
                                for m in markers:
                                  plt.axvline(x=m[0], color='grey', linestyle='--')
                                  plt.text(m[0]-1, 10, m[1], horizontalalignment='right');
                                fname = antenna+"y_"+tuning+"_"+source+".png"
                                plt.savefig(fname)
                                plt.close()				
                                
                                #Output CSV line
                                print("%s,%s,y,%s,%f,%f,%s" % (source, antenna, tuning, ratio * sourceflux, ratio,fname));

                                # SSH to server
                                """
                                r = plumbum.machines.SshMachine("antfeeds.setiquest.info")
                                fro = plumbum.local.path(fname)
                                to =  r.path("www/sefd")
                                plumbum.path.utils.copy(fro, to);
                                """


