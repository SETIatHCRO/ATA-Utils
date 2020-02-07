#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import get_filenames

#sefd_graphs.py
#code will read in data, calculate average SEFD, output one value for X and one value for Y
# and also the png filename. This CVS data is then appropriate for converting to JSON.
# The png files are scp'd to the server

# NOTE: after 1536561956 I used the auto attenuator settings

antennas =  ['2a','2b','2e','3l','1f','5c','4l','4g','2j','2d','4k','1d','2f','5h','3j','3e','1a','1b','1g','1h','2k','2m','3d','4j','5e','2c','4e','2l','2h','5g']

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

#tunings = ["1000.00", "2000.00"]
#antennas = ['1a', '2a']
#sources = ['moon', 'casa']

def list_avg(l):

    if not l or len(l) == 0:
        return 0.0

    sum = 0.0;
    count = 0
    for f in l:
        if f > 0.0:
            sum += f;
            count += 1
    if count > 0:
        return sum / count
    return 0

def list_err(l):

    avg = list_avg(l)

    err_sq_sum = 0.0

    for sefd in l:
        err = math.fabs(sefd - avg)
        err_sq_sum += err*err

    return math.sqrt(err_sq_sum)


def get_source_flux(source, tuning):

    if source == "moon":
        if tuning >= 6000.0:
            return 1.38 * 10**-23 * 270 / ((3 * 10**8) / (tuning * 10**6))**2 * ((((3 * 10**8 / (tuning * 10**6))/6.1/2)**2*3.14)/ (10**-26))
        else:
            return 1.38 * 10**-23 * 270 / ((3 * 10**8) / (tuning * 10**6))**2 * (6.67*10**-5)/ (10**-26)
        #return 1.38 * 10**-23 * 270 / ((3 * 10**8) / (float(tuning) * 10**6))**2 * (6.67*10**-5)/ (10**-26)
    elif source == "casa":
        return 250034 * tuning**-0.667
    elif source == "vira":
        return 39810.7 * tuning**-0.75
    elif source == "taua":
        return 6309.6 * tuning**-0.25

    return 0

def calc_sefd(source, tuning, ratio, goodcnt):

    sourceflux = get_source_flux(source, tuning)
    if(ratio == 0.0):
        return 0.0
    ratio = 1/(ratio / (float(goodcnt)))
    ratio = math.fabs(ratio);
    if 1/ratio < 0.01:
        ratio = 0.0

    return (ratio * sourceflux)

d = {}

for antenna in antennas:
    for source in sources:
        #print source
        for tuning in tunings:	
            for pol in "xy":

                avg_sum = 0.0
                count = 0
                sefd_list = []

                f = open("/home/sonata/data/sefd_all_rms_jan_30_2019.csv")
                line = f.readline()
                while line:


                    parts = line.strip().split(',')

                    #1a,1000.00,x,moon,18.70,18.58,18.28,18.17,18.75,18.09

                    #count += 1
                    #if count > 10:
                    #    exit()
                    #print line

                    if len(parts) != 10:
                        line = f.readline()
                        continue
                    if parts[2] !=  pol:
                        line = f.readline()
                        continue
                    if parts[1] !=  tuning:
                        line = f.readline()
                        continue
                    if parts[3] !=  source:
                        line = f.readline()
                        continue
                    if parts[0] !=  antenna:
                        line = f.readline()
                        continue


                    #print line

                    if float(parts[5]) == 0.0 or float(parts[7]) == 0.0 or float(parts[9]) == 0.0:
                        line = f.readline()
                        continue

                    ratio = 0.0
                    ratio += (float(parts[4]) / float(parts[5]) - 1.0)
                    ratio += (float(parts[6]) / float(parts[7]) - 1.0)
                    ratio += (float(parts[8]) / float(parts[9]) - 1.0)

                    sefd = calc_sefd(source, float(tuning), ratio, 3)
                    if sefd > 0.0:
                        sefd_list.append(sefd)

                    line = f.readline()

                avg = list_avg(sefd_list)
                err = list_err(sefd_list)
                #print sefd_list
                #print avg, err

                if antenna not in d:
                    d[antenna] = {}
                if source not in d[antenna]:
                    d[antenna][source] = {}
                if pol not in d[antenna][source]:
                    d[antenna][source][pol] = []
                d[antenna][source][pol].append([float(tuning), int(avg), int(err)])

print json.dumps(d)







