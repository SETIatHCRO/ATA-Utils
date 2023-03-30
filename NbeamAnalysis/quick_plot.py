'''This is a very quick and dirty plotting tool
    for use with interactive software like VSCode
    that can use jupyter kernel to display outputs.
    The #%% lines break up the cells.
    Hardcode the csv string and filtering parameters.'''

# %%
# import packages
import numpy as np
import pandas as pd
import blimpy as bl
import os, glob
import math
import matplotlib
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})

import plot_target_utils as ptu
%matplotlib inline

# define main plotting function
def plot_beams(name_array, fstart, fstop, drift_rate, SNR, x):
    # make waterfall objects for plotting from the filenames
    fil_array = []
    f1 = min(fstart,fstop)
    f2 = max(fstart,fstop)
    for beam in name_array:
        test_wat = bl.Waterfall(beam, 
                            f_start=f1, 
                            f_stop=f2)
        # print(np.shape(test_wat.data))
        fil_array.append(test_wat)
    
    # initialize the plot
    nsubplots = len(name_array)
    nrows = int(np.floor(np.sqrt(nsubplots)))
    ncols = int(np.ceil(nsubplots/nrows))
    fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize=(20,7))
    
    # call the plotting function and plot the waterfall objects in fil_array
    i=0
    for r in range(nrows):
        for c in range(ncols):
            fil = fil_array[i]
            fil_name = name_array[i]
            ptu.plot_waterfall_subplots(fil, 
                                        fil_name, 
                                        i, 
                                        ax, 
                                        fig, 
                                        f_start=f1, 
                                        f_stop=f2)
            i+=1
    # fix the title
    name_deconstructed = fil.filename.split('/')[-1].split('_')
    MJD = name_deconstructed[1] + '_' + name_deconstructed[2] #+ '_' + name_deconstructed[3]
    fig.suptitle(f'MJD: {MJD} || '+
                 f'fmax: {f2:.6f} MHz || '+
                 f'Drift Rate: {drift_rate:.3f} nHz ({f2*drift_rate/1000:.3f} Hz/s) || '+
                 f'SNR: {SNR:.3f}'+
                 f'\nCorrelation Score: {x:.3f}',
                 size=25)
    fig.tight_layout(rect=[0, 0, 1, 1.05])
    # show the plot
    plt.show()
    return None

# %%
# hardcode the csv string and filtering parameters
csv = '/home/ntusay/scripts/processed/obs_10-30_CCFnbeam.csv'
column = 'x'
value = 0.4

df = pd.read_csv(csv)
signals_of_interest = df[df[column] < value]
# output the number of hits selected so you can see if it's too many
print(f'{len(signals_of_interest)} hits selected')
# %%
# loop over all the hits selected and plot
for index, row in signals_of_interest.reset_index(drop=True).iterrows():
    beams = [row[i] for i in list(signals_of_interest) if i.startswith('fil_')]
    plot_beams(beams,
            row['freq_start'],
            row['freq_end'],
            row['Drift_Rate'],
            row['SNR'],
            row['x'])
# %%
