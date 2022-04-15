#!/home/sonata/miniconda3/bin/python
import argparse
from SNAPobs.snap_hpguppi import populate_meta as hpguppi_populate_meta
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary
from SNAPobs.snap_hpguppi import record_in as hpguppi_record_in
from SNAPobs.snap_hpguppi import populate_meta as hpguppi_populate_meta
from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults
import itertools
from SNAPobs import snap_config, snap_control
from string import Template
from ata_snap import ata_snap_fengine
import casperfpga
import redis
import socket
import re
import yaml

import sync_streams

import os, sys

def sort_rfsoc_config(rfsoc_config):
	pipeline_ids = rfsoc_config['pipeline_ids'].copy()
	pipeline_ids.sort()
	original_indices = [rfsoc_config['pipeline_ids'].index(pipeline_id) for pipeline_id in pipeline_ids]
	
	rfsoc_config_sorted = rfsoc_config.copy()
	rfsoc_config_sorted['pipeline_ids'] = pipeline_ids
	rfsoc_config_sorted['feng_ids'] = [rfsoc_config['feng_ids'][index] for index in original_indices]
	if rfsoc_config['dests'] is not None:
		rfsoc_config_sorted['dests'] = [rfsoc_config['dests'][index] for index in original_indices]
	return rfsoc_config_sorted
	

# sys.path.insert(0, '/home/sonata/miniconda3/bin/')
sys.path.insert(0, '/home/sonata/dev/ata_snap/sw/ata_snap/scripts/')
import snap_feng_init
import rfsoc_feng_init
# sys.path.insert(0, '/home/sonata/dev/ata_snap/sw/ata_snap/src/')


default_cfg_dir="/home/sonata/src/observing_campaign/config_files/"
default_cfg_stem="ataconfig_setinode_sub"
default_stream_subs=[
	'1aA,1fA,1cA',	# snaps 1,2,10
	'2aA,4jA,2hA',	# snaps 3,4,5 
	'1kA,5cA,1hA'		# snaps 6,9,11
]

############ Hands off from here on
parser = argparse.ArgumentParser(description='Configures snaps'
				' as per the internal code.')
parser.add_argument('-s', '--stop-all-eth-first', action='store_true',
										help='Stop the ethernet output of every snap (listed in ATA_SNAP_TAB) before configuring')
parser.add_argument('-p', '--prog-snaps', action='store_true',
										help='Program the snaps being configured')
parser.add_argument('-S', '--sync-only', action='store_true',
										help='Skip configuring the snaps (will still sync them)')
parser.add_argument('-g', '--groupings', nargs='+', type=str,
										help='The sub-grouping of DSP source streams as comma (,) separated lists ["{}"]'.format('", "'.join(default_stream_subs)),
										default=default_stream_subs)
parser.add_argument('-G', '--hostname-groupings', nargs='*', type=str,
										help='The sub-grouping of DSP source stream hostnames as comma (,) separated lists [] (hostnames can be regex, overrules groupings)',
										default=[])
parser.add_argument('-d', '--config-directory', type=str,
										help='The root directory of the sub-grouping configuration yaml files ["{}"]'.format(default_cfg_dir),
										default=default_cfg_dir)
parser.add_argument('-c', '--config-stem', type=str,
										help='The stem of the sub-grouping configuration yaml files (1 indexed) ["{}"]'.format(default_cfg_stem),
										default=default_cfg_stem)
parser.add_argument('-C', '--group-config-stem', type=str,
										help='The stem of the collective configuration yaml file (1 for all groups) [{}]'.format(None),
										default=None)
parser.add_argument('-t', '--test-vector-enable', action='store_true',
										help='Configure the antenna streams to send test vectors [False]',
										default=False)
parser.add_argument('--no-blank', action='store_true',
										help='Do not blank out un-configured pipelines',
										default=False)
parser.add_argument('--dry-run', action='store_true',
										help='Don\'t actually configure anything.')
parser.add_argument('--redishost', type=str, default='redishost',
										help='The redishost\'s name [\'redishost\'].')
args = parser.parse_args()

redis_obj = redis.Redis(args.redishost)

if len(args.hostname_groupings) > 0:
	ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
	args.groupings = []
	for hostname_grouping in args.hostname_groupings:
		antenna_group = []
		for hostname_criterion in hostname_grouping.split(','):
			hostname_pattern = re.compile(hostname_criterion)
			antenna_group += [row['antlo'] for idx,row in ATA_SNAP_TAB.iterrows() if hostname_pattern.match(row['snap_hostname'])]
		args.groupings.append(','.join(antenna_group))


stream_cfgs = []
stream_subs = []
for stream_id, stream_str in enumerate(args.groupings):
	stream_subs.append(stream_str.split(','))
	stream_cfg = os.path.join(args.config_directory, '{}.yml'.format(args.group_config_stem))
	if args.group_config_stem is None:
		stream_cfg = os.path.join(args.config_directory, '{}{}.yml'.format(args.config_stem, stream_id+1))
		if not os.path.exists(stream_cfg):
			stream_cfg = os.path.join(args.config_directory, '{}.yml'.format(args.config_stem))
	
	assert os.path.exists(stream_cfg), '{} path doesn\'t exist'.format(stream_cfg)
	stream_cfgs.append(stream_cfg)

	print('Sub-array #{}: {}\t configured with {}'.format(stream_id, stream_subs[-1], stream_cfgs[-1]))

stream_antlo_names = list(itertools.chain(*stream_subs)) # should be a list of antlo
stream_hostnames = hpguppi_auxillary.get_stream_hostname_per_antenna_names(stream_antlo_names)
stream_antlo_hostname_dict = hpguppi_auxillary.get_stream_hostname_dict_for_antenna_names(stream_antlo_names)

# Collect the redis channels of the hpguppi_daq instances that are
# being streamed to by the antennae to be configured, as well as the
# collation of the ANTNAMES in those redis channels
## This enables the record_in(reset=True) of those instances, as well
## as selective silencing of antennae, such that instances only receive
## packets from a whole configuration

# TODO load IPs of hpguppi_daq instances from the collective destination-IP list
ips = [
	'10.11.1.51',
	'10.11.1.61',
	'10.11.1.52',
	'10.11.1.62',
	'10.11.1.53',
	'10.11.1.63',
	'10.11.1.54',
	'10.11.1.64'
	]

antlo_names = []
hpguppi_redis_reset_chans = []

ifnames_ip_dict = {socket.gethostbyaddr(ip)[0]:ip for ip in ips}
for ip_ifname, ip in ifnames_ip_dict.items():
	# remove -40, -100g-1, -100g-2
	m = re.match(r'(.*)-(\d+g-)(\d+)', ip_ifname)
	host = ip_ifname
	instance = 0
	if m:
			host = m.group(1)
			instance = int(m.group(3)) - 1
	else:
			if not silent:
					print('%s: %s does not have -\d+g-\d+ suffix... taking it verbatim'%(ip, ip_ifname))

	hpguppi_instance_redis_setchan = hpguppi_defaults.REDISGETGW.substitute(host=host, inst=instance)
	antnames = None
	try:
		antnames = hpguppi_auxillary.get_stream_hostnames_of_redis_chan(hpguppi_defaults.redis_obj, hpguppi_instance_redis_setchan)
	except:# RuntimeError:
		print('hpguppi_auxillary.get_stream_hostnames_of_redis_chan failed on {}'.format(hpguppi_instance_redis_setchan))
	
	if antnames is not None:
		for ant_name in stream_antlo_names:
			if ant_name in antnames:
				hpguppi_redis_reset_chans.append(hpguppi_auxillary.redis_set_channel_from_get_channel(hpguppi_instance_redis_setchan))
				antlo_names.extend(antnames)
				break


if args.stop_all_eth_first:
	antstream_hostname_list_to_silence = hpguppi_auxillary.get_stream_hostname_per_antenna_names(antlo_names)
	print('antstream_hostname to silence', antstream_hostname_list_to_silence)
	if not args.dry_run:
		fengs = snap_control.init_snaps(antstream_hostname_list_to_silence)
		snap_control.stop_snaps(fengs)

if not args.dry_run:
	hpguppi_record_in.record_in(hashpipe_targets=hpguppi_redis_reset_chans, reset=True)
else:
	print('hpguppi_daq redis channels to reset:', hpguppi_redis_reset_chans)

if not args.sync_only:
	rfsoc_hostname_regex = r'(?P<boardname>.*)-(?P<pipeline>\d+)$'
	rfsoc_hostname_configurations_dict = {}

	multi_group_config = None
	if args.group_config_stem is not None:
		with open(stream_cfgs[0], 'r') as fh:
			multi_group_config = yaml.load(fh, Loader=yaml.SafeLoader)
			assert isinstance(multi_group_config['voltage_output']['dests'][0], list), 'The voltage_output dests is not a nested list, which is expected of multi-group configuration files.'

	for (sub_id, stream_sub) in enumerate(stream_subs):
		print('Configuring Subarray', sub_id)
		print('\t', stream_sub)

		for (feng_id, stream_antlo_name) in enumerate(stream_sub):
			stream_hostname = stream_antlo_hostname_dict[stream_antlo_name]

			if stream_hostname.startswith('frb-snap'):
				assert multi_group_config is None, 'SNAP configuration has not been expanded to support a single multi-group configuration file.'
				fpgfile = snap_config.get_ata_cfg()['SNAPFPG']
								
				print('{} Reprogramming/configuring snap as FEngine #{:02d} {}'.format('v'*5, feng_id, 'v'*5))
				print('snap_feng_init.py {} {} {} -i {} {}{}{}{}'.format(
					stream_hostname, fpgfile, stream_cfgs[sub_id],
					feng_id,
					'-s ',
					'--eth_volt ',
					'-t ' if args.test_vector_enable else '',
					'--skipprog' if not args.prog_snaps else ''
					)
				)
				if args.dry_run:
					print('*'*5, 'Dry Run', '*'*5)
				else:
					snap_feng_init.run(stream_hostname, fpgfile, stream_cfgs[sub_id],
						feng_id=feng_id,
						sync=True,
						eth_volt=True,
						tvg=args.test_vector_enable,
						skipprog=not args.prog_snaps
					)
				print('{} Reprogramming/configuring snap as FEngine #{:02d} {}\n'.format('^'*5, feng_id, '^'*5))
			
			elif stream_hostname.startswith('rfsoc'):
				fpgfile = snap_config.get_ata_cfg()['RFSOCFPG']
				# take stream_hostname up until last 
				rfsoc_hostname_re_match = re.match(rfsoc_hostname_regex, stream_hostname)
				rfsoc_boardname = rfsoc_hostname_re_match.group('boardname')
				rfsoc_pipeline = int(rfsoc_hostname_re_match.group('pipeline'))-1

				if rfsoc_boardname not in rfsoc_hostname_configurations_dict:
					rfsoc_hostname_configurations_dict[rfsoc_boardname] = {
						'fpga_file'		: fpgfile,
						'config_yml'	: stream_cfgs[sub_id],
						'feng_ids'		: [feng_id],
						'pipeline_ids': [rfsoc_pipeline],
						'dests'				: None,
						'sync'				: True,
						'eth_volt'		: True,
						'tvg'					: args.test_vector_enable,
						'noblank'			: args.no_blank,
						'skip_prog'		: not args.prog_snaps
					}
					if multi_group_config is not None:
						rfsoc_hostname_configurations_dict[rfsoc_boardname]['dests']	= [multi_group_config['voltage_output']['dests'][sub_id]]
							
				else:
					rfsoc_hostname_configurations_dict[rfsoc_boardname]['feng_ids'].append(feng_id)
					rfsoc_hostname_configurations_dict[rfsoc_boardname]['pipeline_ids'].append(rfsoc_pipeline)
					if multi_group_config is not None:
						rfsoc_hostname_configurations_dict[rfsoc_boardname]['dests'].append(multi_group_config['voltage_output']['dests'][sub_id])
				
				print('{} Batched reprogramming/configuring RFSoC {} as FEngine #{:02d} {}'.format('='*5, stream_hostname, feng_id, '='*5))		
			else:
				print('Cannot make out the kind of FEngine board with hostname \'{}\''.format(stream_hostname))
		print()
		
	
	# Batch program the rfsocs
	for rfsoc_boardname, rfsoc_config in rfsoc_hostname_configurations_dict.items():
		print('{} Batched reprogramming/configuring RFSoC {} {}'.format('v'*5, rfsoc_boardname, 'v'*5))	
		rfsoc_hostname = rfsoc_boardname + '-1'
		
		print(rfsoc_config)
		rfsoc_config = sort_rfsoc_config(rfsoc_config)
		print('rfsoc_feng_init.py {} {} {} -i {} -j {} {}{}{}{}{}'.format(
				rfsoc_hostname, rfsoc_config['fpga_file'], rfsoc_config['config_yml'],
				' '.join(map(str, rfsoc_config['feng_ids'])),
				' '.join(map(str, rfsoc_config['pipeline_ids'])),
				'-d {} '.format(' '.join([','.join(dests) for dests in rfsoc_config['dests']])) if rfsoc_config['dests'] else '',
				'-s ' if rfsoc_config['sync'] else '',
				'--eth_volt ' if rfsoc_config['eth_volt'] else '',
				'-t ' if rfsoc_config['tvg'] else '',
				'--noblank ' if rfsoc_config['noblank'] else '',
				'--skipprog' if rfsoc_config['skip_prog'] else ''
				)
			)
		
		if args.dry_run:
			print('*'*5, 'Dry Run', '*'*5)
		else:
			for i in range(3):
				try:
					rfsoc_feng_init.run(
						rfsoc_hostname, rfsoc_config['fpga_file'], rfsoc_config['config_yml'],
						feng_ids = rfsoc_config['feng_ids'],
						pipeline_ids = rfsoc_config['pipeline_ids'],
						dests = rfsoc_config['dests'],
						sync = rfsoc_config['sync'],
						eth_volt = rfsoc_config['eth_volt'],
						tvg = rfsoc_config['tvg'],
						noblank = rfsoc_config['noblank'],
						skipprog = rfsoc_config['skip_prog']
					)
					break
				except BaseException as e:
					if i == 2:
						raise e
					print('Retrying...')

		print('{} Batched reprogramming/configuring RFSoC {} {}\n'.format('^'*5, rfsoc_boardname, '^'*5))

if args.dry_run:
	print('sync_streams.sync({})'.format(stream_hostnames))
else:
	sync_streams.sync(stream_hostnames)

# print('\nPopulating REDIS meta data')
# for (sub_id, stream_sub) in enumerate(stream_subs):
# 	hpguppi_populate_meta.populate_meta(
# 										stream_sub,
# 										None, 
# 										stream_cfgs[sub_id])
