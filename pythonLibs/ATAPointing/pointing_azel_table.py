import numpy as np
import os
import plotly.figure_factory as ff
import plotly.graph_objs as go

import glob
import pandas as pd
from scipy import stats
import sys
import matplotlib.pyplot as plt


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

listr = []

lista = []

listb = ["el_off_mean", "el_off_SDev", "el_off_median"
         , "el_off_MAD", "xel_off_mean", "xel_off_SDev",
         "xel_off_median", "xel_off_MAD" ]

for i, filename in enumerate(sys.argv[1:]):
    #print(filename)
    #lista.append((filename[22:24]))

    lista.append(filename)
    
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

    eloff  = np.array(eloff).astype(np.float64).squeeze()
    azoff  = np.array(azoff).astype(np.float64).squeeze()
    el_com = np.array(el_com).astype(np.float64).squeeze()

    rese = eloff
    resa = azoff
    elcom = el_com
    resx = resa*np.cos(np.radians(elcom))
    
    dats = [(round(np.mean(rese), 4)), (round(np.std(rese), 4)), (round(np.median(rese), 4)), 
           (round(stats.median_absolute_deviation(rese)*MADF, 4)), (round(np.mean(resx), 4)), (round(np.std(resx), 4)),
          (round(np.median(resx), 4)), (round(stats.median_absolute_deviation(resx)*MADF, 4))]
    listr.append(dats)

dat = pd.DataFrame(listr, index=lista, columns=listb)

#plt.figure(figsize=[10,12])

fig, ax = plt.subplots(figsize=(15,15))
ax.set_axis_off()



plt.subplots_adjust(bottom=0.8)
plt.subplots_adjust(left=0.25)
#plt.rcParams["figure.figsize"] = [7.00, 3.50]
#plt.rcParams["figure.autolayout"] = True

table = ax.table(cellText = listr, rowLabels = lista, colLabels = listb)#, colWidths = [0.15, 0.25])

for i in range(len(listr)):
    for j in range(len(listr[i])):
        val = (listr[i][j])
        if np.abs(val) > 0.015:
            table[(i+1, j)].get_text().set_color('red')
            #print("\033[1;31;40m \n"  + str(val))#  " \n")
        elif 0.0075 < np.abs(val) < 0.015:
            table[(i+1, j)].get_text().set_color('orange')
            #print("\033[1;33;40m \n"  + str(val)) # " \n")
        else:
            None





fig = plt.gcf()
ax = plt.gca()
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
ax.set_facecolor(color="black")


table.auto_set_font_size(False)

table.set_fontsize(12)
table.scale(1, 3)

plt.box(on=None)


plt.show()
