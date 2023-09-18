# This file holds functions utilized primarily in DOTnbeam.py

# all imports
import pandas as pd
import numpy as np
import logging
import pickle
import time
import os
import glob
import argparse
import blimpy as bl
import logging
import sys

# logging function
def setup_logging(log_filename):
    # Import the logging module and configure the root logger
    logging.basicConfig(level=logging.INFO, filemode='w', format='%(message)s')

    # Get the root logger instance
    logger = logging.getLogger()

    # Remove any existing handlers from the logger
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # Create a console handler that writes to sys.stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # Create a file handler that writes to the specified file
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Set the logger as the default logger for the logging module
    logging.getLogger('').handlers = [console_handler, file_handler]
    return None

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
    if os.path.exists(log)==False:
        return "incomplete"
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
        # if 'test' in dirpath:
        #     print(f'Skipping "test" folder:\n{dirpath}')
        #     continue
        for f in filenames:
            if f.endswith('.dat') and f.split('beam')[-1].split('.')[0]==beam:
                log_file = os.path.join(dirpath, f).replace('.dat','.log')
                if check_logs(log_file)=="incomplete" or not os.path.isfile(log_file):
                    logging.info(f"{log_file} is incomplete. Please check it. Skipping this file...")
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
        if filtuple[0].split('.')[-1]=='fil':
            col_name = 'fil_'+fil.split('beam')[-1].split('.fil')[0]
        elif filtuple[0].split('.')[-1]=='h5':
            col_name = 'fil_'+fil.split('beam')[-1].split('.h5')[0]
        full_dat_df[col_name] = fil
    # calculate the drift rate in nHz for each hit and add it to the dataframe
    full_dat_df['normalized_dr'] = full_dat_df['Drift_Rate'] / (full_dat_df[['freq_start','freq_end']].max(axis=1) / 10**3)
    return full_dat_df

# use blimpy to grab the data slice from the filterbank file over the frequency range provided
def wf_data(fil,f1,f2):
    return bl.Waterfall(fil,f1,f2).grab_data(f1,f2)

# get the normalization factor of a 2D array
def ACF(s1):
    return ((s1*s1).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]

# correlate two 2D arrays with a dot product and return the correlation score
def sig_cor(s1,s2):
    ACF1=ACF(s1)
    ACF2=ACF(s2)
    DOT =((s1*s2).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]
    x=DOT/np.sqrt(ACF1*ACF2)
    return x

# get the median of the "noise" after removing the bottom and top 5th percentile of data
def noise_median(data_array,p=5):
    return np.median(mid_90(data_array,p))

# get the standard deviation of the "noise" after removing the bottom and top 5th percentile of data
def noise_std(data_array,p=5):
    return np.std(mid_90(data_array,p))

# remove the bottom and top 5th percentile from a data array
def mid_90(da,p=5):
    return da[(da>np.percentile(da,p))&(da<np.percentile(da,100-p))]

# My method for calculating SNR
def mySNR(power):
    # get the median of the noise
    median_noise=noise_median(power)
    # assume the middle 90 percent of the array represent the noise
    noise_els=mid_90(power)             
    # zero out the noise by subtracting off the median
    zeroed_noise=noise_els-median_noise     
    # get the standard deviation of the noise using median instead of mean
    std_noise=np.sqrt(np.median((zeroed_noise)**2))
    # identify signals significantly above the "noise" in the data
    signal_els=power[(power>10*std_noise)&(power>np.percentile(power,95))] 
    if not bool(signal_els.size):
        # if there are no "signals" popping out above the noise
        # this will result in an SNR of 1
        signal=std_noise
    else:
        # the signal is calculated as the median of the highest N elements in the signal candidates
        # where N is the number of time bins or rows in the data matrix
        signal=np.median(sorted(signal_els)[-np.shape(power)[0]:])-median_noise 
    # subtract off the median (previous step) and divide by the standard deviation to get the SNR
    SNR=signal/std_noise
    return SNR

# extract index and dataframe from pickle files to resume from last checkpoint
def resume(pickle_file, df):
    index = 0 # initialize at 0
    if os.path.exists(pickle_file):
        # If a checkpoint file exists, load the dataframe and row index from the file
        with open(pickle_file, "rb") as f:
            index, df = pickle.load(f)
        logging.info(f'\t***pickle checkpoint file found. Resuming from step {index+1}\n')
    return index, df

# comb through each hit in the dataframe and look for corresponding hits in each of the beams.
def comb_df(df, outdir='./', obs='UNKNOWN', resume_index=None, pickle_off=False, sf=4):
    if sf==None:
        sf=4
    # loop over every row in the dataframe
    for r,row in df.iterrows():
        if resume_index is not None and r < resume_index:
            continue  # skip rows before the resume index
        # identify the target beam .fil file 
        matching_col = row.filter(like='fil_').apply(lambda x: x == row['dat_name']).idxmax()
        target_fil = row[matching_col]
        # get the filterbank metadata
        fil_meta = bl.Waterfall(target_fil,load_data=False)
        # determine the frequency boundaries in the .fil file
        minimum_frequency = fil_meta.container.f_start
        maximum_frequency = fil_meta.container.f_stop
        # calculate the narrow signal window using the reported drift rate and metadata
        tsamp = fil_meta.header['tsamp']    # time bin length in seconds
        obs_length=fil_meta.n_ints_in_file * tsamp # total length of observation in seconds
        DR = row['Drift_Rate']              # reported drift rate
        padding=1+np.log10(row['SNR'])/10   # padding based on reported strength of signal
        # calculate the amount of frequency drift with some padding
        half_span=abs(DR)*obs_length*padding  
        if half_span<250:
            half_span=250 # minimum 500 Hz span window
        fmid = row['Corrected_Frequency']
        # signal may not be centered, could drift up or down in frequency space
        # so the frequency drift is added to both sides of the central frequency
        # to ensure it is contained within the window
        f1=round(max(fmid-half_span*1e-6,minimum_frequency),6)
        f2=round(min(fmid+half_span*1e-6,maximum_frequency),6)
        # grab the signal data in the target beam fil file
        frange,s0=wf_data(target_fil,f1,f2)
        # calculate the SNR
        SNR0 = mySNR(s0)
        # get a list of all the other fil files for all the other beams
        other_cols = row.loc[row.index.str.startswith('fil_') & (row.index != matching_col)]
        # initialize empty lists for appending
        # xs=[] # no longer used
        corrs=[]
        mySNRs=[SNR0]
        SNR_ratios=[]
        for col_name, other_fil in other_cols.iteritems():
            # grab the signal data from the non-target fil in the same location
            _,s1=wf_data(other_fil,f1,f2)
            # calculate and append the SNR for the same location in the other beam
            off_SNR = mySNR(s1)
            mySNRs.append(off_SNR)
            # calculate and append the SNR ratio
            SNR_ratios.append(SNR0/off_SNR)
            # calculate and append the correlation score
            corrs.append(sig_cor(s0-noise_median(s0),s1-noise_median(s1)))
            # x scores no longer used
            # xs.append(min(corrs[-1]/(SNR_ratios[-1]/sf),1.0)) 
        # add the correlation scores, SNRs and SNR-ratios to the dataframe
        for i,x in enumerate(SNR_ratios):
            col_name_corrs='corrs_'+other_cols[i].split('beam')[-1].split('.')[0]
            df.loc[r,col_name_corrs] = corrs[i]
            col_name_SNRr='SNR_ratio_'+other_cols[i].split('beam')[-1].split('.')[0]
            df.loc[r,col_name_SNRr] = SNR_ratios[i]
            # col_name_x = 'x_'+other_cols[i].split('beam')[-1].split('.')[0]
            # df.loc[r,col_name_x] = x
        df.loc[r,'mySNRs'] = str(mySNRs)
        # calculate and add average values to the dataframe (useful for N>2 beams)
        if len(SNR_ratios)>0:
            df.loc[r,'corrs'] = sum(corrs)/len(corrs) 
            df.loc[r,'SNR_ratio'] = sum(SNR_ratios)/len(SNR_ratios)  
            # df.loc[r,'x'] = sum(xs)/len(xs)                          
        # pickle the dataframe and row index for resuming
        if pickle_off==False:
            with open(outdir+f'{obs}_comb_df.pkl', 'wb') as f:
                pickle.dump((r, df), f) 
    # remove the pickle checkpoint file after all loops complete
    if os.path.exists(outdir+f"{obs}_comb_df.pkl"):
        os.remove(outdir+f"{obs}_comb_df.pkl") 
    return df

# cross reference hits in the target beam dat with the other beams dats for identical signals
def cross_ref(input_df,sf):
    if len(input_df)==0:
        logging.info("\tNo hits in the input dataframe to cross reference.")
        return input_df
    # first, make sure the indices are reset
    input_df=input_df.reset_index(drop=True)
    # Extract directory path from the first row of the dat_name column
    dat_path = os.path.dirname(input_df['dat_name'].iloc[0])
    # Find all dat files in the directory
    dat_files = [f for f in os.listdir(dat_path) if f.endswith('.dat')]
    # Load the hits from the other dat files into a separate dataframe and store in a list
    dat_dfs = []
    for dat_file in dat_files:
        if dat_file == os.path.basename(input_df['dat_name'].iloc[0]):
            continue  # Skip the dat file corresponding to the dat_name column
        dat_df = pd.read_csv(os.path.join(dat_path, dat_file), delim_whitespace=True,
                             names=['Top_Hit_#','Drift_Rate','SNR','Uncorrected_Frequency',
                                    'Corrected_Frequency','Index','freq_start','freq_end',
                                    'SEFD','SEFD_freq','Coarse_Channel_Number',
                                    'Full_number_of_hits'], skiprows=9)
        dat_dfs.append(dat_df)
    # Iterate through the rows in the input dataframe and prune matching hits
    rows_to_drop = []
    for idx, row in input_df.iterrows():
        drop_row = False # don't drop it unless there's a match
        # Check if values are within tolerance in any of the dat file dataframes
        for dat_df in dat_dfs:
            # check if frequencies match and if reported SNRs are similar within a factor of the expected attenuation
            within_tolerance = ((dat_df['Corrected_Frequency'] - row['Corrected_Frequency']).abs() < 2e-6) & \
                               ((((dat_df['freq_start'] - row['freq_start']).abs() < 2e-6) & \
                               ((dat_df['freq_end'] - row['freq_end']).abs() < 2e-6)) | \
                               ((dat_df['Drift_Rate'] - row['Drift_Rate']).abs() < 1/16)) & \
                               ((dat_df['SNR'] / row['SNR']).abs() >= 1/sf) & \
                               ((row['SNR'] / dat_df['SNR']).abs() <= sf)
            if within_tolerance.any():
                drop_row = True # drop it like it's hot
                break
        # Add the row index to the list of rows that should be dropped
        if drop_row:
            rows_to_drop.append(idx)
    # Drop the rows that were identified as within matching tolerance
    trimmed_df = input_df.drop(rows_to_drop)
    # Return the trimmed dataframe with a reset index
    return trimmed_df.reset_index(drop=True)

# a weak attempt at filtering out duplicate hits due to fscrunching
# not complete or implemented anywhere
def drop_fscrunch_duplicates(input_df,frez=1,time_rez=16):
    if len(input_df)==0:
        logging.info("\tNo hits in the input dataframe to cross reference.")
        return input_df
    # first, make sure the indices are reset
    input_df=input_df.reset_index(drop=True)
    # Extract directory path from the first row of the dat_name column
    dat_path = os.path.dirname(input_df['dat_name'].iloc[0])
    # Find all dat files in the directory
    dat_files = [f for f in os.listdir(dat_path) if f.endswith('.dat')]
    # Load the hits from the other dat files into a separate dataframe and store in a list
    dat_dfs = []
    for dat_file in dat_files:
        if dat_file == os.path.basename(input_df['dat_name'].iloc[0]):
            continue  # Skip the dat file corresponding to the dat_name column
        dat_df = pd.read_csv(os.path.join(dat_path, dat_file), delim_whitespace=True,
                             names=['Top_Hit_#','Drift_Rate','SNR','Uncorrected_Frequency',
                                    'Corrected_Frequency','Index','freq_start','freq_end',
                                    'SEFD','SEFD_freq','Coarse_Channel_Number',
                                    'Full_number_of_hits'], skiprows=9)
        dat_dfs.append(dat_df)
    # Iterate through the rows in the input dataframe and prune matching hits
    rows_to_drop = []
    for idx, row in input_df.iterrows():
        drop_row = False # don't drop it unless there's a match
        # Check if values are within tolerance in any of the dat file dataframes
        for dat_df in dat_dfs:
            # check if frequencies match and if reported SNRs are similar within a factor of the expected attenuation
            within_tolerance = ((dat_df['Corrected_Frequency'] - row['Corrected_Frequency']).abs() < 10e-6) & \
                               ((dat_df['Drift_Rate'] - row['Drift_Rate']).abs() < frez/time_rez) & \
                               ((dat_df['SNR'] / row['SNR']).abs() >= 1/sf) & \
                               ((row['SNR'] / dat_df['SNR']).abs() <= sf)
            if within_tolerance.any():
                drop_row = True # drop it like it's hot
                break
        # Add the row index to the list of rows that should be dropped
        if drop_row:
            rows_to_drop.append(idx)
    # Drop the rows that were identified as within matching tolerance
    trimmed_df = input_df.drop(rows_to_drop)
    # Return the trimmed dataframe with a reset index
    return trimmed_df.reset_index(drop=True)