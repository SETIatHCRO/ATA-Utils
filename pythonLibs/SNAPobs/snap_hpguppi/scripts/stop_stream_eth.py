#!/home/sonata/miniconda3/bin/python
"""
Script to stop the ethernet output of input snap hosts
"""
from SNAPobs import snap_control, snap_config
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary
import re
import time
import argparse
import sys

def collect_feng_obj(antlo_stream_list=None, all_streams=False, check_stop_all=True):
    if all_streams:
        ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
        antstream_hostname_list_to_silence = [stream for stream in ATA_SNAP_TAB.snap_hostname]
        if check_stop_all:
            print(*antstream_hostname_list_to_silence, sep='\n')
            response = input('Are you sure you want to control the ethernet of all the streams (above) (Y/n): ')
            if len(response) > 0 and response[0] in ['n', 'N']:
                print('Aborting...')
                return None
    elif antlo_stream_list is not None and len(antlo_stream_list) > 0:
        print(hpguppi_auxillary.get_stream_hostname_dict_for_antenna_names(antlo_stream_list))
        antstream_hostname_list_to_silence = hpguppi_auxillary.get_stream_hostname_per_antenna_names(antlo_stream_list)

    return snap_control.init_snaps(antstream_hostname_list_to_silence)

if __name__ == '__main__':    
    parser = argparse.ArgumentParser(description='Stops the ethernet output of snaps')
    parser.add_argument(dest='antlo_stream_list', nargs='*', default=None,
                        help='The list of Antenna-LO streams to stop')
    parser.add_argument('-S', '--enable-eth', action='store_true',
                        help='Enable the ethernet output instead of stopping it.')
    parser.add_argument('-H', '--hostnames', nargs='*', type=str,
                    help='The DSP source stream hostnames as comma (,) separated lists [] (hostnames can be regex, overrules groupings)',
                    default=[])
    parser.add_argument('--all', action='store_true',
                        help='Stop the ethernet output of every stream (listed in ATA_SNAP_TAB) before configuring...')
    args = parser.parse_args()

    if len(args.hostnames) > 0:
        ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
        args.antlo_stream_list = []
        for hostname in args.hostnames:
            for hostname_criterion in hostname.split(','):
                hostname_pattern = re.compile(hostname_criterion)
                args.antlo_stream_list += [row['antlo'] for idx,row in ATA_SNAP_TAB.iterrows() if hostname_pattern.match(row['snap_hostname'])]

    feng_objs = collect_feng_obj(args.antlo_stream_list, args.all, True)
    print('Affects the following F-Engine streams:\n', [feng.host for feng in feng_objs])

    if not args.enable_eth:
        print('Ethernet output disabled')
        snap_control.stop_snaps(feng_objs)
    else:
        print('Ethernet output enabled')
        snap_control.enable_ethernet_output(feng_objs)
