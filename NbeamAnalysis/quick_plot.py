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

import blimpy as bl

def sig_cor(s1,s2):
    ACF1=((s1*s1).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]
    ACF2=((s2*s2).sum(axis=1)).sum()/np.shape(s2)[0]/np.shape(s2)[1]
    DOT =((s1*s2).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]
    x=DOT/np.sqrt(ACF1*ACF2)
    return x

def wf_data(fil,f1,f2):
    return bl.Waterfall(fil,f1,f2).grab_data(f1,f2)

# define main plotting function
def plot_beams(name_array, fstart, fstop, drift_rate, SNR, x, save=False, path='/home/ntusay/scripts/temp/',ext='png'):
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
                 f'Drift Rate: {drift_rate:.3f} Hz/s ({drift_rate/f2*1000:.3f} nHz) || '+
                 f'SNR: {SNR:.3f}'+
                 f'\nCorrelation Score: {x:.3f}',
                 size=25)
    fig.tight_layout(rect=[0, 0, 1, 1.05])
    # show the plot
    if save==True:
        path=path
        plt.savefig(f'{path}MJD_{MJD}_SNR_{SNR:.3f}_DR_{drift_rate:.3f}_fstart_{fstart:.6f}.{ext}',
                    bbox_inches='tight',format=f'{ext}',dpi=fig.dpi,facecolor='white', transparent=False)
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
    ax.axvline(cutoff_mad, linestyle=':', linewidth=2, color='red', label=rf'Cutoff at {k:.1f} MADs (x = {cutoff_mad:.4f})')
    ax.set_ylabel('Number per Bin')
    ax.set_xlabel('Beam Correlation Scores')
    ax.legend(loc='upper left',title=f"Observations: {obs}")
    ax.set_xlim(-0.05,1.05)
    print(rf'Cutoff value: {cutoff_mad:.4f} at {k:.1f} MADs')
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
'''
Re-plot interesting beam plots to zoom out/get pdf version.
New correlation score calculated for this wider bandwidth.
Note that the first cell must be run to define the plot_beams function
'''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('/home/ntusay/scripts/NbeamAnalysis/plt_format.mplstyle')
import glob
import os

# input and output params
# 10-27
png='/home/ntusay/scripts/processed2/obs_10-27-2022_plots/MJD_59879_18519_X_0.483_SNR_11.703_fmax_8647.378070.png'
padding=50000 # Hz
png='/home/ntusay/scripts/processed2/obs_10-27-2022_plots/MJD_59879_20811_X_0.260_SNR_10.115_fmax_8243.525317.png'
padding=500000 # Hz
png='/home/ntusay/scripts/processed2/obs_10-27-2022_plots/MJD_59879_22298_X_0.532_SNR_992.480_fmax_6666.750284.png'
padding=50000 # Hz
png='/home/ntusay/scripts/processed2/obs_10-27-2022_plots/MJD_59879_29275_X_0.485_SNR_10.801_fmax_8654.361263.png'
padding=200000 # Hz
png='/home/ntusay/scripts/processed2/obs_10-27-2022_plots/MJD_59879_29275_X_0.503_SNR_10.445_fmax_8654.451684.png'
padding=50000 # Hz
# # 10-28
png='/home/ntusay/scripts/processed2/obs_10-28-2022_plots/MJD_59880_03124_X_0.085_SNR_13.402_fmax_1679.878538.png'
padding=5000 # Hz
png='/home/ntusay/scripts/processed2/obs_10-28-2022_plots/MJD_59880_04559_X_0.083_SNR_17.167_fmax_1989.579324.png'
padding=5000 # Hz
png='/home/ntusay/scripts/processed2/obs_10-28-2022_plots/MJD_59880_07504_X_0.004_SNR_167.142_fmax_1777.805030.png'
padding=2000 # Hz
# # 10-29
png='/home/ntusay/scripts/processed2/obs_10-29-2022_plots/MJD_59881_05127_X_0.207_SNR_16.948_fmax_2340.171170.png'
padding=5000 # Hz
# # 10-30
png='/home/ntusay/scripts/processed2/obs_10-30-2022_plots/MJD_59882_05307_X_0.088_SNR_37.716_fmax_4000.057944.png'
padding=20000 # Hz
# # 11-01
png='/home/ntusay/scripts/processed2/obs_11-01-2022_plots/MJD_59884_18785_X_0.896_SNR_192.699_fmax_8656.000274.png'
padding=700 # Hz
png='/home/ntusay/scripts/processed2/obs_11-01-2022_plots/MJD_59884_18785_X_0.815_SNR_10.947_fmax_8646.465056.png'
padding=300000 # Hz
png='/home/ntusay/scripts/processed2/obs_11-01-2022_plots/MJD_59884_19546_X_0.904_SNR_10.253_fmax_8646.486039.png'
padding=300000 # Hz
# # 11-02
png='/home/ntusay/scripts/processed2/obs_11-02-2022_plots/MJD_59885_13716_X_0.382_SNR_11.212_fmax_5333.403154.png'
padding=30000 # Hz
# # 11-05
png='/home/ntusay/scripts/processed2/obs_11-05-2022_plots/MJD_59888_07902_X_0.430_SNR_145.228_fmax_5777.858606.png'
padding=30000 # Hz
png='/home/ntusay/scripts/processed2/obs_11-05-2022_plots/MJD_59888_14276_X_0.314_SNR_12.313_fmax_7504.042134.png'
padding=2000 # Hz
# # 11-09
png='/home/ntusay/scripts/processed2/obs_11-09-2022_plots/MJD_59892_04666_X_0.622_SNR_23.137_fmax_7514.946641.png'
padding=2000 # Hz
png='/home/ntusay/scripts/processed2/obs_11-09-2022_plots/MJD_59892_10137_X_0.561_SNR_12.011_fmax_7499.998463.png'
padding=3500 # Hz
png='/home/ntusay/scripts/processed2/obs_11-09-2022_plots/MJD_59892_19322_X_0.425_SNR_17.969_fmax_8000.113800.png'
padding=20000 # Hz

save=True
save=False

# The rest will run automatically
png_dir=png.split('MJD_')[0]
pngs=sorted(glob.glob(png_dir+'*.png'))
csv = png.split('-2022_plots')[0]+'_CCFnbeam.csv'
outdir=f'{png_dir.split("-2022_plots")[0]}_interesting/'
if not os.path.exists(outdir):
    os.mkdir(outdir)

df=pd.read_csv(csv)
df=df.sort_values(by='x').reset_index(drop=True).iloc[:500]
pngMJD=png.split('/')[-1].split('MJD_')[-1].split('_X_')[0]
pngX=float(png.split('/')[-1].split('_X_')[-1].split('_SNR_')[0])
pngSNR=float(png.split('/')[-1].split('SNR_')[-1].split('_fmax_')[0])
pngfmax=float(png.split('/')[-1].split('fmax_')[-1].split('.png')[0])

for r,row in df.iterrows():
    MJD="_".join(row.dat_name.split('/')[-1].split("_")[1:3])
    fmax=max(row['freq_end'],row['freq_start'])
    if MJD==pngMJD and round(row['x'],3)==pngX and round(row['SNR'],3)==pngSNR and pngfmax==fmax:
        print(f'{csv.split("/")[-1].split("_CCF")[0]}\t\tIndex: {r}')
        print(f'MJD: {MJD}\tfmax: {row.freq_start}')
        print(f'SNR: {row.SNR:.3f}\t\tx: {row.x:.3f}')
        f1=row['freq_start']
        f2=row['freq_end']
        beams = list(row.filter(regex=r'fil_00..$'))
        plot_beams(beams,f1,f2,row['Drift_Rate'],row['SNR'],row['x'],save=save,path=outdir,ext='pdf')

        f1+=padding*1e-6
        f2-=padding*1e-6

        _,s1=wf_data(beams[0],f2,f1)
        _,s2=wf_data(beams[1],f2,f1)
        x=sig_cor(s1-np.median(s2),s2-np.median(s2))
        print(f'Correlation score over wider ({((f1-f2)*1e3):.3f} kHz) bandwidth: {x:.3f}')

        plot_beams(beams,f1,f2,row['Drift_Rate'],row['SNR'],x,save=save,path=outdir,ext='pdf')
# %%
# for r,row in df.iterrows():
#     MJD="_".join(row.dat_name.split('/')[-1].split("_")[1:3])
#     fmax=max(row['freq_end'],row['freq_start'])
#     if MJD==pngMJD and round(row['x'],3)==pngX and round(row['SNR'],3)==pngSNR and pngfmax==fmax:
#         print(f'{csv.split("/")[-1].split("_CCF")[0]}\t\tIndex: {r}')
#         print(f'MJD: {MJD}\tfmax: {row.freq_start}')
#         print(f'SNR: {row.SNR:.3f}\t\tx: {row.x:.3f}')
#         f1=row['freq_start']
#         f2=row['freq_end']
#         beams = list(row.filter(regex=r'fil_00..$'))
#         _,s1=wf_data(beams[0],f2,f1)
#         x=sig_cor(s1-np.median(s1),s1-np.median(s1))
#         print(f'Autocorrelation score on signal: {x:.3f}')
#         padding=150
#         f1-=padding*1e-6
#         f2-=padding*1e-6
#         _,s1=wf_data(beams[0],f2,f1)
#         _,s2=wf_data(beams[1],f2,f1)
#         x=sig_cor(s1-np.median(s1),s1-np.median(s1))
#         print(f'Autocorrelation score on noise: {x:.3f}')
#         x=sig_cor(s1-np.median(s2),s2-np.median(s2))
#         print(f'Correlation score on noise: {x:.3f}')
# %%
'''
Plotting the 3rd Injection Recovery test that failed:
'Weak' signal on top of RFI
'''
fil0='/home/ntusay/scripts/NbeamAnalysis/injection_test/fil_59884_17225_248799804_trappist1_0001-beam0000.fil'
fil1='/home/ntusay/scripts/NbeamAnalysis/injection_test/fil_59884_17225_248799804_trappist1_0001-beam0001.fil'
beams=[fil0,fil1]
f2 = 6881.280127
f1 = 6881.279876
drift_rate=-0.000993
SNR=79.161705
_,s1=wf_data(beams[0],f1,f2)
_,s2=wf_data(beams[1],f1,f2)
x=sig_cor(s1-np.median(s2),s2-np.median(s2))
path='/home/ntusay/scripts/NbeamAnalysis/injection_test/DOT_results/plots_fixed/failed_test/'
from plot_DOT_hits import plot_beams as pbs
pbs(beams, f1, f2, drift_rate, SNR, x, path, pdf=True)
# %%
