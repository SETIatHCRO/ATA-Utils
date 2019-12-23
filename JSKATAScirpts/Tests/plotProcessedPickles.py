#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
testing processed SEFD pickles
Created on Thu Aug 8 2019

@author: jkulpa
"""


import pickle
import matplotlib.pyplot as plt
import re
import glob
import numpy
import pdb

inputDir = '../../../SEFD_plots/'

ants = set()
freqs = set()
sources = set()

#looking for all combinations of source + antenna + frequency
for file in glob.glob(inputDir + '*.pkl'):
    path_search = re.search('^.*processed_(.*?)_ant_(.*?)_(.*?)_obs*',file)
    sources.add(path_search.group(1))
    ants.add(path_search.group(2))
    freqs.add(path_search.group(3))

#going trough the sets and trying to open files. note that there may be multiple
#files for combination of source + antenna + frequency. We want to plot the mean value
# and plot maximum deviation (std?) from it, separatelly for X and Y
for ant in ants:
    for source in sources:
        lf= len(freqs)
        meanSEFD_X = numpy.zeros(lf)
        meanSEFD_Y = numpy.zeros(lf)
        errSEFD_X = numpy.zeros(lf)
        errSEFD_Y = numpy.zeros(lf)
        freqs_float = numpy.zeros(lf)   
        iK = 0         
        for frset in freqs:
            freq = float(frset)
            freqs_float[iK] = freq
            sefd_list_x = []
            sefd_list_y = []
            sefd_var_x = []
            sefd_var_y = []
            #try:
            for i in xrange(1):
                for file in glob.glob(inputDir + 'processed_' + source + '_ant_' + ant + '_' +  frset + '*.pkl'):
                    fileptr= open(file,'r')
                    cDict = pickle.load(fileptr)
                    fileptr.close()
                    sefd_list_x.append(cDict['SEFD_X'])
                    sefd_list_y.append(cDict['SEFD_X'])
                    sefd_var_x.append(cDict['SEFD_var_X'])
                    sefd_var_y.append(cDict['SEFD_var_Y'])

                #the weighted mean with std weitht is better suited here!s                    
                meanSEFD_X[iK] = numpy.mean(sefd_list_x)
                meanSEFD_Y[iK] = numpy.mean(sefd_list_y)
                
                cstdXpart = numpy.std(sefd_list_x) + numpy.sum(numpy.square(sefd_var_x))
                cstdX = numpy.sqrt(cstdXpart/(numpy.size(sefd_list_x)+1))
                cstdYpart = numpy.std(sefd_list_y) + numpy.sum(numpy.square(sefd_var_y))
                cstdY = numpy.sqrt(cstdYpart/(numpy.size(sefd_list_y)+1))

                
                errSEFD_X[iK] = cstdX
                
                errSEFD_Y[iK] = cstdY
            #except:
                #print('error occured for ' + source + ' source for ' + ant)
            #rough method of iteration trough the set
            iK = iK + 1
            
        plt.clf()
        plt.errorbar(freqs_float,meanSEFD_X,errSEFD_X,None,'x',capsize=5,capthick=3)
        plt.errorbar(freqs_float,meanSEFD_Y,errSEFD_Y,None,'.',capsize=5,capthick=3)
        plt.legend(['X','Y'])
        plt.title('ant ' + ant + ' source ' + source)
        plt.xlabel('freq [MHz]')
        plt.ylabel('SEFD [Jy]')
        plt.savefig(inputDir + 'sefd_freq_ant_' + ant + '_' + source + '.png')
   
    
