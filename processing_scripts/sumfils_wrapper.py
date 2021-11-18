#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
import sys,os
import subprocess
import argparse
from sigpyproc.Readers import FilReader
import numpy as np

from SNAPobs import snap_config

DEFAULT_FNAME   = 'decimated.fil'
DEFAULT_NPROC   = 1
DEFAULT_OUTDIR  = './ics'
DEFAULT_OUTNAME = 'ics'
DEFAULT_SCRIPT  = '/home/obsuser/scripts/sumfils/sumfils'

def main():
    parser = argparse.ArgumentParser(description='Wrapper to call'\
            'sumfilbanks')
    parser.add_argument('ants', nargs = '+', type=str,
            help = 'antennas in observation')
    parser.add_argument('-p', dest='nproc', type=int,
            help = 'nprocesses to run [%i]' %DEFAULT_NPROC,
            default=DEFAULT_NPROC)
    parser.add_argument('-s', dest='script', type=str,
            help = 'sumfils executable [%s]' %DEFAULT_SCRIPT,
            default=DEFAULT_SCRIPT)
    parser.add_argument('-f', dest='filname', type=str,
            default=DEFAULT_FNAME, 
            help = 'fnames to sum [%s]' %DEFAULT_FNAME)
    parser.add_argument('-n', dest='dry_run',
            action='store_true',
            help="Don't execute commands")
    parser.add_argument('-d', dest='outdir', type=str,
            help='outdir to use [%s]' %DEFAULT_OUTDIR,
            default=DEFAULT_OUTDIR)
    parser.add_argument('-o',dest= 'outname', type=str,
            help='outname to use [%s]' %DEFAULT_OUTNAME,
            default=DEFAULT_OUTNAME)

    args = parser.parse_args()

    ants = args.ants
    snap_tab = snap_config.get_ata_snap_tab()

    obs_ant_tab = snap_tab[snap_tab.ANT_name.isin(ants)]
    los = np.unique(obs_ant_tab.LO)

    for lo in los:
        subtab = obs_ant_tab[obs_ant_tab.LO == lo]
        inp_list = " ".join([os.path.join(ant, args.filname) 
                for ant in list(subtab.ANT_name)])
        out_basename = "%s_%s.fil" %(args.outname, lo)
        out_name = os.path.join(args.outdir, out_basename)
        cmd = args.script +\
                " " +\
                inp_list +\
                " " +\
                " -o %s" %out_name +\
                " " +\
                " -p %i" %args.nproc
        cmd_args = [subs for subs in cmd.split(" ") 
                if subs]
        if args.dry_run:
            print(cmd_args)
        else:
            print("Running:")
            print(cmd_args)
            p = subprocess.Popen(cmd_args,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            str_out, str_err = p.communicate()

if __name__ == "__main__":
    main()
