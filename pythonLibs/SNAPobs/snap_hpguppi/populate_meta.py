import re
import yaml
import socket
import numpy as np
import os, sys
from string import Template
from typing import List

from SNAPobs import snap_defaults, snap_config
from ATATools import ata_control

from datetime import datetime
from astropy.time import Time as astropy_Time

from . import snap_hpguppi_defaults as hpguppi_defaults
from . import auxillary as hpguppi_auxillary
from . import record_in as hpguppi_record_in

from ATATools.ata_rest import ATARestException

ATA_SNAP_TAB = snap_config.get_ata_snap_tab()

def _get_stream_mapping(stream_hosts, ignore_control=False):
    """
    1) Get the centre frequency for each of the stream_hosts
    from the REST/control machine, given what tunings are fed to 
    what snaps
    2) Get the antenna name associated with the snap

    An overly complicated function for what it does really
    """
    if type(stream_hosts) != list:
        raise RuntimeError("Please input a list")
    if not all(stream in list(ATA_SNAP_TAB.snap_hostname) for stream in stream_hosts):
        raise RuntimeError("Not all snaps (%s) are provided in the config table (%s)",
                stream_hosts, ATA_SNAP_TAB.snap_hostname)

    obs_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname.isin(stream_hosts)]
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

def _gather_ants(radec, azel, source):
    """
    Returns a single dictionary with every antenna name as key,
    and obs parameters dictionaries as value
    """
    obsDict = {}
    for ant in radec.keys():
        obsvals = {}
        obsvals['SOURCE']                       = source[ant]
        obsvals['RA'], obsvals['DEC']           = radec[ant] if radec[ant] is not None else None, None
        obsvals['AZ'], obsvals['EL']            = azel[ant] if azel[ant] is not None else None, None
        obsDict[ant] = obsvals
    return obsDict

def _safe_ata_control_get(antlist, get_func):
    ret = {}
    for ant in antlist:
        try:
            ret.update(get_func([ant]))
        except:
            ret.update({ant: None})
    return ret

def _get_obs_params(antlo_list):
    ant_list = [ant[:2] for ant in antlo_list]
    ant_list = list(set(ant_list))

    source_s = _safe_ata_control_get(ant_list, ata_control.get_eph_source)
    radec_s = _safe_ata_control_get(ant_list, ata_control.get_ra_dec)
    azel_s  = _safe_ata_control_get(ant_list, ata_control.get_az_el)

    radec   = {}
    azel    = {}
    source  = {}

    # adding LOs to the dictionary
    for antlo in antlo_list:
        ant = antlo[:2]
        lo  = antlo[2]

        azel[ant+lo]    = azel_s[ant]
        source[ant+lo]  = source_s[ant]
        try: # Try getting the ra dec of the source using the ephemeris file name
                # This will fail if we are tracking a non-sidereal source
                # or a custom RA/Dec pair
                radec[ant+lo]   = ata_control.get_source_ra_dec(source[ant+lo])
        except ATARestException as e:
                # These are a bit off because we are using ra/dec values that have been
                # refraction corrected. Offsets are pretty small (sub-arcsecond), so
                # not too major for the ATA
                radec[ant+lo]   = radec_s[ant]

    return _gather_ants(radec, azel, source)


StringList = List[str]# Deprecated in 3.9, can rather use list[str]
def populate_meta(stream_hostnames: StringList, ant_names: StringList, 
									configfile: str=None,
									ignore_control=False,
									hpguppi_daq_instance=-1,
									n_chans=None,
									n_bits=hpguppi_defaults.NBITS,
									start_chan=None,
									dests=None,
                                    max_packet_nchan=hpguppi_defaults.MAX_CHANS_PER_PKT,
									silent=False,
									zero_obs_startstop=True,
									dry_run=False,
                                    default_dir=False,
                                    dut1=False):

    fengine_meta_keyvalues = hpguppi_defaults.fengine_meta_key_values(n_bits)

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
    
    stream_hostname_dict = hpguppi_auxillary.get_stream_hostname_dict_for_antenna_names(ant_names)
    if ant_names is not None and stream_hostnames is None:
        print('stream_hostname_dict', stream_hostname_dict)
        stream_hostnames = [stream_hostname_dict[ant] for ant in ant_names]

    nants      = len(stream_hostnames)
    n_dests    = len(dests)
    sync_time  = ','.join(map(str, np.unique(hpguppi_record_in._get_sync_time_for_streams(stream_hostnames))))
    # snapseq    = ",".join([isnap.replace('frb-snap','').replace('-pi','')
    #     for isnap in stream_hostnames]) #this contains the "physical" snapID

    n_chans_per_dest = n_chans // n_dests

    mapping = _get_channel_selection(dests, start_chan,
            n_chans_per_dest)

    skyfreq_mapping, antname_mapping = _get_stream_mapping(stream_hostnames,
            ignore_control)
    ants_obs_params = _get_obs_params(ant_names)
    source_list = [aop['SOURCE'] for antname, aop in ants_obs_params.items()]
    ant0_obs_params = ants_obs_params[ant_names[0]]

    if len(set(skyfreq_mapping.values())) != 1:
        sys.stderr.write("WARNING: antennas are tuned to different freqs, "
                "OBSFREQ will be given the first value of OBSNFREQ\n")

    if len(set(source_list)) != 1:
        sys.stderr.write("WARNING: antennas do not have the same source")

    assert len(set(list(skyfreq_mapping.values()))) != 0, "subbarray antennas must have the same frequencies"
    lo_obsfreq = skyfreq_mapping[stream_hostnames[0]]
    centre_channel = fengine_meta_keyvalues['FENCHAN']/2
    source     = ant0_obs_params['SOURCE']
    ra_hrs  = ant0_obs_params['RA'][0] # hours
    ra      = ra_hrs * 360 / 24 # convert from hours to degrees
    dec     = ant0_obs_params['RA'][1] #ant0_obs_params['DEC']
    az      = ant0_obs_params['AZ'][0]
    el      = ant0_obs_params['AZ'][1] #ant0_obs_params['EL']
    source =  source.replace(' ', '_')
    if dut1 is True or dut1 is None:
        # get dut1 at the beginning of today
        dut1 = astropy_Time(datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)).get_delta_ut1_utc().value

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
        'dut1'      : dut1,
    }
    for antname in ant_names:
        report_dict['antennae'].append({antname:stream_hostname_dict[antname]})

    for ip_enumer, ip_ifname in enumerate(ifnames_sorted):
        ip = ifnames_ip_dict[ip_ifname]
        chan_lst = mapping_chan_lists[ip_enumer] # keep channel listing as per specification of dests

        n_packets_per_dest = int(np.ceil(n_chans_per_dest / max_packet_nchan))
        n_chans_per_pkt  = n_chans_per_dest // n_packets_per_dest
        schan = chan_lst[0]
        expected_GBps = nants * (n_chans_per_dest/fengine_meta_keyvalues['FENCHAN'])
        expected_GBps *= 2.0 if n_bits == 4 else 4.0 if n_bits == 8 else -1.0

        chan_bw = fengine_meta_keyvalues['FOFF']
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

        ant_names_string = ','.join(ant_names)
        # these are instance specific
        key_val = {
                'OBSBW'    : obsbw,
                'SCHAN'    : schan,
                'NCHAN'    : n_chans_per_dest,
                'OBSNCHAN' : nants*n_chans_per_dest,
                'OBSFREQ'  : obsfreq,
                # 'BINDHOST' : BINDHOST, # static once the instance starts
                # 'BINDPORT' : dest_port, # static once the instance starts
                'CHAN_BW'  : chan_bw,
                'FENCHAN'  : fengine_meta_keyvalues['FENCHAN'],
                'NANTS'    : nants,
                'NPOL'     : fengine_meta_keyvalues['NPOL'],
                'PKTNCHAN' : n_chans_per_pkt,
                'TBIN'     : fengine_meta_keyvalues['TBIN'],
                'NBITS'    : fengine_meta_keyvalues['NBITS'],
                'PKTNTIME' : fengine_meta_keyvalues['N_TIMES_PER_PKT'],
                'SYNCTIME' : sync_time,
                # 'DATADIR'  : DATADIR, # best left to the configuration (numactl grouping of NVMe mounts)
                'PKTFMT'   : hpguppi_defaults.PKTFMT,
                'SOURCE'   : source,
                'RA'       : ra,
                'DEC'      : dec,
                # 'SRC_NAME' : source,    # Rawspec expects these keys (rawspec_rawutils.c#L155-L186)
                # but let record_in determine SRC_NAME such that it is uniform across antennae-groupings, leading to uniform RAW stems
                'RA_STR'   : ra_hrs,    # Rawspec expects these keys (rawspec_rawutils.c#L155-L186)
                'DEC_STR'  : dec,       # Rawspec expects these keys (rawspec_rawutils.c#L155-L186)
                'AZ'       : az,
                'EL'       : el,
                'ANTNAMES' : ant_names_string[0:71],
                'XPCTGBPS' : '{:.3f}GBps {:.3f}Gbps'.format(expected_GBps, expected_GBps*8)
        }

        # manage limited entry length
        if(len(ant_names_string) >= 71): #79 - len('ANTNMS##')
            key_enum = 0
            ant_names_left = ant_names.copy()
            while(len(ant_names_left) > 0):
                num_antnames = len(ant_names_left)
                ant_names_left_string = ','.join(ant_names_left[0:num_antnames])
                while(len(ant_names_left_string) >= 71): #79 - len('ANTNMS##')
                    num_antnames -= 1
                    ant_names_left_string = ','.join(ant_names_left[0:num_antnames])

                if key_enum == 0:
                    key_val['ANTNAMES'] = ant_names_left_string

                key_val['ANTNMS%02d' % key_enum] = ant_names_left_string
                ant_names_left = ant_names_left[num_antnames:]
                key_enum += 1

        if zero_obs_startstop:
            key_val['OBSSTART'] = 0
            key_val['OBSSTOP']  = 0
            
        if default_dir:
            key_val['PROJID']   = hpguppi_defaults.PROJID
            key_val['BANK']     = hpguppi_defaults.BANK
            key_val['BACKEND']  = hpguppi_defaults.BACKEND
        
        if isinstance(dut1, float):
            key_val['DUT1'] = dut1

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