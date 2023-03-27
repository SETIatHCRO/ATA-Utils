# This file holds functions utilized primarily in CCFnbeam.py

import pandas as pd
import numpy as np
import time
import os
import glob
import argparse
import blimpy as bl

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
            if f.endswith('.dat') and f.split('beam')[-1].split('.')[0]==beam:
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
            col_name = row["dat_name"].split('beam')[-1].split('.dat')[0]+'_x_'+other_cols[i].split('beam')[-1].split('.')[0]
            df[col_name] = x
        df.loc[r,'x'] = sum(xs)/len(xs)           # the average correlation coefficient of the signal with the other beams
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
        print(f"ERROR: DELTAF(Hz) values do not match for this tuple:\n{tupl}\nProceeding with first DELTAF(Hz) value anyway.")
    return deltaf[0]

# cross reference hits in the target beam dat with the other beams dats for identical signals
#NOTE: Not yet implemented
def cross_ref(dat_df,dat_file):
    datdir=dat_file.split(dat_file.split('/')[-1])[0]
    dats=sorted(glob.glob(datdir+"*.dat"))
    status=[]
    for h,hit in dat_df.iterrows():
        close_enough_width = 2e-6 # 2 Hz, arbitrary
        freq_res = get_freq_res(dats) # 1.907349 #Hz
        fmid_lower = hit.Corrected_Frequency - close_enough_width
        fmid_upper = hit.Corrected_Frequency + close_enough_width
        fstart_lower = hit.freq_start - close_enough_width
        fstart_upper = hit.freq_start + close_enough_width
        fstop_lower = hit.freq_end - close_enough_width
        fstop_upper = hit.freq_end + close_enough_width
        for d,dat in enumerate(dats):
            df = pd.read_csv(dat_file, delim_whitespace=True, names=['Top_Hit_#','Drift_Rate','SNR',
                                    'Uncorrected_Frequency','Corrected_Frequency','Index','freq_start','freq_end',
                                    'SEFD','SEFD_freq','Coarse_Channel_Number','Full_number_of_hits'], skiprows=9)
            df=df[df.Corrected_Frequency.between(fmid_lower,fmid_upper)].reset_index(drop=True)
            df=df[df.freq_start.between(fstart_lower,fstart_upper)].reset_index(drop=True)
            df=df[df.freq_end.between(fstop_lower,fstop_upper)].reset_index(drop=True)
            if len(df)>0:
                status.append('disqualified')
                break
        # collect all the dats for all the beams to cross reference
        dats=sorted(glob.glob(datdir+dat.split(datdir)[1].split(dat.split('/')[-1])[0]+'*.dat'))
        full_dat_df = load_dat_df(dats,fils)
        full_df = full_dat_df.reset_index(drop=True)
        #from header
        freq_res = get_freq_res(dats) # 1.907349 #Hz
        close_enough_width = 2e-6 #10 Hz, arbitrary
        #getting frequency and drift rate info
        fmid_list = full_df.Corrected_Frequency.values
        fstart_list = full_df.freq_start.values
        fstop_list = full_df.freq_end.values
        used_fmid_list = []
        deleted_hits_indices = []
        success_indices = []
        #loop through all frequencies in the 2-beam set
        for index, trial_fmid in enumerate(fmid_list):
            #check that the frequency hasn't already been used
            if trial_fmid not in used_fmid_list and index not in deleted_hits_indices:
                #look for other hits starting within d of the detected hit
                trial_fmid_lbound = trial_fmid - close_enough_width
                trial_fmid_hbound = trial_fmid + close_enough_width
                trial_fstart_lbound = fstart_list[index] - close_enough_width
                trial_fstart_hbound = fstart_list[index] + close_enough_width
                trial_fstop_lbound = fstop_list[index] - close_enough_width
                trial_fstop_hbound = fstop_list[index] + close_enough_width
                #check off the freq by appending to used_freqs_list
                used_fmid_list.append(trial_fmid)
                #if it is the only hit, it is by definition localized
                if len(fmid_list) == 1:
                    success_indices.append(index)
                #default the hit to "this is localized"
                localized_trial = True
                #for each other hit
                for index_check, fmid_check in enumerate(fmid_list):
                    if index_check != index:
                        #get the characteristics of the "comparison" hit
                        if (trial_fmid_lbound <= fmid_check <= trial_fmid_hbound):
                            if (trial_fstart_lbound <= fstart_list[index_check] <= trial_fstart_hbound):
                                if (trial_fstop_lbound <= fstop_list[index_check] <= trial_fstop_hbound):
                                    #if the check hit is consistent with the trial freq bounds, strike it off, and the trial too
                                    localized_trial = False
                                    deleted_hits_indices.append(index_check)
                #after checking all of the frequencies, go back and deal with the results on the original trial frequency
                if localized_trial == True:
                    success_indices.append(index)
                else:
                    deleted_hits_indices.append(index)
        test_successes = full_df.iloc[success_indices]
        if start_flag == True:
            location_filtered = test_successes
            start_flag = False
        else:
            location_filtered = pd.concat([location_filtered, test_successes])
    return df