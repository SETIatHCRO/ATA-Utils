import casperfpga
import sys
import time
import numpy as np
import argparse
from ATATools import logger_defaults

HIRES = True
if HIRES:
    from ata_snap import ata_snap_fengine


def init_snaps(snap_list):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Initialising snaps: %s" %snap_list)
    if HIRES:
        snaps = [ata_snap_fengine.AtaSnapFengine(snap, 
            transport=casperfpga.KatcpTransport) for snap in snap_list]
    else:
        snaps = [casperfpga.CasperFpga(snap,
            transport = casperfpga.KatcpTransport) for snap in snap_list]
    return snaps


def disconnect_snaps(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("disconnecting snaps")
    for snap in snaps:
        if HIRES:
            snap.fpga.disconnect()
        else:
            snap.transport._timeout = 0.5
            snap.disconnect()


def set_acc_len(snaps, acclen):
    logger = logger_defaults.getModuleLogger(__name__)
    hosts = [snap.host for snap in snaps]
    logger.info("Setting accumulation of snaps: %s to "\
            "a length of: %i" %(",".join(hosts), acclen))
    for snap in snaps:
        if HIRES:
            snap.set_accumulation_length(acclen)
        else:
            snap.write_int('timebase_sync_period', 
                    acclen * 4096 // 4) # convert to FPGA clocks (4096-point FFT, adc is operating as demux 4


def arm_snaps(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Arming snaps...")

    disable_ethernet_output(snaps)

    if HIRES:
        current_sync = snaps[0].sync_get_ext_count()
    else:
        current_sync = snaps[0].read_int("sync_count")
    time.sleep(0.05)

    if HIRES:
        while(snaps[0].sync_get_ext_count() == current_sync):
            time.sleep(0.05)
    else:
        while(snaps[0].read_int("sync_count") == current_sync):
            time.sleep(0.05)

    if HIRES:
        sync_time_arr = []
        for snap in snaps:
            sync_time = snap.sync_arm()
            sync_time_arr.append(sync_time)
        assert len(set(sync_time_arr)) == 1, "Sync times is different across all FPGAs!"

    else:
        sync_time = int(np.ceil(time.time())) + 2 # Number of seconds for sync is det rmined by design
        # PPS passed!
        for snap in snaps:
            snap.write_int("sync_arm", 1)
            snap.write_int("sync_arm", 0)
            # Writing new sync time to snap memory
            snap.write_int("sync_sync_time", sync_time)

    enable_ethernet_output(snaps)

    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Snaps armed successfully, synctime: %i" %sync_time)
    return sync_time



def disable_ethernet_output(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Disabling ethernet output")
    if HIRES:
        for snap in snaps:
            snap.eth_reset()
    else:
        for snap in snaps:
            snap.write_int("tge_en", 0)
            snap.write_int("tge_rst", 1)
            snap.write_int("tge_ctr_rst", 1)

def enable_ethernet_output(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Enabling ethernet output")
    if HIRES:
        for snap in snaps:
            snap.eth_enable_output(enable=True)
    else:
        for snap in snaps:
            snap.write_int("tge_en", 1)
            snap.write_int("tge_rst", 0)
            snap.write_int("tge_ctr_rst", 0)




def stop_snaps(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Stopping SNAPs")
    if HIRES:
        for snap in snaps:
            snap.eth_enable_output(enable=False)
    else:
        for snap in snaps:
            snap.write_int("tge_en", 0)


def get_acc_len_single(snap):
    if HIRES:
        tb_syn_period = snap.fpga.read_int('timebase_sync_period')
        return float(tb_syn_period/snap.n_chans_f/2*8) # *2 for real-FFT; /8 for ADC demux
    else:
        tb_syn_period = snap.read_int('timebase_sync_period')
        return float(tb_syn_period / (4096/4))
