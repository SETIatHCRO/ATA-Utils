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
    parser.add_argument("-freqs", type=list_parser, nargs="+", help="optional tuple of frequencies")
    args = parser.parse_args()
    odict = vars(args)
    if odict["outdir"]:
        outdir = odict["outdir"][0]
        if outdir[-1] != "/":
            outdir += "/"
        odict["outdir"] = outdir  
    return odict

# function to help parse space separated tuple input from command line 
def list_parser(input_str):
    try:
        # Split the input string by spaces and convert each element to a float
        parsed_list = list(map(float, input_str.split()))
        return parsed_list[0]
    except ValueError:
        raise argparse.ArgumentTypeError("Invalid list format. Use space-separated floating-point numbers.")

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
def plot_beams(name_array, fstart, fstop, drift_rate=None, SNR=None, SNRr=None, x=None, path='./', pdf=False):
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
    filename=ptu.make_title(fig,MJD,f2,drift_rate,SNR,SNRr,x)
    # save the plot
    if pdf==True:
        ext='pdf'
    else:
        ext='png'
    plt.savefig(f'{path}{filename}.{ext}',
                bbox_inches='tight',format=ext,dpi=fig.dpi,facecolor='white', transparent=False)
    plt.close()
    return None

def plot_by_freqs(df0,freqs,path,pdf):
    df = df0.drop_duplicates(subset="dat_name", keep="first")
    for index, row in df.reset_index(drop=True).iterrows():
        beams = [row[i] for i in list(df) if i.startswith('fil_')]
        fstart=max(freqs)
        fend=min(freqs)
        print(f'Plotting {index+1}/{len(df)} from {fend:.6f} MHz to {fstart:.6f} MHz\n{row["dat_name"]}\n')
        plot_beams(beams,fstart,fend,path=path,pdf=pdf)
    return len(df)

def filter_df(df,column,operator,value):
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
    return signals_of_interest

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
    freqs = cmd_args["freqs"]           # optional, custom frequency span
    paths_cleared=[]                    # clobber counter

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

    # load the csv into a df and filter based on the input parameters
    df = pd.read_csv(csv)
    if freqs: # circumvent regular plotting in the case of bespoke frequency bounds
        if not column or not operator or not value:
            num_plots = plot_by_freqs(df,freqs,path,pdf)
        else:
            signals_of_interest = filter_df(df,column,operator,value)
            num_plots = plot_by_freqs(signals_of_interest,freqs,path,pdf)
        # This block prints the elapsed time of the entire program.
        end, time_label = get_elapsed_time(start)
        print(f"\n\t{num_plots} hits plotted in %.2f {time_label}.\n" %end)
        return None
    elif not column or not operator or not value:
        print(f"Default filtering: 500 lowest scoring hits.")
        signals_of_interest = df.sort_values(by='x').reset_index(drop=True).iloc[:500]
        print(f"Max score in this set: {signals_of_interest.iloc[-1].x:.3f}")
    else:
        signals_of_interest = filter_df(df,column,operator,value)
    print(f"{len(signals_of_interest)}/{len(df)} total hits from the input dataframe will be plotted.")

    # iterate through the csv of interesting hits and plot row by row
    for index, row in signals_of_interest.reset_index(drop=True).iterrows():
        # make an array of the filenames for each beam based on the column names
        beams = [row[i] for i in list(signals_of_interest) if i.startswith('fil_')]
        
        # determine frequency range for plot
        fstart = row['freq_start']
        fend = row['freq_end']

        # determine frequency span over which to plot based on drift rate
        fmid=row['Corrected_Frequency']
        fil_meta=bl.Waterfall(beams[0],load_data=False)
        obs_length=fil_meta.n_ints_in_file * fil_meta.header['tsamp']
        half_span=abs(row['Drift_Rate'])*obs_length*1.2  # x1.2 for padding
        if half_span<250:
            half_span=250
        fstart=round(fmid+half_span*1e-6,6)
        fend=round(fmid-half_span*1e-6,6)
        
        # plot
        print(f'Plotting {index+1}/{len(signals_of_interest)} starting at {fstart:.6f} MHz, X score: {row["x"]:.3f}')
        plot_beams(beams,
                    fstart,
                    fend,
                    row['Drift_Rate'],
                    row['SNR'],
                    row['SNR_ratio'],
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