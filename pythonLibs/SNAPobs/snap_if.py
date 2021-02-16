from ata_snap import ata_snap_fengine
from SNAPobs import snap_defaults, snap_config
from ATATools import ata_helpers, logger_defaults
from ATATools.device_lock import set_device_lock, release_device_lock

import sys,os

import casperfpga
import subprocess
import numpy as np
import pandas as pd


START_ATTN = 27
TARGET_RMS = 17

MAX_ATT = 31.5
MIN_ATT = 0.0


ATA_CFG      = snap_config.get_ata_cfg()
ATA_SNAP_IF  = snap_config.get_ata_snap_if() 
ATA_SNAP_TAB = snap_config.get_ata_snap_tab()

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
    logger = logger_defaults.getModuleLogger(__name__)
    command = "ssh sonata@gain-module1 "
    command += "'python attenuatorMain.py"
    command += " -n "
    command += " ".join([str(i) for i in antlist])
    command += " -a "
    command += " ".join(["%.1f"%i for i in attenlist])
    command += "'"

    logger.info(command)

    process = subprocess.Popen(command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=True)

    stdout, stderr = process.communicate()
    #print(stdout)
    #print(stderr)



def tune_if(snap_hosts, fpgfile=None, 
        target_rms=TARGET_RMS):
    """
    Function to tune the IF
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("IF tuner entered")

    assert type(snap_hosts) == list

    if type(snap_hosts[0]) == str:
        snaps_dict = {snap: ata_snap_fengine.AtaSnapFengine(snap,
            transport=casperfpga.KatcpTransport) for snap in snap_hosts}
    elif type(snap_hosts[0]) == ata_snap_fenging.AtaSnapFengine:
        snaps_dict = {snap.hostname:snap for snap in snap_hosts}

    if not fpgfile:
        fpgfile = FPGFILE

    for feng in snaps_dict.values():
        feng.fpga.get_system_information(fpgfile)

    snap_names = list(snaps_dict.keys())

    if_tab = ATA_SNAP_IF[ATA_SNAP_IF.snap_hostname.isin(snap_names)]
    ant_ch = if_tab.values[:,1:].flatten()
    logger.info("Tuning: %s" %if_tab.snap_hostname)
    logger.info("Attemp chans: %s" %ant_ch)

    prev_attn = np.array([START_ATTN]*len(ant_ch))

    for i in range(3):
        prev_attn[prev_attn > MAX_ATT] = MAX_ATT
        prev_attn[prev_attn < MIN_ATT] = MIN_ATT
        setatten(ant_ch, prev_attn)
        rms = []
        for snap_name in list(if_tab.snap_hostname.values):
            snap = snaps_dict[snap_name]

            set_device_lock(snap_name)
            x,y = snap.adc_get_samples()
            release_device_lock(snap_name)

            rms.append(x.std())
            rms.append(y.std())

        rms = np.array(rms)
        d_attn = 20*np.log10(rms/target_rms)
        prev_attn = round50th(prev_attn + d_attn)
    logger.info("IF tuner ended")


def tune_if_ants(ant_list, target_rms=TARGET_RMS):
    assert type(ant_list) == list

    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(ant_list)]
    snap_hosts = list(obs_ant_tab.snap_hostname.values)
    tune_if(snap_hosts, target_rms=target_rms)


def getatten(ant_list):
    logger = logger_defaults.getModuleLogger(__name__)
    assert type(ant_list) == list
    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(ant_list)]

    antchnumber = []
    for _, row in obs_ant_tab.iterrows():
        this_snap_if = ATA_SNAP_IF[ATA_SNAP_IF.snap_hostname == row.snap_hostname]
        antchnumber.append(this_snap_if['chx'].values[0]) #yuck
        antchnumber.append(this_snap_if['chy'].values[0])

    command = "ssh sonata@gain-module1 "
    command += "'python attenuatorMain.py"
    command += " -n "
    command += " ".join(antchnumber)
    command += " -g "
    command += "'"
    logger.info(command)

    process = subprocess.Popen(command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=True)

    stdout, stderr = process.communicate()
    ch_if_attn = _translate_if_output(stdout)

    i = 0
    retdict = {}
    for _, row in obs_ant_tab.iterrows():
        this_snap_if = ATA_SNAP_IF[ATA_SNAP_IF.snap_hostname == row.snap_hostname]
        retdict[row.ANT_name+"x"] = float(ch_if_attn[this_snap_if['chx'].values[0]])
        retdict[row.ANT_name+"y"] = float(ch_if_attn[this_snap_if['chy'].values[0]])

    return retdict


def _translate_if_output(stdout):
    # stdout of shape: '(1, 13.5)\n(2, 14.0)\n(9, 7.5)\n(10, 0.5)\n(13, 5.5)\n(14, 3.5)
    ret = stdout.decode().strip()

    pairs = ret.split("\n")
    retdict = {}
    for i in pairs:
        tmp = i.strip("(").strip(")")
        tmp = tmp.replace(" ","").split(",")
        retdict[tmp[0]] = tmp[1]
    print(retdict)
    return retdict
