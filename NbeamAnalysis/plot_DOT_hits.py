'''
This program plots hits listed in the csv that is output from DOTnbeam or DOTparallel.
The output waterfall plots are generated using information in the csv dataframe to access and 
plot the filterbank data for each beam over the time and frequency of the hit detected in the 
target beam. The waterfall colormap of each subplot is scaled to the data in the target beam.

Note that although the only input file is a csv file, that csv file should contain filepaths 
to the filterbank files needed to be accessed in order to generate the plots.

plot_utils.py is required for modularized functions.

Typical basic command line usage looks something like:
    python NbeamAnalysis/plot_DOT_hits.py <path_to_csv> -o <output_dir>

There are 3 main plotting modes:
    1.  Default plotting first filters all hits above the nominal cutoff, calculated as
        SNR-ratios above 0.9*sf*x^2, where sf is the attenuation value (default=4.0),
        x is the correlation score and 0.9 is included for padding. If there are more than 
        500 (this number is adjustable with the -cutoff input flag) hits above this cutoff, 
        the hits are sorted by SNR-ratio. If more than 500 have SNR-ratios above sf, 
        attenuation value, then they are sorted by correlation score and the 500 lowest 
        scoring hits are plotted. 

    2.  Custom column sorting and plotting is available through optional input arguments.
        All hits can be plotted through clever employment of the optional input arguments, if desired.

    3.  Individual plots over specified a frequency range can be made with the "-freqs" flag 
        by specifying the start and end frequencies. Note that without additional sorting/filtering, 
        this will produce a plot for each unique dat/fil in the dataframe 
        that span the specified frequencies.
'''

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
    parser.add_argument('-sf', type=float, default=4.0,
                        help='optional attenuation value for filtering')
    parser.add_argument('-cutoff', type=int, default=500,
                        help='optionally set the number of plots above cutoff in default plotting mode')
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

# filter dataframe on optional input parameters
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
    # signals_of_interest = signals_of_interest.sort_values(by='x').reset_index(drop=True)
    signals_of_interest = signals_of_interest.sort_values(by='SNR_ratio',ascending=False).reset_index(drop=True)
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
    sf = cmd_args["sf"]                 # optional, default = 4.0
    cutnum = cmd_args["cutoff"]         # optional, default = 500
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
        if pdf:
            ext='*.pdf'
        else:
            ext='*.png'
        purge(path,ext)
        paths_cleared.append(path)

    # load the csv into a dataframe and filter based on the input parameters
    df = pd.read_csv(csv)

    # plotting mode 1: circumvent regular plotting in the case of bespoke frequency bounds 
    if freqs:
        if not column or not operator or not value:
            num_plots = plot_by_freqs(df,freqs,path,pdf)
        else:
            signals_of_interest = filter_df(df,column,operator,value)
            num_plots = ptu.plot_by_freqs(signals_of_interest,freqs,path,pdf)
        end, time_label = get_elapsed_time(start)
        print(f"\n\t{num_plots} hits plotted in %.2f {time_label}.\n" %end)
        # This is where the program ends for this plotting mode.
        return None
    # plotting mode 2: default plotting
    elif not column or not operator or not value:
        print(f"\nDefault filtering:\nUp to the {cutnum} lowest correlation scores with an SNR-ratio above the attenuation value of {sf:.2f}\n")
        xcutoff=np.linspace(-0.5,1.5,20)
        ycutoff=0.9*sf*xcutoff**2
        dfx=df[np.interp(df.corrs,xcutoff,ycutoff)<df.SNR_ratio].reset_index(drop=True)
        dfx=dfx.sort_values(by='SNR_ratio',ascending=False).reset_index(drop=True)
        if len(dfx[dfx.SNR_ratio>sf])>cutnum:
            dfx=dfx[dfx.SNR_ratio>sf].reset_index(drop=True)
            signals_of_interest = dfx.sort_values(by='corrs',ascending=True).reset_index(drop=True).iloc[:cutnum]
        else:
            signals_of_interest = dfx.iloc[:cutnum]
        print(f"Min score in this set: {signals_of_interest.iloc[0].corrs:.3f}")
        print(f"Max score in this set: {signals_of_interest.iloc[-1].corrs:.3f}")
    # plotting mode 3: custom dataframe filtering from input arguments
    else:
        signals_of_interest = filter_df(df,column,operator,value)

    print(f"{len(signals_of_interest)} hits will be plotted out of {len(df)} total from the input dataframe.")

    # iterate through the csv of interesting hits and plot row by row
    for index, row in signals_of_interest.reset_index(drop=True).iterrows():
        # make an array of the filenames for each beam based on the column names
        beams = [row[i] for i in list(signals_of_interest) if i.startswith('fil_')]
        
        # determine frequency range for plot
        fstart = row['freq_start']
        fend = row['freq_end']

        # determine frequency span over which to plot based on drift rate
        fil_meta = bl.Waterfall(beams[0],load_data=False)
        minimum_frequency = fil_meta.container.f_start
        maximum_frequency = fil_meta.container.f_stop
        tsamp = fil_meta.header['tsamp']    # time bin length in seconds
        obs_length = fil_meta.n_ints_in_file * tsamp # total length of observation in seconds
        DR = row['Drift_Rate']              # reported drift rate
        padding=1+np.log10(row['SNR'])/10   # padding based on reported strength of signal
        # calculate the amount of frequency drift with some padding
        half_span=abs(DR)*obs_length*padding  
        if half_span<250:
            half_span=250 # minimum 500 Hz span window
        fmid = row['Corrected_Frequency']
        fstart=round(max(fmid-half_span*1e-6,minimum_frequency),6)
        fend=round(min(fmid+half_span*1e-6,maximum_frequency),6)
        
        # plot
        print(f'Plotting {index+1}/{len(signals_of_interest)} with central frequency {fmid:.6f} MHz,'+
                f' and SNR ratio: {row["SNR_ratio"]:.3f}')
        ptu.plot_beams(beams,
                    fstart,
                    fend,
                    row['Drift_Rate'],
                    SNR=row['SNR'],
                    corrs=row['corrs'],
                    SNRr=row['SNR_ratio'],
                    path=path,
                    pdf=pdf)

    # Print the elapsed time of the entire program.
    end, time_label = get_elapsed_time(start)
    print(f"\n\t{len(signals_of_interest)} hits plotted in %.2f {time_label}.\n" %end)
    return None
# run it!
if __name__ == "__main__":
    main()