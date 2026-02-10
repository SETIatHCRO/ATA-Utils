#!/home/sonata/miniconda3/bin/python
import re
import argparse
from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults

regex_hostname_range = r'(.*?)\[([\d\-,]+)\](.*)'

def process_range_string(range_string):
    ret = []
    if '-' in range_string:
        range_bounds = range_string.split('-')
        for id_ in range(int(range_bounds[0]), int(range_bounds[1])+1):
            ret.append(str(id_))
    else:
        ret = range_string.split(',')
    return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get key-values from a Hashpipe instance.')
    parser.add_argument('-t', '--hashpipe-targets', nargs='+', type=str, default=[],
        help='hashpipe targets formed as `hostname:[inst...]`, comma-delimited listed pairs, for the observation.'+
        '\nhostname can contain a `[\d,-]` specified range.'
    )

    parser.add_argument('-p', '--post-proc', action='store_true',
        help='get from the postprocpype redis-hashes, for the Post-Processing Pypelines')

    parser.add_argument('-k', '--keys', type=str, nargs='*', default=[],
        help='Specify keys. Only these will be read.')
    args = parser.parse_args()

    hpguppi_redis_get_channels = {}
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

        hpguppi_redis_get_channels.update({
            f"{hostname}.{instid}": (
                hpguppi_defaults.REDISGETGW
                if not args.post_proc
                else hpguppi_defaults.REDISPOSTPROCHASH
            ).substitute(
                host=hostname,
                inst=instid
            )
            for hostname in hostnames
            for instid in instances
        })

    keyval_dict = {}
    for inst_str, inst_gw in hpguppi_redis_get_channels.items():
        keyvals = {
            args.keys[i]: v.decode() if v is not None else v
            for i, v in enumerate(
                hpguppi_defaults.redis_obj.hmget(
                    inst_gw,
                    args.keys
                )
            )
        }
        print(f"{inst_str}:\t{keyvals}")
