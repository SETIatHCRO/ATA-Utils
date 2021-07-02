#!/home/sonata/miniconda3/bin/python
from SNAPobs.snap_hpguppi import populate_meta as hpguppi_populate_meta
import socket
import time
from datetime import datetime, timezone
from string import Template

from ata_snap import ata_snap_fengine
import struct
import casperfpga
from SNAPobs import snap_control
from ATATools import ata_control

from numpy import unique, sum

from SNAPobs import snap_defaults, snap_config

from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary

# Collate the snap hostnames
streams_to_marshall = [i.snap_hostname for i in snap_config.get_ata_snap_tab().itertuples()]

# Gather antenna-configuration for the listed snaps
stream_ant_name_dict = hpguppi_auxillary.get_antenna_name_dict_for_stream_hostnames(streams_to_marshall)
antenna_names = [ant_name for stream_name, ant_name in stream_ant_name_dict.items()]

def eth_get_dest_port(feng, interfaces='all'):
  '''
  Retrieves the destination port(s) for the interface list of the FEngine object.

  Parameters
  ----------
  feng: ata_snap_fengine
    Will collect destination ports for this FEngine
  interfaces: List[int] or 'all'
    Will collect destination ports for this FEngine

  Returns
  -------
  [port 0:feng.n_interfaces]
  '''
  PORT_MASK = (0xffff << 2)
  if interfaces == 'all':
      interfaces = range(feng.n_interfaces)
  elif type(interfaces) != list:
      interfaces = [int(interfaces)]
  try:
    return [
        (feng.fpga.read_uint('eth%d_ctrl'%interface) & PORT_MASK) >> 2
          for interface in interfaces
      ]
  except:
    return []

def eth_get_output_enabled(feng, interfaces='all'):
  ENABLE_MASK =  0x00000002
  if interfaces == 'all':
    interfaces = range(feng.n_interfaces)
  elif type(interfaces) != list:
    interfaces = [int(interfaces)]
  return [
    (feng.fpga.read_uint("eth%d_ctrl" % i) & ENABLE_MASK) != 0
    for i in interfaces
  ]

def packet_header_dict_from_Q(Q):
  header = {}
  header['feng_id'] = (Q >> 0) & 0xffff
  header['chans'] = (Q >> 16) & 0xffff
  header['n_chans'] = (Q >> 32) & 0xffff
  header['is_time_fastest'] = bool(Q >> 48)
  header['is_8_bit'] = bool(Q >> 49)
  header['first'] = bool(Q >> 56)
  header['valid'] = bool(Q >> 57)
  header['last'] = bool(Q >> 58)
  return header

def read_feng_chan_dest_ips(feng, ignore_null_packets=True):
  per_interface = [read_chan_dest_ips(feng, interface, ignore_null_packets=ignore_null_packets)
        for interface in range(feng.n_interfaces)]
  ret = per_interface[0]
  for interface in range(1, feng.n_interfaces):
    ret.extend(per_interface[interface])
  return ret

def calc_n_words(feng):
  return feng.n_chans_f * feng.n_times_per_packet * feng.n_pols // ata_snap_fengine.TGE_N_SAMPLES_PER_WORD // feng.packetizer_granularity

def get_packet_ips(feng, interface, n_words):
  ips_raw = feng.fpga.read('packetizer%d_ips' % interface, 4*n_words)
  return struct.unpack('>%dI' % n_words, ips_raw)

def get_packet_headers(feng, interface, n_words):
  hs_raw = feng.fpga.read('packetizer%d_header' % interface, 8*n_words)
  return struct.unpack('>%dQ' % n_words, hs_raw)

def get_feng_id(feng):
  hs = get_packet_headers(feng, 0, 1)
  return packet_header_dict_from_Q(hs[0])['feng_id']

def read_chan_dest_ips(feng, interface, ignore_null_packets=True):
  '''
  Processes the packet-details of an interface in the FEngines object,
  returning the destination IP addresses of the FEngine's channels.
  The output is collapsed on matching destination IP addresses, resulting
  in a list of IP addresses per range of channels.

  Parameters
  ----------
  feng: ata_snap_fengine
    The FEngine in questions
  interface: int
    The interface enumeration of the FEngine in questions

  Returns
  -------
  [{dest: ip_str, start: int, end: int, header: dict} ... ]
  '''
  interfacesEnabled = [False]
  try:
    interfacesEnabled = eth_get_output_enabled(feng, interface)
  except casperfpga.transport_katcp.KatcpRequestFail:
    return []
  
  if not interfacesEnabled[0]:
    return []

  n_words = calc_n_words(feng)

  ips = get_packet_ips(feng, interface, n_words)
  hs = get_packet_headers(feng, interface, n_words)

  times_per_word = None # 64 // (2*2*n_bits)
  packetizer_chan_granularity = None # feng.packetizer_granularity // times_per_word    

  packet_dest_ips = []
  if (not ignore_null_packets) or (ips[0] != 0):
    header = packet_header_dict_from_Q(hs[0])

    times_per_word = 64 // (2*2* (8 if header['is_8_bit'] else 4 ))
    packetizer_chan_granularity = feng.packetizer_granularity // times_per_word    

    packet_dest_ips = [{'dest':ips[0], 'start_chan':header['chans'], 'end_chan':header['chans']+packetizer_chan_granularity, 'packet_nchan':header['n_chans']}] 

  for idx,ip in enumerate(ips[1:]):
    if (not ignore_null_packets) or (ip != 0):
      header = packet_header_dict_from_Q(hs[idx])
      if times_per_word is None:
        times_per_word = 64 // (2*2* (8 if header['is_8_bit'] else 4 ))
        packetizer_chan_granularity = feng.packetizer_granularity // times_per_word    
      if header['valid']:
        if len(packet_dest_ips) > 0 and packet_dest_ips[-1]['dest'] == ip:
          if header['chans'] >= packet_dest_ips[-1]['start_chan']:
            end_chan = header['chans'] + packetizer_chan_granularity 
            if packet_dest_ips[-1]['end_chan'] < end_chan:
              packet_dest_ips[-1]['end_chan'] = end_chan
        else:
          packet_dest_ips.append({'dest':ip, 'start_chan':header['chans'], 'end_chan':header['chans']+packetizer_chan_granularity, 'packet_nchan':header['n_chans']})

  for packet_dest_ip in packet_dest_ips:
    packet_dest_ip['end_chan'] += packet_dest_ip['packet_nchan']

    packet_dest_ip['dest'] = ata_snap_fengine._int_to_ip(packet_dest_ip['dest'])
    packet_dest_ip['n_chans'] = packet_dest_ip['end_chan'] - packet_dest_ip['start_chan']
    packet_dest_ip['n_strm'] = packet_dest_ip['n_chans'] // packet_dest_ip['packet_nchan']

  return packet_dest_ips

def prune_null_dest_ips_and_headers(packet_details):
  return [detail for detail in packet_details if detail['dest'] != '0.0.0.0']

def list_el_approx_equal(list_a, list_b, eps=0.01):
  if len(list_a) == len(list_b):
    if len(list_a) == 0:
      return True
    else:
      return all([abs(list_a[i] - list_b[i]) < eps for i in range(len(list_a))])
  else:
    return False

def collect_values_from_dict(dictionary, keys):
  return [dictionary[key] for key in keys]

# Create the AtaSnapFengine list from the names
fengs = snap_control.init_snaps(streams_to_marshall, get_system_information=False)
hostname_feng_dict = {feng.host:feng for feng in fengs}

# print([eth_get_dest_port(feng) for feng in fengs])
# exit(0)

last_groups = []
last_destinations = []
last_skyfreq_mapping, _ = hpguppi_populate_meta._get_stream_mapping(streams_to_marshall)
last_skyfreq_mapping = collect_values_from_dict(last_skyfreq_mapping, streams_to_marshall)
antname_nolo_list = list(set([ant[:2] for ant in antenna_names]))
last_az_el = ata_control.get_az_el(antname_nolo_list)
last_eph_source = ata_control.get_eph_source(antname_nolo_list)

exceptions_caught = 0
exception_limit = 5

have_published = False
different_conf = True
last_published = 0
while(True):
  # Collect the destination
  feng_interface_dest_details = {feng.host:
    [read_chan_dest_ips(feng, interface, ignore_null_packets=True)
      for interface in range(feng.n_interfaces)
    ] for feng in fengs
  }

  groups = []
  destinations = []
  skyfreq_mapping, _ = hpguppi_populate_meta._get_stream_mapping(streams_to_marshall)
  skyfreq_mapping = collect_values_from_dict(skyfreq_mapping, streams_to_marshall)
  az_el = ata_control.get_az_el(antname_nolo_list)
  eph_source = ata_control.get_eph_source(antname_nolo_list)

  for streamname, dest_details in feng_interface_dest_details.items():
    if dest_details not in destinations:
      destinations.append(dest_details)
      groups.append([streamname])
    else:
      groups[destinations.index(dest_details)].append(streamname)

  same = [
    groups == last_groups,
    destinations == last_destinations,
    list_el_approx_equal(skyfreq_mapping, last_skyfreq_mapping),
    # all([list_el_approx_equal(az_el[ant_name], last_az_el[ant_name]) for ant_name in antname_nolo_list]),
    all([eph_source[ant_name] == last_eph_source[ant_name] for ant_name in antname_nolo_list])
  ]
  if all(same) and (not have_published or (time.time() - last_published > 10)) : # Seems stable, but haven't published
    new_publication = not have_published
    have_published = True

    if new_publication:
      print('### Start of updates ###')
      print(datetime.now(timezone.utc))
      
    for i in range(len(groups)):
      try:
        if new_publication:
          print(groups[i])
          print(destinations[i])

        interface_details = [details for details in destinations[i] if len(details) != 0]
        n_interfaces = len(interface_details)
        if n_interfaces == 0:
          if new_publication:
            print('No active interfaces detected\n')
          continue
        
        start_chan = None
        n_chan = 0 # not ideal, collects the largest number of channels sent per destination
        destIps = []
        max_nchan_per_packet = 0
        
        for interface in destinations[i]:
          for dest_details in interface:
            start_chan = min(dest_details['start_chan'], start_chan) if start_chan is not None else dest_details['start_chan']
            n_chan = max(dest_details['n_chans'], n_chan)
            destIps.append(dest_details['dest'])
            max_nchan_per_packet = max(dest_details['packet_nchan'], max_nchan_per_packet)
        
        destIps = unique(destIps)
        n_chan = n_chan*len(destIps) # assume each destination receives the same number of channels

        feng_id_hostname_dict = {get_feng_id(hostname_feng_dict[hostname]):hostname for hostname in groups[i]}
        feng_ids = sorted(feng_id_hostname_dict)
        stream_hostnames = [feng_id_hostname_dict[feng_id] for feng_id in feng_ids]

        if new_publication:
          print('start_chan', start_chan)
          print('n_chan', n_chan)
          print('destIps', destIps)

          meta_args = '-s {} -a {} -C {} -c {} -d {} --silent'.format(
            ' '.join(stream_hostnames), 
            ' '.join([stream_ant_name_dict[stream] for stream in stream_hostnames]),
            start_chan,
            n_chan,
            ' '.join(destIps),
            max_nchan_per_packet
          )
          print('meta_args:', meta_args)
        
        hpguppi_populate_meta.populate_meta(
                  stream_hostnames,
                  [stream_ant_name_dict[stream] for stream in stream_hostnames], 
                  None,
                  n_chans=n_chan,
                  start_chan=start_chan,
                  dests=destIps,
                  silent=not new_publication,
                  zero_obs_startstop=False,
                  dry_run=False,
                  max_packet_nchan=max_nchan_per_packet,
                  default_dir=different_conf)
        
        if new_publication:
          print()
        exceptions_caught = 0
      except:
        exceptions_caught += 1
        if exceptions_caught > exception_limit:
          print('Too many exceptions (%d)'%exception_limit)
          exit(1)

        print('Unexpected data, anticipating that reconfiguration is in progress')
        time.sleep(5)
        break

    if new_publication:
      print(datetime.now(timezone.utc))
      print('#### End of updates ####')
    else:
      print('#### Repeated previous update', datetime.now(timezone.utc), ' ####')

    last_published = time.time()
  elif not all (same):
    have_published = False
    different_conf = not (same[0] or same[1])
  else: # groups and destinations are stable and have published
    different_conf = False

  time.sleep(0.5)

  last_groups = groups
  last_destinations = destinations
  last_skyfreq_mapping = skyfreq_mapping
  last_az_el = az_el
  last_eph_source = eph_source

exit(0)

# import numpy as np
# import argparse
# import redis
# import time
# from SNAPobs import snap_defaults
# import casperfpga
# import sys
# from SNAPobs import snap_dada
# from math import isclose
# from ATATools import ata_control, logger_defaults

# # print(ata_control.get_az_el(ant_name_list))
# # print(snap_dada.get_freq_auto(ant_name_list))

# antenna_info = snap_dada.get_obs_params(ant_name_list, None)
# print(antenna_info.keys())

# def discern_antenna_groups(antenna_info_dicts):
# 	groups = []
# 	discerning_keys = [
# 		'RFFREQ',
# 		'SOURCE',
# 		'AZ',
# 		'EL'
# 	]
# 	for ant_name in antenna_info_dicts:
# 		antenna_info_dict = antenna_info_dicts[ant_name]
# 		print(antenna_info_dict)
# 		ant_params = {key:antenna_info_dict[key] for key in discerning_keys}
# 		groupid = -1
# 		for i in range(len(groups)):
# 			group = groups[i]
# 			group_match = True
# 			for key in discerning_keys:
# 				if type(group[key]) == float:
# 					group_match = isclose(group[key], ant_params[key], abs_tol=0.01)
# 				else:
# 					group_match = group[key] == ant_params[key]
# 				if not group_match:
# 					break
# 			if group_match:
# 				groupid = i
# 				break
    
# 		if groupid == -1:
# 			groups.append(ant_params)
  
# 	return groups

# grouped_antenna_info = discern_antenna_groups(antenna_info)
# print(grouped_antenna_info)
# print(len(grouped_antenna_info))