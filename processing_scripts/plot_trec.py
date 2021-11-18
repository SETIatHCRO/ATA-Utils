#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
import sys,os
import pandas as pd
import numpy as np
import glob
import datetime

import argparse

# Make plots looks nicer
RCPARAMS="/home/caluser/utils/rcparams.py"
if os.path.exists(RCPARAMS):
    exec(open(RCPARAMS,"r").read())
else:
    print("rcparams file not found, skipping it")


ALLANTS = ["1a", "1f", "1c", "2a", "2b", "2h", "3d",
        "3c", "4g", "1k", "5c", "1h", "4j", "2l", "2k",
        "1e", "1g", "2c", "2e", "2j", "2m", "3l", "5b"]

BASERESULTS = "/home/caluser/Results"
DT_FMT="%Y-%m-%d-%H:%M:%S"
BOUNDS=[-10, 250]
COLORS = plt.rcParams['axes.prop_cycle'].by_key()['color']
COLORS = COLORS*10
COLUMNS_TO_PRINT = ['TatmTcmb_On', 'AtmosAtten_On', 'Tau']



def main():
    parser = argparse.ArgumentParser(description='Plot receiver temperature')
    parser.add_argument('-nobs', type=int,
            help='number of observations to plot [default: 6]', required=False,
            default=6)
    parser.add_argument('-ants', nargs = '+', type=str,
            help='antennas to plot [default: all]', required=False)
    parser.add_argument('-source', type=str,
            help='source to plot [default: all]', default="", required=False)
    parser.add_argument('-basedir', default=BASERESULTS, type=str,
            help='basedir to use [default: %s]' %BASERESULTS, required=False)
    parser.add_argument('-savedir', type=str,
            help='basedir to save plots [default: None, i.e. display to screen]')

    # parse arguments
    args = parser.parse_args()
    baseresults = args.basedir
    source = args.source
    nobs = args.nobs
    ants = args.ants

    # list all observations
    resdirs = os.listdir(baseresults)
    # select the specified source if input
    resdirs = np.array([r for r in resdirs if source in r])

    # get the utcs associated with the observations
    # and sort in time
    utcs = [datetime.datetime.strptime(t.split("_")[1], DT_FMT)
            for t in resdirs]
    sources = np.array([t.split("_")[0] for t in resdirs])

    args_sort = np.argsort(utcs)
    utcs    = np.array(utcs)[args_sort] # sort in time
    resdirs = resdirs[args_sort] # sort result directories in time
    sources = sources[args_sort] # sort sources

    # select the last X observations to plot
    resdirs_to_process = resdirs[-nobs:]
    utcs_to_process    = utcs[-nobs:]
    sources_to_process = sources[-nobs:]

    # dictionary to store the figure number for each antenna
    ants_fignumb_dict={ant:i for i,ant in enumerate(ALLANTS)}

    print("Directories to process:")
    print(resdirs_to_process)
    print("-"*79)
    
    print(" ".join(COLUMNS_TO_PRINT))

    iproc = 0
    ant_processed = []
    # loop through each result directory and plot
    for resdir, utc in zip(resdirs_to_process, utcs_to_process):
        # names of results csv files
        # example: 5c_Results.csv
        if not ants: 
            results = [os.path.basename(r)
                    for r in glob.glob(os.path.join(baseresults, resdir, "*_Results.csv"))]
        else: # select only the antennas specified
            #print(ants)
            results = []
            for ant in ants:
                results+= [os.path.basename(r)
                        for r in glob.glob(os.path.join(baseresults, resdir, 
                            "%s_Results.csv" %ant))]

        print_once = 1
        # loop through each antenna
        for i, r_file in enumerate(results):
            ant_name = r_file.split("_")[0] #r_file example: 5c_Results.csv
            ant_processed.append(ant_name)
            if ant_name not in ALLANTS:
                print("%s is not in ALLANTS, please add it" %ant_name)
                sys.exit(-1)

            fig = plt.figure(ants_fignumb_dict[ant_name])
            if fig.axes: 
                ax1, ax2 = fig.axes
            else: #if figure defined for first time
                widths = [3]
                heights = [3, 3, 1.5]
                spec = fig.add_gridspec(ncols=1, nrows=3, width_ratios=widths,
                        height_ratios=heights)
                ax1 = fig.add_subplot(spec[0])
                ax2 = fig.add_subplot(spec[1])

            data = pd.read_csv(os.path.join(baseresults, resdir, r_file))

            # do some data masking
            mask_x = (data['TRCVR_x_1'] < BOUNDS[0]) |\
                    (data['TRCVR_x_1'] > BOUNDS[1])
            data.loc[mask_x, 'TRCVR_x_1'] = 10000 #np.nan

            mask_y = (data['TRCVR_y_1'] < BOUNDS[0]) |\
                    (data['TRCVR_y_1'] > BOUNDS[1])
            data.loc[mask_y, 'TRCVR_y_1'] = 10000 #np.nan

            label1 = sources_to_process[iproc]+" "+\
                    datetime.datetime.strftime(utcs_to_process[iproc], DT_FMT)
            label2 = sources_to_process[iproc]+" "+\
                    datetime.datetime.strftime(utcs_to_process[iproc], DT_FMT)

            ax1.plot(data['Frequency'], data['TRCVR_x_1'], color=COLORS[iproc],
                    label=label1)
            ax2.plot(data['Frequency'], data['TRCVR_y_1'], color=COLORS[iproc],
                    label=label2)
            if print_once:
                print(data[COLUMNS_TO_PRINT].values[-1])
                print_once = 0


        iproc += 1

    ant_processed = np.unique(ant_processed)
    # Now format all the plots
    for ant_name in ant_processed:
        ant_n = ants_fignumb_dict[ant_name]
        fig = plt.figure(ant_n)
        ax1, ax2 = fig.axes

        # Put a legend to the right of the current axis
        ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.35), fontsize='x-small',
          fancybox=True, shadow=True, ncol=2)

        ax2.set_xlabel("Frequency [GHz]")
        ax1.set_ylabel("Trec_x [K]")
        ax2.set_ylabel("Trec_y [K]")

        ax1.set_ylim(*BOUNDS)
        ax2.set_ylim(*BOUNDS)
        ax1.set_title(ant_name)

        ax1.grid(which = 'minor', alpha = 0.3)
        ax1.grid(which = 'major', alpha = 0.7)
        ax2.grid(which = 'minor', alpha = 0.3)
        ax2.grid(which = 'major', alpha = 0.7)

        ax1.minorticks_on()
        ax2.minorticks_on()

        box1 = ax1.get_position()
        box2 = ax2.get_position()
        ax1.set_position([box1.x0, box1.y0, box1.width * 0.98, box1.height])
        ax2.set_position([box2.x0, box2.y0, box2.width * 0.98, box2.height])

    # save plots to disk in pdf format if -savedir is passed
    if args.savedir:
        for ant_name in ant_processed:
            ant_n = ants_fignumb_dict[ant_name]
            fig = plt.figure(ant_n)
            sdir = os.path.join(args.savedir,"%s.png" %ant_name)
            fig.savefig(sdir, bbox_inches='tight', dpi=600)
    # otherwise display to screen
    else:
        plt.show()


if __name__ == "__main__":
    main()
