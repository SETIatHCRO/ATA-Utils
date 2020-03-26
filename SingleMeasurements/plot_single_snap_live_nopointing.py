#!/usr/bin/python

import sys
import logging
import time
from optparse import OptionParser

from SNAPobs import snap_defaults,snap_recorder,snap_plot
from ATATools import ata_control,logger_defaults,ata_positions,snap_array_helpers

default_fpga_file = snap_defaults.plot_snap_file
default_rms = snap_defaults.rms

def main():

    # Define the argumants
    parser = OptionParser(usage= 'Usage %prog options host',
            description='Plot spectra on the screen with a single antenna')

    #parser.add_argument('hosts', type=str, help = hostnamesHelpString)
    parser.add_option('--fpga', dest='fpga_file', type=str, action="store", default=default_fpga_file,
                        help = '.fpgfile to program')
    parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
                        help ="More on-screen information")
    parser.add_option('-f', dest='freq', type=float, action="store", default=1420.0,
                        help ='observation frequency, in MHz. Only one set of frequencies')

    (options,args) = parser.parse_args()

    if(options.verbose):
        logger = logger_defaults.getProgramLogger("SNAP_SIMPLE_PLOT",loglevel=logging.INFO)
    else:
        logger = logger_defaults.getProgramLogger("SNAP_SIMPLE_PLOT",loglevel=logging.WARNING)

    if len(sys.argv) <= 1:
        logger.warning("no options provided")
        parser.print_help()
        sys.exit(1)

    host = args[0]
    fpga_file = options.fpga_file
    freq = options.freq
    do_snap_plot_simple(host,freq, fpga_file)

    exit()

def do_snap_plot_simple(snaphost,freq, fpga_file):

    logger = logger_defaults.getModuleLogger(__name__)

    logger.info("starting plotting")

    snap_plot.plotAuto(snaphost,freq,fpga_file)


if __name__== "__main__":
    main()

