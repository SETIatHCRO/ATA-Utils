#!/home/sonata/miniconda3/bin/python
import argparse
import socket
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary
from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults

def publish_keyval_dict_to_redis(keyval_dict, redis_targets, dry_run=False):
    print(keyval_dict)
    redis_publish_command = hpguppi_auxillary.redis_publish_command_from_dict(keyval_dict)
    redis_pubsub_channels = [chan.decode() for chan in hpguppi_defaults.redis_obj.pubsub_channels()]
    if dry_run:
        print('*** Dry Run ***')
    else:
        print('Publishing to:')
        for rtarget in redis_targets:
            if rtarget in redis_pubsub_channels:
                print('\t', rtarget)
                hpguppi_defaults.redis_obj.publish(rtarget, redis_publish_command)
            else:
                print('\t# ', rtarget)
                hpguppi_defaults.redis_obj.hset(rtarget, mapping=keyval_dict)

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

    publish_keyval_dict_to_redis(keyval_dict, channels, dry_run=args.dry_run)
