#!/home/sonata/miniconda3/bin/python
"""
Script to sync snap hosts
"""
from SNAPobs import snap_control, snap_config
from ata_snap import ata_snap_fengine
import redis
import argparse
import sys
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary
import re

def sync(stream_list=None, all_snaps=False, check_sync_all=True):
    if all_snaps:
        ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
        stream_list = [snap for snap in ATA_SNAP_TAB.snap_hostname]
        if check_sync_all:
            print(*stream_list, sep='\n')
            response = input('Are you sure you want to sync all the snaps (above) (Y/n): ')
            if len(response) > 0 and response[0] in ['n', 'N']:
                print('Aborting...')
                return


    if stream_list is not None and len(stream_list) > 0:
        print("Syncing: ")
        print(stream_list)

        fengs = snap_control.init_snaps(stream_list)
        host_unique_fengs = {}
        for feng in fengs:
            host_name = feng.host
            if host_name.startswith('rfsoc'):
                host_name = re.match(r'(rfsoc\d+.*)-\d+$', host_name).group(1)
            if host_name not in host_unique_fengs:
                host_unique_fengs[host_name] = feng
            
        if len(host_unique_fengs) < len(fengs):
            fengs = [feng for feng in host_unique_fengs.values()]
            print('Simplified F-Engines to unique hosts:', [feng.host for feng in fengs])
        
        sync_time = snap_control.arm_snaps(fengs)
        print("Synctime is: %i" %sync_time)

        print("Writing sync time to redis database")
        r = redis.Redis(host='redishost')
        r.set('SYNCTIME', sync_time)
        print(r.get('SYNCTIME'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Syncs antenna streams')
    parser.add_argument('stream_list', nargs='*', type=str,
                        help='The list of antenna streams to sync')
    parser.add_argument('--all', action='store_true',
                        help='Sync every snap (listed in ATA_SNAP_TAB) before configuring...')
    args = parser.parse_args()
    if args.stream_list is not None and len(args.stream_list) > 0:
        sync(hpguppi_auxillary.get_stream_hostname_per_antenna_names(args.stream_list))
    elif args.all:
        sync(None, args.all, True)
    else:
        print('Provide a antenna streams to sync or use \'--all\'')
        exit(1)
