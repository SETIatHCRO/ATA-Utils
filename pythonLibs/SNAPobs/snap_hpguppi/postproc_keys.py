import redis
from string import Template
from . import snap_hpguppi_defaults as hpguppi_defaults

def set_keys(redis_set_channels, key_value_dict,
                dry_run=False, silent=False
                ):

    r = redis.Redis(host=hpguppi_defaults.REDISHOST)
    cmd = '\n'.join([key+'='+value for key, value in key_value_dict.items()])
    if not silent:
        print('Setting the following keys:\n\t', cmd.replace('\n', '\n\t').replace('=', '\t=\t'),'\nin channels:')
    for channel in redis_set_channels:
        if not silent:
            print('\t', channel)

        if not dry_run:
            r.publish(channel, cmd)
        else:
            if not silent:
                print('***Dry Run***')