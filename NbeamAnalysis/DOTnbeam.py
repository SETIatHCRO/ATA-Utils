# The program uses a simple correlation to identify if similar signals exist in target and off-target beams
# DOT_utils.py and plot_target_utils.py required for modularized functions
# The main outputs of this program are a csv, a diagnostic histogram plot and a plot of SNR vs correlation score.

    # Import Packages
import pandas as pd
import pickle
import numpy as np
import time
import os
import sys
import glob
import argparse
import matplotlib.pyplot as plt
import DOT_utils as DOT
import logging
from plot_utils import diagnostic_plotter

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
    parser.add_argument('-update', action='store_true',
                        help='overwrite files if they already exist')
    parser.add_argument('-tag', '--tag',metavar='tag',type=str,nargs=1,default=None,
                        help='output files label')
    parser.add_argument('-xsf', action='store_true',
                        help='flag to turn off spatial filtering')
    parser.add_argument('-store', action='store_true',
                        help='flag to retain pickle files after successful completion')
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


    # Main program execution
def main():
    start=time.time()

    # parse the command line arguments
    cmd_args = parse_args()
    datdir = cmd_args["datdir"]     # required input
    fildir = cmd_args["fildir"]     # optional (but usually necessary)
    beam = cmd_args["beam"][0]      # optional, default = 0
    beam = str(int(beam)).zfill(4)  # force beam format as four char string with leading zeros. Ex: '0010'
    outdir = cmd_args["outdir"]     # optional (defaults to current directory)
    update = cmd_args["update"]     # optional constant output, flag on or default off
    tag = cmd_args["tag"]           # optional file label, default = None
    xsf = cmd_args["xsf"]           # optional, flag to turn off spatial filtering
    store = cmd_args["store"]       # optional, flag to retain pickle files

    # create the output directory if the specified path does not exist
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # set a unique file identifier based on info in the datdir if available
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

    # find and get a list of tuples of all the dat files corresponding to each subset of the observation
    dat_files,errors = DOT.get_dats(datdir,beam)
    # make sure dat_files is not empty
    if not dat_files:
        logging.info(f'\n\tERROR: No .dat files found in subfolders.'+
                f'Please check the input directory and/or beam number, and then try again:\n{datdir}\n')
        sys.exit()
    if errors:
        print(f'{errors} errors when gathering dat files in the input directory. Check the log for skipped files.')

    # check for pickle checkpoint files to resume from, or initialize the dataframe
    full_df = pd.DataFrame()
    d, full_df = DOT.resume(outdir+f"{obs}_full_df.pkl", full_df)
    ndats=len(dat_files[d:])
    hits=0
    exact_matches=0
    skipped=0
    
    # loop through the list of tuples, starting from the last processed file (d), 
    # perform cross-correlation to pare down the list of hits, and put the remaining hits into a dataframe.
    for i, dat in enumerate(dat_files[d:]):
        # Increment the loop counter (d) by 1 so that it starts from the next file in the next iteration
        d += 1
        mid=time.time()
        # make a tuple with the corresponding .fil files
        fils=sorted(glob.glob(fildir+dat.split(datdir)[-1].split(dat.split('/')[-1])[0]+'*.fil'))
        if not fils:
            fils=sorted(glob.glob(fildir+dat.split(datdir)[-1].split(dat.split('/')[-1])[0]+'*.h5'))
        if not fils:
            print(f'\n\tWARNING! Could not locate filterbank files in:\n\t{fildir+dat.split(datdir)[-1].split(dat.split('/')[-1])[0]}')
            print(f'\tSkipping {dat}\n')
            skipped+=1
            continue
        # make a dataframe containing all the hits from all the .dat files in the tuple and sort them by frequency
        df0 = DOT.load_dat_df(dat,fils)
        df0 = df0.sort_values('Corrected_Frequency').reset_index(drop=True)
        if xsf==False:  # apply spatial filtering unless turned off with xsf flag (default is to run it)
            df = DOT.cross_ref(df0)
            exact_matches+=len(df0)-len(df)
            hits+=len(df0)
            logging.info(f"{len(df0)-len(df)}/{len(df0)} hits removed as exact frequency matches. "+
                    f"Combing through the remaining {len(df)} hits in dat file {d}/{len(dat_files)}:\n{dat}")
        else:
            df = df0
            logging.info("No spatial filtering being applied since xsf flag was toggled on input command.")
        # check for checkpoint pickle files to resume from
        resume_index, df = DOT.resume(outdir+f"{obs}_comb_df.pkl",df)
        # comb through the dataframe and cross-correlate each hit to identify any that show up in multiple beams
        if df.empty:
            print(f'\n\tWARNING! Empty dataframe constructed from dat file:\n\t{dat}')
            print(f'\tSkipping this dat file...\n')
            skipped+=1
            continue
        temp_df = DOT.comb_df(df,outdir,obs,resume_index=resume_index)
        full_df = pd.concat([full_df, temp_df],ignore_index=True)
        # Save the current state to the checkpoint file
        with open(outdir+f"{obs}_full_df.pkl", "wb") as f:
            pickle.dump((d, full_df), f)

        if (update or i==ndats-1) and 'x' in full_df.columns and full_df['x'].notnull().any():
            # save the full dataframe to csv
            full_df.to_csv(f"{outdir}{obs}_DOTnbeam.csv")

            # plot the histograms for hits within the target beam
            diagnostic_plotter(full_df, obs, saving=True, outdir=outdir)

            # plot the average correlation scores vs the SNR for each hit in the target beam
            xs = full_df.x
            SNR = full_df.SNR
            fig,ax=plt.subplots(figsize=(12,10))
            plt.scatter(xs,SNR,color='orange',alpha=0.5,edgecolor='k')
            plt.xlabel('Average Correlation Scores')
            plt.ylabel('SNR')
            plt.yscale('log')
            plt.xlim(-0.01,1.01)
            plt.savefig(outdir + f'{obs}_SNRx.png',
                        bbox_inches='tight',format='png',dpi=fig.dpi,facecolor='white', transparent=False)
            plt.close()

        # print processing time for this loop
        end, time_label = DOT.get_elapsed_time(mid)
        logging.info(f"\tProcessed in %.2f {time_label}.\n" %end)

    # remove the full dataframe pickle file after all loops complete
    if store==False:
        os.remove(outdir+f"{obs}_full_df.pkl")

    # This block prints the elapsed time of the entire program.
    if store==False:
        logging.info(completion_code+"\n")
    else:
        logging.info("\n")
    if skipped:
        print(f'\n\t{skipped} dat files skipped.\n\tCheck the log for skipped filenames.\n')
    end, time_label = DOT.get_elapsed_time(start)
    logging.info(f"\t{len(dat_files)} dats with {hits} total hits cross referenced and {exact_matches} hits removed as exact matches.")
    logging.info(f"\t\tThe remaining {hits-exact_matches} hits were correlated and processed in %.2f {time_label}.\n" %end)
    logging.info(f"\t{len(full_df[full_df.x>0.75])}/{len(full_df)} hits above an average correlation score of 0.75")
    logging.info(f"\t{len(full_df[full_df.x<0.75])}/{len(full_df)} hits below an average correlation score of 0.75")
    logging.info(f"\t{len(full_df[full_df.x<0.5])}/{len(full_df)} hits below an average correlation score of 0.5")
    logging.info(f"\t{len(full_df[full_df.x<0.25])}/{len(full_df)} hits below an average correlation score of 0.25")
    logging.info(f"\nThe full dataframe was saved to: {outdir}{obs}_DOTnbeam.csv")
    return None
# run it!
if __name__ == "__main__":
    main()
