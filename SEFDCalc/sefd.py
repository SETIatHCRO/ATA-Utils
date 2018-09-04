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

#print os.listdir('.')

#Should add rest of antennas

#this code should be refactored to produce an SEFD from a single on/off sequence at one frequency
#SEFDcalc.py <wild_card_for_on_off_sequence>
#code will read in data, calculate average SEFD, output one value for X and one value for Y


antennas = ["1e",
        "1f",
        "1h",
        "1k",
        "2a",
        "2b",
        "2e",
        "2h",
        "2j",
        "2m",
        "3d",
        "3l",
        "4j",
        "4k",
        "4g",            
        "5c"]


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

#antennas = ["1f"];
#tunings = ["4001.00"];


#tunings = ["3000.00"]
sources = ["moon",
        "casa",
        "vira",
        "taua"]

#sources = ["moon"]

colors = ['rosybrown',
        'royalblue',
        'saddlebrown',
        'salmon',
        'sandybrown',
        'seagreen',
        'seashell',
        'sienna',
        'skyblue',
        'slateblue',
        'slategray',
        'springgreen',
        'steelblue',
        'tan',
        'teal',
        'thistle',
        'tomato',
        'turquoise',
        'violet',
        'wheat',
        'deepskyblue',
        'dodgerblue',
        'firebrick',
        'floralwhite',
        'forestgreen',
        'fuchsia',
        'gainsboro',
        'gold',
        'goldenrod',
        'gray',
        'green',
        'greenyellow',
        'honeydew',
        'hotpink',
        'indianred',
        'indigo',
        'ivory',
        'khaki',
        'lavender',
        'lavenderblush',
        'lawngreen',
        'lemonchiffon']

symbols = [r'$\bigotimes$',
        r'$\bigstar$']


"""
fig, ax = plt.subplots()
ax.set_xlim((1000,8000))
ax.set_ylim((100,1000000))
ax.set_yscale("log", nonposy='clip')
"""

for antenna in antennas:

        for source in sources:

                freqlist = []
                antennalist = []
                sefdlist = []

                for tuning in tunings:	

                        #print antenna
                        #print source
                        #print tuning


                        #mylist = sorted([f for f in glob.glob("*moon*" + antenna +"*" + tuning +"*obsid199.pkl")])
                        mylist = sorted([f for f in glob.glob("*"+source+"*" + antenna +"*" + tuning +"*.pkl")])		
                        #print mylist
                        z = range(len(mylist))
                        power0 = np.zeros(1);
                        power1 = np.zeros(1);
                        ratio0 = 0.0
                        ratio1 = 0.0
                        goodcnt0 = 0;
                        goodcnt1 = 0;

                        for i in z[::2]:
                                try:
                                    dataon = pickle.load(open(mylist[i],'r'))
                                    dataoff = pickle.load(open(mylist[i+1],'r'))
                                    """
                                    print mylist[i] 
                                    print mylist[i+1]
                                    print " "
                                    """
                                except:
                                    continue

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
                               
                                freqlist.append(float(tuning))
                                antennalist.append(colors[antennas.index(antenna) * 2 + 0])
                                sefdlist.append(ratio * sourceflux)

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
                                
                                freqlist.append(float(tuning))
                                antennalist.append(colors[antennas.index(antenna) * 2 + 1])
                                sefdlist.append(ratio * sourceflux)

                
                """
                try: 
                    ax.scatter(freqlist, sefdlist, color=antennalist, s=50, marker=symbols[sources.index(source)], alpha=.4)
                except:
                    print source, "Exception"
                """
                


""" 
labelnames = []
labelcolors = []
for antenna in antennas:
        labelnames.append(antenna + '-X')
        labelcolors.append(colors[antennas.index(antenna) * 2 + 0])
        labelnames.append(antenna + '-Y')
        labelcolors.append(colors[antennas.index(antenna) * 2 + 1])

patches = [ plt.plot([],[], marker="o", ms=10, ls="", mec=None, color=labelcolors[i], 
            label="{:s}".format(labelnames[i]) )[0]  for i in range(len(labelnames)) ]

plt.legend(handles=patches, 
           loc='upper center', ncol=5, numpoints=1 )

#plt.show()

plt.savefig("complete.png")


#whatever_data=pickle.load( open( sys.argv[1], "rb" ) )
#print whatever_data.keys()
#print sys.argv[1]
""" 



