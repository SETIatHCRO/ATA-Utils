from numpy import ceil
import redis
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

DEFAULT_START_IN = 2
DEFAULT_OBS_TIME = 300.

r = redis.Redis(host=hpguppi_defaults.REDISHOST)

def _log_recording(start_time, npackets, end_time, redisset):
    logdir = '~'
    if os.path.exists('/home/sonata/logs'):
        logdir = '/home/sonata/logs'
		
    with open(os.path.join(logdir, 'record_in_log.csv'), 'a', newline='') as csvfile:
        csvwr = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwr.writerow([str(datetime.fromtimestamp(start_time)), str(npackets), str(datetime.fromtimestamp(end_time)), str(redisset)])

def _get_sync_time_for_snaps(snaps):
    fengs = snap_control.init_snaps(snaps)
    return [fengs[i].fpga.read_int('sync_sync_time') for i in range(len(snaps))]

def _stitch_pattern_for_sequence(pattern, sequence):
    return [seq.join(pattern.split(',')) for seq in sequence.split(',')]

def _get_snaps_of_instance(redis_obj, redis_chan):
    return _stitch_pattern_for_sequence(redis_obj.hget(redis_chan, "SNAPPAT").decode(), redis_obj.hget(redis_chan, "SNAPSEQ").decode())

def _block_until_key_has_value(hashes, key, value, verbose=True):
    len_per_value = 50//len(hashes)
    value_slice = slice(-len_per_value, None)
    while True:
        rr = [r.hget(hsh, key) for hsh in hashes]
        rets = [r.decode() if(r) else "NONE" for r in rr]
        if verbose:
            print_strings = [
                ('{: ^%d}'%len_per_value).format(r[value_slice]) for r in rets
            ]
            print('[{: ^66}]'.format(', '.join(print_strings)), end='\r')
        if all([t[0:len(value)]==value for t in rets]):
            if verbose:
                print()
            break
        time.sleep(1)

def block_until_hpguppi_idling(hashes, verbose=True):
    _block_until_key_has_value(hashes, "DAQSTATE", "idling", verbose=verbose)
        
def block_until_post_processing_waiting(hashes, verbose=True):
    _block_until_key_has_value(hashes, "PPSTATUS", "WAITING", verbose=verbose)

def record_in(
				obs_delay_s=DEFAULT_START_IN,
				obs_duration_s=DEFAULT_OBS_TIME,
				hpguppi_instance_ids=[-1],
				force_synctime=False,
				reset=False,
				dry_run=False,
				log=True
				):
    for instance in hpguppi_instance_ids:
        if instance > -1:
            print("Start recording on instance", instance)

            REDISSET = hpguppi_defaults.REDISSETGW.substitute(host=socket.gethostname(), inst=instance)
            if force_synctime:
                sync_time = int(r.get("SYNCTIME"))
                print("OBSSTART and OBSSTOP values based on redishost's SYNCTIME of", sync_time)
            else:
                REDISGET = hpguppi_defaults.REDISGETGW.substitute(host=socket.gethostname(), inst=instance)
                # print(REDISGET)
                # print(r.hget(REDISGET, "SNAPPAT"))
                # print(r.hget(REDISGET, "SNAPSEQ"))
                snaps = _get_snaps_of_instance(r, REDISGET)
                # print(snaps)
                sync_times = _get_sync_time_for_snaps(snaps)
                if len(set(sync_times)) == 1:
                    sync_time = sync_times[0]
                else:
                    print("Hashpipe instance", instance, "has the following snaps, with non-uniform sync-times:")
                    for i in range(len(snaps)):
                        print(snaps[i], sync_times[i])
                    print("Cannot reliably start a recording.")
                    exit(1)
        else:
            REDISSET  = 'hashpipe:///set'
            sync_time = int(r.get("SYNCTIME"))
            print("Will broadcast the OBSSTART and OBSSTOP values, based on redishost's SYNCTIME of", sync_time)

        if reset:
            obsstart = 0
            obsstop = 0
            # cmd = "OBSSTART=0\nOBSSTOP=0"
            t_in_2 = False
        else:
            t_now  = time.time()
            t_in_2 = int(ceil(t_now + obs_delay_s))

            tdiff = t_in_2 - sync_time

            obsstart = int(tdiff/hpguppi_defaults.TBIN)

            npckts_to_record = int(obs_duration_s/hpguppi_defaults.TBIN)
            obsstop = obsstart + npckts_to_record

        cmd = "OBSSTART=%i\nOBSSTOP=%i"  %(obsstart, obsstop)
        print(REDISSET, "\tOBSSTART: %i,\tOBSSTOP : %i\n" %(obsstart, obsstop))


        if not dry_run:
            r.publish(REDISSET, cmd)
            if log and not reset:
                _log_recording(
                    t_in_2,
                    npckts_to_record,
                    t_in_2+obs_duration_s,
                    REDISSET
                    )
        else:
            print('***DRY RUN***')
