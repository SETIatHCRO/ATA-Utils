#!/usr/bin/env python
import numpy as np
import pandas as pd
from scipy import stats
import sys

MADF = 1.4826 #conversion from MAD to STD

def help_statement():
    print("This script shows the pointing errors for azimuth and elevation for all entennae recorded")

if len(sys.argv) == 1:
    print("Please pass some files")
    help_statement()
    sys.exit(-1)

if sys.argv[1] == "-h" or sys.argv[1] == "--help":
    help_statement()
    sys.exit(0)

for i, filename in enumerate(sys.argv[1:]):
    print(filename)

    with open(filename) as f:
        lines1 = f.readlines()[25:]

        eloff =[]
        azoff = []
        el_com = []
#get elevation
        for x in lines1:
            eloff.append(x.split(',')[6])

        pd.__version__
#get azimuth
        for y in lines1:
            g = np.array(y.split(','))
            #print(g)
            df = pd.DataFrame(g).T
            #print(df[5])
            df[5] = df[5].str.split(r'!').str.get(1)
            #print(df[5])
            azoff.append(df[5])
            #print(df)

#get el_com
        for z in lines1:
            el_com.append(z.split(',')[1])

        f.close()

    eloff  = np.array(eloff).astype(float).squeeze()
    azoff  = np.array(azoff).astype(float).squeeze()
    el_com = np.array(el_com).astype(float).squeeze()

    rese = eloff
    resa = azoff
    elcom = el_com
    resx = resa*np.cos(np.radians(elcom))

    #print(resx.shape)
    print("elevation offset mean = " + str(round(np.mean(rese), 4)))
    print("elevation offset std = " + str(round(np.std(rese), 4)))
    print("elevation offset median = " + str(round(np.median(rese), 4)))
    print("elevation offset MAD = " + str(round(stats.median_abs_deviation(rese)*MADF, 4)))
    
    #print(" ")
    #print("azimuth offset mean = " + str(np.mean(resa)))
    #print("azimuth offset std = " + str(np.std(resa)))
    #print("azimuth offset median = " + str(np.median(resa)))
    #print("azimuth offset MAD = " + str(stats.median_abs_deviation(resa)*MADF))

    print("mean offset xel = " + str(round(np.mean(resx), 4)))
    print("std offset xel = " + str(round(np.std(resx), 4)))
    print("median offset xel = " + str(round(np.median(resx), 4)))
    print("MAD offset xel = " + str(round(stats.median_abs_deviation(resx)*MADF, 4)))

    print(" ")
    print(" ")
