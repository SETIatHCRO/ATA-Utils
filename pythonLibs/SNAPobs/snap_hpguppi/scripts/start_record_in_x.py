#!/home/sonata/miniconda3/bin/python
import argparse
import redis
import re
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
parser.add_argument('-d', '--dry-run', action='store_true',
        help='dry run (don\'t publish)')
parser.add_argument('-b', '--broadcast', action='store_true',
        help='Broadcast on hpguppi:///set instead of targetting the hpguppi hosts specified by hpguppi-[hostname-pattern, host-ids, instances] arguments')

parser.add_argument('-t', '--hashpipe-targets', nargs='+', type=str, default=[],
        help='hashpipe targets formed as `hostname:[inst...]`, comma-delimited listed pairs, for the observation.'+
        '\nhostname can contain a `[\d,-]` specified range.'
)
parser.add_argument('-H', '--hashpipe-host-ids', nargs='+', type=str, default=[],
        help='the range of host ids, comma delimited, for the hashpipe machines')
parser.add_argument('-I', '--hashpipe-instances', nargs='+', type=str, default=['0-1'],
        help='the range of instance ids, comma delimited, for the hashpipe machines')

parser.add_argument('-S', action='store_true',
        help='Use redishost\'s SYNCTIME value (instead of the values from the antenna-stream boards).')
parser.add_argument('--nbits', type=int, default=8,
        help='The number of bits per sample\'s complex-component, from which TBIN is determined.')
args = parser.parse_args()

regex_hostname_range = r'(.*?)\[([\d\-,]+)\](.*)'

hashpipe_targets = None
log_string_per_channel = None
if not args.broadcast:
        def process_range_string(range_string):
                ret = []
                if '-' in range_string:
                        range_bounds = range_string.split('-')
                        for id_ in range(int(range_bounds[0]), int(range_bounds[1])+1):
                                ret.append(str(id_))
                else:
                        ret = range_string.split(',')
                return ret

        hashpipe_targets = {}
        hpguppi_redis_get_channels = []
        if len(args.hashpipe_targets) > 0:
                for hostname_inst_pairstring in args.hashpipe_targets:
                        hostnames_str, inst_cs_str = hostname_inst_pairstring.split(':')
                        instances = process_range_string(inst_cs_str)

                        hostnames = [hostnames_str] 

                        hostname_range_match = re.match(regex_hostname_range, hostnames_str)
                        if hostname_range_match is not None:
                                hostname_pattern = [
                                        hostname_range_match.group(1),
                                        hostname_range_match.group(3)
                                ]
                                hostname_range = process_range_string(hostname_range_match.group(2))
                                hostnames = [hostid.join(hostname_pattern) for hostid in hostname_range]
                        
                        for hostname in hostnames:
                                hashpipe_targets[hostname] = instances

                        hpguppi_redis_get_channels.extend(
                                hpguppi_auxillary.generate_hpguppi_redis_get_channels(
                                        hostnames, instances
                                )
                        )
        elif len(args.hashpipe_host_ids) > 0:
                instances = []
                for instance_str in args.hashpipe_instances:
                        instances.extend(process_range_string(instance_str))
                for hostnames_str in args.hashpipe_host_ids:
                        hostnames = [hostnames_str] 

                        hostname_range_match = re.match(regex_hostname_range, hostnames_str)
                        if hostname_range_match is not None:
                                hostname_pattern = [
                                        hostname_range_match.group(1),
                                        hostname_range_match.group(3)
                                ]
                                hostname_range = process_range_string(hostname_range_match.group(2))
                                hostnames = [hostid.join(hostname_pattern) for hostid in hostname_range]
                        
                        for hostname in hostnames:
                                hashpipe_targets[hostname] = instances

                        hpguppi_redis_get_channels.extend(
                                hpguppi_auxillary.generate_hpguppi_redis_get_channels(
                                        hostnames, instances
                                )
                        )


        print(hpguppi_redis_get_channels)
        try:
                log_string_per_channel = hpguppi_auxillary.generate_freq_auto_string_per_channel(
                                hpguppi_defaults.redis_obj, hpguppi_redis_get_channels
                )
        except:
                pass

hpguppi_record_in.record_in(
    obs_delay_s=args.i,
    obs_duration_s=args.n,
    hashpipe_targets=hashpipe_targets,
    universal_synctime=args.S,
    universal_tbin=hpguppi_defaults.fengine_meta_key_values(args.nbits)['TBIN'],
    universal_source_name="UNKNOWN",
    reset=args.r,
    dry_run=args.dry_run,
    log=True,
    log_string_per_channel=log_string_per_channel
    )
