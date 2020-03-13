#!/usr/bin/vim

#author: Janusz S. Kulpa

"""
This is an scheme file to write own python scripts to control ATA antennas
That probably should be done in python notebook, but I'm trying to keep things simple

So first: make sure that ATA-Utils and ATA-Utils-priv are installed and obs credentials
are downloaded. Many of the scripts requires access to obs computer as well.
Ask Janusz S. Kulpa or Alex Pollak about it
"""

from ATATools import ata_control,logger_defaults
from ATAobs import obs_db

def theMainFunction(various_options):
    #ant_list = ['1a','2b']
    logger = logger_defaults.getModuleLogger(__name__)
    try:
        ata_control.reserve_antennas(ant_list)
    except:
        logger.exception("can't reserve antennas")
        raise

    try:
        #there is no guarantee that the antenna LNA's are on. Check it and if needed turn them on
        ata_control.try_on_lnas(ant_list)

        #point the antenna to the source after generation the ephemeris. This function may be 
        #insufficient for some non-standard targets. notify me (J.S. Kulpa) if it needs expanding
        ata_control.make_and_track_ephems(source, ant_list );

        #autotune the pam values
        ata_control.autotune(ant_list)

        #set LO A and feed focus
        ata_control.set_freq(freq, full_ant_str)

        #snap0-2 only:
        #if using RFSwitch, switch to those antennas. In general, using RFswitch means that you should use also 
        #ant_groups = ata_control.get_snap_dictionary(ant_list)
        #so you know which antennas are hooked up where andin general use only one ant from each group at a time
        #and build cirrent_ant_list based on ant_groups
        #ata_control.rf_switch_thread(current_ant_list)
        #also if using snaps, you should probably call
        #attendict = snap_observations.setRMS(ant_dict,fpga_file,default_rms)
        #cobsid = snap_observations.record_same(...)
        #obs_db.updateAttenVals(cobsid,attendict)
        #obs_db.markRecordingsOK([cobsid])
        #and that's it
        #but let's get away from snap0-2 from now on, so you are free to ignore it completely

        #grouping recordings into observation set
        #if you want to create new observation set, call:
        #obs_set_id = obs_db.getNewObsSetID("THIS IS MY OBS SET DESCRIPTION!")
        #if you already have an exiting observation set, make sure it does exist:
        #obs_db.getSetData(obs_set_id)
        #if it is a single-shot, leave it as none
        #obs_set_id=None

        #initializing the new recording for backend and type see:
        #ATAobs.obs_common.getRecType and ATAobs.obs_common.getRecBackend
        recid = obs_db.initRecording(freq,obstype,backend,desc,obsuser,obs_set_id)
        #now, we populate the second table with each antenna pointing
        #most likely az_ and el_offset should be set to 0
        #the last one is set to True to fetch pam settings to the db
        obs_db.initAntennasTable(recid,ant_list,source,az_offset,el_offset,True)
        #we are about to start the recordings, let's note what the starting time is
        obs_db.startRecording(recid)
        #here you should put your function call to do the recording and wait for it to be complete
        #if you are calculating the signal power, in the meantime of afterwards tou can you can call:
        obs_db.updateRMSVals(recid,rmsDict)
        #where rmsdict looks like that:
        #rmsDict={'1a':{'rmsx': 15.2,'rmsy':16.231}}
        #or
        #rmsDict={'1a':{'rmsx': 15.2,'rmsy':16.231},'2b':{'rmsx': 15.2,'rmsy':16.231}}
        #ok, measurements are done, so:
        obs_db.stopRecording(recid)
        #now, if it was a single shot or measurements in the set are independent from each other, call
        obs_db.markRecordingsOK([recid])
        #but if this is a set of recordings (e.g. On-Off where a you need several recordings close in time
        #to finish successfully, you should wait and populate a list of recordings, then call
        #obs_db.markRecordingsOK(all_that_recids)

    except:
        #do whatever you want if something crashed, Yes, some functions can raise the exception
    finally:
        #does not matter if that succeeded or not, you should always release the antennas
        # the do_park bool determines if the antennas should go back do default position
        # for the debugging process, it's better to let them be, because you won't waste time
        # to re-acquire the source, but in normal operation you should by default part the antennas
        ata_control.release_antennas(ant_list, do_park)

def main():
    #parse options and call the main function

    #get logger (you can also use getFileLogger instead
    if(options.verbose):
        logger = logger_defaults.getProgramLogger("myProg",loglevel=logging.INFO)
    else:
        logger = logger_defaults.getProgramLogger("myProg",loglevel=logging.WARNING)


if __name__== "__main__":
    main()

