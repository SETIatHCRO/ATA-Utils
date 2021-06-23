import re
import yaml
import socket
import numpy as np
import os, sys
from string import Template
from typing import List

from SNAPobs import snap_defaults, snap_config
from SNAPobs.snap_dada import snap_dada
from ATATools import ata_control

from . import snap_hpguppi_defaults as hpguppi_defaults
from . import auxillary as hpguppi_auxillary

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
def populate_meta(stream_hostnames: StringList, ant_names: StringList, 
									configfile: str=None,
									ignore_control=False,
									hpguppi_daq_instance=-1,
									n_chans=None,
									start_chan=None,
									dests=None,
                                    max_packet_nchan=hpguppi_defaults.MAX_CHANS_PER_PKT,
									silent=False,
									zero_obs_startstop=True,
									dry_run=False,
                                    default_dir=False):

    if configfile is not None and configfile != '':
        if not os.path.exists(configfile):
            print('Specified configfilepath', configfile, ' does not exist... ')
        else:
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
        return

    if ant_names is None and stream_hostnames is not None:
        ant_name_dict = hpguppi_auxillary.get_antenna_name_dict_for_stream_hostnames(stream_hostnames)
        print('ant_name_dict', ant_name_dict)
        ant_names = [ant_name_dict[snap] for snap in stream_hostnames]
    elif ant_names is not None and stream_hostnames is None:
        stream_hostname_dict = hpguppi_auxillary.get_stream_hostname_dict_for_antenna_names(ant_names)
        print('stream_hostname_dict', stream_hostname_dict)
        stream_hostnames = [stream_hostname_dict[ant] for ant in ant_names]

    nants      = len(stream_hostnames)
    n_dests    = len(dests)
    sync_time  = int(hpguppi_defaults.redis_obj.get('SYNCTIME'))
    # snapseq    = ",".join([isnap.replace('frb-snap','').replace('-pi','')
    #     for isnap in stream_hostnames]) #this contains the "physical" snapID

    n_chans_per_dest = n_chans // n_dests

    mapping = _get_channel_selection(dests, start_chan,
            n_chans_per_dest)

    skyfreq_mapping, antname_mapping = _get_snap_mapping(stream_hostnames,
            ignore_control)
    ants_obs_params = snap_dada.get_obs_params(ant_names)
    source_list = [aop['SOURCE'] for antname, aop in ants_obs_params.items()]
    ant0_obs_params = ants_obs_params[ant_names[0]]

    if len(set(skyfreq_mapping.values())) != 1:
        sys.stderr.write("WARNING: antennas are tuned to different freqs, "
                "OBSFREQ will be given the first value of OBSNFREQ\n")

    if len(set(source_list)) != 1:
        sys.stderr.write("WARNING: antennas do not have the same source")

    assert len(set(list(skyfreq_mapping.values()))) != 0, "subbarray antennas must have the same frequencies"
    lo_obsfreq = skyfreq_mapping[stream_hostnames[0]]
    centre_channel = hpguppi_defaults.FENCHAN/2
    source     = ant0_obs_params['SOURCE']
    ra      = ant0_obs_params['RA']
    dec     = ant0_obs_params['DEC']
    az      = ant0_obs_params['AZ']
    el      = ant0_obs_params['EL']

    # logic to deal with multi-instance hashpipes
    # if the gethostbyaddr(ip0) == gethostbyaddr(ip1), assume that
    # ip0 is inst 0, and ip1 is inst 1
    prev_host = "" 
    prev_inst = 0

    # sort the ips by hostname, so that the inst++ works properly, assuming
    # that sequential instances have lexically sequential hostnames
    ifnames_ip_dict = {socket.gethostbyaddr(ip)[0]:ip for ip in mapping.keys()}
    ifnames_sorted = sorted(ifnames_ip_dict.keys())
    mapping_chan_lists = [chan_lst for chan_lst in mapping.values()]

    report_dict = {
        'nchan'     : n_chans,
        'schan'     : start_chan,
        'SOURCE'    : source,
        'RA'        : ra,
        'DEC'       : dec,
        'AZ'        : az,
        'EL'        : el,
        'antennae'  : [],
        'dests'     : [],
    }
    for antname in ant_names:
        report_dict['antennae'].append({antname:snap_hostname_dict[antname]})

    for ip_enumer, ip_ifname in enumerate(ifnames_sorted):
        ip = ifnames_ip_dict[ip_ifname]
        chan_lst = mapping_chan_lists[ip_enumer] # keep channel listing as per specification of dests

        n_packets_per_dest = int(np.ceil(n_chans_per_dest / max_packet_nchan))
        n_chans_per_pkt  = n_chans_per_dest // n_packets_per_dest
        schan = chan_lst[0]
        nstrm = n_chans_per_dest // n_chans_per_pkt


        chan_bw = hpguppi_defaults.FOFF
        obsbw   = len(chan_lst)*chan_bw
        band_centre_chan = np.mean(np.array(chan_lst) + 0.5)
        obsfreq = lo_obsfreq + (band_centre_chan - centre_channel - 0.5)*chan_bw 
        if not silent:
            print(ip, schan, band_centre_chan)
        
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
            inst = prev_inst + 1
        else:
            inst = 0
        
        prev_inst = inst
        prev_host = host
        if hpguppi_daq_instance > -1:
            channel_name = hpguppi_defaults.REDISSETGW.substitute(host=host, inst=hpguppi_daq_instance)
        else:
            channel_name = hpguppi_defaults.REDISSETGW.substitute(host=host, inst=inst)

        # these are instance specific
        key_val = {
                'OBSBW'    : obsbw,
                'SCHAN'    : schan,
                'NSTRM'    : nstrm,
                'OBSFREQ'  : obsfreq,
                # 'BINDHOST' : BINDHOST, # static once the instance starts
                # 'BINDPORT' : dest_port, # static once the instance starts
                'CHAN_BW'  : chan_bw,
                'FENCHAN'  : hpguppi_defaults.FENCHAN,
                'NANTS'    : nants,
                'NPOL'     : hpguppi_defaults.NPOL,
                'PKTNCHAN' : n_chans_per_pkt,
                'TBIN'     : hpguppi_defaults.TBIN,
                'NBITS'    : hpguppi_defaults.NBITS,
                'PKTNTIME' : hpguppi_defaults.N_TIMES_PER_PKT,
                'SYNCTIME' : sync_time,
                # 'DATADIR'  : DATADIR, # best left to the configuration (numactl grouping of NVMe mounts)
                'PKTFMT'   : hpguppi_defaults.PKTFMT,
                'SOURCE'   : source,
                'RA'       : ra,
                'DEC'      : dec,
                # 'SRC_NAME' : source,    # Rawspec expects these keys (rawspec_rawutils.c#L155-L186)
                # but let record_in determine SRC_NAME such that it is uniform across antennae-groupings, leading to uniform RAW stems
                'RA_STR'   : ra,        # Rawspec expects these keys (rawspec_rawutils.c#L155-L186)
                'DEC_STR'  : dec,       # Rawspec expects these keys (rawspec_rawutils.c#L155-L186)
                'AZ'       : az,
                'EL'       : el,
                'ANTNAMES' : ",".join(ant_names)
        }
        if zero_obs_startstop:
            key_val['OBSSTART'] = 0
            key_val['OBSSTOP']  = 0
            
        if default_dir:
            key_val['PROJID']   = hpguppi_defaults.PROJID
            key_val['BANK']     = hpguppi_defaults.BANK
            key_val['BACKEND']  = hpguppi_defaults.BACKEND

        redis_publish_command = hpguppi_auxillary.redis_publish_command_from_dict(key_val)
        if not silent:
            print("channel_name:", channel_name)
            print(redis_publish_command)
            print()

        if not dry_run:
            hpguppi_defaults.redis_obj.publish(channel_name, redis_publish_command)
        else:
            print('^^^Dry Run^^^\n')

        report_dict['dests'].append({
            'ip':ip,
            'hostname':ip_ifname,
            'obsfreq':obsfreq,
            'schan':schan,
            'redis_channel':channel_name,
        })
    return report_dict