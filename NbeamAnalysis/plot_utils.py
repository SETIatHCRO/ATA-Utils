'''
plotting utility functions mainly used in plot_DOT_hits.py
'''

    # Import packages
import numpy as np
import pandas as pd
import blimpy as bl
import os, sys
import math
from functools import reduce
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator
from matplotlib.ticker import NullFormatter
import DOT_utils as DOT
plt.rcParams.update({'font.size': 22})
plt.rcParams['axes.formatter.useoffset'] = False

# Check if $DISPLAY is set (for handling plotting on remote machines with no X-forwarding)

if 'DISPLAY' in os.environ.keys():
    import pylab as plt
else:
    matplotlib.use('Agg')
    import pylab as plt

MAX_PLT_POINTS      = 65536                  # Max number of points in matplotlib plot
MAX_IMSHOW_POINTS   = (8192, 4096)           # Max number of points in imshow plot

    # Define Functions
def db(x, offset=0):
    """ Convert linear to dB """
    return 10 * np.log10(x + offset)

def normalize(x,xmin=None,xmax=None):
    if xmin==None:
        xmin=x.min()
    if xmax==None:
        xmax=x.max()
    return (x-xmin)/(xmax-xmin)

def rebin(d, n_x=None, n_y=None, n_z=None):
    """ Rebin data by averaging bins together
    Args:
    d (np.array): data
    n_x (int): number of bins in x dir to rebin into one
    n_y (int): number of bins in y dir to rebin into one
    Returns:
    d: rebinned data with shape (n_x, n_y)
    """
    if n_x is None:
        n_x = 1
    else:
        n_x = math.ceil(n_x)
    if n_y is None:
        n_y = 1
    else:
        n_y = math.ceil(n_y)
    if n_z is None:
        n_z = 1
    else:
        n_z = math.ceil(n_z)
    if d.ndim == 3:
        d = d[:int(d.shape[0] // n_x) * n_x, :int(d.shape[1] // n_y) * n_y, :int(d.shape[2] // n_z) * n_z]
        d = d.reshape((d.shape[0] // n_x, n_x, d.shape[1] // n_y, n_y, d.shape[2] // n_z, n_z))
        d = d.mean(axis=5)
        d = d.mean(axis=3)
        d = d.mean(axis=1)
    elif d.ndim == 2:
        d = d[:int(d.shape[0] // n_x) * n_x, :int(d.shape[1] // n_y) * n_y]
        d = d.reshape((d.shape[0] // n_x, n_x, d.shape[1] // n_y, n_y))
        d = d.mean(axis=3)
        d = d.mean(axis=1)
    elif d.ndim == 1:
        d = d[:int(d.shape[0] // n_x) * n_x]
        d = d.reshape((d.shape[0] // n_x, n_x))
        d = d.mean(axis=1)
    else:
        raise RuntimeError("Only NDIM <= 3 supported")
    return d

def calc_extent(plot_f=None, plot_t=None, MJD_time=False):
    """ Setup plotting edges.
    """
    plot_f_begin = plot_f[0]
    plot_f_end = plot_f[-1] + (plot_f[1] - plot_f[0])
    span = np.abs(plot_f_begin - plot_f_end)
    if span > 1:
        factor=1
    elif span*10**3>1:
        factor=10**3
    elif span*10**6>1:
        factor=10**6
    else:
        factor=10**9
    plot_f_begin = span/2*factor
    plot_f_end = span/-2*factor
    plot_t_begin = plot_t[0]
    plot_t_end = plot_t[-1] + (plot_t[1] - plot_t[0])
    if MJD_time:
        extent = (plot_f_begin, plot_f_end, plot_t_begin, plot_t_end)
    else:
        extent = (plot_f_begin, plot_f_end, 0.0, (plot_t_end - plot_t_begin) * 24. * 60. * 60)
    return extent

# subplotting workhorse function. Actually gets the data and adds it to the subplots.
def plot_waterfall_subplots(plot_f, plot_data, plot_t, i, ax, fig, axes, f_start=None, f_stop=None, 
                            xmin=None, xmax=None, logged=True, cb=True, MJD_time=False, **kwargs):
    # imshow does not support int8, so convert to floating point
    plot_data = plot_data.astype('float32')
    # plot the power in logspace unless the data is weird and has zeroes or negatives
    if logged:
        if not plot_data.all()<=0.0:
            plot_data = db(plot_data)
    # Make sure waterfall plot is under 4k*4k
    dec_fac_x, dec_fac_y = 1, 1
    if plot_data.shape[0] > MAX_IMSHOW_POINTS[0]:
        dec_fac_x = int(plot_data.shape[0] / MAX_IMSHOW_POINTS[0])
    if plot_data.shape[1] > MAX_IMSHOW_POINTS[1]:
        dec_fac_y = int(plot_data.shape[1] / MAX_IMSHOW_POINTS[1])
    plot_data = rebin(plot_data, dec_fac_x, dec_fac_y)
    # normalize the power to the range of the target beam
    if xmin==None or xmax==None:
        xmin=plot_data.min()
        xmax=plot_data.max()
    plot_data = normalize(plot_data,xmin,xmax)
    # calculate the plot extent/axes and make the subplot
    extent = calc_extent(plot_f=plot_f, plot_t=plot_t, MJD_time=MJD_time)
    im = ax.imshow(plot_data,
               aspect='auto',
               origin='lower',
               rasterized=True,
               interpolation='nearest',
               extent=extent,
               cmap='viridis',
               vmin=0, 
               vmax=1,
               **kwargs)
    if np.shape(np.shape(axes))[0]>1:
        nrows=np.shape(axes)[0]
        ncols=np.shape(axes)[1]
    else:
        nrows=1
        ncols=len(axes)
    # add colorbar
    if cb and i%ncols==ncols-1:
        fig.colorbar(im, ax=ax, shrink=0.9, pad=0.01)
    # get the x-axis label right for the frequency scale
    if np.abs(plot_f[0]-plot_f[-1]) > 1:   
        label = 'MHz'
    elif np.abs(plot_f[0]-plot_f[-1])*10**3 > 1:
        label = 'kHz'
    elif np.abs(plot_f[0]-plot_f[-1])*10**6 > 1:
        label = 'Hz'
    else:
        label = 'GHz?'
    freq_mid = (plot_f[1]+plot_f[-1])/2   
    if i//ncols==nrows-1: 
        ax.set_xlabel(f"Frequency [{label}]\nCentered at {freq_mid:.6f} MHz")
        ax.tick_params(axis='x', which='major', labelsize=22)
        ax.tick_params(axis='x', which='minor', labelsize=14)
    else:
        ax.set_xticklabels([])
    # set the y-axis label
    if MJD_time and i%ncols==0:
        ax.set_ylabel("Time [MJD]")
    elif i%ncols==0:
        ax.set_ylabel("Time [s]")
    else:
        ax.set_yticklabels([])
    return 

# makes both the title of the plot and the filename
def make_title(fig,MJD,f2,fmid,drift_rate,SNR,corrs,SNRr,x=None):
    title=f'MJD: {MJD} || fmax: {f2:.6f} MHz'
    filename=f"MJD_{MJD}_fmid{fmid:.6f}"
    if drift_rate:
        title+=f' || Drift Rate: {drift_rate:.3f} Hz/s ({drift_rate/f2*1000:.3f} nHz)'
        filename+=f"_DR{drift_rate:.3f}"
    if SNR:
        title+=f'\nturboSETI SNR: {SNR:.2f}'
    if corrs:
        title+=f' || DOT Score: {corrs:.2f}'
        filename+=f"_x{corrs:.2f}"
    if SNRr:
        title+=f' || SNR ratio: {SNRr:.2f}'
        filename+=f"_SNRr{SNRr:.2f}"
    # if x:
    #     title+=f' || X score: {x:.3f}'
    #     filename+=f"_X_{x:.3f}"
    fig.suptitle(title,size=25)
    return filename

def customize_subplot_frame(ax, linewidth=8, color='r'):
    ax.spines['top'].set_linewidth(linewidth)
    ax.spines['bottom'].set_linewidth(linewidth)
    ax.spines['left'].set_linewidth(linewidth)
    ax.spines['right'].set_linewidth(linewidth)
    ax.spines['top'].set_color(color)
    ax.spines['bottom'].set_color(color)
    ax.spines['left'].set_color(color)
    ax.spines['right'].set_color(color)
    return None

# first plotting function that sets up the plot, 
# sends info to the subplotter, gets the title and saves the plot.
def plot_beams(name_array, fstart, fstop, drift_rate=None, nstacks=1, nbeams=2, MJD=None, 
                target=0, SNR=None, corrs=None, SNRr=None, path='./', pdf=False):
    # make waterfall objects for plotting from the filenames
    wf_obj_array = []
    f1 = min(fstart,fstop)
    f2 = max(fstart,fstop)
    fmid=round((f2+f1)/2,6)
    for fil in name_array:
        wf_obj = bl.Waterfall(fil, 
                            f_start=f1, 
                            f_stop=f2)
        wf_obj_array.append(wf_obj)
    # initialize the plot
    nsubplots = len(name_array)
    fig, axes = plt.subplots(nrows=nstacks, ncols=nbeams, 
                            figsize=(11*nbeams,7*nstacks), 
                            gridspec_kw={'width_ratios': [1, 1.2]})
    fig.subplots_adjust(hspace=0.07, wspace=0.04)
    # collect target data for min/max normalizing
    target_f, target_data = wf_obj_array[target].grab_data(min(f1, f2),max(f1, f2), 0)
    if not target_data.all()<=0.0:
        xmin=db(target_data).min()
        xmax=db(target_data).max()
    else:
        xmin=target_data.min()
        xmax=target_data.max()
    rowSNRs=[]
    target_col=target%nbeams
    target_row=target//nbeams
    # call the plotting function and plot the waterfall objects in wf_obj_array
    for i in range(nsubplots):
        # get plot data
        plot_f, plot_data = wf_obj_array[i].grab_data(min(f1, f2),max(f1, f2))
        plot_t = wf_obj_array[i].timestamps
        # calculate SNR for this data
        rowSNRs.append(DOT.mySNR(plot_data))
        # initialize the subplot axis and feed it to the plotting function
        ax = [axes[i//nbeams,i%nbeams] if nstacks>1 else axes[i]][0]
        plot_waterfall_subplots(plot_f, plot_data, plot_t, i, ax, fig, axes,
                                f_start=f1, f_stop=f2, xmin=xmin, xmax=xmax)
        # set subplot titles for target and off-target beams
        if i%nbeams==target_col:
            subplot_title=f"target beam "
        else:
            subplot_title=f"off beam "
        # MJD in number of secs (i.e. out of 86400, not out of 100000)
        sub_MJD="_".join(os.path.basename(name_array[i]).split("_")[1:3])
        if not MJD and i==target:
            MJD=sub_MJD
        # MJD only necessary for subplot titles when stacking
        if nstacks>1: 
            subplot_title+=f"MJD: {sub_MJD} || "
        # target beam gets my SNR label
        if i%nbeams==target_col: 
            subplot_title+=f"SNR: {rowSNRs[i%nbeams]:.2f}"
        # off-target beam gets SNRr relative to target beam
        if i%nbeams!=target_col and target_col==0: 
            subplot_title+=f"SNR ratio: {rowSNRs[target_col]/rowSNRs[i%nbeams]:.2f}"
        elif nstacks>1 and target_col!=0: # this will probably break if the target beam isn't 0
            print(f"\tTarget beam: {target_col} not first column of subplots. Cannot report SNRr.")
        elif SNRr and target_col!=0:
            subplot_title+=f"SNR ratio: {SNRr:.2f}"
        if i%nbeams==nbeams-1 and nstacks>1:
            rowSNRs=[]  # reset SNR array at the end of each row of subplots
        ax.set_title(subplot_title,pad=10)
        if target//nbeams == i//nbeams and nstacks>1:
            customize_subplot_frame(ax) # add bold colored frame to identify target when stacking
    # set the overall plot title and filename
    filename=make_title(fig,MJD,f2,fmid,drift_rate,SNR,corrs,SNRr)
    # tighten up the plots and adjust the spacing
    if nstacks>1:
        fig.tight_layout(rect=[0, 0, 1.0, 1.0])
        fig.subplots_adjust(hspace=0.11, wspace=0.02)
    else:
        fig.tight_layout(rect=[0, 0, 1, 1.05])
    # save the plot
    if pdf==True:
        ext='pdf'
    else:
        ext='png'
    plt.savefig(f'{path}{filename}{["_stacked" if nstacks>1 else ""][0]}.{ext}',
                bbox_inches='tight',format=ext,dpi=fig.dpi,facecolor='white', transparent=False)
    plt.close()
    return None

# initial function to set up plotting by manually input frequencies
def plot_by_freqs(df0,obs_dir,freqs,stack=None,nbeams=2,tbeam=0,drift_rate=None,
                    MJD=None,SNR=None,corrs=None,SNRr=None,path="./",pdf=None):
    df = df0.drop_duplicates(subset="dat_name", keep="first").reset_index(drop=True)
    fstart=max(freqs)
    fend=min(freqs)
    for index, row in df.iterrows():
        fil_names = [row[i] for i in list(df) if i.startswith('fil_')]
        target_fil=fil_names[tbeam]
        if check_freqs(target_fil,freqs)=='out_of_bounds':
            # print(f"Input frequencies {freqs} not within the frequency span of the data in",
            #         f"\n{target_fil.split(obs_dir)[-1]}\nSkipping this file.")
            df.drop(index, inplace=True)
    for index, row in df.reset_index(drop=True).iterrows():
        fil_names = [row[i] for i in list(df) if i.startswith('fil_')]
        target_fil=fil_names[tbeam]
        if stack>=1:
            fil_names=get_stacks(fil_names,obs_dir,nbeams,stack)
            nstacks=int(len(fil_names)/nbeams)
            target_idx=fil_names.index(target_fil)
        else:
            target_idx=tbeam
            nstacks=1
        MJD="_".join(os.path.basename(target_fil).split("_")[1:3]) # MJD in number of secs
        print(f'Plotting {index+1}/{len(df)} from {fend:.6f} MHz to {fstart:.6f} MHz\n{row["dat_name"]}\n')
        if len(df)==1:
            drift_rate=row['Drift_Rate']
            SNR=row['SNR']
            corrs=row['corrs']
            SNRr=row['SNR_ratio']
        plot_beams(fil_names, fstart, fend, drift_rate, nstacks, nbeams, 
                    MJD, target_idx, SNR, corrs, SNRr, path, pdf)
    return len(df)

# used in plot_by_freqs() to check if the frequencies are within 
# the bounds of the filterbank file 
def check_freqs(fil,freqs):
    fil_meta = bl.Waterfall(fil,load_data=False)
    minimum_frequency = fil_meta.container.f_start
    maximum_frequency = fil_meta.container.f_stop
    for freq in freqs:
        if freq>maximum_frequency or freq<minimum_frequency:
            return 'out_of_bounds'
    return 'within_bounds'

# for a given observation with multiple integrations, stacking of plots is available.
# this function finds the other fils associated with the other integrations to stack.
def get_stacks(target_fils,obs_dir,nbeams,stack):
    fil_names=target_fils.copy()
    # get the subdirectory tree structure including file in the input observation directory
    subdir_filepath=target_fils[0].split(obs_dir)[-1]
    file_depth=subdir_filepath.count("/")
    # get the MJD from the filename to mask it from the search
    fil_MJD="_".join(target_fils[0].split('/')[-1].split("_")[1:3])
    if len(fil_MJD)!=11:
        print(f"\n\tERROR: MJD not recovered correctly from filename. Cannot stack plots.")
        sys.exit()
    # determine unique subdirectories in the filepath, typically indicating a specific frequency range
    unique_subs=[i for i in subdir_filepath.split("/") if fil_MJD not in i]
    # get the file extension, whether fil or h5 or whatever
    ext=os.path.splitext(target_fils[0])[-1]
    # walk through all subdirectories and search for similar files at
    # the same depth, within similar unique subfolders if any, and with different MJDs
    for dirpath, dirnames, filenames in os.walk(obs_dir):
        current_depth=(dirpath+["" if dirpath==obs_dir else "/"][0]).count("/")-obs_dir.count("/")
        subpath=dirpath.split(obs_dir)[-1]
        if all(sub in subpath for sub in unique_subs) and current_depth==file_depth:
            for f in filenames:
                if fil_MJD not in f and f.endswith(ext):
                    # if get_frange(dirpath+["" if dirpath==obs_dir else "/"][0]+f) == [round(f1,6),round(f2,6)]:
                    fil_names.append(dirpath+["" if dirpath==obs_dir else "/"][0]+f)
    fil_names = sorted(eject_isolates(fil_names,nbeams),reverse=True)
    targets=[fil_names.index(i) for i in target_fils]
    fils_per_layer=stack*nbeams
    stack_start=max(0,min(targets)-fils_per_layer)
    stack_end=min(max(targets)+fils_per_layer+1,len(fil_names))
    stacked=fil_names[stack_start:stack_end]
    return [x for sublist in (reversed(stacked[i:i+nbeams]) for i in range(0, len(stacked), nbeams)) for x in sublist]

# helper function to eliminate errant single files without companion beams
def eject_isolates(fil_names,nbeams):
    for f in fil_names:
        beam=f.split("beam")[-1].split(".")[0]
        for b in range(nbeams):
            if beam==str(b).zfill(4):
                continue
            elif f.replace("beam"+beam,"beam"+str(b).zfill(4)) not in fil_names:
                fil_names.remove(f)
    return fil_names
            
# helper function to return min/max frequency range of a filterbank file from metadata
def get_frange(f):
    fil_meta = bl.Waterfall(f,load_data=False)
    f1 = fil_meta.container.f_start
    f2 = fil_meta.container.f_stop
    return [round(f1,6),round(f2,6)]

# helper function for determining commonality in a list of strings
def longest_common_substring(str1, str2):
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_length, end_index = 0, 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = dp[i - 1][j - 1] + 1 if str1[i - 1] == str2[j - 1] else 0
            if dp[i][j] > max_length:
                max_length, end_index = dp[i][j], i - 1
    return str1[end_index - max_length + 1:end_index + 1]

# determine the observation directory from the commonality in the filepath strings
def get_obs_dir(fils_list):
    lcs = reduce(longest_common_substring, fils_list)
    return ["/".join(lcs.split("/")[:-1])+"/" if "/"!=lcs[-1] else lcs][0]
    

# plots the histograms showing snr, frequency, and drift rates of all the hits
# mainly just used at the end of DOTnbeam or DOTparallel
def diagnostic_plotter(df, tag, saving=False, log=True, outdir='./'):
    # initialize figure with subplots
    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=((20,5)))
    label_size=20
    tick_label_size=14
    tick_size=4
    w=2
    # snr histogram subplot
    s=0
    ax[s].semilogy()
    ax[s].tick_params(axis='both', which='major', size=tick_size, labelsize=tick_label_size, width=w)
    ax[s].set_xlabel('SNR',size=label_size)
    ax[s].set_ylabel('Count',size=label_size)
    ax[s].set_title('SNR Distribution',size=label_size)
    ax[s].hist(df['SNR'], 
         bins=100,
         range=[0,1000],
        color='rebeccapurple');
    # freq histogram subplot
    s=1
    if log == True:
        ax[s].semilogy()
    ax[s].tick_params(axis='both', which='major', size=tick_size, labelsize=tick_label_size, width=w)
    ax[s].set_xlabel('Frequency (GHz)',size=label_size)
    ax[s].set_ylabel('Count',size=label_size)
    ax[s].set_title('Frequency Distribution',size=label_size)
    ax[s].hist(df['Corrected_Frequency'], 
        bins=100,
        color='teal');
    # drift rate histogram subplot
    s=2
    ax[s].semilogy()
    ax[s].tick_params(axis='both', which='major', size=tick_size, labelsize=tick_label_size, width=w)
    ax[s].set_xlabel('Drift Rate (nHz)',size=label_size)
    ax[s].set_ylabel('Count',size=label_size)
    ax[s].set_title('Drift Rate Distribution',size=label_size)
    ax[s].hist(df['normalized_dr'], 
         bins=100,
        color='firebrick');
    # adjust layout and save figure
    fig.text(0.5, 0.98, tag.replace('sfh','spatially_filtered_hits').replace('_',' '), va='top', ha='center', size=26)
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    if saving == True:
        plt.savefig(outdir + tag + '_diagnostic_plots.jpg')
        plt.close()
    else:
        plt.show()
    return None