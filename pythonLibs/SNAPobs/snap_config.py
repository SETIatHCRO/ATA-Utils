import os,sys
import pandas as pd

from SNAPobs import snap_defaults
from ATATools import ata_helpers


ATA_SHARE_DIR = snap_defaults.share_dir
ATA_CFG = ata_helpers.parse_cfg(os.path.join(ATA_SHARE_DIR,
    'ata.cfg'))
ATA_BASE_OBS_DIR = ATA_CFG['OBSDIR']

_snap_tab = open(os.path.join(ATA_SHARE_DIR, 'ata_snap.tab'))
_snap_tab_names = [name for name in _snap_tab.readline().strip().lstrip("#").split(" ")
        if name]
ATA_SNAP_TAB = pd.read_csv(_snap_tab, delim_whitespace=True, index_col=False,
        names=_snap_tab_names, dtype=str)
_snap_tab.close()

#extend ATA_SNAP_TAB with antlo
ANTLO = [ant+lo.upper() for ant,lo in zip(ATA_SNAP_TAB.ANT_name, ATA_SNAP_TAB.LO)]
ATA_SNAP_TAB.insert(ATA_SNAP_TAB.shape[1], "antlo", ANTLO, True)


_snap_if = open(os.path.join(ATA_SHARE_DIR, 'ata_if.cfg'))
_snap_if_names = [name for name in _snap_if.readline().strip().lstrip("#").split(" ")
        if name]

ATA_SNAP_IF = pd.read_csv(_snap_if, delim_whitespace=True, index_col=False,
        names=_snap_if_names, dtype=str)
_snap_if.close()


def get_ata_cfg():
    return ATA_CFG

def get_ata_snap_tab():
    return ATA_SNAP_TAB

def get_ata_snap_if():
    return ATA_SNAP_IF

def get_ata_base_obs_dir():
    return ATA_BASE_OBS_DIR
