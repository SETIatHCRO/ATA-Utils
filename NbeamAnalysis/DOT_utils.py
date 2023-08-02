# This file holds functions utilized primarily in DOTnbeam.py

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

def setup_logging(log_filename):
    # Import the logging module and configure the root logger
    logging.basicConfig(level=logging.INFO, format='%(message)s')

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

# use blimpy to grab the data slice from the filterbank file over the frequency range in this row
def wf_data(fil,f1,f2):
    return bl.Waterfall(fil,f1,f2).grab_data(f1,f2)

# get the normalization factor of a 2D array
def ACF(s1):
    return ((s1*s1).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]

# correlate two 2D arrays and return the correlation score
def sig_cor(s1,s2):
    ACF1=ACF(s1)
    ACF2=ACF(s2)
    DOT =((s1*s2).sum(axis=1)).sum()/np.shape(s1)[0]/np.shape(s1)[1]
    x=DOT/np.sqrt(ACF1*ACF2)
    return x

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
def comb_df(df, outdir='./', obs='UNKNOWN', resume_index=None):
    # loop over every row in the dataframe
    for r,row in df.iterrows():
        if resume_index is not None and r < resume_index:
            continue  # skip rows before the resume index
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
        # initialize empty correlation score lists for appending
        xs=[]
        SNR_ratios=[]
        for col_name, other_fil in other_cols.iteritems():
            # grab the data from the non-target fil in the same location
            _,s2=wf_data(other_fil,fstart,fstop)
            # correlate the signal in the target beam with the same location in the non-target beam
            # subtracting off the median of the off-target beam to roughly center the noise around zero.
            xs.append(sig_cor(s1-np.median(s2),s2-np.median(s2))) 
            SNR_ratios.append(ACF(s1-np.median(s2))/ACF(s2-np.median(s2)))
        # loop over each correlation score in the tuple to add to the dataframe
        for i,x in enumerate(xs):
            col_name_SNRr='SNR_ratio_'+other_cols[i].split('beam')[-1].split('.')[0]
            df.loc[r,col_name_SNRr] = SNR_ratios[i]
            col_name_x = row["dat_name"].split('beam')[-1].split('.dat')[0]+'_x_'+other_cols[i].split('beam')[-1].split('.')[0]
            df.loc[r,col_name_x] = x
        if len(xs)>0:   # this conditional makes the code not break if there's only one filterbank file for some reason
            df.loc[r,'SNR_ratio'] = sum(SNR_ratios)/len(SNR_ratios)     # the average SNR_ratios with the other beams
            df.loc[r,'x'] = sum(xs)/len(xs)           # the average correlation score of the signal with the other beams  
        # pickle the dataframe and row index for resuming
        with open(outdir+f'{obs}_comb_df.pkl', 'wb') as f:
            pickle.dump((r, df), f) 
    # remove the pickle checkpoint file after all loops complete
    if os.path.exists(outdir+f"{obs}_comb_df.pkl"):
        os.remove(outdir+f"{obs}_comb_df.pkl") 
    return df

# retrieve the frequency resolution of the dat files from their headers (should all be the same)
def get_freq_res(tupl):
    deltaf=[]
    for dat in tupl:
        searchfile = open(dat,'r').readlines()
        for line in searchfile:
            if "DELTAF(Hz):  " in line:
                deltaf.append(float(line.split("DELTAF(Hz):  ")[-1].split("	")[0]))
    if deltaf[0]!=deltaf[1]:
        logging.info(f"ERROR: DELTAF(Hz) values do not match for this tuple:\n{tupl}\nProceeding with first DELTAF(Hz) value anyway.")
    return deltaf[0]

# cross reference hits in the target beam dat with the other beams dats for identical signals
def cross_ref(input_df):
    if len(input_df)==0:
        return input_df
    # first, make sure the indices are reset
    input_df=input_df.reset_index(drop=True)
    # Extract directory path from the first row of the dat_name column
    dat_path = os.path.dirname(input_df['dat_name'].iloc[0])
    
    # Find all dat files in the directory
    dat_files = [f for f in os.listdir(dat_path) if f.endswith('.dat')]
    
    # Load each dat file into a separate dataframe and store in a list
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
    
    # Iterate through rows in input dataframe and prune if necessary
    rows_to_drop = []
    for idx, row in input_df.iterrows():
        drop_row = False
        
        # Check if values are within tolerance in any of the dat file dataframes
        for dat_df in dat_dfs:
            within_tolerance = ((dat_df['Corrected_Frequency'] - row['Corrected_Frequency']).abs() < 2e-6) & \
                               ((dat_df['freq_start'] - row['freq_start']).abs() < 2e-6) & \
                               ((dat_df['freq_end'] - row['freq_end']).abs() < 2e-6) & \
                               ((dat_df['SNR'] / row['SNR']).abs() >= 0.5)
            if within_tolerance.any():
                drop_row = True
                break
        
        # Add row to list of rows to drop if within tolerance in any of the dat file dataframes
        if drop_row:
            rows_to_drop.append(idx)
            # print(f'dropped row: {idx}')
            # print(f'{row}')
    
    # Drop rows that are within tolerance
    trimmed_df = input_df.drop(rows_to_drop)
    
    # Reset index and return trimmed dataframe
    return trimmed_df.reset_index(drop=True)