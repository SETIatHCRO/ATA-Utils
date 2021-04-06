import redis
import re
import yaml
import socket
import numpy as np
import sys
from string import Template
from typing import List

from SNAPobs import snap_defaults, snap_config
from ATATools import ata_control

from . import snap_hpguppi_defaults

ATA_SNAP_TAB = snap_config.get_ata_snap_tab()

def _get_snap_mapping(snap_hosts, ignore_control=False):
    """
    1) Get the centre frequency for each of the snap_hosts
    from the REST/control machine, given what tunings are fed to 
    what snaps
    2) Get the antenna name associated with the snap

    An overly complicated function for what it does really
    """
    if type(snap_hosts) != list:
        raise RuntimeError("Please input a list")
    if not all(snap in list(ATA_SNAP_TAB.snap_hostname) for snap in snap_hosts):
        raise RuntimeError("Not all snaps (%s) are provided in the config table (%s)",
                snap_hosts, ATA_SNAP_TAB.snap_hostname)

    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname.isin(snap_hosts)]
    los = np.unique(obs_ant_tab.LO)

    retdict_skyfreq = {}
    for lo in los:
        hostname_sub_list = list(obs_ant_tab[obs_ant_tab.LO == lo].snap_hostname)
        if ignore_control:
            skyfreq = 1400
        else:
            skyfreq = ata_control.get_sky_freq(lo=lo)
        tmp_dict = {snap:freq for snap,freq in zip(hostname_sub_list, 
            [skyfreq]*len(hostname_sub_list))}
        retdict_skyfreq.update(tmp_dict)

    retdict_antname = {i.snap_hostname:i.ANT_name for i in obs_ant_tab.itertuples()}
    return retdict_skyfreq, retdict_antname


def _get_channel_selection(dests, start_chan, n_chans_per_dest):
    mapping = {}
    for dn,d in enumerate(dests):
        mapping[d] = list(range(start_chan + dn*n_chans_per_dest,
            start_chan + (dn+1)*n_chans_per_dest))
    return mapping


StringList = List[str]# Deprecated in 3.9, can rather use list[str]
def populate_meta(snap_hostnames: StringList, ant_names: StringList, 
									configfile: str=None,
									ignore_control=False,
									hpguppi_daq_instance=-1,
									n_chans=None,
									start_chan=None,
									dests=None,
									silent=False,
									dry_run=False):

    r = redis.Redis(host=REDISHOST)

    if configfile != '':
        with open(configfile, 'r') as fh:
            config = yaml.load(fh, Loader=yaml.SafeLoader)

        dest_port = config.get('dest_port')

        voltage_config = config.get('voltage_output')

        dests      = voltage_config['dests']
        n_chans    = voltage_config['n_chans']
        start_chan = voltage_config['start_chan']

    if any([dests is None,
						n_chans is None,
						start_chan is None]):
        print('\nNeed either a configuration file or explicit values for: dests, n_chans, start_chan!')
        print('dests:', dests)
        print('n_chans:', n_chans)
        print('start_chan:', start_chan)
        print()
        exit(1)

    nants      = len(snap_hostnames)
    n_dests    = len(dests)
    sync_time  = int(r.get('SYNCTIME'))
    snapseq    = ",".join([isnap.replace('frb-snap','').replace('-pi','')
        for isnap in snap_hostnames]) #this contains the "physical" snapID

    n_chans_per_dest = n_chans // n_dests

    mapping = _get_channel_selection(dests, start_chan,
            n_chans_per_dest)

    skyfreq_mapping, antname_mapping = _get_snap_mapping(snap_hostnames,
            ignore_control)
    source_dict = ata_control.get_eph_source(ant_names)
    radec_dict = ata_control.getRaDec(ant_names)
    azel_dict  = ata_control.getAzEl(ant_names)

    if len(set(skyfreq_mapping.values())) != 1:
        sys.stderr.write("WARNING: antennas are tuned to different freqs, "
                "OBSFREQ will be given the first value of OBSNFREQ\n")

    if len(set(source_dict.values())) != 1:
        sys.stderr.write("WARNING: antennas do not have the same source")

    assert len(set(list(skyfreq_mapping.values()))) != 0, "subbarray antennas must have the same frequencies"
    lo_obsfreq = skyfreq_mapping[snap_hostnames[0]]
    centre_channel = FENCHAN/2
    source     = source_dict[ant_names[0]]
    ra,dec     = radec_dict[ant_names[0]]
    az,el      = azel_dict[ant_names[0]]

    # logic to deal with multi-instance hashpipes
    # if the gethostbyaddr(ip0) == gethostbyaddr(ip1), assume that
    # ip0 is inst 0, and ip1 is inst 1
    prev_host = "" 
    prev_inst = 0

    for ip,chan_lst in mapping.items():
        n_packets_per_dest = int(np.ceil(n_chans_per_dest / MAX_CHANS_PER_PKT))
        n_chans_per_pkt  = n_chans_per_dest // n_packets_per_dest
        schan = chan_lst[0]
        nstrm = n_chans_per_dest // n_chans_per_pkt


        chan_bw = FOFF
        obsbw   = len(chan_lst)*chan_bw
        band_centre_chan = np.mean(np.array(chan_lst) + 0.5)
        obsfreq = lo_obsfreq + (band_centre_chan - centre_channel - 0.5)*chan_bw 
        if not silent:
            print(ip, schan, band_centre_chan)
        
        ip_ifname = socket.gethostbyaddr(ip)[0]
        # remove -40, -100g-1, -100g-2
        m = re.match(r'(.*)-\d+g.*', ip_ifname)
        if m:
            host = m.group(1)
        else:
            if not silent:
                print('%s: %s does not have -\d+g.* suffix... taking it verbatim'%(ip, ip_ifname))
            host = ip_ifname
        if not silent:
            print(host)

        if host == prev_host:
            prev_inst += 1
        inst = prev_inst
        prev_host = host
        if hpguppi_daq_instance > -1:
            channel_name = REDISSETGW.substitute(host=host, inst=hpguppi_daq_instance)
        else:
            channel_name = REDISSETGW.substitute(host=host, inst=inst)

        # these are instance specific
        key_val = {
                'OBSBW'    : obsbw,
                'SCHAN'    : schan,
                'NSTRM'    : nstrm,
                'OBSFREQ'  : obsfreq,
                # 'BINDHOST' : BINDHOST, # static once the instance starts
                # 'BINDPORT' : dest_port, # static once the instance starts
                'CHAN_BW'  : chan_bw,
                'FENCHAN'  : FENCHAN,
                'NANTS'    : nants,
                'NPOL'     : NPOL,
                'PKTNCHAN' : n_chans_per_pkt,
                'TBIN'     : TBIN,
                'NBITS'    : NBITS,
                'PKTNTIME' : N_TIMES_PER_PKT,
                'SYNCTIME' : sync_time,
                'PROJID'   : PROJID,
                'BANK'     : BANK,
                'BACKEND'  : BACKEND,
                # 'DATADIR'  : DATADIR, # best left to the configuration (numactl grouping of NVMe mounts)
                'PKTFMT'   : PKTFMT,
                'SNAPPAT'  : SNAPPAT,
                'SNAPSEQ'  : snapseq,
                'SOURCE'   : source,
                'RA'       : ra,
                'DEC'      : dec,
                'AZ'       : az,
                'EL'       : el,
                'OBSSTART' : OBSSTART,
                'OBSSTOP'  : OBSSTOP,
                'ANTNAMES' : ",".join(ant_names)
        }

        key_val_str = "\n".join(['%s=%s' %(key,val)
            for key,val in key_val.items()])
        if not silent:
            print("channel_name:", channel_name)
            print(key_val_str)
            print()

        if not dry_run:
            # publish them values
            r.publish(channel_name, key_val_str)
        else:
            print('^^^Dry Run^^^\n')
