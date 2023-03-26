#NOTE: DRIFT RATE CHECKING CURRENTLY TURNED OFF
# This code is currently hardcoded to identify TRAPPIST integration folders in get_dat_tuples() function
# This is the "standard" way of comparing the hits between dat files:
# It cross checks the frequency of each hit in the target beam dat list with those in the off-target beam dat list.
# This is slow and less precise than the newer, cross-correlation method used in CCF2beam.py

#generic packages
import os
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

def load_dat_df(dat_file_tuple,filtuple):
    for i,dat_file in enumerate(dat_file_tuple):
        dat_df = pd.read_csv(dat_file, 
                         delim_whitespace=True, 
                         names=['Top_Hit_#','Drift_Rate','SNR','Uncorrected_Frequency','Corrected_Frequency',
                                'Index','freq_start','freq_end','SEFD','SEFD_freq','Coarse_Channel_Number',
                                'Full_number_of_hits'],
                        skiprows=9)
        if i == 0:
            full_dat_df = dat_df[['Drift_Rate','SNR','Index','Corrected_Frequency',
                                'freq_start','freq_end','Coarse_Channel_Number','Full_number_of_hits']]
            full_dat_df = full_dat_df.assign(fil_name = filtuple[i])
            full_dat_df = full_dat_df.assign(dat_name = dat_file)
            # full_dat_df = full_dat_df.assign(beam = dat_file.split('beam')[1].split('.')[0])
        else:
            append_dat_df = dat_df[['Drift_Rate','SNR','Index','Corrected_Frequency',
                                'freq_start','freq_end','Coarse_Channel_Number','Full_number_of_hits']]
            append_dat_df = append_dat_df.assign(fil_name = filtuple[i])
            append_dat_df = append_dat_df.assign(dat_name = dat_file)
            # append_dat_df = full_dat_df.assign(beam = dat_file.split('beam')[1].split('.')[0])
            full_dat_df = pd.concat([full_dat_df, append_dat_df])
        full_dat_df['normalized_dr'] = full_dat_df['Drift_Rate'] / (full_dat_df['freq_start'] / 10**3)
    return full_dat_df

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
    datdir = cmd_args["datdir"]     # required input
    fildir = cmd_args["fildir"]     # optional (but usually necessary)
    beam = cmd_args["beam"][0]      # optional, default = 0
    beam = str(int(beam)).zfill(4)  # force beam format as four char string with leading zeros. Ex: '0010'
    outdir = cmd_args["outdir"]     # optional (defaults to current directory)

    # create the outdir if the specified path does not exist
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # find and get a list of tuples of all the dat files corresponding to each subset of the observation
    dat_files,errors = get_dats(datdir,beam)
    print(f"{len(dat_files)} dat files found for processing within the subdirectories of:\n{datdir}")
    
    location_filtered = pd.DataFrame()
    target_hits=0
    
    #allows concatenation of localized hit arrays at the end
    start_flag = True
    
    for d,dat in enumerate(dat_files):
        print(f'Working on tuple:\n{dat}\n')
        # make a tuple with the corresponding .fil files
        fils=sorted(glob.glob(fildir+dat.split(datdir)[1].split(dat.split('/')[-1])[0]+'*.fil'))
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

        target_hits += len(full_dat_df[full_dat_df['dat_name'].str.contains("beam"+beam+".dat")])

    # This block outputs the dataframe as a csv file with the name of the observation
    # sfh = spatially filtered hits
    try:
        obs="obs_"+"-".join([i.split('-')[1:3] for i in datdir.split('/') if ':' in i][0])
    except:
        obs="obs_UNKNOWN"
    # print(f'filepath:\n{outdir}{obs}_sfh_{consider_dr}dr.csv')
    location_filtered.to_csv(f"{outdir}{obs}_sfh.csv")

    filtered_hits = len(location_filtered[location_filtered['dat_name'].str.contains("beam"+beam+".dat")])

    # This block prints the elapsed time of the entire program.
    end, time_label = get_elapsed_time(start)
    print(f"\n\t{errors} log file errors.")
    print(f"\t{filtered_hits} hits remain out of {target_hits} original hits in the target beam")
    print(f"\t{len(dat_files)} dat tuples processed in %.2f {time_label}.\n" %end)
    return None
# run it!
if __name__ == "__main__":
    main()
