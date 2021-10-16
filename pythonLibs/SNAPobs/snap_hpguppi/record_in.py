from numpy import ceil
import re
import time
from datetime import datetime
import socket
from string import Template

import csv

from ata_snap import ata_snap_fengine
from SNAPobs import snap_control
import casperfpga
import os

from . import snap_hpguppi_defaults as hpguppi_defaults
from . import auxillary as hpguppi_auxillary

from ATATools import ata_control

DEFAULT_START_IN = 2
DEFAULT_OBS_TIME = 300.

def _log_recording(start_time, duration, obsstart, npackets, redisset_chan_list, chan_log_strings):
    logdir = '~'
    if os.path.exists('/home/sonata/logs'):
        logdir = '/home/sonata/logs'
		
    with open(os.path.join(logdir, 'record_in_log.csv'), 'a', newline='') as csvfile:
        csvwr = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for i, redisset_chan in enumerate(redisset_chan_list):
            row_strings = [
                str(datetime.fromtimestamp(start_time)),
                str(duration),
                str(obsstart),
                str(npackets),
                str(redisset_chan),
                str(chan_log_strings[i]) if chan_log_strings is not None else ''
            ]
            csvwr.writerow(row_strings)

def _get_sync_time_for_streams(stream_hostnames):
    fengs = snap_control.init_snaps(stream_hostnames)
    return [feng.fpga.read_int('sync_sync_time') for feng in fengs]

def _get_uniform_source_name_for_streams(streams):
    ant_names_no_LO = [ant_name[0:-1] for ant_name in hpguppi_auxillary.get_antenna_name_per_stream_hostnames(streams)]
    source_dict = ata_control.get_eph_source(ant_names_no_LO[0:1])
    return source_dict[ant_names_no_LO[0]]

def _block_until_key_has_value(hashes, key, value, verbose=True):
    len_per_value = 50//len(hashes)
    value_slice = slice(-len_per_value, None)
    while True:
        rr = [hpguppi_defaults.redis_obj.hget(hsh, key) for hsh in hashes]
        rets = [r.decode() if(r) else "NONE" for r in rr]
        if verbose:
            print_strings = [
                ('{: ^%d}'%len_per_value).format(ret[value_slice]) for ret in rets
            ]
            print('[{: ^66}]'.format(', '.join(print_strings)), end='\r')
        if all([ret[0:len(value)]==value for ret in rets]):
            if verbose:
                print()
            break
        time.sleep(1)

def block_until_hpguppi_idling(hashes, verbose=True):
    _block_until_key_has_value(hashes, "DAQSTATE", "idling", verbose=verbose)
        
def block_until_post_processing_waiting(hashes, verbose=True):
    _block_until_key_has_value(hashes, "PPSTATUS", "WAITING", verbose=verbose)

def _publish_obs_start_stop(redis_obj, channel_list, obsstart, obsstop, obs_source_name, dry_run=False):
    cmd = "OBSSTART=%i\nOBSSTOP=%i\n"  %(obsstart, obsstop)
    cmd += "PKTSTART=%i\nPKTSTOP=%i"  %(obsstart, obsstop)
    if obs_source_name:
        cmd +="\nSRC_NAME=%s" % obs_source_name

    if isinstance(channel_list, str):
        channel_list = [channel_list]
    
    for channel in channel_list:
        print(channel, cmd.replace('\n', '\t'))
        if not dry_run:
            redis_obj.publish(channel, cmd)
    if dry_run:
        print('***DRY RUN***')

def _calculate_obs_start_stop(t_start, duration_s, sync_time, tbin):
    tdiff = t_start - sync_time

    obsstart = int(tdiff/tbin)

    npckts_to_record = int(duration_s/tbin)
    obsstop = obsstart + npckts_to_record
    return obsstart, obsstop, npckts_to_record

def record_in(
				obs_delay_s=DEFAULT_START_IN,
				obs_duration_s=DEFAULT_OBS_TIME,
                tbin=hpguppi_defaults.fengine_meta_key_values()['TBIN'],
				hpguppi_redis_set_channels=None,
				force_synctime=True,
				reset=False,
				dry_run=False,
				log=True,
                log_string_per_channel=None
				):
    
    obsstart = 0
    obsstop = 0
    t_now  = time.time()
    t_in_x = int(ceil(t_now + obs_delay_s))

    if hpguppi_redis_set_channels is None:
        hpguppi_redis_set_channels = [hpguppi_defaults.REDISSET]

    recording_source_name = None

    universal_sync_time = None
    if reset:
        print('Resetting observations:')
    elif force_synctime:
        universal_sync_time = int(hpguppi_defaults.redis_obj.get('SYNCTIME'))
        print("Will broadcast the OBSSTART and OBSSTOP values, based on redishost's SYNCTIME of", universal_sync_time)
        print()
    
    if not reset:
        sync_times = []
        recording_stream_hostname_list = []
        for channel_i, channel in enumerate(hpguppi_redis_set_channels):
            assert re.match(hpguppi_defaults.REDISSETGW_re, channel) or channel == hpguppi_defaults.REDISSET

            if not reset and not force_synctime:
                stream_hostnames = hpguppi_auxillary.get_stream_hostnames_of_redis_chan(hpguppi_defaults.redis_obj, hpguppi_auxillary.redis_get_channel_from_set_channel(channel))
                recording_stream_hostname_list.extend(stream_hostnames)

                channel_sync_times = _get_sync_time_for_streams(stream_hostnames)
                sync_times.extend(channel_sync_times)
                if len(set(sync_times)) != 1:
                    print("Hpguppi channel", channel, "has the following stream_hostnames, with non-uniform sync-times:")
                    for i in range(len(stream_hostnames)):
                        print(stream_hostnames[i], channel_sync_times[i])
                    print("Cannot reliably start a recording.")
                    return False
        
        sync_time = universal_sync_time if force_synctime else sync_times[0]
        obsstart, obsstop, npackets = _calculate_obs_start_stop(t_in_x, obs_duration_s, sync_time, tbin)

        if recording_source_name is None:
            if len(recording_stream_hostname_list) == 0:
                recording_stream_hostname_list = hpguppi_auxillary.get_stream_hostnames_of_redis_chan(
                    hpguppi_defaults.redis_obj,
                    hpguppi_auxillary.redis_get_channel_from_set_channel(hpguppi_redis_set_channels[0])
                )
            
            recording_source_name = _get_uniform_source_name_for_streams(recording_stream_hostname_list)
    
    _publish_obs_start_stop(hpguppi_defaults.redis_obj, hpguppi_redis_set_channels, obsstart, obsstop, recording_source_name, dry_run)
    if log and not reset:# and not dry_run:
        _log_recording(
            t_in_x,
            obs_duration_s,
            obsstart,
            npackets,
            hpguppi_redis_set_channels,
            log_string_per_channel
            )

    return True
