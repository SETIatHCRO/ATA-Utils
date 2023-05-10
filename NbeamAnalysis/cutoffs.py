'''
Cutoff calculation and plots using Median Absolute Deviation (MAD)
'''
# imports
import pandas as pd
import numpy as np
import matplotlib
import subprocess
import matplotlib.pyplot as plt
plt.style.use('/home/ntusay/scripts/NbeamAnalysis/plt_format.mplstyle')
import glob

# functions
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
    return cutoff_mad,k

# input and output params
path='/home/ntusay/scripts/processed2/'
outdir=path
save=True          # Set this to True to save the histogram plots
plot_hits=False     # Set this to True to plot all the hits below the cutoff

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
    cutoff_mad,k = mkplt(temp_x,fig,ax,c,obs=obs)
    outliers+=len(temp_x[temp_x<cutoff_mad])
    if plot_hits==True:
        # plot the hits
        input_commands = [csv, "-o", f"{outdir}/obs_{obs}_plots/","-col","x","-op","lt","-val",cutoff_mad,"-clobber"]
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
mkplt(x,fig,ax,numx=4000)
if save==True:
    ext='pdf'
    plt.savefig(outdir + f'MAD_combined.{ext}',
                bbox_inches='tight',format=ext,dpi=fig.dpi,facecolor='white', transparent=False)
    print(f"Plot saved to {outdir}MAD_combined.{ext}")
plt.show()
plt.close()
print(f'Total individual values below cutoffs: {outliers}')