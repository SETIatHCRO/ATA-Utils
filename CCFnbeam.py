# The program uses a simple correlation to identify if similar signals exist in target and off-target beams

    # Import Packages
import pandas as pd
import numpy as np
import time
import os
import glob
import argparse
import blimpy as bl
import blimpy.waterfall as wf
import blimpy.io.sigproc as sp
import matplotlib.pyplot as plt
import scipy.stats as st
from numpy.linalg import norm
from astropy.stats import sigma_clip as sc

    # Define Functions
# parse the input arguments:
def parse_args():
    parser = argparse.ArgumentParser(description='Process ATA 2beam filterbank data.')
    parser.add_argument('datdir', metavar='/observation_base_dat_directory/', type=str, nargs=1,
                        help='full path of observation directory with subdirectories for integrations and seti-nodes containing dat tuples')
    parser.add_argument('-f','--fildir', metavar='/observation_base_fil_directory/', type=str, nargs=1,
                        help='full path of directory with same subdirectories leading to fil files, if different from dat file location.')
    parser.add_argument('-o', '--outdir',metavar='/output_directory/', type=str, nargs=1,default='./',
                        help='output target directory')
    parser.add_argument('-b', '--beam',metavar='target_beam',type=str,nargs=1,default='0',
                        help='target beam, 0 or 1. Default is 0.')
    args = parser.parse_args()
    # Check for trailing slash in the directory path and add it if absent
    odict = vars(args)
    if odict["datdir"]:
        datdir = odict["datdir"][0]
        if datdir[-1] != "/":
            datdir += "/"
        odict["datdir"] = datdir  
    if odict["fildir"]:
        fildir = odict["fildir"][0]
        if fildir[-1] != "/":
            fildir += "/"
        odict["fildir"] = fildir  
    else:
        odict["fildir"] = datdir
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

# check log file for completeness
def check_logs(log):
    status="fine"
    searchfile = open(log,'r').readlines()
    if searchfile[-1]!='===== END OF LOG\n':
        status="incomplete"
    return status

# retrieve a list of .dat files, each with the full path of each .dat file for the target beam
def get_dats(root_dir,beam):
    """Recursively finds all files with the '.dat' extension in a directory
    and its subdirectories, and returns a list of the full paths of files 
    where each file corresponds to the target beam."""
    errors=0
    dat_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith('.dat') and f.split('beam')[1].split('.')[0]==beam:
                log_file = os.path.join(dirpath, f).replace('.dat','.log')
                if check_logs(log_file)=="incomplete" or not os.path.isfile(log_file):
                    print(f"{log_file} is incomplete. Please check it. Skipping this file...")
                    errors+=1
                    continue
                dat_files.append(os.path.join(dirpath, f))
    return dat_files,errors

# load the data from the input .dat file for the target beam and its corresponding .fil files 
# for all beams formed in the same observation and make a single concatenated dataframe 
def load_dat_df(dat_file,filtuple):
    # make a dataframe of all the data in the .dat file below the headers
    #NOTE: This assumes a standard turboSETI .dat file format with the listed headers
    dat_df = pd.read_csv(dat_file, 
                delim_whitespace=True, 
                names=['Top_Hit_#','Drift_Rate','SNR', 'Uncorrected_Frequency','Corrected_Frequency','Index',
                        'freq_start','freq_end','SEFD','SEFD_freq','Coarse_Channel_Number','Full_number_of_hits'],
                skiprows=9)
    # initiate the final dataframe as a subset of the relevant bits of the .dat dataframe
    full_dat_df = dat_df[['Drift_Rate','SNR', 'Index', 'Uncorrected_Frequency','Corrected_Frequency',
                            'freq_start','freq_end','Coarse_Channel_Number','Full_number_of_hits']]
    # add the path and filename of the .dat file to the dataframe
    full_dat_df = full_dat_df.assign(dat_name = dat_file)
    # loop over each .fil file in the tuple to add to the dataframe
    for i,fil in enumerate(filtuple):
        col_name = 'fil_'+fil.split('beam')[-1].split('.fil')[0]
        full_dat_df[col_name] = fil
    # calculate the drift rate in nHz for each hit and add it to the dataframe
    full_dat_df['normalized_dr'] = full_dat_df['Drift_Rate'] / (full_dat_df[['freq_start','freq_end']].max(axis=1) / 10**3)
    return full_dat_df

# use blimpy to grab the data slice from the filterbank file over the frequency range in this row
def wf_data(fil,f1,f2):
    return bl.Waterfall(fil,f1,f2).grab_data(f1,f2)

# correlate two 2D arrays and return the correlation coefficient
def sig_cor(s1,s2):
    ACF1=((s1*s1).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]
    ACF2=((s2*s2).sum(axis=1)).sum()/np.shape(s2)[0]/np.shape(s2)[1]
    CCF =((s1*s2).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]
    x=CCF/np.sqrt(ACF1*ACF2)
    return x

# comb through each hit in the dataframe and look for corresponding hits in each of the beams.
def comb_df(df):
    # loop over every row in the dataframe
    for r,row in df.iterrows():
        # identify the target beam .fil file 
        matching_col = row.filter(like='fil_').apply(lambda x: x == row['dat_name']).idxmax()
        target_fil = row[matching_col]
        # identify the frequency range of the signal in this row of the dataframe
        f1=row['freq_start']
        f2 = row['freq_end']
        fstart= min(f1,f2)
        fstop = max(f1,f2)
        # grab the signal data in the target beam fil file
        frange,s1=wf_data(target_fil,fstart,fstop)
        # get a list of all the other fil files for all the other beams
        other_cols = row.loc[row.index.str.startswith('fil_') & (row.index != matching_col)]
        # initialize empty correlation coefficient lists for appending
        xs=[]
        for col_name, other_fil in other_cols.iteritems():
            # grab the data from the non-target fil in the same location
            _,s2=wf_data(other_fil,fstart,fstop)
            # correlate the signal in the target beam with the same location in the non-target beam
            xs.append(sig_cor(s1,s2))
        # loop over each correlation score in the tuple to add to the dataframe
        for i,x in enumerate(xs):
            col_name = row["dat_name"].split('beam')[-1].split('.fil')[0]+'_x_'+other_cols[i].split('beam')[-1].split('.fil')[0]
            df[col_name] = x
        df.loc[r,'x'] = sum(xs)/len(xs)           # the average correlation coefficient of the signal with the other beams
    return df

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
    return None


    # Main program execution
def main():
    print("\nExecuting program...")
    start=time.time()

    # parse the command line arguments
    cmd_args = parse_args()
    datdir = cmd_args["datdir"]     # required input
    fildir = cmd_args["fildir"]     # optional (but usually necessary)
    beam = cmd_args["beam"][0]      # optional, default = 0
    beam = str(int(beam)).zfill(4)  # force beam format as four char string with leading zeros. Ex: '0010'
    outdir = cmd_args["outdir"]     # optional (defaults to current directory)

    # create the output directory if the specified path does not exist
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # find and get a list of tuples of all the dat files corresponding to each subset of the observation
    dat_files,errors = get_dats(datdir,beam)

    # initialize the final dataframe that will contain all the uncorrelated hits
    full_df=pd.DataFrame()
    
    # loop through the list of tuples, perform cross-correlation to pare down the list of hits, 
    # and put the remaining hits into a dataframe.
    for d,dat in enumerate(dat_files):
        print(f'Working on dat:\n{dat}')
        # make a tuple with the corresponding .fil files
        fils=sorted(glob.glob(fildir+dat.split(datdir)[1].split(dat.split('/')[-1])[0]+'*.fil'))
        # make a dataframe containing all the hits from all the .dat files in the tuple and sort them by frequency
        df = load_dat_df(dat,fils)
        df = df.sort_values('Corrected_Frequency').reset_index(drop=True)
        print(f"{len(df)} hits in this dat file.\n")
        # comb through the dataframe and cross-correlate each hit to identify any that show up in multiple beams
        temp_df = comb_df(df)
        full_df = pd.concat([full_df, temp_df],ignore_index=True)

    # save the full dataframe to csv
    try:
        obs="obs_"+"-".join([i.split('-')[1:3] for i in datdir.split('/') if ':' in i][0])
    except:
        obs="obs_UNKNOWN"
    full_df.to_csv(f"{outdir}{obs}_CCFnbeam.csv")

    # plot the histograms for hits within the target beam
    diagnostic_plotter(full_df, obs, saving=True, outdir=outdir)

    # plot the average correlation scores vs the SNR for each hit in the target beam
    xs = full_df.x
    SNR = full_df.SNR
    plt.scatter(xs,SNR,color='orange',alpha=0.5,edgecolor='k')
    plt.xlabel('Average Correlation Scores')
    plt.ylabel('SNR')
    plt.yscale('log')
    plt.savefig(outdir + f'{obs}_SNRx.png')
    plt.close()

    # This block prints the elapsed time of the entire program.
    end, time_label = get_elapsed_time(start)
    print(f"\t{len(dat_files)} dats with {len(full_df)} hits processed in %.2f {time_label}.\n" %end)
    print(f"The full dataframe was saved to: {outdir}{obs}_CCFnbeam.csv")
    return None
# run it!
if __name__ == "__main__":
    main()
