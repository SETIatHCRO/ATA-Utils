from ata_snap import ata_snap_fengine
from SNAPobs import snap_defaults, snap_config, snap_control
from ATATools import ata_helpers, logger_defaults
from ATATools.device_lock import set_device_lock, release_device_lock
import warnings

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


def setatten(antpol_dict):
    """
    antpol_dict: dict with example values
        {'1ax': 12.0, '1ay': 13.5}
    """

    logger = logger_defaults.getModuleLogger(__name__)
    all_ants_list = []
    for antpol, attenval in antpol_dict.items():
        if not (antpol.endswith("x") or antpol.endswith("y")):
            raise RuntimeError("Antpol (%s) doesn't end with 'x' or 'y'"
                    %(antpol))
        ant = antpol[:-1]
        all_ants_list.append(ant)

    all_ants_list = list(set(all_ants_list))

    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(all_ants_list)]
    attemp_modules = set(ATA_SNAP_IF.module.tolist())


    for att_mod in attemp_modules:
        ata_snap_if_this_attmod  = ATA_SNAP_IF[ATA_SNAP_IF.module == att_mod]

        if_channels = []
        atten_values = []
        for antpol, attenval in antpol_dict.items():
            ant = antpol[:-1]
            pol = antpol[-1]
            if ant not in list(ATA_SNAP_TAB.ANT_name):
                raise RuntimeError("Antenna (%s) not in antenna list: %s"
                        %(ant, list(ATA_SNAP_TAB.ANT_name)))
            snap_hostname = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name == ant].snap_hostname.values[0]
            if not snap_hostname in list(ata_snap_if_this_attmod.snap_hostname):
                continue
            snap_if_entry = ATA_SNAP_IF[ATA_SNAP_IF.snap_hostname == snap_hostname]

            if_ch = snap_if_entry['ch'+pol].values[0]

            if_channels.append(if_ch)
            atten_values.append(attenval)

        if not if_channels:
            continue

        _setatten(if_channels, atten_values, att_mod)


def _setatten(chanlist, attenlist, module=0):
    logger = logger_defaults.getModuleLogger(__name__)
    command = "ssh sonata@gain-module%i "%int(module)
    command += "'python attenuatorMain.py"
    command += " -n "
    command += " ".join([str(i) for i in chanlist])
    command += " -a "
    command += " ".join(["%.1f"%i for i in attenlist])
    command += "'"

    logger.info(command)
    print(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=True)

    stdout, stderr = process.communicate()
    #print(stdout)
    #print(stderr)



def tune_if(snap_hosts):
    """
    Function to tune the IF
    """
    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("IF tuner entered")

    assert type(snap_hosts) == list

    if type(snap_hosts[0]) == str:
        snaps = snap_control.init_snaps(snap_hosts)
        snaps_dict = {snap_name: snaps[isnap_name] for isnap_name,snap_name
                in enumerate(snap_hosts)}
    #elif type(snap_hosts[0]) == ata_snap_fenging.AtaSnapFengine:
    #    snaps_dict = {snap.hostname:snap for snap in snap_hosts}

    snap_control.get_system_information(list(snaps_dict.values()))

    snap_names = list(snaps_dict.keys())

    if_tab = ATA_SNAP_IF[ATA_SNAP_IF.snap_hostname.isin(snap_names)]
    #ant_ch = if_tab.values[:,1:].flatten()
    att_numbs = if_tab.module.unique()
    for att_num in att_numbs:
        print(if_tab)
        print(att_num)
        if_tab_sub = if_tab[if_tab.module == att_num]
        print(if_tab_sub)
        ant_ch = if_tab_sub[['chx', 'chy']].values.flatten()

        logger.info("Tuning: %s" %if_tab.snap_hostname)
        logger.info("Attemp chans: %s" %ant_ch)

        prev_attn = np.array([START_ATTN]*len(ant_ch))
        target_rms = []
        for host_name in if_tab_sub.snap_hostname:
            print(host_name)
            if host_name.startswith("frb-snap"):
                target_rms.append(17) #X pol
                target_rms.append(17) #Y pol
            elif host_name.startswith("rfsoc"):
                target_rms.append(1024) #X pol
                target_rms.append(1024) #Y pol
            else:
                print("Something is wrong")
                sys.exit(-1)
        target_rms = np.array(target_rms)

        for i in range(3):
            if np.any(prev_attn > MAX_ATT):
                warn_ant_ch = ant_ch[prev_attn > MAX_ATT]
                warn_prev_attn = prev_attn[prev_attn > MAX_ATT]
                warnings.warn("Trying to set attenuator on channels %s to values %s, which is more than max [%i]"
                        %(list(warn_ant_ch), list(warn_prev_attn), MAX_ATT))
                prev_attn[prev_attn > MAX_ATT] = MAX_ATT
            if np.any(prev_attn < MIN_ATT):
                warn_ant_ch = ant_ch[prev_attn < MIN_ATT]
                warn_prev_attn = prev_attn[prev_attn < MIN_ATT]
                warnings.warn("Trying to set attenuator on channels %s to values %s, which is less than min [%i]"
                        %(list(warn_ant_ch), list(warn_prev_attn), MIN_ATT))
                prev_attn[prev_attn < MIN_ATT] = MIN_ATT

            _setatten(ant_ch, prev_attn, att_num)
            rms = []
            for snap_name in list(if_tab_sub.snap_hostname.values):
                snap = snaps_dict[snap_name]

                set_device_lock(snap_name)
                x,y = snap.adc_get_samples()
                x = np.array(x)
                y = np.array(y)
                print(np.std(x),np.std(y))
                release_device_lock(snap_name)

                rms.append(x.std())
                rms.append(y.std())

            rms = np.array(rms)
            d_attn = 20*np.log10(rms/target_rms)
            prev_attn = round50th(prev_attn + d_attn)
        snap_control.disconnect_snaps(snap_hosts)
        logger.info("IF tuner ended")


def tune_if_ants(ant_list, target_rms=TARGET_RMS):
    assert type(ant_list) == list

    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(ant_list)]
    snap_hosts = list(obs_ant_tab.snap_hostname.values)
    print("snap_hosts:")
    print(snap_hosts)
    tune_if(snap_hosts)


def tune_if_antslo(antlo_list):
    assert type(antlo_list) == list

    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.antlo.isin(antlo_list)]
    snap_hosts = list(obs_ant_tab.snap_hostname.values)
    print("snap_hosts:")
    print(snap_hosts)
    tune_if(snap_hosts)



"""
def getatten(ant_list):
    logger = logger_defaults.getModuleLogger(__name__)
    assert type(ant_list) == list
    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(ant_list)]

    attemp_modules = set(ATA_SNAP_IF.module.tolist())

    retdict = {}

    for att_mod in attemp_modules:
        antchnumber = []
        ata_snap_if_this_attmod = ATA_SNAP_IF[ATA_SNAP_IF.module == att_mod]

        for _, row in obs_ant_tab.iterrows():
            this_snap_if = ata_snap_if_this_attmod[ata_snap_if_this_attmod.snap_hostname \
                    == row.snap_hostname]
            if this_snap_if.shape[0] == 0:
                continue
            antchnumber.append(this_snap_if['chx'].values[0]) #yuck
            antchnumber.append(this_snap_if['chy'].values[0])

        if (len(antchnumber) == 0): #nothing on current module
            continue 

        command = "ssh sonata@gain-module%i " %(int(att_mod))
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

        for _, row in obs_ant_tab.iterrows():
            this_snap_if = ata_snap_if_this_attmod[
                    ata_snap_if_this_attmod.snap_hostname == row.snap_hostname]
            if this_snap_if.shape[0] == 0:
                continue
            retdict[row.ANT_name+"x"] = float(ch_if_attn[this_snap_if['chx'].values[0]])
            retdict[row.ANT_name+"y"] = float(ch_if_attn[this_snap_if['chy'].values[0]])

    return retdict
"""

def getatten(antlo_list):
    """
    antlo_list: list if ant_los similar to:
       "1aA", "1kA", "1kB", "1hB", "2aA", "2aB", "3dc"
    where the last letter in the name is the LO letter

    returns:
        dict with keys same as antlo_list, but appended with
        "x" and "y" for each polarisation, and the attenuation value
        as dictionary values
    """

    logger = logger_defaults.getModuleLogger(__name__)
    assert type(antlo_list) == list

    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.antlo.isin(antlo_list)]

    assert len(obs_ant_tab) == len(antlo_list)

    ata_snap_if = ATA_SNAP_IF[
            ATA_SNAP_IF.snap_hostname.isin(obs_ant_tab.snap_hostname)]

    att_modules = ata_snap_if.module.unique()

    retdict = {}

    for att_mod in att_modules:
        this_snap_if = ata_snap_if[ata_snap_if.module == att_mod]

        antchnumber = []
        for _,row in this_snap_if.iterrows():
            antchnumber.append(row.chx)
            antchnumber.append(row.chy)

        command = "ssh sonata@gain-module%i " %(int(att_mod))
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

        for _, row in this_snap_if.iterrows():
            antlo = obs_ant_tab[obs_ant_tab.snap_hostname == row.snap_hostname].antlo.values[0]
            retdict[antlo+"x"] = float(ch_if_attn[row['chx']])
            retdict[antlo+"y"] = float(ch_if_attn[row['chy']])

    return retdict



def _translate_if_output(stdout):
    # python 2 output
    # stdout of shape: '(1, 13.5)\n(2, 14.0)\n(9, 7.5)\n(10, 0.5)\n(13, 5.5)\n(14, 3.5)
    # python 3 output
    # stdout of shape: 1 15.0\n2 15.0\n11 15.0\n12 15.0\n

    ret = stdout.decode().strip()

    pairs = ret.split("\n")
    retdict = {}
    for i in pairs:
        if i.startswith("("):
            tmp = i.strip("(").strip(")")
            tmp = tmp.replace(" ","").split(",")
        else:
            tmp = i.split(" ")

        retdict[tmp[0]] = tmp[1]
    #print(retdict)
    return retdict
