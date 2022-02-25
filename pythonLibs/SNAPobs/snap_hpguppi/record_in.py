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
	
    if isinstance(redisset_chan_list, str):
        redisset_chan_list = [redisset_chan_list]

    with open(os.path.join(logdir, 'record_in_log.csv'), 'a', newline='') as csvfile:
        csvwr = csv.writer(csvfile, delimiter=',',
                            quotechar='\'', quoting=csv.QUOTE_MINIMAL)
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
    fengs = snap_control.init_snaps(hpguppi_auxillary.filter_unique_hostnames(stream_hostnames))
    sync_times = [feng.fpga.read_int('sync_sync_time') for feng in fengs]
    snap_control.disconnect_snaps(fengs)
    return sync_times

def _get_uniform_source_name_for_streams(streams):
    ant_names_no_LO = [ant_name[0:-1] for ant_name in hpguppi_auxillary.get_antenna_name_per_stream_hostnames(streams)]
    source_dict = ata_control.get_eph_source(ant_names_no_LO[0:1])
    return source_dict[ant_names_no_LO[0]].replace(' ', '_')

def _block_until_key_has_value(hashes, key, value, verbose=True):
    len_per_value = 80//len(hashes)
    value_slice = slice(-len_per_value, None)
    while True:
        rr = [hpguppi_defaults.redis_obj.hget(hsh, key) for hsh in hashes]
        rets = [r.decode() if(r) else 'NONE' for r in rr]
        if verbose:
            print_strings = [
                ('{: ^%d}'%len_per_value).format(ret[value_slice]) for ret in rets
            ]
            print('[{: ^80}]'.format(', '.join(print_strings)), end='\r')
        if all([ret.startswith(value) for ret in rets]):
            if verbose:
                print()
            break
        time.sleep(1)

def block_until_hpguppi_idling(hashes, verbose=True):
    _block_until_key_has_value(hashes, 'DAQSTATE', 'idling', verbose=verbose)
        
def block_until_post_processing_waiting(hashes, verbose=True):
    _block_until_key_has_value(hashes, 'PPSTATUS', 'WAITING', verbose=verbose)

def _publish_obs_start_stop(redis_obj, channel_list, obsstart, obsstop, obs_source_name, dry_run=False):
    # cmd = 'OBSSTART=%i\nOBSSTOP=%i\n'  %(obsstart, obsstop)
    cmd = 'PKTSTART=%i\nPKTSTOP=%i'  %(obsstart, obsstop)
    if obs_source_name:
        cmd +='\nSRC_NAME=%s' % obs_source_name

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
    hashpipe_targets=None,
    universal_synctime=False,
    universal_tbin=None,
    universal_source_name=None,
    reset=False,
    dry_run=False,
    log=True,
    log_string_per_channel=None
):
    '''
    Writes PKTSTART and PKTSTOP, which control observation range, to the
    hashpipe instances specified.

    Parameters
    ----------
    obs_delay_s: num
        The delay, from now, after which the observation range begins (in seconds)
    obs_duration: num
        The duration of the observation range (in seconds)
    hashpipe_targets: None,list,dict [None]
        The hashpipe-instances to target.
        If None, then broadcast to all instances (on redis channel
        'hashpipe://set').
        If a list, then a list of redis channels (asserted to be of template
        'hashpipe://${host}/${inst}/set').
        If a dict, expected to be of form {hostname: [instance_num]}
    universal_synctime: bool [False]
        If true, consult the default Redis hash for 'SYNCTIME'.
        Else, consult each hashpipe instance and ensure uniformity.
    universal_tbin: num (situational) [None]
        The universal `tbin` value to use. Only used if broadcasting the
        observation range, i.e. if hashpipe_targets == 'hashpipe:///set' or
        hashpipe_targets is None.
    universal_source_name: str [None]
        The universal `SRC_NAME` to publish. Only used if broadcasting the
        observation range, i.e. if hashpipe_targets == 'hashpipe:///set' or
        hashpipe_targets is None.
    reset: bool [False]
        Set the observation range to [PKTSTART=0, PKTSTOP=0].
    dry_run: bool [False]
        Don't publish key-values to Redis, just print-out.
    log: bool [True]
        Log a statement of the observation range in record_in_log.csv, per
        channel published to (not if reset).
    log_string_per_channel: list(string) [None]
        A string to append to each log entry.

    Returns
    -------
    bool: True if no issue occurred, False otherwise.
    '''
    
    if hashpipe_targets is None:
        hashpipe_targets = [hpguppi_defaults.REDISSET]
    else:
        # ignore any universal values passed in
        universal_tbin = False
        universal_source_name = False

    if hpguppi_defaults.REDISSET in hashpipe_targets:
        # not possible to query universal tbin/source_name from broadcast channel
        assert universal_tbin is not None, 'universal_tbin argument must be provided in the case of broadcast'
        assert universal_source_name is not None, 'universal_source_name argument must be provided in the case of broadcast'
        assert universal_synctime, 'universal_synctime argument must be True in the case of broadcast'

    if isinstance(hashpipe_targets, dict):
        # fabricate the channels from {hostname: [instance_num]} dict
        hashpipe_targets = hpguppi_auxillary.redis_hashpipe_set_channels_from_dict(hashpipe_targets)

    if reset:
        print('Resetting observations:')
    elif universal_synctime:
        universal_synctime = int(hpguppi_defaults.redis_obj.get('SYNCTIME'))
        print(
            ('Will broadcast the OBSSTART and OBSSTOP values, based on'
                'redishost\'s SYNCTIME of'),
            universal_synctime
        )
        print()
    
    target_sync_times = {}
    target_tbin_values = {}
    target_source_names = {}
    # gather data first, then calculate obsstart/stop for syncronicity
    # (reading sync_time from the FEngines is the biggest bottleneck)
    for set_channel in hashpipe_targets:
        assert (re.match(hpguppi_defaults.REDISSETGW_re, set_channel) or
         set_channel == hpguppi_defaults.REDISSET
        )
        if not reset:
            if set_channel != hpguppi_defaults.REDISSET:
                get_channel = hpguppi_auxillary.redis_get_channel_from_set_channel(
                    set_channel
                )
                # get the hostnames of the antenna streams for this hashpipe instance
                stream_hostnames = hpguppi_auxillary.get_stream_hostnames_of_redis_chan(
                    hpguppi_defaults.redis_obj, get_channel
                )

            if universal_synctime is False: # 
                channel_sync_times = _get_sync_time_for_streams(stream_hostnames)
                channel_synct_times_setlen = len(set(channel_sync_times))
                if channel_synct_times_setlen == 0:
                    print(
                        'Hpguppi channel',
                        get_channel,
                        'has nostream_hostnames, excluding from observation.'
                    )
                    continue
                elif channel_synct_times_setlen > 1:
                    error_statement = (
                        'Hpguppi channel {} has the following'
                        'stream_hostnames, with non-uniform sync-times:\n'
                    ).format(get_channel)
                    for i in range(len(stream_hostnames)):
                        error_statement += "{} {}\n".format(
                            stream_hostnames[i],
                            channel_sync_times[i]
                        )
                    error_statement = (
                        'Cannot reliably start a recording: {}'.format(
                            error_statement
                        )
                    )
                    raise RuntimeError(error_statement)
                
                target_sync_times[set_channel] = channel_sync_times[0]
            else: # universal_synctime
                target_sync_times[set_channel] = universal_synctime
            
            if universal_tbin is False:
                tbin = hpguppi_defaults.redis_obj.hget(get_channel, 'TBIN')
                try:
                    target_tbin_values[set_channel] = float(tbin)
                except:
                    error_statement = (
                        'Cannot reliably start a recording: Hpguppi channel {} '
                        'has a non-numeric TBIN value {}.').format(
                            get_channel, tbin)
                    raise RuntimeError(error_statement)
            else:
                target_tbin_values[set_channel] = float(universal_tbin)

            if universal_source_name is False:
                target_source_names[set_channel] = _get_uniform_source_name_for_streams(stream_hostnames)
            else:
                target_source_names[set_channel] = universal_source_name

        
    assert len(target_sync_times.keys()) == len(target_tbin_values.keys()) == len(target_source_names.keys())

    obsstart = 0
    obsstop = 0
    npackets = 0
    t_now  = time.time()
    t_in_x = int(ceil(t_now + obs_delay_s))

    for target_i, target_set_chan in enumerate(target_sync_times.keys()):
        if not reset:
            sync_time = target_sync_times[target_set_chan]
            tbin = target_tbin_values[target_set_chan]
            source_name = target_source_names[target_set_chan]
            obsstart, obsstop, npackets = _calculate_obs_start_stop(t_in_x, obs_duration_s, sync_time, tbin)

        _publish_obs_start_stop(hpguppi_defaults.redis_obj, target_set_chan, obsstart, obsstop, source_name, dry_run)
    
        if log and not reset and not dry_run:
            _log_recording(
                t_in_x,
                obs_duration_s,
                obsstart,
                npackets,
                target_set_chan,
                log_string_per_channel[target_i:]
            )

    return target_sync_times.keys()
