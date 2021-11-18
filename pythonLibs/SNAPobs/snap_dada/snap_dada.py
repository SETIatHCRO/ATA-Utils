from ATATools import ata_control, ata_coords, ata_helpers, logger_defaults
from .. import snap_control, snap_defaults, snap_dirs, snap_config, snap_if

from . import snap_dada_control, snap_dada_defaults

import datetime
import logging
import time
import os,sys
import numpy as np
import pandas as pd
from pathlib import Path

ATA_CFG      = snap_config.get_ata_cfg()
ATA_SNAP_TAB = snap_config.get_ata_snap_tab()

ATA_BASE_OBS_DIR = ATA_CFG['OBSDIR']

MYCWD = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_HDR_PATH = os.path.join(MYCWD, snap_defaults.template_header)

UTCFMT = ATA_CFG['UTCFMT']

def dup_arr(a, i):
    ii = len(a)
    dup = a * (i//ii)
    dup += a[:i%ii]
    return dup


def set_freq_auto(freqs, ant_list):
    """
    Automatically sets sky/focus frequencies
    according to the ant-LO mapping in the config files
    """
    logger = logger_defaults.getModuleLogger(__name__)
    if type(freqs) in [float, int]:
        freqs = [freqs]*len(ant_list)

    assert len(freqs) == len(ant_list),\
            "Number of requested frequencies should match number of antennas"

    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(ant_list)]
    los = pd.unique(obs_ant_tab.LO)

    lo_freq_mapping = {}
    for ant,freq in zip(ant_list,freqs):
        obs_ant = obs_ant_tab[obs_ant_tab.ANT_name==ant]
        obs_ant_lo = str(obs_ant.LO.values.squeeze())
        if obs_ant_lo in lo_freq_mapping:
            assert freq == lo_freq_mapping[obs_ant_lo],\
                    "A wrong LO-ant mapping for ant: %s" %(obs_ant.ANT_name)
        else:
            lo_freq_mapping[obs_ant_lo] = freq

    for lo,freq in lo_freq_mapping.items():
        ants_sub = list(obs_ant_tab[obs_ant_tab.LO == lo].ANT_name)
        logger.info("Setting {freq:.2f} (LO: {lo:s}) sky freq for"\
                "ants: ({ants:s})".format(freq=float(freq), lo=lo,
                    ants=",".join(ants_sub)))
        ata_control.set_freq(freq, ants_sub, lo)


"""
def get_freq_auto(ant_list):
    Automatically gets sky/focus frequencies
    according to the ant-LO mapping in the config files
    logger = logger_defaults.getModuleLogger(__name__)

    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(ant_list)]
    los = pd.unique(obs_ant_tab.LO)

    retdict = {}

    for lo in los:
        ants_sub_list = list(obs_ant_tab[obs_ant_tab.LO == lo].ANT_name)
        skyfreq = ata_control.get_freq(ants_sub_list, lo=lo)
        retdict.update(skyfreq)

    return retdict
"""


def get_freq_auto(antlo_list):
    logger = logger_defaults.getModuleLogger(__name__)

    ant_list = list(set([ant[:2] for ant in antlo_list]))
    los  = list(set(ant[2] for ant in antlo_list))

    focus_freq = ata_control.get_freq_focus(ant_list)
    sky_freq   = {lo:ata_control.get_sky_freq(lo) for lo in los}

    retdict = {}

    for antlo in antlo_list:
        ant = antlo[:2]
        lo  = antlo[2]
        retdict[antlo] = [sky_freq[lo], focus_freq[ant]]

    return retdict


def write_obs_finished(obs_basedir):
    Path(os.path.join(obs_basedir, "obs.finished")).touch()


def mark_obs_for_heimdall(utc):
    base_obs = os.path.join(ATA_BASE_OBS_DIR, utc)
    Path(os.path.join(base_obs, "obs.heimdall")).touch()


def get_utc_dada_now(t_sec):
    t = datetime.timedelta(seconds=t_sec)
    return (datetime.datetime.now()+t).strftime(UTCFMT)


#def rfc_to_cfreq(rfreq, ifc, srate):
#    return rfreq - (srate*3./4 - ifc)

def rfc_to_cfreq(rfreq, ifc, bw):
    return rfreq - (bw/2. - ifc)

def get_nearest_pow_2(n):
    lgn = np.log2(n)
    pos = np.ceil(lgn)
    return np.int(pow(2, pos))


def gather_ants(radec, azel, skyfreq, pamvals, detvals, ifattnvals, source):
    """
    Returns a signle dictionary with every antenna name as key,
    and obs parameters dictionaries as value
    """
    obsDict = {}
    for ant in radec.keys():
        obsvals = {}
        obsvals['SOURCE']                       = source[ant]
        obsvals['RA'], obsvals['DEC']           = radec[ant]
        obsvals['AZ'], obsvals['EL']            = azel[ant]
        obsvals['RFFREQ'], obsvals['FOCUSFREQ'] = skyfreq[ant]
        obsvals['BW']                           = snap_defaults.bw
        obsvals['BANDWIDTH']                    = snap_defaults.bw
        obsvals['ANT']                          = ant
        obsvals['NCHAN']                        = snap_defaults.nchan
        obsvals['PAMx']                         = pamvals['%sx' %ant]
        obsvals['PAMy']                         = pamvals['%sy' %ant]
        obsvals['PAMDETx']                      = detvals['%sx' %ant]
        obsvals['PAMDETy']                      = detvals['%sy' %ant]
        obsvals['IFATTNx']                      = ifattnvals['%sx' %ant]
        obsvals['IFATTNy']                      = ifattnvals['%sy' %ant]
        obsDict[ant] = obsvals
    return obsDict



def create_header_line(key, val):
    h = ""
    h += key
    h += " "*(15-len(key))
    h += str(val)
    h += " "*10
    h += "\n"
    return h



def create_headers(obsParams):
    ant_list = list(obsParams.keys())
    template_header = open(TEMPLATE_HDR_PATH, "r").readlines()
    headers = {}
    for ant in ant_list:
        obsParams[ant]['RA'] = ata_coords.hour2hms(obsParams[ant]['RA'])
        obsParams[ant]['DEC'] = ata_coords.deg2dms(obsParams[ant]['DEC'])
        header = template_header.copy()
        for key, val in obsParams[ant].items():
            header.append(create_header_line(key, val))
        headers[ant] = header
    return headers




def add_discone(obsParams):
    first_ant = list(obsParams.keys())[0]
    obsParams[snap_defaults.discone_name] = obsParams[first_ant].copy()
    obsParams[snap_defaults.discone_name]['RA'] = 0.0
    obsParams[snap_defaults.discone_name]['DEC'] = 0.0
    obsParams[snap_defaults.discone_name]['AZ'] = 0.0
    obsParams[snap_defaults.discone_name]['EL'] = 0.0
    obsParams[snap_defaults.discone_name]['ANT'] = snap_defaults.discone_name
    obsParams[snap_defaults.discone_name]['FOCUSFREQ'] = 0.0


"""
def get_obs_params(ant_list, given_source):
    getting every that has to do with source/obsfreq/position
    # add special case for discone
    if snap_defaults.discone_name in ant_list:
        discone = True
        ant_list.remove(snap_defaults.discone_name)
    else:
        discone = False

    if given_source:
        source = {ant:given_source for ant in ant_list}
    else:
        # get source from control
        source = ata_control.get_eph_source(ant_list)
    radec = ata_control.getRaDec(ant_list)
    azel = ata_control.getAzEl(ant_list)
    skyfreq = get_freq_auto(ant_list)
    pamvals = ata_control.get_pams(ant_list)
    detvals = ata_control.get_dets(ant_list)
    ifattnvals = snap_if.getatten(ant_list)

    #assert sorted(list(radec.keys())) == sorted(ant_list)
    obsParams = gather_ants(radec, azel, skyfreq, pamvals,
            detvals, ifattnvals, source)
    if discone:
        add_discone(obsParams)
        ant_list.append(snap_defaults.discone_name)

    return obsParams
"""


def get_obs_params(antlo_list):
    ant_list = [ant[:2] for ant in antlo_list]
    ant_list = list(set(ant_list))

    source_s = ata_control.get_eph_source(ant_list)
    radec_s = ata_control.getRaDec(ant_list)
    azel_s  = ata_control.getAzEl(ant_list)
    pamvals_s = ata_control.get_pams(ant_list)
    detvals_s = ata_control.get_dets(ant_list)
    #ifattnvals

    radec   = {}
    azel    = {}
    pamvals = {}
    detvals = {}
    source  = {}

    # adding LOs to the dictionary
    for antlo in antlo_list:
        ant = antlo[:2]
        lo  = antlo[2]
        radec[ant+lo]   = radec_s[ant]
        azel[ant+lo]    = azel_s[ant]
        source[ant+lo]  = source_s[ant]
        pamvals[ant+lo+"x"] = pamvals_s[ant+"x"]
        pamvals[ant+lo+"y"] = pamvals_s[ant+"y"]
        detvals[ant+lo+"x"] = detvals_s[ant+"x"]
        detvals[ant+lo+"y"] = detvals_s[ant+"y"]

    skyfreq     = get_freq_auto(antlo_list)
    ifattnvals = snap_if.getatten(antlo_list)

    obsParams = gather_ants(radec, azel, skyfreq,
            pamvals, detvals, ifattnvals, source)

    return obsParams


def write_dada_header(headerdir, headerlist):
    open(headerdir, "w").writelines(headerlist)


def check_if_valid_ants(ant_list):
    valid_ants = ATA_CFG['ACTIVE_ANTS']
    mask = [ant in valid_ants for ant in ant_list]
    if not(all(mask)):
        raise RuntimeError("Antennas provided: %s\n"\
                "not all included in valid antennas: %s"\
                %(ant_list, valid_ants))


def start_recording(antlo_list, tobs, npolout = 2, ics=False, 
        acclen=None, dbnull=None, disable_rfi=False, source=None):
    logger =  logger_defaults.getModuleLogger(__name__)

    if len(antlo_list[0]) != 3:
        raise RuntimeError("Make sure to include the LO in the ant list")

    ant_list = [ant[:2] for ant in antlo_list] #can be duplicated
    lo_list  = [ant[2] for ant in antlo_list]

    check_if_valid_ants(ant_list)

    #sub_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(ant_list)]
    sub_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.antlo.isin(antlo_list)]

    if len(sub_tab) != len(antlo_list):
        raise RuntimeError("The specified ant-los (%s) are not in the configuration file (%s)"
                %(antlo_list, sub_tab[['snap_hostname', 'ANT_name', 'LO']]))

    snap_names = list(sub_tab.snap_hostname)

    # better put them in a dictionary
    snaps = {}
    s = snap_control.init_snaps(snap_names)
    #for iant,ant in enumerate(ant_list):
    #    snaps[ant] = s[iant]
    for isnap_name, snap_name in enumerate(snap_names):
        ant = (sub_tab.ANT_name[sub_tab.snap_hostname == snap_name]).values[0]
        lo  = (sub_tab.LO[sub_tab.snap_hostname == snap_name]).values[0].upper()
        snaps[ant+lo] = s[isnap_name]

    # set accumulation length if provided
    if not acclen:
        acclen = snap_dada_defaults.acclen
    snap_control.set_acc_len(list(snaps.values()), acclen)

    snap_control.stop_snaps(list(snaps.values()))

    obsParams = get_obs_params(antlo_list)

    for ant in obsParams:
        acc_len = snap_control.get_acc_len_single(snaps[ant])
        obsParams[ant]['TSAMP'] =\
          1./(np.abs(obsParams[ant]['BW'])/obsParams[ant]['NCHAN']/acc_len) #in microsec
        obsParams[ant]['HOST'] = snaps[ant].host


    grace_period = 2.0 #seconds
    # now create a utc start as rough estimate
    utc_str = get_utc_dada_now(grace_period)
    logger.info("UTC start: %s" %utc_str)

    # add utc start to headers
    for ant in obsParams:
        obsParams[ant]['UTC_START'] = utc_str

    # create obs base directory
    logger.debug("Creating obs directories")
    base_obs = os.path.join(ATA_BASE_OBS_DIR, utc_str)
    snap_dirs.create_dir(base_obs)

    if ics:
        snap_dirs.create_dir(os.path.join(base_obs, "ICS"))
    for ant in antlo_list:
        snap_dirs.create_dir(os.path.join(base_obs, ant))

    #buflogfile = os.path.join(base_obs, "dadadb.log")
    buflogfile = os.path.join(ATA_CFG['LOGDIR'], "dadadb.log")
    
    #reduce size of buffers in case low time resolution
    fact = max(1, get_nearest_pow_2(acclen/snap_dada_defaults.acclen))

    if ics:
        keylist = snap_dada_control.gen_key_list(len(snaps)+1)
        bufsze_list = [snap_dada_defaults.bufsze//fact]*(len(snaps)+1)
        snap_dada_control.create_buffers(keylist, bufsze_list, buflogfile)
    else:
        keylist = snap_dada_control.gen_key_list(len(snaps))
#        bufsze_list = [snap_dada_defaults.bufsze]*len(snaps)
        bufsze_list = [snap_dada_defaults.bufsze//fact]*(len(snaps))
        snap_dada_control.create_buffers(keylist, bufsze_list, buflogfile)

    # Always start at the start+0.3 of a second
    ata_helpers.wait_until(np.ceil(time.time()) + 0.3)
    unix_time_start = time.time() + grace_period
    expected_synctime = int(np.ceil(unix_time_start)) + 2

    for ant in obsParams:
        obsParams[ant]['SYNC_TIME'] = expected_synctime
        obsParams[ant]['IFC'] = snap_defaults.ifc
        cfreq = rfc_to_cfreq(obsParams[ant]['RFFREQ'], 
                snap_defaults.ifc, snap_defaults.bw)
        obsParams[ant]['CFREQ'] = cfreq
        obsParams[ant]['FREQ'] = cfreq
        obsParams[ant]['ORDER'] = "TF"
        if ics:
            obsParams[ant]['ICS'] = 'True'
        else:
            obsParams[ant]['ICS'] = 'False'
        obsParams[ant]['SOURCE'] = obsParams[ant]['SOURCE'].replace(" ","_")


    ata_helpers.wait_until(unix_time_start-1)
    synctime = snap_control.arm_snaps(list(snaps.values()))
    logger.info("Expected synctime: %i, synctime: %i",
            expected_synctime, synctime)
    if expected_synctime != synctime:
        print(unix_time_start)
        print(time.time())
    # Make sure synctime match what is expected
    assert expected_synctime == synctime, "synctimes do not match"


    headers = create_headers(obsParams)
    header_paths = []
    #for ant in sub_tab.ANT_name:
    for antlo in sub_tab.antlo:
        header_paths.append(os.path.join(base_obs, antlo,
            "obs.header"))
        write_dada_header(header_paths[-1], headers[antlo])

    logger.info("Starting udp capture code")
    #cpu_cores = list(range(8, len(ant_list)+8))
    #cpu_cores = snap_dada_defaults.NIC_cores[:len(ant_list)]
    cpu_cores = dup_arr(snap_dada_defaults.NIC_cores, len(ant_list))
    udpdb_logs = [os.path.join(ATA_CFG['LOGDIR'], "udpdb_%s.log")
            %hostn for hostn in list(sub_tab.snap_hostname)]
    if ics:
        snap_dada_control.udpdb(list(sub_tab.snap_hostname), list(sub_tab.recv_host),
                list(sub_tab.recv_port), cpu_cores, header_paths, keylist[:-1],
                udpdb_logs)
    else:
        snap_dada_control.udpdb(list(sub_tab.snap_hostname), list(sub_tab.recv_host),
                list(sub_tab.recv_port), cpu_cores, header_paths, keylist,
                udpdb_logs)

    if dbnull:
        snap_dada_control.dbnull(keylist)
    else:
        #dbsigproc_cores = snap_dada_defaults.proc_cores[:len(ant_list)]
        dbsigproc_cores = dup_arr(snap_dada_defaults.proc_cores, len(antlo_list))
        if ics:
            #snap_dada_control.dbsigproc(keylist[-1])
            raise RuntimeError("ICS mode not fully implemented")
        else:
            dbsigproc_logs = [os.path.join(ATA_CFG['LOGDIR'], "dbsigproc_%s.log")
                %hostn for hostn in list(sub_tab.snap_hostname)]
            snap_dada_control.dbsigproc(keylist, dbsigproc_cores, 
                    dbsigproc_logs, npolout,
                    base_obs, invert_freqs=True, disable_rfi=disable_rfi)


    logger.info("Recording... waiting for obs finish time")
    time.sleep(tobs)

    logger.info("Stopping obs")
    snap_control.stop_snaps(list(snaps.values()))
    time.sleep(1)

    snap_dada_control.destroy_buffers(keylist, buflogfile)
    snap_control.disconnect_snaps(list(snaps.values()))
    logger.info("Obs ended")
    write_obs_finished(base_obs)

    return utc_str

if __name__ == "__main__":
    logger = logger_defaults.getProgramLogger("TEST", loglevel=logging.INFO)
    ant_list = ["1a", "2b", "rfi"]
    tobs = 10 #seconds
    start_recording(ant_list, tobs, npolout=2, ics=False)
