#!/home/sonata/miniconda3/bin/python
from SNAPobs.snap_hpguppi import populate_meta as hpguppi_populate_meta
import socket
import time
import traceback
from datetime import datetime, timezone
from string import Template

import ata_snap
from ata_snap import ata_snap_fengine, ata_rfsoc_fengine
import struct
import casperfpga
from SNAPobs import snap_control
from ATATools import ata_control

from SNAPobs import snap_defaults, snap_config

from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary

import tomli as tomllib # from python 3.11 tomllib is a standard package

# Collate the snap hostnames
def generate_stream_antnames_to_marshall():
  streams_to_marshall = [i.snap_hostname for i in snap_config.get_ata_snap_tab().itertuples() if i.snap_hostname.startswith('rfsoc')]

  # Gather antenna-configuration for the listed snaps
  stream_ant_name_dict = hpguppi_auxillary.get_antennalo_name_dict_for_stream_hostnames(streams_to_marshall)
  antenna_names = [ant_name for stream_name, ant_name in stream_ant_name_dict.items()]
  return streams_to_marshall, antenna_names

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
  return feng.n_chans_f * feng.n_times_per_packet * feng.n_pols // feng.tge_n_samples_per_word // feng.packetizer_granularity

def get_feng_id(feng):
  return feng._read_headers(n_words=1)[0]['feng_id']

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
    print('Failed to query ethernet status of {}[{}]'.format(feng.host, interface))
    return []
  
  if not interfacesEnabled[0]:
    # print('The ethernet output of {}[{}] is disabled'.format(feng.host, interface))
    return []

  try:
    if isinstance(feng, ata_rfsoc_fengine.AtaRfsocFengine):
      feng._read_parameters_from_fpga()
      feng._calc_output_ids()
      feng_headers = feng._read_headers()
    else:
      feng_headers = feng._read_headers(interface)
  except:
    print('Failed to query headers of {}[{}]'.format(feng.host, interface))
    return []

  test_vectors_enabled = feng.fpga.read_int('spec_tvg_tvg_en')
  
  packet_dest_ips = []
  for header in feng_headers:
    if header['valid'] and header['first']:
      ip = header['dest']
      
      if len(packet_dest_ips) > 0 and packet_dest_ips[-1]['dest'] == ip:
        packet_dest_ips[-1]['end_chan'] = header['chans']
      else:
        packet_dest_ips.append({'dest':ip, 'start_chan':header['chans'], 'end_chan':header['chans'], 'packet_nchan':header['n_chans'], 'is_8bit':header['is_8_bit']})

  for packet_dest_ip in packet_dest_ips:
    packet_dest_ip['end_chan'] += packet_dest_ip['packet_nchan']
    
    packet_dest_ip['n_chans'] = packet_dest_ip['end_chan'] - packet_dest_ip['start_chan']

    packet_dest_ip['n_strm'] = packet_dest_ip['n_chans'] / packet_dest_ip['packet_nchan']
    if packet_dest_ip['n_chans'] % packet_dest_ip['packet_nchan'] != 0:
      print('Read headers from {} that indicate non-integer number of streams, there is probably an issue in the collation procedure: {} / {} = {}'.format(feng.host, packet_dest_ip['n_chans'], packet_dest_ip['packet_nchan'], packet_dest_ip['n_strm']))
    packet_dest_ip['n_strm'] = int(0.5 + packet_dest_ip['n_strm'])
    
    packet_dest_ip['test_vectors'] = test_vectors_enabled

  # print('{}[{}]: {}\n'.format(feng.host, interface, packet_dest_ips))
  return packet_dest_ips

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

'''
  Iterate through the antname_nolo_list and catch the antnames that failed.
  Return the collection of successful results (a dict whose keys list the
  successful antnames), and the list of antnames that the function failed for.
'''
def ata_control_get_safe(antname_nolo_list, get_func):
  ret = {}
  failed_antname_nolo_list = []
  for antname_nolo in antname_nolo_list:
    try:
      ret.update(get_func([antname_nolo]))
    except:
      failed_antname_nolo_list.append(antname_nolo)
  return ret, failed_antname_nolo_list


### Begin

streams_to_marshall, antenna_names = generate_stream_antnames_to_marshall()
antname_nolo_list = list(set([ant[:2] for ant in antenna_names]))
# Create the AtaSnapFengine list from the names
fengs = snap_control.init_snaps(streams_to_marshall)#, load_system_information=False)
hostname_feng_dict = {feng.host:feng for feng in fengs}


last_groups = []
last_destinations = []
last_skyfreq_mapping, _ = hpguppi_populate_meta._get_stream_mapping(streams_to_marshall)
last_skyfreq_mapping = collect_values_from_dict(last_skyfreq_mapping, streams_to_marshall)

last_az_el, failed_antname_nolo_list = ata_control_get_safe(antname_nolo_list, ata_control.get_az_el)
safe_antname_nolo_list = list(last_az_el.keys())
last_eph_source = ata_control.get_eph_source(safe_antname_nolo_list)

last_reference_antenna_name = None

exceptions_caught = 0
exception_limit = 5

have_published = False
last_published = 0
section_strings = [
  'Grouping',  
  'Destinations', 
  'Frequency',
  'AzEl',
  'Source' 
]
sections_updated = [False for i in range(len(section_strings))]

while(True):
  # TODO: reconsult the ANT TAB file periodically. This requires a `reload_ata_tab` in snap_config...

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
  az_el, failed_antname_nolo_list = ata_control_get_safe(antname_nolo_list, ata_control.get_az_el)
  safe_antname_nolo_list = list(az_el.keys())
  eph_source = ata_control.get_eph_source(safe_antname_nolo_list)

  for streamname, dest_details in feng_interface_dest_details.items():
    if dest_details not in destinations:
      destinations.append(dest_details)
      groups.append([streamname])
    else:
      groups[destinations.index(dest_details)].append(streamname)

  reference_antenna_name = last_reference_antenna_name
  try:
    with open("/opt/mnt/share/telinfo_ata.toml", "rb") as f:
      toml_dict = tomllib.load(f)
      reference_antenna_name = toml_dict.get('reference_antenna_name', None)
  except BaseException as err:
    print(f"Exception reading telinfo_ata.toml: {err}")

  same = [
    groups == last_groups,
    destinations == last_destinations,
    list_el_approx_equal(skyfreq_mapping, last_skyfreq_mapping),
    # all([list_el_approx_equal(az_el[ant_name], last_az_el[ant_name]) for ant_name in safe_antname_nolo_list]),
    all([eph_source[ant_name] == last_eph_source[ant_name] for ant_name in safe_antname_nolo_list])
  ]
  if all(same) and (not have_published or (time.time() - last_published > 10)) : # Seems stable, but haven't published
    new_publication = not have_published and all(sections_updated[0:1])
    have_published = True
    updated_section_strings = []
    for section_idx, updated in enumerate(sections_updated):
      if updated:
        updated_section_strings.append(section_strings[section_idx])
      sections_updated[section_idx] = False
    print('Updated sections:', ', '.join(updated_section_strings))

    if new_publication:
      print('### Start of updates ###')
      print(datetime.now(timezone.utc))

    # build up LO independent additional meta-data
    lo_freqs = list(
        map(
            str,
            set(skyfreq_mapping)
        )
    )
    lo_freqs.sort()
    additional_metadata = {
      'LO_FREQS': '-'.join(lo_freqs)
    }
      
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
        stream_is_8bit = None
        
        for interface in destinations[i]:
          for dest_details in interface:
            start_chan = min(dest_details['start_chan'], start_chan) if start_chan is not None else dest_details['start_chan']
            n_chan = max(dest_details['n_chans'], n_chan)
            if dest_details['dest'] not in destIps:
              destIps.append(dest_details['dest'])
            max_nchan_per_packet = max(dest_details['packet_nchan'], max_nchan_per_packet)
            if stream_is_8bit is None:
              stream_is_8bit = dest_details['is_8bit']
            elif stream_is_8bit != dest_details['is_8bit']:
              print('Incosistent sample bit depth in streams detected!')

        n_chan = n_chan*len(destIps) # assume each destination receives the same number of channels

        feng_id_hostname_dict = {get_feng_id(hostname_feng_dict[hostname]):hostname for hostname in groups[i]}
        stream_hostnames = [feng_id_hostname_dict[feng_id] for feng_id in sorted(feng_id_hostname_dict.keys())]

        if new_publication:
          print('n_ant', len(stream_hostnames))
          print('start_chan', start_chan)
          print('n_chan', n_chan)
          print('destIps', destIps)

          meta_args = '-s {} -a {} -C {} -c {} -d {} --silent'.format(
            ' '.join(stream_hostnames), 
            ' '.join(hpguppi_auxillary.get_antennalo_name_per_stream_hostnames(stream_hostnames)),
            start_chan,
            n_chan,
            ' '.join(destIps),
            max_nchan_per_packet
          )
          print('meta_args:', meta_args)
        
        hpguppi_populate_meta.populate_meta(
                  stream_hostnames,
                  hpguppi_auxillary.get_antennalo_name_per_stream_hostnames(stream_hostnames),
                  None,
                  n_chans=n_chan,
                  n_bits=8 if stream_is_8bit else 4,
                  start_chan=start_chan,
                  dests=destIps,
                  silent=not new_publication,
                  zero_obs_startstop=False,
                  dry_run=False,
                  max_packet_nchan=max_nchan_per_packet,
                  dut1=True,
                  additional_metadata=additional_metadata,
                  reference_antenna_name=reference_antenna_name
        )
        
        if new_publication:
          print()
        exceptions_caught = 0
      except (RuntimeError, Exception) as e:
        print("Exception: ", e, traceback.format_exc())
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
    for section_idx, not_updated in enumerate(same):
      sections_updated[section_idx] = sections_updated[section_idx] or not not_updated
    have_published = False
  else: # groups and destinations are stable and have published
    pass

  time.sleep(0.5)

  last_groups = groups
  last_destinations = destinations
  last_skyfreq_mapping = skyfreq_mapping
  last_az_el = az_el
  last_eph_source = eph_source
  last_reference_antenna_name = reference_antenna_name
