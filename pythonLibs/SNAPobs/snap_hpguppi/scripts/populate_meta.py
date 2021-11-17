#!/home/sonata/miniconda3/bin/python
import argparse
from SNAPobs.snap_hpguppi import populate_meta as hpguppi_populate_meta
from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults

parser = argparse.ArgumentParser(description='Program to populate'
				'meta data in redis database on compute nodes')
parser.add_argument('-s', dest='snaphosts', nargs='+', type=str,
				help='fpga host names')
parser.add_argument('-a', dest='antnames', nargs='+', type=str,
				help='antenna names')
parser.add_argument('-i', dest='ignore_control',
				help='ignore the sky frequency from the antennas',
				action='store_true')
parser.add_argument('-H', dest='hpguppi_daq_instance',
				help='specify the instance enumeration of the hpguppi_daq whose meta is being populated',
				default=-1, type=int)
parser.add_argument('-c', dest='n_chans',
				help='the number of channels being transmitted by the snaps',
				type=int)
parser.add_argument('-C', dest='start_chan',
				help='the lowest channel being transmitted by the snaps',
				type=int)
parser.add_argument('-P', dest='pkt_nchan_max',
				help='the maximum number of channels per packet sent by the snaps [{}]'.format(hpguppi_defaults.MAX_CHANS_PER_PKT),
				type=int, default=hpguppi_defaults.MAX_CHANS_PER_PKT)
parser.add_argument('-d', dest='dests', nargs='+', type=str,
				help='the destinations of the snaps')
parser.add_argument('configfile', type=str, nargs='?', default='',
				help='Config file used to program snaps')
parser.add_argument('-r', dest='dry_run', action='store_true',
				help='Dry run (do not publish)')
parser.add_argument('--silent', action='store_true',
				help='No printout')

args = parser.parse_args()

hpguppi_populate_meta.populate_meta(
									args.snaphosts,
									args.antnames, 
									args.configfile,
									ignore_control=args.ignore_control,
									hpguppi_daq_instance=args.hpguppi_daq_instance,
									n_chans=args.n_chans,
									start_chan=args.start_chan,
									dests=args.dests,
									silent=args.silent,
									max_packet_nchan=args.pkt_nchan_max,
									# zero_obs_startstop=
									dry_run=args.dry_run
									# default_dir=
)