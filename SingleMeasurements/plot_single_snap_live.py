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
    parser = OptionParser(usage= 'Usage %prog options',
            description='Run an recording with multiple antennas')

    #parser.add_argument('hosts', type=str, help = hostnamesHelpString)
    parser.add_option('--fpga', dest='fpga_file', type=str, action="store", default=default_fpga_file,
                        help = '.fpgfile to program')
    parser.add_option('-a', dest='ant', type=str, action="store", default=None,
                        help ='antenna name eg: \"2j\".')
    parser.add_option('-s', dest='source', type=str, action="store", default=None,
                        help ='source name to record')
    parser.add_option('-f', dest='freq', type=float, action="store", default=None,
                        help ='observation frequency, in MHz. Only one set of frequencies')
    parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
                        help ="More on-screen information")

    (options,args) = parser.parse_args()

    if(options.verbose):
        logger = logger_defaults.getProgramLogger("SNAP_OBS",loglevel=logging.INFO)
    else:
        logger = logger_defaults.getProgramLogger("SNAP_OBS",loglevel=logging.WARNING)

    if len(sys.argv) <= 1:
        logger.warning("no options provided")
        parser.print_help()
        sys.exit(1)

    if options.ant:
        ant_str = options.ant
    else:
        logger.error("antennas were not provided and no config file")
        raise RuntimeError("no antenna string")

    if options.freq:
        freq = options.freq
    else: 
        logger.error("no frequency set")
        raise RuntimeError("no frequency set")

    if options.source:
        source = options.source
    else: 
        logger.error("sources was not provided")
        raise RuntimeError("no source string")

    fpga_file = options.fpga_file
    
    do_snap_plot(ant_str,freq, source, fpga_file)

    exit()

def do_snap_plot(ant_str,freq, source, fpga_file):

    logger = logger_defaults.getModuleLogger(__name__)

    ant_list = snap_array_helpers.string_to_array(ant_str);
    full_ant_str = snap_array_helpers.array_to_string(ant_list)

    try:
        ant_groups = ata_control.get_snap_dictionary(ant_list)
    except:
        logstr = "unable to match antennas with snaps"
        logger.exception(logstr)
        raise
    
    if len(ant_list) != 1:
        logger.error('only 1 antenna allowed')
        raise RuntimeError('only 1 antenna allowed')

    if len(ant_groups) != 1:
        logger.error('only 1 antenna allowed')
        raise RuntimeError('only 1 antenna allowed')

    ant_dict = {}
    for csnap in ant_groups:
        if len(ant_groups[csnap]) != 1:
            logger.error('only one antenna per snap allowed, got {}: {}'.format(csnap,",".join(ant_groups[csnap])))
            raise RuntimeError("only 1 antenna per snap allowed")

        snaphost = csnap
        currAnt = ant_groups[csnap][0]
    
    logger.info("Reserving antennas %s in bfa antgroup" % full_ant_str)
    try:
        ata_control.reserve_antennas(ant_list)
    except:
        logstr = "unable to reserve the antennas"
        logger.exception(logstr)
        raise

    logger.info("starting plotting")
    try:
        ata_control.try_on_lna(currAnt)
        source_status = ata_positions.ATAPositions.getFirstInListThatIsUp([source])
        if not source_status:
            errormsg = 'source {} is not up (or too close to sun/moon)... terminating observation set {}'.format(source,obs_set_id)
            logger.error(errormsg)
            raise RuntimeError(errormsg)
        if source_status['status'] != 'up':
            if source_status['status'] == 'next_up':
                errormsg = 'source {} is not up (or too close to sun/moon). Will be up in {} minutes. Terminating observation set {}'.format(source,source_status['minutes'],obs_set_id)
            else:
                errormsg = 'source {} is not up (or too close to sun/moon)... terminating observation set {}'.format(source,obs_set_id)
            logger.error(errormsg)
            raise RuntimeError(errormsg)


        logger.info("pointing the antennas")
        ata_control.make_and_track_ephems(source, currAnt );
        logger.info("autotuning")
        ata_control.autotune(currAnt)
        ata_control.rf_switch_thread([currAnt])

        logger.info("changing to frequency {}".format(freq))
        ata_control.set_freq(freq, currAnt)
        snap_recorder.setSnapRMS(snaphost,currAnt,fpga_file,default_rms)
        snap_plot.plotAuto(snaphost,freq,fpga_file)

    except KeyboardInterrupt:
        logger.info("Keyboard interuption")
    except Exception as e:
        logger.exception("something went wrong")
        errmsg = "Finishing recording - failed: {}".format(e)
        raise
    finally: 
        logger.info("shutting down")
        ata_control.release_antennas(ant_list, False)

if __name__== "__main__":
    main()

