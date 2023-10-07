'''
This is the parallelized version of the DOTnbeam code. It does the same thing over multiple cores, 
but currently lacks the ability to pickle states for resuming an interrupted process.

This program uses a dot product to correlate power in target and off-target beams 
in an attempt to quantify the localization of identified signals.
Additionally, the SNR-ratio between the beams is evaluated as well
for comparison with the expected attenuation value.

DOT_utils.py and plot_target_utils.py are required for modularized functions.

The outputs of this program are:
    1. csv of the full dataframe of hits, used for plotting with plot_DOT_hits.py
    2. diagnostic histogram plot
    3. plot of SNR-ratio vs Correlation Score
    4. logging output text file

Typical basic command line usage looks something like:
    python NbeamAnalysis/DOTparallel.py <dat_dir> -f <fil_dir> -sf -o <output_dir>

NOTE: the subdirectory tree structure for the <dat_dir> and <fil_dir> must be identical
'''

    # Import Packages
import pandas as pd
import numpy as np
import time
import os
import sys
import glob
import argparse
import matplotlib.pyplot as plt
import DOT_utils as DOT
import logging
import psutil
import threading
from multiprocessing import Pool, Manager, Lock, Process
from plot_utils import diagnostic_plotter

    # Define Functions
# monitor and print CPU usage during the parallel execution
def monitor_cpu_usage(samples):
    while not exit_flag.is_set():
        cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
        samples.append(cpu_usage)

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
    parser.add_argument('-tag', '--tag',metavar='tag',type=str,nargs=1,default=None,
                        help='output files label')
    parser.add_argument('-ncore', type=int, nargs='?', default=None,
                        help='number of cpu cores to use in parallel')
    parser.add_argument('-sf', type=float, nargs='?', const=4, default=None,
                        help='flag to turn on spatial filtering with optional attenuation value for filtering')
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

    # dat processing function for parallelization.
# perform cross-correlation to pare down the list of hits if flagged with sf, 
# and put the remaining hits into a dataframe.
def dat_to_dataframe(args):
    dat, datdir, fildir, outdir, obs, sf, count_lock, proc_count, ndats = args
    start = time.time()
    with count_lock:
        dat_name = "/".join(dat.split("/")[-2:])
        proc_count.value += 1
        logging.info(f'\nProcessing dat file {proc_count.value}/{ndats}\n\t{dat_name}')
        hits,skipped,exact_matches=0,0,0
        # make a tuple with the corresponding fil/h5 files
        fils=sorted(glob.glob(fildir+dat.split(datdir)[-1].split(dat.split('/')[-1])[0]+dat_name.split('/')[-1][:-8]+'*fil'))
        if not fils:
            fils=sorted(glob.glob(fildir+dat.split(datdir)[-1].split(dat.split('/')[-1])[0]+dat_name.split('/')[-1][:-8]+'*h5'))
        if not fils:
            logging.info(f'\tWARNING! Could not locate filterbank files in:\n\t{fildir+dat.split(datdir)[-1].split(dat.split("/")[-1])[0]}')
            logging.info(f'\tSkipping...\n')
            skipped+=1
            mid, time_label = DOT.get_elapsed_time(start)
            logging.info(f"Finished processing in %.2f {time_label}." %mid)
            return pd.DataFrame(),hits,skipped,exact_matches
        # make a dataframe containing all the hits from all the dat files in the tuple and sort them by frequency
        df0 = DOT.load_dat_df(dat,fils)
        df0 = df0.sort_values('Corrected_Frequency').reset_index(drop=True)
        if df0.empty:
            logging.info(f'\tWARNING! No hits found in this dat file.')
            logging.info(f'\tSkipping...')
            skipped+=1
            mid, time_label = DOT.get_elapsed_time(start)
            logging.info(f"Finished processing in %.2f {time_label}." %mid)
            return pd.DataFrame(),hits,skipped,exact_matches
        # apply spatial filtering if turned on with sf flag (default is off)
        if sf!=None:  
            df = DOT.cross_ref(df0,sf)
            exact_matches+=len(df0)-len(df)
            hits+=len(df0)
            mid, time_label = DOT.get_elapsed_time(start)
            logging.info(f"\t{len(df0)-len(df)}/{len(df0)} hits removed as exact frequency matches in %.2f {time_label}." %mid)
            start = time.time()
        else:
            df = df0
            hits+=len(df0)
        # comb through the dataframe, correlate beam power for each hit and calculate attenuation with SNR-ratio
        if df.empty:
            logging.info(f'\tWARNING! Empty dataframe constructed after spatial filtering of dat file.')
            logging.info(f'\tSkipping this dat file because there are no remaining hits to comb through...')
            skipped+=1
            mid, time_label = DOT.get_elapsed_time(start)
            logging.info(f"Finished processing in %.2f {time_label}." %mid)
            return pd.DataFrame(),hits,skipped,exact_matches
        else:
            logging.info(f"\tCombing through the remaining {len(df)} hits.")
            temp_df = DOT.comb_df(df,outdir,obs,pickle_off=True,sf=sf)
        mid, time_label = DOT.get_elapsed_time(start)
        logging.info(f"Finished processing in %.2f {time_label}." %mid)
        return temp_df,hits,skipped,exact_matches


    # Main program execution
def main():
    start=time.time()

    global exit_flag
    exit_flag = threading.Event()
    samples=[]  # Store CPU usage samples
    # Start a thread to monitor CPU usage during parallel execution
    monitor_thread = threading.Thread(target=monitor_cpu_usage, args=(samples,))
    monitor_thread.start()

    # parse the command line arguments
    cmd_args = parse_args()
    datdir = cmd_args["datdir"]     # required input
    fildir = cmd_args["fildir"]     # optional (but usually necessary)
    beam = cmd_args["beam"][0]      # optional, default = 0
    beam = str(int(beam)).zfill(4)  # force beam format as four char string with leading zeros. Ex: '0010'
    outdir = cmd_args["outdir"]     # optional (defaults to current directory)
    tag = cmd_args["tag"]           # optional file label, default = None
    ncore = cmd_args["ncore"]       # optional, set number of cores to use, default = all
    sf = cmd_args["sf"]             # optional, flag to turn off spatial filtering

    # create the output directory if the specified path does not exist
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # set a unique file identifier if not defined by input
    if tag == None:
        try:
            obs="obs_"+"-".join([i.split('-')[1:3] for i in datdir.split('/') if ':' in i][0])
        except:
            obs="obs_UNKNOWN"
    else:
        obs = tag[0]

    # configure the output log file
    logfile=outdir+f'{obs}_out.txt'
    completion_code="Program complete!"
    if os.path.exists(logfile):
        searchfile=open(logfile,'r').readlines()
        for line in searchfile:
            if completion_code in line:
                os.remove(logfile)
                break
    DOT.setup_logging(logfile)
    logger = logging.getLogger()
    logging.info("\nExecuting program...")
    logging.info(f"Initial CPU usage for each of the {os.cpu_count()} cores:\n{psutil.cpu_percent(percpu=True)}")

    # find and get a list of tuples of all the dat files corresponding to each subset of the observation
    dat_files,errors = DOT.get_dats(datdir,beam)
    # make sure dat_files is not empty
    if not dat_files:
        logging.info(f'\n\tERROR: No .dat files found in subfolders.'+
                f'Please check the input directory and/or beam number, and then try again:\n{datdir}\n')
        sys.exit()
    if errors:
        logging.info(f'{errors} errors when gathering dat files in the input directory. Check the log for skipped files.')

    if sf==None:
        logging.info("\nNo spatial filtering being applied since sf flag was not toggled on input command.\n")
    
    ndats=len(dat_files)

    # Here's where things start to get fancy with parellelization
    if ncore==None:
        num_processes = os.cpu_count()
    else:
        num_processes = ncore
    logging.info(f"\n{num_processes} cores requested by user for parallel processing.")
    # Initialize the Manager object for shared variables
    manager = Manager()
    count_lock = manager.Lock()
    proc_count = manager.Value('i', 0)  # Shared integer to track processed count
    # Execute the parallelized function
    input_args = [(dat_file, datdir, fildir, outdir, obs, sf, count_lock, proc_count, ndats) for dat_file in dat_files]
    with Pool(num_processes) as pool:
        results = pool.map(dat_to_dataframe, input_args)

    # Process the results as needed
    result_dataframes, hits, skipped, exact_matches = zip(*results)

    # Concatenate the dataframes into a single dataframe
    full_df = pd.concat(result_dataframes, ignore_index=True)

    # Do something with the counters if needed
    total_hits = sum(hits)
    total_skipped = sum(skipped)
    total_exact_matches = sum(exact_matches)

    if sf==None:
        sf=4

    if 'SNR_ratio' in full_df.columns and full_df['SNR_ratio'].notnull().any():
        # plot the histograms for hits within the target beam
        diagnostic_plotter(full_df, obs, saving=True, outdir=outdir)

        # plot the SNR ratios vs the correlation scores for each hit in the target beam
        x = full_df.corrs
        SNRr = full_df.SNR_ratio
        fig,ax=plt.subplots(figsize=(12,10))
        plt.scatter(x,SNRr,color='orange',alpha=0.5,edgecolor='k')
        plt.xlabel('Correlation Score')
        plt.ylabel('SNR-ratio')
        ylims=plt.gca().get_ylim()
        xlims=plt.gca().get_xlim()
        xcutoff=np.linspace(xlims[0],xlims[1],20)
        ycutoff=0.9*sf*xcutoff**2
        plt.plot(xcutoff,ycutoff,linestyle='--',color='k',alpha=0.5,label='Nominal Cutoff')
        plt.axhspan(sf,max(ylims[1],6.5),color='green',alpha=0.25,label='Attenuated Signals')
        plt.axhspan(1/sf,sf,color='grey',alpha=0.25,label='Similar SNRs')
        plt.axhspan(min(0.2,ylims[0]),1/sf,color='brown',alpha=0.25,label='Off-beam Attenuated')
        plt.ylim(min(-0.2,ylims[0]),max(ylims[1],6.5))
        plt.xlim(-0.1,1.1)
        plt.legend().get_frame().set_alpha(0) 
        plt.grid(which='major', axis='both', alpha=0.5,linestyle=':')
        plt.savefig(outdir + f'{obs}_SNRx.png',
                    bbox_inches='tight',format='png',dpi=fig.dpi,facecolor='white', transparent=False)
        plt.close()

        above_cutoff=0
        for i,score in enumerate(x):
            if np.interp(score,xcutoff,ycutoff)<SNRr[i]:
                above_cutoff+=1
    logging.info(f"\n**Final results:")
    
    # Final print block
    if total_skipped>0:
        logging.info(f'\n\t{total_skipped}/{ndats} dat files skipped. Check the log for skipped filenames.\n')
    end, time_label = DOT.get_elapsed_time(start)
    logging.info(f"\t{len(dat_files)} dats with {total_hits} total hits cross referenced and {total_exact_matches} hits removed as exact matches.")
    logging.info(f"\tThe remaining {total_hits-total_exact_matches} hits were correlated and processed in \n\n\t\t%.2f {time_label}.\n" %end)
    logging.info(f"\t{len(full_df[full_df.SNR_ratio>sf])}/{len(full_df)} hits above a SNR-ratio of {sf:.1f}\n")
    logging.info(f"\t{above_cutoff}/{len(full_df)} hits above the nominal cutoff.")
    
    full_df.to_csv(f"{outdir}{obs}_DOTnbeam.csv")
    if 'SNR_ratio' not in full_df.columns or full_df['SNR_ratio'].isnull().any():
        # save the broken dataframe to csv
        logging.info(f"\nScores in full dataframe not filled out correctly. Please check it:\n{outdir}{obs}_DOTnbeam.csv")
    else:
        logging.info(f"\nThe full dataframe was saved to: {outdir}{obs}_DOTnbeam.csv")

    # Signal the monitoring thread to exit
    exit_flag.set()

    # Allow some time for the monitoring thread to finish
    monitor_thread.join(timeout=5)  # Adjust the timeout if needed

    # Calculate and print the average CPU usage over time
    if samples:
        num_samples = len(samples)
        num_cores = len(samples[0])
        avg_cpu_usage = [round(sum(cpu_usage[i] for cpu_usage in samples) / num_samples,1) for i in range(num_cores)]

        logging.info(f"\nFinal average CPU usage over {num_cores} cores:")
        logging.info(avg_cpu_usage)

    logging.info(f"\n\tProgram complete!\n")
    return None
# run it!
if __name__ == "__main__":
    main()
