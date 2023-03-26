#NOTE: DRIFT RATE CHECKING CURRENTLY TURNED OFF
# This code is currently hardcoded to identify TRAPPIST integration folders in get_dat_tuples() function
# This is the "standard" way of comparing the hits between dat files:
# It cross checks the frequency of each hit in the target beam dat list with those in the off-target beam dat list.
# This is slow and less precise than the newer, cross-correlation method used in CCF2beam.py

#generic packages
import pandas as pd
import numpy as np
import time
import glob
import argparse

#parse the input arguments:
def parse_args():
    parser = argparse.ArgumentParser(description='Process ATA 2beam filterbank data.')
    parser.add_argument('datdir', metavar='/observation_base_dat_directory/', type=str, nargs=1,
                        help='full path of observation directory with subdirectories for integrations and seti-nodes containing dat tuples')
    parser.add_argument('-f','--fildir', metavar='/observation_base_fil_directory/', type=str, nargs=1,
                        help='full path of directory with same subdirectories leading to fil files, if different from dat file location.')
    parser.add_argument('-o', '--outdir',metavar='/output_directory/', type=str, nargs=1,default='./',
                        help='output target directory')
    parser.add_argument('-fd', '--filteron',metavar='filtering_parameters', type=str, nargs=1,default='f',
                        help='set the filter to include frequency [f], drift rate [d] or both [fd]. Default is frequency only.')
    parser.add_argument('-clobber', action='store_true',
                        help='overwrite files if they already exist')
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

def load_dat_df(dat_file_tuple,filtuple):
    for i,dat_file in enumerate(dat_file_tuple):
        dat_df = pd.read_csv(dat_file, 
                         delim_whitespace=True, 
                         names=['Top_Hit_#',
                                'Drift_Rate',
                                'SNR', 
                                'Uncorrected_Frequency',
                                'Corrected_Frequency',
                                'Index', 
                                'freq_start',
                                'freq_end',
                                'SEFD',
                                'SEFD_freq',
                                'Coarse_Channel_Number',
                                'Full_number_of_hits'],
                        skiprows=9)
        if i == 0:
            full_dat_df = dat_df[['Drift_Rate',
                                'SNR', 
                                'Index', 
                                'Corrected_Frequency',
                                'freq_start',
                                'freq_end',
                                'Coarse_Channel_Number',
                                'Full_number_of_hits']]
            full_dat_df = full_dat_df.assign(fil_name = filtuple[i])
            full_dat_df = full_dat_df.assign(dat_name = dat_file)
            # full_dat_df = full_dat_df.assign(beam = dat_file.split('beam')[1].split('.')[0])
        else:
            append_dat_df = dat_df[['Drift_Rate',
                                'SNR', 
                                'Index', 
                                'Corrected_Frequency',
                                'freq_start',
                                'freq_end',
                                'Coarse_Channel_Number',
                                'Full_number_of_hits']]
            append_dat_df = append_dat_df.assign(fil_name = filtuple[i])
            append_dat_df = append_dat_df.assign(dat_name = dat_file)
            # append_dat_df = full_dat_df.assign(beam = dat_file.split('beam')[1].split('.')[0])
            full_dat_df = pd.concat([full_dat_df, append_dat_df])
        full_dat_df['normalized_dr'] = full_dat_df['Drift_Rate'] / (full_dat_df['freq_start'] / 10**3)
    return full_dat_df

#elapsed time function
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

def check_logs(logs):
    status="fine"
    for log in logs:
        searchfile = open(log,'r').readlines()
        if searchfile[-1]!='===== END OF LOG\n':
            status="incomplete"
    return status

def get_dat_tuples(data_dir):
    dat_tuples=[]  
    errors=0
    ints = sorted(glob.glob(f'{data_dir}*trappist*/')) # hard-coded for TRAPPIST system
    for n,i in enumerate(ints):
        nodes = sorted(glob.glob(f'{i}seti-node*/'))
        for node in nodes:
            logs = sorted(glob.glob(f'{node}fil*.log'))
            if check_logs(logs)=="incomplete" or len(logs)<2 :
                print(f"One or more logs in node {node} is incomplete. Please check it. Skipping this tuple...")
                errors+=1
                continue
            dat_tuples.append(sorted(glob.glob(f'{node}fil*.dat')))
    return dat_tuples,errors

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

def main():
    print("\nExecuting program...")
    start=time.time()

    # parse any command line arguments
    cmd_args = parse_args()
    datdir = cmd_args["datdir"]
    fildir = cmd_args["fildir"]
    outdir = cmd_args["outdir"]
    clobber = cmd_args["clobber"]
    filteron = cmd_args["filteron"]

    # find and get a list of all the pairs of dat files
    dat_tuples,errors = get_dat_tuples(datdir)

    # something to play with later
    # set to 'using' to pass the conditional check
    if 'd' not in filteron:
        consider_dr='no'
    else:
        consider_dr='using'
    
    #allows concatenation of localized hit arrays at the end
    start_flag = True
    
    for t,tupl in enumerate(dat_tuples):
        print(f'Working on tuple:\n{tupl}\n')
        filtuple=[(fildir+l.split(datdir)[1])[:-3]+'fil' for l in tupl]
        full_dat_df = load_dat_df(tupl,filtuple)
        full_df = full_dat_df.reset_index(drop=True)
        #from header
        freq_res = get_freq_res(tupl) # 1.907349 #Hz
        close_enough_width = 10 / 10**6 #10 Hz, arbitrary
        close_enough_dr = 0.05 # Hz/s, arbitrary as well
        #getting frequency and drift rate info
        freq_list = full_df.Corrected_Frequency.values
        dr_list = full_df.Drift_Rate.values
        used_freqs_list = []
        deleted_hits_indices = []
        success_indices = []
        #loop through all frequencies in the 2-beam set
        for index, trial_freq in enumerate(freq_list):
            #check that the frequency hasn't already been used
            if trial_freq not in used_freqs_list and index not in deleted_hits_indices:
                #get the drift rate and snr for the hit
                trial_dr = dr_list[index]
                #look for other hits starting within d of the detected hit
                trial_freq_lbound = trial_freq - close_enough_width
                trial_freq_hbound = trial_freq + close_enough_width
                #check off the freq by appending to used_freqs_list
                used_freqs_list.append(trial_freq)
                #if it is the only hit, it is by definition localized
                if len(freq_list) == 1:
                    success_indices.append(index)
                #default the hit to "this is localized"
                localized_trial = True
                #for each other hit
                for index_check, freq_check in enumerate(freq_list):
                    if index_check != index:
                        #get the characteristics of the "comparison" hit
                        check_dr = dr_list[index_check]
                        if 'f' in filteron and 'd' in filteron:
                            if (abs(trial_dr) - close_enough_dr <= abs(check_dr) <= abs(trial_dr) + close_enough_dr) and (trial_freq_lbound <= freq_check <= trial_freq_hbound):
                                #if the check hit is consistent with the trial freq bounds AND drift rate, strike it off, and the trial too
                                localized_trial = False
                                deleted_hits_indices.append(index_check)
                        elif 'f' in filteron:
                            if (trial_freq_lbound <= freq_check <= trial_freq_hbound): 
                                #if the check hit is consistent with the trial freq bounds, strike it off, and the trial too
                                localized_trial = False
                                deleted_hits_indices.append(index_check)
                        elif 'd' in filteron:
                            if (abs(trial_dr) - close_enough_dr <= abs(check_dr) <= abs(trial_dr) + close_enough_dr):
                                #if the check hit is consistent with the trial freq bounds AND drift rate, strike it off, and the trial too
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

    # This block outputs the dataframe as a csv file with the name of the observation
    # sfh = spatially filtered hits, dr = drift rate
    obs="obs_"+"-".join(datdir.split('/')[-2].split('-')[1:3])
    # print(f'filepath:\n{outdir}{obs}_sfh_{consider_dr}dr.csv')
    location_filtered.to_csv(f"{outdir}{obs}_sfh_{consider_dr}dr.csv")

    # This block prints the elapsed time of the entire program.
    end, time_label = get_elapsed_time(start)
    print(f"\n\t{errors} log file errors.")
    print(f"\t{len(dat_tuples)} dat tuples processed in %.2f {time_label}.\n" %end)
    return None
# run it!
if __name__ == "__main__":
    main()
