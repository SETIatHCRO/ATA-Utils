'''
This is the serial version of the code. It does the same thing as DOTparallel.py, 
but processes one dat file at a time and utilizes pickle states for resuming an interrupted process.

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
    python NbeamAnalysis/DOTnbeam.py <dat_dir> -f <fil_dir> -sf -o <output_dir>

NOTE: the subdirectory tree structure for the <dat_dir> and <fil_dir> must be identical
'''

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
    parser.add_argument('-sf', type=float, nargs='?', const=4, default=None,
                        help='flag to turn on spatial filtering with optional attenuation value for filtering')
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
    sf = cmd_args["sf"]             # optional, flag to turn off spatial filtering
    store = cmd_args["store"]       # optional, flag to retain pickle files

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
    logging.info("\nExecuting program...\n")

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
        dat_name = "/".join(dat.split("/")[-2:])
        logging.info(f'Processing dat file {i+1}/{ndats}:\n\t{dat_name}')
        mid=time.time()
        # make a tuple with the corresponding .fil files
        fils=sorted(glob.glob(fildir+dat.split(datdir)[-1].split(dat.split('/')[-1])[0]+'*fil'))
        if not fils:
            fils=sorted(glob.glob(fildir+dat.split(datdir)[-1].split(dat.split('/')[-1])[0]+'*h5'))
        if not fils:
            logging.info(f'\tWARNING! Could not locate filterbank files in:\n\t{fildir+dat.split(datdir)[-1].split(dat.split("/")[-1])[0]}')
            logging.info(f'\tSkipping this dat file...')
            skipped+=1
            end, time_label = DOT.get_elapsed_time(mid)
            logging.info(f"Finished processing in %.2f {time_label}.\n" %end)
            continue
        elif len(fils)==1:
            logging.info(f'\tWARNING! Could only locate 1 filterbank file in:\n\t{fildir+dat.split(datdir)[-1].split(dat.split("/")[-1])[0]}')
            logging.info(f'\tProceeding with caution...')
        # make a dataframe containing all the hits from all the .dat files in the tuple and sort them by frequency
        df0 = DOT.load_dat_df(dat,fils)
        df0 = df0.sort_values('Corrected_Frequency').reset_index(drop=True)
        if df0.empty:
            logging.info(f'\tWARNING! No hits found in this dat file.')
            logging.info(f'\tSkipping this dat file...')
            skipped+=1
            end, time_label = DOT.get_elapsed_time(mid)
            logging.info(f"Finished processing in %.2f {time_label}.\n" %end)
            continue
        # apply spatial filtering if turned on with sf flag (default is off)
        if sf!=None:  
            df = DOT.cross_ref(df0,sf)
            exact_matches+=len(df0)-len(df)
            hits+=len(df0)
            logging.info(f"\t{len(df0)-len(df)}/{len(df0)} hits removed as exact frequency matches. ")
            logging.info(f"\tCombing through the remaining {len(df)} hits.")
        else:
            df = df0
            hits+=len(df0)
            logging.info("No spatial filtering being applied since sf flag was not toggled on input command.")
        # check for checkpoint pickle files to resume from
        resume_index, df = DOT.resume(outdir+f"{obs}_comb_df.pkl",df)
        # comb through the dataframe, correlate beam power for each hit and calculate attenuation with SNR-ratio
        if df.empty:
            logging.info(f'\tWARNING! Empty dataframe constructed after spatial filtering.')
            logging.info(f'\tSkipping this dat file...')
            skipped+=1
            end, time_label = DOT.get_elapsed_time(mid)
            logging.info(f"Finished processing in %.2f {time_label}.\n" %end)
            continue
        temp_df = DOT.comb_df(df,outdir,obs,resume_index=resume_index,sf=sf)
        full_df = pd.concat([full_df, temp_df],ignore_index=True)
        # Increment the loop counter (d) by 1 so that it starts from the next file in the next iteration
        d += 1
        # Save the current state to the checkpoint file
        with open(outdir+f"{obs}_full_df.pkl", "wb") as f:
            pickle.dump((d, full_df), f)

        if sf==None:
            sf_nom=4
        else:
            sf_nom=sf

        if (update or i==ndats-1) and 'SNR_ratio' in full_df.columns and full_df['SNR_ratio'].notnull().any():
            # save the full dataframe to csv
            full_df.to_csv(f"{outdir}{obs}_DOTnbeam.csv")

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
            ycutoff=0.9*sf_nom*xcutoff**2
            plt.plot(xcutoff,ycutoff,linestyle='--',color='k',alpha=0.5,label='Nominal Cutoff')
            plt.axhspan(sf_nom,max(ylims[1],6.5),color='green',alpha=0.25,label='Attenuated Signals')
            plt.axhspan(1/sf_nom,sf_nom,color='grey',alpha=0.25,label='Similar SNRs')
            plt.axhspan(min(0.2,ylims[0]),1/sf_nom,color='brown',alpha=0.25,label='Off-beam Attenuated')
            plt.ylim(min(-0.2,ylims[0]),max(ylims[1],6.5))
            plt.xlim(-0.1,1.1)
            plt.legend().get_frame().set_alpha(0) 
            plt.grid(which='major', axis='both', alpha=0.5,linestyle=':')
            plt.savefig(outdir + f'{obs}_SNRx.png',
                        bbox_inches='tight',format='png',dpi=fig.dpi,facecolor='white', transparent=False)
            plt.close()

        # print processing time for this loop
        end, time_label = DOT.get_elapsed_time(mid)
        logging.info(f"Finished processing in %.2f {time_label}.\n" %end)

    # remove the full dataframe pickle file after all loops complete
    if store==False:
        logging.info(completion_code+"\n")
        if os.path.exists(outdir+f"{obs}_full_df.pkl"):
            os.remove(outdir+f"{obs}_full_df.pkl")
    else:
        logging.info("\n")

    full_df.to_csv(f"{outdir}{obs}_DOTnbeam.csv")

    above_cutoff=0
    for i,score in enumerate(x):
        if np.interp(score,xcutoff,ycutoff)<SNRr[i]:
            above_cutoff+=1
    logging.info(f"**Final results:")

    # This block prints the elapsed time of the entire program.
    if skipped:
        logging.info(f'\n\t{skipped}/{ndats} dat files skipped. Check the log for skipped filenames.\n')
    end, time_label = DOT.get_elapsed_time(start)
    logging.info(f"\t{len(dat_files)} dats with {hits} total hits cross referenced and {exact_matches} hits removed as exact matches.")
    logging.info(f"\tThe remaining {hits-exact_matches} hits were correlated and processed in \n\n\t\t%.2f {time_label}.\n" %end)
    if 'SNR_ratio' in full_df.columns and full_df['SNR_ratio'].notnull().any():
        logging.info(f"\t{len(full_df[full_df.SNR_ratio>sf_nom])}/{len(full_df)} hits above a SNR-ratio of {sf_nom:.1f}\n")
        logging.info(f"\t{above_cutoff}/{len(full_df)} hits above the nominal cutoff.")
    elif 'SNR_ratio' in full_df.columns:
        logging.info(f"\n\tSNR_ratios missing for some hits, possibly due to missing filterbank files. Please check the log.")
    elif 'mySNRs'==full_df.columns[-1]:
        logging.info(f"\n\tSingle SNR calculated, possibly due to only one filterbank file being found. Please check the log.")
    
    if 'SNR_ratio' not in full_df.columns or full_df['SNR_ratio'].isnull().any():
        # save the broken dataframe to csv
        logging.info(f"\nScores in full dataframe not filled out correctly. Please check it:\n{outdir}{obs}_DOTnbeam.csv")
    else:
        logging.info(f"\nThe full dataframe was saved to: {outdir}{obs}_DOTnbeam.csv\n")
    return None
# run it!
if __name__ == "__main__":
    main()
