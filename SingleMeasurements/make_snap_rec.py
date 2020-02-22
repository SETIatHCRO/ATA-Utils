#!/usr/bin/env python3

import sys
import logging
import time
from optparse import OptionParser

from SNAPobs import snap_defaults,snap_observations
from ATATools import ata_control,logger_defaults,ata_positions,snap_array_helpers
from ATAobs import obs_db
import ATAComm 

default_fpga_file = snap_defaults.spectra_snap_file
default_captures = 120
default_rms = snap_defaults.rms

def single_snap_recording(ant_dict,obs_set_id,obstype,obsuser,obsdesc,freq,fpga_file,source,ncaptures):
    """
    do a series of On Off observations for given set ID
    """
    logger= logger_defaults.getModuleLogger(__name__)

    desc = obsdesc
    filefragment = "single_rec_{}".format(source)
    attendict = snap_observations.setRMS(ant_dict,fpga_file,default_rms)
    cobsid = snap_observations.record_same(ant_dict,freq,source,ncaptures,
        obstype,obsuser,desc,filefragment,"SNAP",0.0,0.0,fpga_file,obs_set_id)
    obs_db.updateAttenVals(cobsid,attendict)
    
    #if we got to this point without raising an exception, we are marking all measurements as OK
    logger.info("marking observations {} as OK".format(cobsid))
    obs_db.markRecordingsOK([cobsid])

def main():

    # Define the argumants
    parser = OptionParser(usage= 'Usage %prog options',
            description='Run an recording with multiple antennas')

    #parser.add_argument('hosts', type=str, help = hostnamesHelpString)
    parser.add_option('--fpga', dest='fpga_file', type=str, action="store", default=default_fpga_file,
                        help = '.fpgfile to program')
    parser.add_option('-n', dest='ncaptures', type=int, action="store", default=default_captures,
                        help ='Number of data captures (for each correlation product)')
    parser.add_option('-i', dest='obs_set', type=int, action="store", default=None,
                        help ='Observation set ID. If present it will continue previous observations. If not set, and no --new, observation will be a ``single`` obs')
    parser.add_option('-a', dest='ants', type=str, action="store", default=None,
                        help ='Comma separated array list of ATA antennas, eg: \"2j,2d,4k\". Must be from different snaps')
    parser.add_option('-s', dest='source', type=str, action="store", default=None,
                        help ='source name to record')
    parser.add_option('-f', dest='freq', type=float, action="store", default=None,
                        help ='observation frequency, in MHz. Only one set of frequencies')
    parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
                        help ="More on-screen information")
    parser.add_option('-m', '--mail', dest='mail', action="store", default=None,
                        help ="The recipient e-mail address (if different from default)")
    parser.add_option('--new', dest='new_obs', type=str, action="store", default=None,
                        help = 'description of new observation set')
    parser.add_option('-t','--type', dest='obs_type', type=str, action="store", default="OTHER",
                        help ='observation type, eg: \"CALIBRATION\", \"OTHER\", \"PULSAR\", \"FRB\".')
    parser.add_option('-u','--user', dest='obs_user', type=str, action="store", default="unknown",
                        help ='observation type, eg: \"CALIBRATION\", \"OTHER\", \"PULSAR\", \"FRB\".')
    parser.add_option('-d','--desc', dest='obs_desc', type=str, action="store", default="single observation",
                        help ='observation description, eg: \"long Pulsar description\"')
    parser.add_option('-p', '--park', dest='do_park', action="store_true", default=False,
                        help ="Park the antennas afterwards")

    (options,args) = parser.parse_args()

    if(options.verbose):
        logger = logger_defaults.getProgramLogger("SNAP_OBS",loglevel=logging.INFO)
    else:
        logger = logger_defaults.getProgramLogger("SNAP_OBS",loglevel=logging.WARNING)

    if len(sys.argv) <= 1:
        logger.warning("no options provided")
        parser.print_help()
        sys.exit(1)

    if options.mail:
        ATAComm.setRecipient(options.mail)

    if options.ants:
        ant_str = options.ants
    else:
        logger.error("antennas were not provided and no config file")
        raise RuntimeError("no antenna string")

    obs_set_id = None
    if options.obs_set: 
        if options.new_obs:
            logger.error("both -i and --new option specified. Aborting")
            raise RuntimeError("-i and --new options were specified")

        try:
            obs_set_id = options.obs_set
            obs_db.getSetData(obs_set_id)
        except:
            logger.error("Data set id {} does not exist".format(obs_set_id))
            raise 
    
    if options.new_obs:
        obs_set_id = obs_db.getNewObsSetID(options.new_obs)
        logger.info("got set id {}".format(obs_set_id))

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

    ncaptures = options.ncaptures
    fpga_file = options.fpga_file
    obsuser = options.obs_user
    obstype = options.obs_type
    obsdesc = options.obs_desc
    do_park = options.do_park

    if obsuser == 'unknown':
        logger.warning("user {} specified. You should put the observer name as -u option. C-c to cancel. Resuming in 5s".format(obsuser))
        time.sleep(5)
    
    do_snap_rec(ant_str,freq, source, ncaptures, obs_set_id, fpga_file, obsuser, obstype, obsdesc, do_park)

    exit()

def do_snap_rec(ant_str,freq, source, ncaptures, obs_set_id, fpga_file, obsuser, obstype, obsdesc, do_park=False):

    logger = logger_defaults.getModuleLogger(__name__)

    ant_list = snap_array_helpers.string_to_array(ant_str);
    full_ant_str = snap_array_helpers.array_to_string(ant_list)

    try:
        ant_groups = ata_control.get_snap_dictionary(ant_list)
    except:
        logstr = "unable to match antennas with snaps"
        logger.exception(logstr)
        raise

    ant_dict = {}
    for csnap in ant_groups:
        if len(ant_groups[csnap]) != 1:
            logger.error('only one antenna per snap allowed, got {}: {}'.format(csnap,",".join(ant_groups[csnap])))
            raise RuntimeError("only 1 antenna per snap allowed")
        ant_dict[csnap] = ant_groups[csnap][0]
    
    if obs_set_id:
        info_string = ("Starting observation:\nDataset ID {4:d}\n\nAnts: {0!s}\nFreq: {1:0.2f}\n"
                "Source: {2:s}\nCaptures {3:d}\n"
                "Type: {5:s} by {6:s} [{7:s}]").format(full_ant_str, freq, source,ncaptures,obs_set_id,obstype,obsuser,obsdesc)
    else:
        info_string = ("Starting observation:\nNO Dataset ID!\n\nAnts: {0!s}\nFreq: {1:0.2f}\n"
                "Source: {2:s}\nCaptures {3:d}\n"
                "Type: {5:s} by {6:s} [{7:s}]").format(full_ant_str, freq, source,ncaptures,obs_set_id,obstype,obsuser,obsdesc)


    logger.info(info_string)
    ATAComm.sendMail("SNAP Obs started",info_string)
    ATAComm.postSlackMsg(info_string)

    logger.info("Reserving antennas %s in bfa antgroup" % full_ant_str)
    try:
        ata_control.reserve_antennas(ant_list)
    except:
        logstr = "unable to reserve the antennas"
        logger.exception(logstr)
        ATAComm.sendMail("SNAP Obs exception",logstr)
        raise

    logger.info("starting observations")
    try:
        ata_control.try_on_lnas(ant_list)
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
        ata_control.make_and_track_ephems(source, full_ant_str );
        logger.info("autotuning")
        ata_control.autotune(full_ant_str)
        ata_control.rf_switch_thread(ant_list)

        logger.info("changing to frequency {}".format(freq))
        ata_control.set_freq(freq, full_ant_str)

        single_snap_recording(ant_dict,obs_set_id,obstype,obsuser,obsdesc,freq,fpga_file,source,ncaptures)
    
        ATAComm.sendMail("SNAP recording ended","Finishing measurements - success")
        ATAComm.postSlackMsg("Finishing recording - success")
    except KeyboardInterrupt:
        logger.info("Keyboard interuption")
        ATAComm.sendMail("SNAP recording ended","Finishing measurements - keyboard interrupt, obsid {}".format(obs_set_id))
        ATAComm.postSlackMsg("Finishing recording - keyboard interrupt")
    except Exception as e:
        logger.exception("something went wrong")
        errmsg = "Finishing recording - failed, obsid {}: {}".format(obs_set_id,e)
        ATAComm.sendMail("SNAP recording ended",errmsg)
        ATAComm.postSlackMsg(errmsg)
        raise
    finally: 
        logger.info("shutting down")
        ata_control.release_antennas(ant_list, do_park)

if __name__== "__main__":
    main()

