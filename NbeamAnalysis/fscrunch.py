'''This program takes a filterbank or h5 file and bins the frequencies 
    based on time resolution up to a maximum drift rate in Hz/s 
    calculated from the frequencies in the file.
    
    It produces a set of "scrunched" files, each of which can be run
    through turboSETI to search for hits.'''

    # Import packages
import argparse
import pandas as pd
import numpy as np
import os
import glob
import time
from blimpy.bl_scrunch import bl_scrunch as scrunch
from blimpy.io.sigproc import read_header as rh
import blimpy as bl
from turbo_seti.find_doppler import FindDoppler
import shutil
import codecs
import logging

    # Define functions
# parse input arguments
def parse_args():
    parser = argparse.ArgumentParser(description='turboSETI processing diagnostics.')
    parser.add_argument('fildir', metavar='/fil_or_h5_file', type=str, nargs=1,
                        help='the original filterbank or h5 file to be worked on.')
    parser.add_argument('-o', '--outdir',metavar='OUT_DIR', type=str, nargs=1,default='./',
                        help='Location for output files. Default: local dir.')
    parser.add_argument('-M', dest='MDR', metavar='MAX_DRIFT_RATE', type=float, default=200.0,
                        help='Maximum drift rate in nHz. Used to calculate drift in Hz/s with file freqs. Default = 200.0 nHz')
    parser.add_argument('-s', dest='SNR', metavar='SNR', type=float, default=25.0,
                        help='Signal to noise ratio. Default = 25.0')
    # parser.add_argument('-n', '--new_filename',metavar='NEW_FILENAME', type=str,
    #                     help='New filename. Default: replaces the file extension with .scrunched.fil or .scrunched .h5.')
    parser.add_argument('-f', dest='Scrunch_Factor', metavar='F_SCRUNCH', type=int, default=2,
                        help='Number of frequency channels to average (scrunch) together. Default = 2')
    # parser.add_argument('-d', '--delete_input', action='store_true',
    #                     help='This option deletes the scrunched files after conversion.')
    args = parser.parse_args()
    odict = vars(args)
    if odict["fildir"]:
        fildir = odict["fildir"][0]
        if fildir[-1] != "/":
            fildir += "/"
        odict["fildir"] = fildir  
    if odict["outdir"]:
        outdir = odict["outdir"][0]
        if outdir[-1] != "/":
            outdir += "/"
        odict["outdir"] = outdir  
    else:
        odict["outdir"] = ""
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

# concatenate the existing .dat files in the output directory
def concat_dats(outdir,maxDR):
    # Find all dats in the directory labeled with _DR_ by the scrunch loop
    dats = sorted(glob.glob(outdir+'*_DR_*.dat'))
    
    # Get the bulky header and tweak it
    header=open(dats[0],'r').readlines()[:9]
    for ell,line in enumerate(header):
        if 'File ID:' in line:
            # Edit File ID to match the respective h5 file
            header[ell]=line.split('_DR_')[0]+'.h5 \n'
        if 'max_drift_rate' in line:
            # Edit the maximum drift rate to match the final maximum
            header[ell]=line.split('max_drift_rate: ')[0]+f'max_drift_rate: {maxDR:.6f}\tobs_length: '+line.split('obs_length: ')[-1]
    
    # Now get all the data from each dat file in a dataframe and delete each dat file.
    full_dat_df=pd.DataFrame()
    for i,dat_file in enumerate(dats):
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
        full_dat_df = pd.concat([full_dat_df, dat_df])
        os.remove(dat_file)

    # set the final concatenated dat name
    dat_name = dats[0].split('_DR_')[0]+'.dat'  
    # write the header into it (Note: this will overwrite any existing dat of that same name)
    with codecs.open(dat_name,'w',"utf-8") as f:
        for line in header:
            quiet=f.write(line)
    # Add the fully concatenated dataframe into the file
    full_dat_df.to_csv(dat_name,sep='\t',mode='a',header=None,encoding="utf-8")
    return None

# concatenate the log files similar to the dats
def concat_logs(outdir):
    logs = sorted(glob.glob(outdir+'*_DR_*.log'))
    log_name = logs[0].split('_DR_')[0]+'.log'
    first=open(logs[0],'r').readlines()[:-1]    
    with codecs.open(log_name,'w',"utf-8") as f:
        for line in first:    
            quiet=f.write(line)
    os.remove(logs[0])
    for log in logs[1:]:    
        searchfile=open(log,'r').readlines()[:-1]   
        with codecs.open(log_name,'a',"utf-8") as f:
            quiet=f.write('\n')
            for line in searchfile:    
                quiet=f.write(line)
            quiet=f.write('\n')
        os.remove(log)
    codecs.open(log_name,'a',"utf-8").write('===== END OF LOG\n')
    return None

    # Main program execution
def main():
    print("\nExecuting program...")
    start=time.time()

    # parse any command line arguments
    cmd_args = parse_args()
    print('\nUsing the following input arguments:')
    for cmd in cmd_args:
        print(f"{cmd}\t\t{cmd_args[f'{cmd}']}")
    print('\n')
    fildir = cmd_args["fildir"]         # required input
    outdir = cmd_args["outdir"]         # optional input, defaults in current directory
    MaxDrift_nHz = cmd_args["MDR"]      # optional input, defaults to 200.0 nHz
    SNR = cmd_args["SNR"]               # optional input, defaults to 25
    sf = cmd_args["Scrunch_Factor"]     # optional input, defaults to 2 (double)

    # gather all the filterbank files to be processed in the input directory
    fils = sorted(glob.glob(fildir+'*.fil'))
    if not fils:
        fils = sorted(glob.glob(fildir+'*.h5'))

    # process each filterbank file in the list
    for fil in fils:
        loop_start=time.time()
        # use file header to get freq and tsamp
        max_freq=rh(fil)['fch1']
        tsamp = rh(fil)['tsamp']
        
        # calculate the list of drift rate intervals up to the maximum
        MaxDrift_Hz2 = MaxDrift_nHz*max_freq/1000
        fbin = 1/tsamp
        DR_list = fbin*sf**np.arange(np.ceil(np.log(MaxDrift_Hz2/fbin)/np.log(sf))+1)
        
        # loop over the list of drift rates and make the frequency scrunched h5s
        filename=fil.split('/')[-1]
        minDR=0
        for i,DR in enumerate(DR_list):
            # rename the filterbank file based on the drift rate range to identify as a "scrunched" file
            if i==0:
                # set up "scrunched" filename
                new_filename=filename.split('.')[0]+f"_DR_{i}-{i+1}.h5"
                # compress .fil files into .h5 files, rename it with _DR_, remove the vanilla h5
                if fil.split('.')[-1]=='fil':
                    print(f'\nConverting .fil file into .h5 file. \nPlacing in {outdir} with new name...\n')
                    bl.fil2h5.make_h5_file(fil,out_dir=outdir)
                    shutil.copyfile(outdir+filename[:-3]+'h5', outdir+new_filename)
                    os.remove(outdir+filename[:-3]+'h5')
                # if it's already in h5 format, just copy it into the output folder and rename it
                elif fil.split('.')[-1]=='h5':
                    print(f'\nInput file already in h5 format. \nCopying h5 into {outdir} with new name...\n')
                    shutil.copyfile(fil, outdir+new_filename)
                # Remove any extraneous copies of the original filterbank file from the output directory
                if os.path.isfile(outdir+filename) and outdir != fildir:
                    print(f'\tRemoving original file from {outdir}...\n')
                    os.remove(outdir+filename)
            
            # use the existing "scrunched" file to continue scrunching the frequency bins and searching for hits
            else:
                fil = outdir+filename   # new_filename becomes filename after the first iteration
                new_filename=filename.split('_DR_')[0]+f"_DR_{i}-{i+1}.h5"
                print(f'\nScrunching {filename} by a factor of {sf}...\n')
                new_start=time.time()
                # scrunch it with blimpy tools
                scrunch(fil, 
                        out_dir=outdir, 
                        new_filename=new_filename, 
                        max_load=None, 
                        f_scrunch=sf)
                # remove the previous scrunched file
                os.remove(fil)
                end, time_label = get_elapsed_time(new_start)
                print(f"\n\tThis scrunch took %.2f {time_label}.\n" %end)

            filename=new_filename   # make the newly scrunched file the file to work on

            # execute FindDoppler to search for hits in this newly frequency scrunched regime
            print(f'\nExecuting turboSETI over a drift rate range of {minDR} to {DR}...\n')
            new_start=time.time()
            FindDoppler(outdir+new_filename,
                        max_drift=DR,
                        min_drift=minDR,
                        snr=SNR,
                        out_dir=outdir,
                        gpu_backend='y',
                        log_level_int=logging.WARNING).search(n_partitions=1)
            end, time_label = get_elapsed_time(new_start)
            print(f"\n\tThis hit search took %.2f {time_label}.\n" %end)

            minDR=DR    # make the drift rate in the list the new minimum drift rate for the next iteration

        # remove the final h5 file.
        os.remove(outdir+new_filename)

        # clean up the dats and logs.
        concat_dats(outdir,DR_list[-1])
        concat_logs(outdir)
        print('\n\tdats and log consolidated.\n')
        
        end, time_label = get_elapsed_time(loop_start)
        print(f"\n\tThis file took %.2f {time_label} to process.\n" %end)

    # This block prints the elapsed time of the entire program.
    end, time_label = get_elapsed_time(start)
    print(f"\n\tThis whole program took %.2f {time_label}.\n" %end)
    return None
# run it!
if __name__ == "__main__":
    main()