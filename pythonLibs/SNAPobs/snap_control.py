import casperfpga
import sys
import time
import numpy as np
import argparse
import warnings
from ATATools import logger_defaults

from ata_snap import ata_snap_fengine


def init_snaps(snap_list, get_system_information=False):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Initialising snaps: %s" %snap_list)
    snaps = [ata_snap_fengine.AtaSnapFengine(snap, 
        transport=casperfpga.KatcpTransport) for snap in snap_list]

    if get_system_information:
        if type(get_system_information) == bool:
            from .snap_config import get_ata_cfg
            ata_cfg = get_ata_cfg()
            fpg_file = ata_cfg['SNAPFPG']
        elif type(get_system_information) == str:
            fpg_file = get_system_information

        for snap in snaps:
            snap.fpga.get_system_information(fpg_file)

    return snaps


def disconnect_snaps(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("disconnecting snaps")
    for snap in snaps:
        try:
            snap.fpga.disconnect()
        except Exception as e:
            warnings.warn(str(e))


def set_acc_len(snaps, acclen):
    logger = logger_defaults.getModuleLogger(__name__)
    hosts = [snap.host for snap in snaps]
    logger.info("Setting accumulation of snaps: %s to "\
            "a length of: %i" %(",".join(hosts), acclen))
    for snap in snaps:
        snap.set_accumulation_length(acclen)


def arm_snaps(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Arming snaps...")

    disable_ethernet_output(snaps)

    current_sync = snaps[0].sync_get_ext_count()
    time.sleep(0.05)

    while(snaps[0].sync_get_ext_count() == current_sync):
        time.sleep(0.05)

    sync_time_arr = []
    for snap in snaps:
        sync_time = snap.sync_arm()
        sync_time_arr.append(sync_time)
    if len(set(sync_time_arr)) != 1:
        for i,snap in enumerate(snaps):
            print(snap.host, sync_time_arr[i])
        raise RuntimeError("Sync times is different across all FPGAs!")

    enable_ethernet_output(snaps)

    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Snaps armed successfully, synctime: %i" %sync_time)
    return sync_time



def disable_ethernet_output(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Disabling ethernet output")
    for snap in snaps:
        snap.eth_reset()

def enable_ethernet_output(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.debug("Enabling ethernet output")
    for snap in snaps:
        snap.eth_enable_output(enable=True)


def stop_snaps(snaps):
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Stopping SNAPs")
    for snap in snaps:
        snap.eth_enable_output(enable=False)


def get_acc_len_single(snap):
    tb_syn_period = snap.fpga.read_int('timebase_sync_period')
    return float(tb_syn_period/snap.n_chans_f/2*8) # *2 for real-FFT; /8 for ADC demux
