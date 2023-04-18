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
def plot_beams(name_array, fstart, fstop, drift_rate, SNR, x, save=False):
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
    if save==True:
        path='/home/ntusay/scripts/temp/'
        plt.savefig(f'{path}MJD_{MJD}_SNR_{SNR:.3f}_DR_{drift_rate:.3f}_fstart_{fstart:.6f}.png',
                    bbox_inches='tight',format='png',dpi=fig.dpi,facecolor='white', transparent=False)
        plt.show()
        plt.close()
    else:
        plt.show()
    return None

# %%
# hardcode the csv string and filtering parameters
csv = '/home/ntusay/scripts/processed/obs_10-30_CCFnbeam.csv'
csv = '/home/ntusay/scripts/processed/obs_10-28_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed/obs_10-29_CCFnbeam.csv'
csv = '/home/ntusay/scripts/NbeamAnalysis/injection_test/CCF_results/obs_UNKNOWN_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/Mars_fscrunched/redo/obs_UNKNOWN_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/Mars_test/redo/obs_UNKNOWN_CCFnbeam.csv'
csv = '/home/ntusay/scripts/processed2/obs_11-01_CCFnbeam.csv'
column = 'x'
value = 0.5

df = pd.read_csv(csv)
signals_of_interest = df[df[column] < value]
signals_of_interest = signals_of_interest.sort_values(by='x').reset_index(drop=True)
# signals_of_interest = df[df.x*np.log10(df.SNR)<=1]
# signals_of_interest = df[df['Corrected_Frequency'].between(8425,8440)]
# output the number of hits selected so you can see if it's too many
print(f'{len(signals_of_interest)} hits selected out of {len(df)}')
# %%
# loop over all the hits selected and plot
for index, row in signals_of_interest.reset_index(drop=True).iterrows():
    print(f"Index: {index}")
    beams = [row[i] for i in list(signals_of_interest) if i.startswith('fil_')]
    plot_beams(beams,
            row['freq_start'],
            row['freq_end'],
            row['Drift_Rate'],
            row['SNR'],
            row['x'],
            save=False)
# %%
j = 36
dHz = 2000*1e-6
row = signals_of_interest.iloc[j]
beams = [row[i] for i in list(signals_of_interest) if i.startswith('fil_')]
plot_beams(beams,
        row['freq_start']+dHz,
        row['freq_end']-dHz,
        row['Drift_Rate'],
        row['SNR'],
        row['x'],
        save=False)
# %%
# This is me playing with 3D plotting to include drift rate on top of correlation score and SNR
# It feels somewhat useless so far
x = df.x
y = df.SNR
z = abs(df.Drift_Rate)
fig = plt.figure(figsize=(12, 12))
ax = fig.add_subplot(projection='3d')
ax.scatter(xs=x,ys=y,zs=z)
ax.set_xlabel('x')
ax.set_ylabel('SNR')
ax.set_zlabel('Drift Rate')
plt.show()
# %%
df=df.sort_values('x')
x=df.x
# y=np.log10(df.SNR)**(1/x)**(1/x)+10
y=((1-x)*10)**(1/x)**(1/x)+200
# y=x**2*np.log10(df.SNR)
# y=1/x+15
# y=df.x**np.log10(df.SNR)
# plt.scatter(x,y)
# plt.scatter(df.x,df.SNR)
plt.scatter(x,df.SNR*np.log10(df.ACF))
plt.plot(x,y,color='g',linestyle='--')
# x=[0.4,0.897,0.925,0.962,1]
# y=[max(df.SNR),34.814,15.379,10.645,10]
# x=np.linspace(min(df.x),1,len(df))
# y=np.logspace(np.log10(max(df.SNR)),1,len(df))
# plt.plot(x,y,color='r')
# plt.hlines(y=1,xmin=0,xmax=1,color='g',linestyle='--')
plt.yscale('log')
plt.show()
# Count the number of points below the line
num_points_below_line = 0
for i in range(len(df)):
    if df.SNR[i]*np.log10(df.ACF[i]) < y[i]:
        num_points_below_line += 1

# Print the number of points below the line
print(f"Number of points below the line: {num_points_below_line}/{len(df)}")
# %%
