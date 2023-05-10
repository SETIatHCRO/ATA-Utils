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

import plot_utils as ptu
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
'''
Filter individual csvs on a value.
Output number of hits selected.
'''
# hardcode the csv string and filtering parameters
csv = '/home/ntusay/scripts/processed2/obs_10-27_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed/obs_10-29_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/NbeamAnalysis/injection_test/CCF_results/obs_UNKNOWN_CCFnbeam.csv'
csv = '/home/ntusay/scripts/Mars_fscrunched/redo/obs_UNKNOWN_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/Mars_test/redo/obs_UNKNOWN_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed2/obs_11-09_CCFnbeam.csv'
column = 'x'
value = 0.2

df = pd.read_csv(csv)
signals_of_interest = df[df[column] < value]
signals_of_interest = signals_of_interest.sort_values(by='x').reset_index(drop=True)
# signals_of_interest = df[df.x*np.log10(df.SNR)<=1]
# signals_of_interest = df[df['Corrected_Frequency'].between(8425,8440)]
# output the number of hits selected so you can see if it's too many
print(f'{len(signals_of_interest)} hits selected out of {len(df)}')
# %%
'''
Loop over all the hits selected and plot both beams
'''
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
'''
Pick a specific row to look at and plot the beams
with some frequency width.
'''
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
'''
This is me playing with 3D plotting 
to include drift rate on top of correlation score and SNR.
It feels somewhat useless so far
'''
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
'''
Scatter Plot of SNR vs Score for ALL observations
'''
import glob
import pandas as pd
import matplotlib.pyplot as plt
%matplotlib inline
path='/home/ntusay/scripts/processed2/'
csvs = sorted(glob.glob(path+'*.csv'))
full_df = pd.DataFrame()
column = 'x'
value = 0.2903

for csv in csvs:
    temp_df = pd.read_csv(csv)
    print(f'{len(temp_df[temp_df[column] <= value])} hits in csv {csv.split("/")[-1].split("_CCF")[0]}')
    full_df = pd.concat([full_df, temp_df],ignore_index=True)
xs = full_df.x
SNR = full_df.SNR
# DR = abs(full_df.Drift_Rate)
fig,ax=plt.subplots(figsize=(12,10))
plt.scatter(xs,SNR,color='orange',alpha=0.5,edgecolor='k')
plt.xlabel('Average Correlation Scores')
plt.ylabel('SNR')
plt.yscale('log')
plt.xlim(-0.01,1.01)
# plt.savefig(outdir + f'{obs}_SNRx.png',
#             bbox_inches='tight',format='png',dpi=fig.dpi,facecolor='white', transparent=False)
plt.show()

signals_of_interest = full_df[full_df[column] <= value]
print(f'{len(signals_of_interest)} hits selected out of {len(full_df)}')
# %%
'''
Probing the noise between two beams of the same observation
'''
import pandas as pd
import matplotlib.pyplot as plt
%matplotlib inline
csv1='/home/ntusay/scripts/median_test/obs_UNKNOWN_CCFnbeam.csv'
csv2='/home/ntusay/scripts/Mars_fscrunched/redo/obs_UNKNOWN_CCFnbeam.csv'
# csv1='/home/ntusay/scripts/median_test/obs_11-01_CCFnbeam.csv'
# csv2='/home/ntusay/scripts/processed2/obs_11-01_CCFnbeam.csv'
csv1='/home/ntusay/scripts/plot_test/noise_test0.csv'
csv2='/home/ntusay/scripts/plot_test/noise_test1.csv'
# df1=pd.read_csv(csv1).sort_values(by="Corrected_Frequency")
# df2=pd.read_csv(csv2).sort_values(by="Corrected_Frequency")
df1=pd.read_csv(csv1)
df2=pd.read_csv(csv2)
fig,ax=plt.subplots(figsize=(20,8))
plt.scatter(df1.freqs1,abs(df2.medians2-df1.medians1)/df1.medians1,s=1)
# plt.scatter(df2.freqs2,df2.medians2)
# plt.xlabel('median percent difference')
# plt.ylabel('difference in correlation scores')
# plt.xlim(1950,2450)
plt.show()
# %%
'''
This KDE approach doesn't work for large data arrays.
Histogram is way better and easier.
'''
import time
start=time.time()
import glob
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt

# Load data
path='/home/ntusay/scripts/processed2/'
csvs = sorted(glob.glob(path+'*.csv'))
full_df = pd.DataFrame()
for csv in csvs:
    temp_df = pd.read_csv(csv)
    full_df = pd.concat([full_df, temp_df],ignore_index=True)
full_df = full_df.sort_values(by='x').reset_index(drop=True)
x = full_df['x']
# csv = '/home/ntusay/scripts/processed2/obs_10-27_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed2/obs_10-28_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed2/obs_10-29_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed2/obs_10-30_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed2/obs_11-01_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed2/obs_11-02_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed2/obs_11-05_CCFnbeam.csv'
# csv = '/home/ntusay/scripts/processed2/obs_11-09_CCFnbeam.csv'
# print(f"{csv.split('/')[-1].split('_CCF')[0]}")
# df = pd.read_csv(csv)
# df = df.sort_values(by='x').reset_index(drop=True)
# x = df['x']

# Estimate the density of the points using a Gaussian kernel
density_func = gaussian_kde(x)

# Evaluate the density function at each point
density = density_func(x)

# Compute a threshold below which points are considered low-density
percentile = 0.1
threshold = np.percentile(density, percentile)

# Identify points with low density
low_density_indices = np.where(density < threshold)[0]

# Find the maximum x value of the low-density points that is less than the maximum x value of the high-density points
last_low_density_index = low_density_indices[-1]
high_density_indices = np.where(density >= threshold)[0]
max_high_density_x = np.max(x[high_density_indices])
x_threshold = np.max(x[low_density_indices[x[low_density_indices] < max_high_density_x]])

# Plot the results
fig, ax = plt.subplots()
ax.hist(x, bins=50, density=True, alpha=0.5, color='blue')
ax.scatter(x, density, color='red',s=20)
ax.axhline(threshold, linestyle='--', color='gray')
ax.axvline(x_threshold, linestyle='--', color='green')
ax.set_xlabel('Average Correlation Score')
ax.set_ylabel('Density')
plt.show()
print(f'Max correlation score for the bottom {percentile} percentile: {x_threshold:.3f}')
print(f'There are {len(full_df[full_df.x <= x_threshold])} hits less than or equal to this threshold.')
# %%
'''
Diagnostic Plotter
'''
from plot_utils import diagnostic_plotter as dp
import glob
import pandas as pd

# Load data
path='/home/ntusay/scripts/processed2/'
csvs = sorted(glob.glob(path+'*.csv'))
full_df = pd.DataFrame()
for csv in csvs:
    temp_df = pd.read_csv(csv)
    full_df = pd.concat([full_df, temp_df],ignore_index=True)
full_df = full_df.sort_values(by='x').reset_index(drop=True)
dp(full_df,tag='ALL_obs')

# %%
'''
Cutoff calculation and plots using Median Absolute Deviation (MAD)
'''
import pandas as pd
import numpy as np
import matplotlib
import subprocess
import matplotlib.pyplot as plt
plt.style.use('/home/ntusay/scripts/NbeamAnalysis/plt_format.mplstyle')
import glob

def calculate_cutoffs(xs, k):
    mad = np.median(np.abs(xs - np.median(xs)))
    median = np.median(xs)
    cutoff_mad = median - k * mad
    return cutoff_mad

def calculate_sigmas(xs, cutoff_mad):
    mad = np.median(np.abs(xs - np.median(xs)))
    median = np.median(xs)
    k = (median - cutoff_mad) / mad
    return k

def mkplt(x, fig, ax, c=(0, 0), numx=500, obs='All'):
    # set params
    k = int(np.log10(len(x)*np.log10(len(x))**2))
    # k = 8
    log=False
    bins = 100

    # # calculate cutoff from MAD at some sigma k
    # cutoff_mad = calculate_cutoffs(x, k)

    # calculate the sigma given some cutoff value
    cutoff_mad=sorted(x)[numx]
    k = calculate_sigmas(x, cutoff_mad)
    if isinstance(ax, np.ndarray):
        nrows, ncols = ax.shape  # get the number of rows and columns in ax
        row, col = c // ncols, c % ncols  # compute the row and column indices
        ax = ax[row, col]
    n, xbin, _ = ax.hist(x, bins, log=log,color='C0', edgecolor='C0')
    ax.stairs(n, xbin,color='purple')
    ax.axvline(np.median(x), linestyle='--', linewidth=2, color='orange', label=f'Median (x = {np.median(x):.4f})')
    ax.axvline(cutoff_mad, linestyle=':', linewidth=2, color='red', label=rf'{k:.1f}$\sigma$ MAD Cutoff (x = {cutoff_mad:.4f})')
    ax.set_ylabel('Number per Bin')
    ax.set_xlabel('Beam Correlation Scores')
    ax.legend(loc='upper left',title=f"Observations: {obs}")
    ax.set_xlim(-0.05,1.05)
    print(rf'MAD cutoff value: {cutoff_mad:.4f} at {k:.1f} sigma')
    print(f'Number of values below MAD cutoff: {len(x[x < cutoff_mad])}/{len(x)}')
    print(f'Percent of values above MAD cutoff: {(len(x) - len(x[x < cutoff_mad])) / len(x) * 100:.3f}%')
    print('------------------------------------------')
    return cutoff_mad

# input and output params
path='/home/ntusay/scripts/processed2/'
outdir=path
save=True
plot_hits=False

# get input data csvs
csvs = sorted(glob.glob(path+'*.csv'))
full_df = pd.DataFrame()
# initialize outliers counter
outliers=0
# initialize the plot with subplots
fig, ax = plt.subplots(nrows=4, ncols=2, figsize=(12,16))
# loop over each csv to make subplots
for c,csv in enumerate(csvs):
    temp_df = pd.read_csv(csv)
    temp_df = temp_df.sort_values(by='x').reset_index(drop=True)
    temp_x = temp_df['x']
    obs=csv.split('obs_')[-1].split('_CCF')[0]+'-2022'
    print(obs)
    cutoff_mad = mkplt(temp_x,fig,ax,c,obs=obs)
    outliers+=len(temp_x[temp_x<cutoff_mad])
    if plot_hits==True:
        # plot the hits
        input_commands = [csv, "-o", f"obs_{obs}_plots", "-col","x","-op","lt","-val",cutoff_mad,"-clobber"]
        process = subprocess.Popen(["python", "plot_DOT_hits.py"] + input_commands, stdout=subprocess.PIPE)
        output, error = process.communicate()
    full_df = pd.concat([full_df, temp_df],ignore_index=True)
# finalize the subplots
fig.tight_layout()
if save==True:
    ext='pdf'
    plt.savefig(outdir + f'MAD_subplots.{ext}',
                bbox_inches='tight',format=ext,dpi=fig.dpi,facecolor='white', transparent=False)
    print(f"Plot saved to {outdir}MAD_subplots.{ext}")
plt.show()
plt.close()

# sort and prep the combined data
full_df = full_df.sort_values(by='x').reset_index(drop=True)
obs = 'All'
x = full_df['x']
print(obs)
fig,ax=plt.subplots(1,1,figsize=(10,6))
mkplt(x,fig,ax,numx=4000)#,save=True,outdir=path)
save=False
if save==True:
    ext='pdf'
    plt.savefig(outdir + f'MAD_combined.{ext}',
                bbox_inches='tight',format=ext,dpi=fig.dpi,facecolor='white', transparent=False)
    print(f"Plot saved to {outdir}MAD_combined.{ext}")
plt.show()
plt.close()
# print(f'Total individual values below cutoffs: {outliers}')

# %%
