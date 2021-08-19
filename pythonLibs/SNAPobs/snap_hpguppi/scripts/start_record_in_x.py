#!/home/sonata/miniconda3/bin/python
import argparse
import redis
from SNAPobs.snap_hpguppi import record_in as hpguppi_record_in
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary
from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults

parser = argparse.ArgumentParser(description='start observation '
        'in x seconds')
parser.add_argument('-n', type=float, default=hpguppi_record_in.DEFAULT_OBS_TIME,
        help='Total obs time [%.1f]' %hpguppi_record_in.DEFAULT_OBS_TIME)
parser.add_argument('-i', type=int, default=hpguppi_record_in.DEFAULT_START_IN,
        help='Seconds from now to start obs [%i]' %hpguppi_record_in.DEFAULT_START_IN)
parser.add_argument('-r', action='store_true',
        help='Reset OBSSTART and OBSSTOP to 0')
parser.add_argument('-d', action='store_true',
        help='dry run (don\'t publish)')
parser.add_argument('-b', '--broadcast', action='store_true',
        help='Broadcast on hpguppi:///set instead of targetting the hpguppi hosts specified by hpguppi-[hostname-pattern, host-ids, instances] arguments')
parser.add_argument('-P', '--hpguppi-hostname-pattern', nargs=2, type=str, default=['seti-node', ''],
        help='the prefix and suffix for the hostnames of the hpguppi machines')
parser.add_argument('-H', '--hpguppi-host-ids', nargs='+', type=str, default=['1-3'],
        help='the range of host ids, comma delimited, for the hpguppi machines')
parser.add_argument('-I', '--hpguppi-instances', nargs='+', type=str, default=['0-1'],
        help='the range of instance ids, comma delimited, for the hpguppi machines')
parser.add_argument('-S', action='store_true',
        help='Use redishost\'s SYNCTIME value (instead of the values from the antenna-stream boards themselvs).')
args = parser.parse_args()

hpguppi_redis_set_channels = None
log_string_per_channel = None
if not args.broadcast:
        def process_range_strings(range_strings):
                ret = []
                for range_str in range_strings:
                        if '-' in range_str:
                                range_bounds = range_str.split('-')
                                for id_ in range(int(range_bounds[0]), int(range_bounds[1])+1):
                                        ret.append(str(id_))
                        else:
                                ret.append(range_str)
                return ret


        hpguppi_hostname_ids = process_range_strings(args.hpguppi_host_ids)
        hpguppi_instance_ids = process_range_strings(args.hpguppi_instances)
        hpguppi_hostnames = [hostid.join(args.hpguppi_hostname_pattern) for hostid in hpguppi_hostname_ids]

        hpguppi_redis_set_channels = hpguppi_auxillary.generate_hpguppi_redis_set_channels(hpguppi_hostnames, hpguppi_instance_ids)
        hpguppi_redis_get_channels = hpguppi_auxillary.generate_hpguppi_redis_get_channels(hpguppi_hostnames, hpguppi_instance_ids)

        r = redis.Redis(host=hpguppi_defaults.REDISHOST)
        print(hpguppi_redis_get_channels)
        try:
                log_string_per_channel = hpguppi_auxillary.generate_freq_auto_string_per_channel(r, hpguppi_redis_get_channels)
        except:
                pass

hpguppi_record_in.record_in(
    obs_delay_s=args.i,
    obs_duration_s=args.n,
    hpguppi_redis_set_channels=hpguppi_redis_set_channels,
    force_synctime=args.S,
    reset=args.r,
    dry_run=args.d,
    log=True,
    log_string_per_channel=log_string_per_channel
    )
