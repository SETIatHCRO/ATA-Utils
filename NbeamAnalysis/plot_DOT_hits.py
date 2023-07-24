# This program plots the hits listed in a csv comparing multiple beams 
# formed in the field of view of a single observation.
# This will work for any number of beams.
# The input will take any csv file, but it should be structured with columns:
# ,drift_rate,SNR,freq_start,freq_end,onfile,offfile,datdir
# Note that the onfile should be listed first, and all offfiles should come after

    # Import packages
import numpy as np
import pandas as pd
import blimpy as bl
import os, glob
import math
import argparse
import time
import matplotlib
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})

import plot_utils as ptu

    # Define Functions
# parse the input arguments. 
# required: csv containing the hits to be plotted 
def parse_args():
    parser = argparse.ArgumentParser(description='Process ATA 2beam filterbank data.')
    parser.add_argument('csv', metavar='/plot_target_csv/', type=str, nargs=1,
                        help='CSV file with correlation scores for target beam hits')
    parser.add_argument('-o', '--outdir',metavar="", type=str, nargs=1,
                        help='output target directory')
    parser.add_argument('-col',metavar="", type=str, default=None,
                        help='Name of the column in the csv to filter on')
    parser.add_argument('-op',metavar="", type=str, choices=['lt', 'gt', 'is'], default=None,
                        help='Operator for filtering: less than (lt), greater than (gt), or equal to (is)')
    parser.add_argument('-val',metavar="", type=str, default=None, help='Filter value')
    parser.add_argument('-clobber', action='store_true',
                        help='overwrite files if they already exist')
    parser.add_argument('-pdf', action='store_true',
                        help='plot file format as pdf (default is png)')
    parser.add_argument('-DR', action='store_true',
                        help='flag to plot frequency range using drift rate instead of given span')
    args = parser.parse_args()
    odict = vars(args)
    if odict["outdir"]:
        outdir = odict["outdir"][0]
        if outdir[-1] != "/":
            outdir += "/"
        odict["outdir"] = outdir  
    return odict

# elapsed time function
def get_elapsed_time(start=0):
    end = time.time() - start
    time_label = 'seconds'    
    if end > 3600:
        end = end/3600
        time_label = 'hours'
    elif end > 60:
        end = end/60
        time_label = 'minutes'
    return end, time_label

# clobber function to remove old files (optional)
def purge(dir, pattern):
    old_plots = glob.glob(dir+pattern)
    print(f'\nRemoving {len(old_plots)} old plots from {dir}\n')
    for f in old_plots:
        os.remove(f)

# plot the hit using the plotting function from plot_target_utils.py
def plot_beams(name_array, fstart, fstop, drift_rate, SNR, x, path, pdf=False):
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
    # save the plot
    if pdf==True:
        ext='pdf'
    else:
        ext='png'
    plt.savefig(f'{path}MJD_{MJD}_X_{x:.3f}_SNR_{SNR:.3f}_fmax_{f2:.6f}.{ext}',
                bbox_inches='tight',format=ext,dpi=fig.dpi,facecolor='white', transparent=False)
    plt.close()
    return None

    # Main program execution
def main():
    print("\nExecuting program...")
    start=time.time()

    # parse any command line arguments
    cmd_args = parse_args()
    csv = cmd_args["csv"][0]            # required input
    outdir = cmd_args["outdir"]         # optional, default to datdir listed in csv
    column = cmd_args["col"]            # optional, default None
    operator = cmd_args["op"]           # optional, default None
    value = cmd_args["val"]             # optional, default None
    clobber = cmd_args["clobber"]       # optional, flag on or default off
    pdf = cmd_args["pdf"]               # optional, flag on or default off
    DR = cmd_args["DR"]                 # optional, flag on or default off
    paths_cleared=[]                    # clobber counter

    # load the csv into a df and filter based on the input parameters
    df = pd.read_csv(csv)
    if not column or not operator or not value:
        print(f"Default filtering: 500 lowest scoring hits.")
        signals_of_interest = df.sort_values(by='x').reset_index(drop=True).iloc[:500]
        print(f"Max score in this set: {signals_of_interest.iloc[-1].x:.3f}")
    else:
        # Infer the data type of the column from the dataframe
        column_dtype = df[column].dtype
        # Convert filter value to the correct data type
        value = column_dtype.type(value)
        # Apply the filter based on the operator
        if operator == 'lt':
            signals_of_interest = df[df[column] < value]
        elif operator == 'gt':
            signals_of_interest = df[df[column] > value]
        elif operator == 'is':
            signals_of_interest = df[df[column] == value]
        signals_of_interest = signals_of_interest.sort_values(by='x').reset_index(drop=True)
    print(f"{len(signals_of_interest)}/{len(df)} total hits from the input dataframe will be plotted.")

    # iterate through the csv of interesting hits and plot row by row
    for index, row in signals_of_interest.reset_index(drop=True).iterrows():
        # make an array of the filenames for each beam based on the column names
        beams = [row[i] for i in list(signals_of_interest) if i.startswith('fil_')]
        # set the path where the plots will be saved (optionally remove old plots with clobber)
        if not outdir:
            path="/".join(csv.split("/")[:-1])+f'/{csv.split("/")[-1].split(".")[0]}_plots/'
        else:
            path=outdir
        if not os.path.exists(path):
            os.mkdir(path)
        if clobber and path not in paths_cleared:
            purge(path,'*.png')
            paths_cleared.append(path)
        # determine frequency range for plot
        fstart = row['freq_start']
        fend = row['freq_end']
        if DR==True:
            fmid=(fstart+fend)/2
            searchfile=open(row['dat_name'],'r').readlines()
            for line in searchfile:
                if 'obs_length: ' in line:
                    obs_length=float(line.split('\n')[0].split('obs_length: ')[-1])
            half_span=row['Drift_Rate']*obs_length
            if half_span<250:
                half_span=250
            fstart=round(fmid+half_span*1e-6,6)
            fend=round(fmid-half_span*1e-6,6)
        # plot
        print(f'Plotting {index}/{len(signals_of_interest)} starting at {row["freq_start"]:.6f} MHz, correlation score: {row["x"]:.3f}')
        plot_beams(beams,
                    fstart,
                    fend,
                    row['Drift_Rate'],
                    row['SNR'],
                    row['x'],
                    path,
                    pdf)

    # This block prints the elapsed time of the entire program.
    end, time_label = get_elapsed_time(start)
    print(f"\n\t{len(signals_of_interest)} hits plotted in %.2f {time_label}.\n" %end)
    return None
# run it!
if __name__ == "__main__":
    main()