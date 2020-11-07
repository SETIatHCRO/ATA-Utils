from ata_snap import ata_snap_fengine
from SNAPobs import snap_defaults
from ATATools import ata_helpers
import sys,os

from collections import OrderedDict
import casperfpga
import subprocess
import numpy as np


START_ATTN = 27
TARGET_RMS = 17

MAX_ATT = 31.5
MIN_ATT = 0.0


ATA_SHARE_DIR = snap_defaults.share_dir
ATA_CFG = ata_helpers.parse_cfg(os.path.join(ATA_SHARE_DIR,
    'ata.cfg'))
_snap_if = open(os.path.join(ATA_SHARE_DIR, 'ata_if.cfg'))
_snap_if_names = [name for name in _snap_if.readline().strip().lstrip("#").split(" ")
        if name]


ATA_SNAP_IF = pd.read_csv(_snap_if, delim_whitespace=True, index_col=False,
        names=_snap_if_names, dtype=str)
_snap_if.close()

FPGFILE = ATA_CFG['SNAPFPG']



def round50th(list_n):
    ans = []
    for a in list_n:
        mod = a%1
        int_a = np.round(a-mod)
        if mod < 0.25:
            ans.append(float(int_a))
        elif mod >= 0.25 and mod <= 0.75:
            ans.append(float(int_a) + 0.5)
        else:
            ans.append(float(int_a) + 1)
    return np.array(ans)



def setatten(antlist, attenlist):
    command = "ssh sonata@gain-module1 "
    command += "'python attenuatorMain.py"
    command += " -n "
    command += " ".join([str(i) for i in antlist])
    command += " -a "
    command += " ".join(["%.1f"%i for i in attenlist])
    command += "'"

    print(command)

    process = subprocess.Popen(command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=True)

    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)



def tune_if(snap_hosts, fpgfile=None):

    assert type(snap_hosts) == list

    if type(snap_hosts[0]) == str:
        snaps_dict = {snap: ata_snap_fengine.AtaSnapFengine(snap,
            transport=casperfpga.KatcpTransport) for snap in snap_hosts}
    elif type(snap_hosts[0]) == ata_snap_fenging.AtaSnapFengine:
        snaps_dict = {snap.hostname:snap for snap in snap_hosts}

    if not fpgfile:
        fpgfile = FPGFILE

    for feng in snaps_dict.values():
        feng.fpgs.get_system_information(fpgfile)


    if_tab = ATA_SNAP_IF[ATA_SNAP_IF.snap_hostname.isin(snap_names)]
    ant_ch = if_tab.values[:,1:].flatten()

    prev_attn = np.array([START_ATTN]*len(ant_ch))

    for i in range(3):
        prev_attn[prev_attn > MAX_ATT] = MAX_ATT
        prev_attn[prev_attn < MIN_ATT] = MIN_ATT
        setatten(ant_ch, prev_attn)
        rms = []
        for snap_name in list(if_tab.snap_hostname.values):
            snap = snaps_dict[snap_name]
            x,y = snap.adc_get_samples()
            rms.append(x.std())
            rms.append(y.std())

        rms = np.array(rms)
        d_attn = 20*np.log10(rms/TARGET_RMS)
        prev_attn = round50th(prev_attn + d_attn)
