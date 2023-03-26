# This program runs a statistical analysis on the hits contained within an input csv file
# and outputs a new csv ready for plotting images of the target and off-target beams.
# It also outputs a plot with histograms showing the statistics of the hits in the target beam.
# The input csv must contain headers and data for:
# Drift_Rate - The drift rate of each hit as calculated by turboSETI
# SNR - The signal to noise ratio associated with each hit
# freq_start - The start of the frequency slice, usually about 100 Hz from the signal
# freq_end - The end of the frequency slice, usually about 100 Hz from the signal
# dat_name - The full path and filename of the .dat file where each hit was recorded
# fil_name - The full path and filename of the .fil file containing the actual signal data

    # Import Packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import time

    # Define Functions
# parse the input arguments:
def parse_args():
    parser = argparse.ArgumentParser(description='Process ATA 2beam filterbank data.')
    parser.add_argument('csv', metavar='/spatially_filtered_csv/', type=str, nargs=1,
                        help='csv file with spatially filtered results for 2 beams')
    parser.add_argument('-o', '--outdir',metavar='/output_directory/', type=str, nargs=1,default='./',
                        help='output target directory')
    parser.add_argument('-b', '--beam',metavar='target_beam',type=str,nargs=1,default='0',
                        help='target beam, 0 or 1. Default is 0.')
    parser.add_argument('-clobber', action='store_true',
                        help='overwrite files if they already exist')
    args = parser.parse_args()
    # Check for trailing slash in the directory path and add it if absent
    odict = vars(args)
    if odict["outdir"]:
        outdir = odict["outdir"][0]
        if outdir[-1] != "/":
            outdir += "/"
        odict["outdir"] = outdir  
    else:
        odict["outdir"] = ""
    # Returns the input argument as a labeled array
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

# plots the histograms showing snr, frequency, and drift rates of all the hits
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
    ax[s].hist(df['freq_start'], 
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
    return None

    # Main program execution
def main():
    print("\nExecuting program...")
    start=time.time()

    # parse any command line arguments
    cmd_args = parse_args()
    csv = cmd_args["csv"][0]            # required input
    outdir = cmd_args["outdir"]         # optional
    beam = cmd_args["beam"]             # optional, default = 0
    clobber = cmd_args["clobber"]       # optional (currently does nothing)

    # read the csv into a dataframe & get the number of beams in the data
    passed_filtering = pd.read_csv(csv) 
    beams = sorted(set([int(i[-12:].split('.fil')[0].split('beam')[1]) for i in passed_filtering.fil_name]))
    offbeams = [i for i in beams if i!=int(beam)]
    nbeams = len(beams)
    # identify the target beam based on the input
    target_beam = 'beam'+beam.zfill(4)
    # create a copy of a subset of the dataframe with only those hits that show in the target beam
    target_only = passed_filtering[(passed_filtering["fil_name"].str.contains(target_beam))]

    print(f'\nThere are {len(target_only)} hits for the target beam out of {len(passed_filtering)} total hits.\n')

    # plot the histograms for hits within the target beam
    diagnostic_plotter(target_only, csv.split('/')[-1][:-4], saving=True, outdir=outdir)

    # sort and find some maxima in the target only hit data
    target_only.reset_index(drop=True, inplace=True)
    snr_max_row = target_only[target_only['SNR'] == target_only['SNR'].max()]
    dr_max_row = target_only[target_only['Drift_Rate'] == target_only['Drift_Rate'].max()]

    # set up the plotting csv column headers
    target_psf_plot_input = pd.DataFrame(columns=['drift_rate', 'SNR', 'freq_start', 'freq_end', 'onfile'])
                    ### FIX THE HARDCODING OF COLUMNS HERE. NEED TO BE ABLE TO HAVE MULTIPLE OFFFILES FOR N BEAMS ###

    # anonymous function for inserting keys into a dictionary at any position
    insert = lambda _dict, obj, pos: {k: v for k, v in (list(_dict.items())[:pos]+list(obj.items())+list(_dict.items())[pos:])}

    # iterate over each row and build a new dataframe
    for i, row in target_only.iterrows():
        # Print the maxima
        if i == snr_max_row.index:
            print(f"\t\t\tSNR max row:\n{row}\n")
        if i == dr_max_row.index:
            print(f"\t\t\tDrift_Rate max row:\n{row}\n")
        # grab the data
        drift_rate = row['Drift_Rate']
        SNR= row['SNR']
        freq_start = row['freq_start']  # - 100 Hz
        freq_end = row['freq_end']      # + 100 Hz
        onfile_dat = row['dat_name']
        datdir='/'.join(onfile_dat.split('/')[:-1])+'/'
        onfile = row['fil_name']
        # initialize a temporary dictionary for the dataframe of this row only
        temp_dict = {'drift_rate': drift_rate,
                    'SNR': SNR,
                    'freq_start': freq_start, 
                    'freq_end': freq_end, 
                    'onfile':onfile,
                    'datdir':datdir}
        # add all the offbeams to the dictionary
        for i,off in enumerate(offbeams):
            temp_dict = insert(temp_dict,{f'offfile{i}':onfile.replace("beam"+beam.zfill(4),"beam"+str(off).zfill(4))},-1)
        # make a dataframe of this row using the temporary dictionary
        temp_df = pd.DataFrame(data=temp_dict, index=[i])
        # add this temporary dataframe to the main dataframe we are building
        target_psf_plot_input = pd.concat([target_psf_plot_input,temp_df],ignore_index=True)

    # save the dataframe to a csv
    obs=csv.split('.csv')[0].split('/')[-1]
    target_psf_plot_input.to_csv(f'{outdir}{obs[:9]}_plot_target.csv')

    # This block prints the elapsed time of the entire program.
    end, time_label = get_elapsed_time(start)
    print(f"\t{csv} processed in %.2f {time_label}.\n" %end)
    return None
# run it!
if __name__ == "__main__":
    main()
