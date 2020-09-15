from ATATools import ata_control, ata_coords, ata_helpers, logger_defaults
from SNAPobs import snap_control, snap_defaults, snap_dirs

from . import snap_dada_control, snap_dada_defaults

import datetime
import logging
import time
import os,sys
import numpy as np
import pandas as pd
from pathlib import Path


ATA_SHARE_DIR = snap_defaults.share_dir
ATA_CFG = ata_helpers.parse_cfg(os.path.join(ATA_SHARE_DIR, 
    'ata.cfg'))
ATA_BASE_OBS_DIR = ATA_CFG['OBSDIR']

#ATA_SNAP_TAB = np.loadtxt(os.path.join(ATA_SHARE_DIR, 'ata_snap.tab'),
#        dtype=str)
_snap_tab = open(os.path.join(ATA_SHARE_DIR, 'ata_snap.tab'))
_snap_tab_names = [name for name in _snap_tab.readline().strip().lstrip("#").split(" ") 
        if name]
ATA_SNAP_TAB = pd.read_csv(_snap_tab, delim_whitespace=True, index_col=False, 
        names=_snap_tab_names, dtype=str)
MYCWD = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_HDR_PATH = os.path.join(MYCWD, snap_defaults.template_header)

UTCFMT = ATA_CFG['UTCFMT']


def write_obs_finished(obs_basedir):
    Path(os.path.join(obs_basedir, "obs.finished")).touch()


def get_utc_dada_now(t_sec):
    t = datetime.timedelta(seconds=t_sec)
    return (datetime.datetime.now()+t).strftime(UTCFMT)


#def rfc_to_cfreq(rfreq, ifc, srate):
#    return rfreq - (srate*3./4 - ifc)

def rfc_to_cfreq(rfreq, ifc, srate):
    return rfreq - (srate/2. - ifc)

def get_nearest_pow_2(n):
    lgn = np.log2(n)
    pos = np.ceil(lgn)
    return np.int(pow(2, pos))


def gather_ants(radec, azel, skyfreq, pamvals, detvals, source):
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
        obsvals['PAMx']                         = pamvals['ant%sx' %ant]
        obsvals['PAMy']                         = pamvals['ant%sy' %ant]
        obsvals['PAMDETx']                      = detvals['ant%sx' %ant]
        obsvals['PAMDETy']                      = detvals['ant%sy' %ant]
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


def get_obs_params(ant_list, given_source):
    """
    getting every that has to do with source/obsfreq/position
    """
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
    skyfreq = ata_control.get_freq(ant_list)
    pamvals = ata_control.get_pams(ant_list)
    detvals = ata_control.get_dets(ant_list)

    #assert sorted(list(radec.keys())) == sorted(ant_list)
    obsParams = gather_ants(radec, azel, skyfreq, pamvals,
            detvals, source)
    if discone:
        add_discone(obsParams)
        ant_list.append(snap_defaults.discone_name)

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


def start_recording(ant_list, tobs, npolout = 2, ics=False, 
        acclen=None, dbnull=None, disable_rfi=False, source=None):
    logger =  logger_defaults.getModuleLogger(__name__)

    check_if_valid_ants(ant_list)
    snap_names = []

    sub_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(ant_list)]
    snap_names = list(sub_tab.snap_hostname)

    # better put them in a dictionary
    snaps = {}
    s = snap_control.init_snaps(snap_names)
    for iant,ant in enumerate(ant_list):
        snaps[ant] = s[iant]

    # set accumulation length if provided
    if not acclen:
        acclen = snap_dada_defaults.acclen
    snap_control.set_acc_len(list(snaps.values()), acclen)

    snap_control.stop_snaps(list(snaps.values()))

    obsParams = get_obs_params(ant_list, source)

    for ant in obsParams:
        acc_len = snap_control.get_acc_len_single(snaps[ant])
        obsParams[ant]['TSAMP'] =\
          1./(np.abs(obsParams[ant]['BW'])/obsParams[ant]['NCHAN']/acc_len) #in microsec
        obsParams[ant]['HOST'] = snaps[ant].host


    grace_period = 3 #seconds
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
    for ant in ant_list:
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

    unix_time_start = time.time() + grace_period
    expected_synctime = int(np.ceil(unix_time_start)) + 2

    for ant in obsParams:
        obsParams[ant]['SYNC_TIME'] = expected_synctime
        obsParams[ant]['IFC'] = snap_defaults.ifc
        cfreq = rfc_to_cfreq(obsParams[ant]['RFFREQ'], 
                snap_defaults.ifc, snap_defaults.srate)
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


    headers = create_headers(obsParams)
    header_paths = []
    for ant in sub_tab.ANT_name:
        header_paths.append(os.path.join(base_obs, ant,
            "obs.header"))
        write_dada_header(header_paths[-1], headers[ant])

    logger.info("Starting udp capture code")
    #cpu_cores = list(range(8, len(ant_list)+8))
    cpu_cores = snap_dada_defaults.NIC_cores[:len(ant_list)]
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
        dbsigproc_cores = snap_dada_defaults.proc_cores[:len(ant_list)]
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
