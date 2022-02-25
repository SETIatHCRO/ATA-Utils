#!/home/sonata/miniconda3/bin/python
import argparse
import socket
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary
from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Set key-values for a Hashpipe instance.')
    parser.add_argument('-d', '--dry-run', action='store_true',
        help='dry run (don\'t publish)')
    parser.add_argument('-I', type=int, nargs='*', default=[-1],
        help='hashpipe instance id to target [-1: for broadcast]')
    parser.add_argument('-H', type=str, nargs='*', default=[socket.gethostname()],
        help='hashpipe instance hostname to target [$hostname]')

    parser.add_argument('-p', '--post-proc', action='store_true',
        help='publish to postprocpype redis-hashes, for the Post-Processing Pypelines')

    parser.add_argument('key_values', type=str, nargs='*', default=[],
        help='Specify key=value strings. Only these will be published')
    args = parser.parse_args()

    channels =[]

    if -1 in args.I:
        print('Broadcasting the key-values')
        if not args.post_proc:
            channels.append(hpguppi_defaults.REDISSET)
        else:
            channels.append(hpguppi_defaults.REDISPOSTPROCSET)
    else:
        redis_chan_template = hpguppi_defaults.REDISSETGW if not args.post_proc else hpguppi_defaults.REDISPOSTPROCHASH

        for hostname in args.H:
            for instance in args.I:
                channels.append(redis_chan_template.substitute(host=hostname, inst=instance))
    
    keyval_dict = {}
    for key_value_str in args.key_values:
        key_value = key_value_str.split('=')
        keyval_dict[key_value[0]] = key_value[1]

    hpguppi_auxillary.publish_keyval_dict_to_redis(keyval_dict, channels, dry_run=args.dry_run)
