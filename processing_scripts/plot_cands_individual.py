#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
import pandas as pd
import numpy as np
import matplotlib 

from skimage.measure import block_reduce

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from sigpyproc.Readers import FilReader

from tqdm import tqdm

import sys
import os
import argparse

# Make plots look better
RCPARAMS = "/home/obsuser/utils/rcparams.py"
if os.path.exists(RCPARAMS):
    exec(open(RCPARAMS,"r").read())

SNR_THRESH = 9.
W_THRESH = 100 * 1e-3 
DM_THRESH = 20.

MAXN = 100

COL_NAMES = "SNR tsample tsec boxcar DMi DM nneigh tstart tend"
COL_NAMES = COL_NAMES.split(" ")


def main():
    parser = argparse.ArgumentParser(description='Sum filterbank'\
            'files')
    parser.add_argument('-c', dest='candfile', type=str,
            help="heimdall's candidate file")
    parser.add_argument('-f', dest='filfile', type=str,
            help="filterbank file")
    parser.add_argument('-s', dest='show', action='store_true',
            help='iteratively show, rather than save, plots')
    parser.add_argument('-u', dest='utc', type=str, default="",
            help='utc name (to append to png name')
    parser.add_argument('-n', dest='maxcand', type=int,
            help='Maximum number of candidates to plot [default: %i]' %(MAXN),
            default=MAXN)
    parser.add_argument('-z', '--zap_chans', dest='zap_chans',
            action='append', nargs=2,
            type=int, help='channels to zap')

    args = parser.parse_args()

    all_candidates = pd.read_table(args.candfile, index_col=False, 
            names=COL_NAMES)
    # hack to get the sampling time
    tsamp = (all_candidates.tsec/all_candidates.tsample).mean()

    box_thresh = int(np.log2(W_THRESH / tsamp))

    all_candidates = all_candidates[(all_candidates.SNR > SNR_THRESH) 
            & (all_candidates.boxcar <= box_thresh) 
            & (all_candidates.DM > DM_THRESH)]


    basedir = os.path.dirname(args.candfile)
    candsdir = os.path.join(basedir, "candidates")
    if not args.show:
        if not os.path.isdir(candsdir):
            os.mkdir(candsdir)

    fil = FilReader(args.filfile)
    nskip = int(0.3/fil.header.tsamp)

    print ("ncands: %i" %all_candidates.shape[0])

    pbar = tqdm(total=all_candidates.shape[0])

    if all_candidates.shape[0] > args.maxcand:
        print ("WARNING: number of candidates (%i) is greater than"\
                "the maximum allowed (%i)" %(all_candidates.shape[0],
                    args.maxcand))
        if not os.path.exists("cands.warning"):
            open("cands.warning", 'a').close()

    icand = 0
    for ind, cand in all_candidates.iterrows():
        dm_smear_sec = (8.3 * fil.header.bandwidth*1e-3 *\
                cand.DM * (fil.header.fcenter*1e-3)**(-3))*1e-3
        dm_smear_nsamp = int(dm_smear_sec / fil.header.tsamp)
        istart = int(cand.tsample) - nskip
        istart = 0 if istart < 0 else istart
        block = fil.readBlock(istart,
                dm_smear_nsamp + 2*nskip)
        # zap unwanted channels
        if args.zap_chans:
            for low_freq, high_freq in args.zap_chans:
                block[low_freq:high_freq] = 0. #np.nan
        disp_org = block.dedisperse(cand.DM)
        if cand.SNR < 10:
            ffactor = 32
        elif cand.SNR < 15:
            ffactor = 16
        elif cand.SNR < 20:
            ffactor = 8
        else:
            ffactor = 1

        tfactor = min(8, int(2**cand.boxcar))
        disp = block_reduce(disp_org, (ffactor, tfactor),
                func=np.sum, cval=np.mean(disp_org))
        
        matplotlib.use("Agg")

        fig = plt.figure(0)
        fig.suptitle("SNR = %.2f, DM = %.2f, boxcar width = %i" 
                %(cand.SNR, cand.DM, cand.boxcar))
        gs = gridspec.GridSpec(2, 1)
        gs.update(hspace=0)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1], sharex=ax1)

        ts = disp.sum(axis=0)
        x = np.arange(int(cand.tsample) - nskip, 
                int(cand.tsample) - nskip + len(ts)*tfactor, tfactor)

        ax1.plot(x*fil.header.tsamp, ts)
        ax1.get_xaxis().set_visible(False)

        ylim = ax1.get_ylim()
        ax1.vlines(np.array([cand.tsample - (2**cand.boxcar/2),
            cand.tsample + (2**cand.boxcar/2)])*fil.header.tsamp -\
                    tfactor/2*fil.header.tsamp, 
            ymin=ylim[0], ymax=ylim[1], lw=1, ls='--')

        if args.zap_chans:
            for low_freq, high_freq in args.zap_chans:
                disp_org[low_freq:high_freq] = np.nan
            disp_org = block_reduce(disp_org, (ffactor, tfactor),
                    func=np.sum, cval=np.mean(disp_org))

        ax2.imshow(disp_org, interpolation='nearest', aspect='auto',
                extent=[x[0]*fil.header.tsamp, 
                    x[-1]*fil.header.tsamp, 
                    fil.header.fbottom, fil.header.ftop])
        ax2.set_ylabel("Frequency (MHz)")
        ax2.set_xlabel("Time since obs_start")

        if args.show:
            plt.show()
        else:
            basefigname = "tsamp_%i_dm_%.2f.png" % (cand.tsample, cand.DM)
            if args.utc:
                basefigname = args.utc+"_"+basefigname 
            figname = os.path.join(candsdir, basefigname)
            plt.savefig(figname, fmt='png', bbox_inches='tight')
        plt.close(fig)
        pbar.update(1)
        if icand > args.maxcand:
            sys.exit(-1)
        icand+=1
    pbar.close()


if __name__ == "__main__":
    main()
