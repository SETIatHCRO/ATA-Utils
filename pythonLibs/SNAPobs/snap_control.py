import casperfpga
import sys
import time
import numpy as np
import argparse
from ATATools import logger_defaults


def init_snaps(snap_list):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Initialising snaps: %s" %snap_list)
    snaps = [casperfpga.CasperFpga(snap,
        transport = casperfpga.TapcpTransport) for snap in snap_list]
    return snaps


def disconnect_snaps(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("disconnecting snaps")
    for snap in snaps:
        snap.disconnect()


def arm_snaps(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Arming snaps...")

    disable_ethernet_output(snaps)

    current_sync = snaps[0].read_int("sync_count")
    time.sleep(0.05)
    while(snaps[0].read_int("sync_count") == current_sync):
        time.sleep(0.05)

    sync_time = int(np.ceil(time.time())) + 2 # Number of seconds for sync is det rmined by design
    # PPS passed!
    for snap in snaps:
        snap.write_int("sync_arm", 1)
        snap.write_int("sync_arm", 0)
        # Writing new sync time to snap memory
        snap.write_int("sync_sync_time", sync_time)

    logger.debug("Enabling ethernet output")
    for snap in snaps:
        snap.write_int("tge_rst", 0)
        snap.write_int("tge_ctr_rst", 0)
        snap.write_int("tge_en", 1)

    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Snaps armed successfully, synctime: %i" %sync_time)
    return sync_time



def disable_ethernet_output(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Disabling ethernet output")
    for snap in snaps:
        snap.write_int("tge_en", 0)
        snap.write_int("tge_rst", 1)
        snap.write_int("tge_ctr_rst", 1)



def stop_snaps(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Stopping SNAPs")
    for snap in snaps:
        snap.write_int("tge_en", 0)
