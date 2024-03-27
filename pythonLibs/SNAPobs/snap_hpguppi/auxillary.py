from SNAPobs import snap_config, snap_dada
from . import snap_hpguppi_defaults as hpguppi_defaults
import re
import time

# Gather antenna-names for the listed stream hostnames
def get_antenna_name_dict_for_stream_hostnames(stream_hostnames):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(snap in list(ATA_SNAP_TAB.snap_hostname) for snap in stream_hostnames):
      raise RuntimeError("Not all stream hostnames (%s) are provided in the config table (%s)",
              stream_hostnames, ATA_SNAP_TAB.snap_hostname)
  stream_hostnames_ants = [
    ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname == stream_hostname]
      for stream_hostname in stream_hostnames
  ]
  return {i.iloc[0]['snap_hostname']:i.iloc[0]['antlo'] for i in stream_hostnames_ants}

# List antenna-names instead of the given stream names
def get_antenna_name_per_stream_hostnames(stream_hostnames):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(snap in list(ATA_SNAP_TAB.snap_hostname) for snap in stream_hostnames):
      raise RuntimeError("Not all snaps (%s) are provided in the config table (%s)",
              stream_hostnames, ATA_SNAP_TAB.snap_hostname)
  stream_hostnames_ants = [
    ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname == stream_hostname]
      for stream_hostname in stream_hostnames
  ]
  return [i.iloc[0]['antlo'] for i in stream_hostnames_ants]

# Gather stream hostnames for the listed antenna names
def get_stream_hostname_dict_for_antenna_names(antenna_names):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(ant in list(ATA_SNAP_TAB.antlo) for ant in antenna_names):
      raise RuntimeError("Not all antennae (%s) are provided in the config table (%s)",
              antenna_names, ATA_SNAP_TAB.antlo)
  antenna_names_ants = [
    ATA_SNAP_TAB[ATA_SNAP_TAB.antlo == antenna_name]
      for antenna_name in antenna_names
  ]
  return {i.iloc[0]['antlo']:i.iloc[0]['snap_hostname'] for i in antenna_names_ants}

# List stream hostnames instead of the listed antenna names
def get_stream_hostname_per_antenna_names(antenna_names):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(ant in list(ATA_SNAP_TAB.antlo) for ant in antenna_names):
      raise RuntimeError("Not all antennae (%s) are provided in the config table (%s)",
              antenna_names, ATA_SNAP_TAB.antlo)
  antenna_names_ants = [
    ATA_SNAP_TAB[ATA_SNAP_TAB.antlo == antenna_name]
      for antenna_name in antenna_names
  ]
  return [i.iloc[0]['snap_hostname'] for i in antenna_names_ants]

def redis_get_channel_from_set_channel(set_channel):
  match = re.match(hpguppi_defaults.REDISSETGW_re, set_channel)
  return hpguppi_defaults.REDISGETGW.substitute(
    host=match.group('host'),
    inst=match.group('inst')
  )

def redis_set_channel_from_get_channel(get_channel):
  match = re.match(hpguppi_defaults.REDISGETGW_re, get_channel)
  return hpguppi_defaults.REDISSETGW.substitute(
    host=match.group('host'),
    inst=match.group('inst')
  )

def _generate_hpguppi_redis_channels(
  hpguppi_hostnames,
  hpguppi_instance_ids,
  redisgw_template
):
  return [redisgw_template.substitute(host=hostname, inst=instid) 
          for hostname in hpguppi_hostnames for instid in hpguppi_instance_ids]

def generate_hpguppi_redis_set_channels(
  hpguppi_hostnames,
  hpguppi_instance_ids
):
  return _generate_hpguppi_redis_channels(
    hpguppi_hostnames,
    hpguppi_instance_ids,
    hpguppi_defaults.REDISSETGW
  )

def generate_hpguppi_redis_get_channels(
  hpguppi_hostnames,
  hpguppi_instance_ids
):
  return _generate_hpguppi_redis_channels(
    hpguppi_hostnames,
    hpguppi_instance_ids,
    hpguppi_defaults.REDISGETGW
  )

def generate_freq_auto_string_per_channel(
  redis_obj,
  hpguppi_redis_get_channels
):
  log_string_per_channel = []
  for channel in hpguppi_redis_get_channels:
    snaps = get_stream_hostnames_of_redis_chan(redis_obj, channel)
    antdict = get_antenna_name_dict_for_stream_hostnames(snaps)
    log_string_per_channel.append(
      str(snap_dada.get_freq_auto([antdict[snap] for snap in snaps]))
    )
  return log_string_per_channel

def redis_hget_retry(redis_obj, redis_chan, key, retry_count=5):
  value = None
  while value is None and retry_count > 0:
    try:
      value = redis_obj.hget(redis_chan, key).decode()
    except:
      pass
    retry_count -= 1
  return value

def get_antennae_of_redis_chan(redis_obj, redis_chan):
  antennae_names = redis_hget_retry(redis_obj, redis_chan, 'ANTNAMES')
  if antennae_names is None:
    antennae_names = []
  else:
    antennae_names = antennae_names.split(',')
  
  antennae_count = redis_hget_retry(redis_obj, redis_chan, 'NANTS')
  if antennae_count is None:
    antennae_count = 0
  else:
    antennae_count = int(antennae_count)
  key_enum = 0
  while(antennae_count > len(antennae_names)):
    key_enum += 1
    ant_names = redis_hget_retry(redis_obj, redis_chan, 'ANTNMS%02d'%key_enum)
    if ant_names is None:
      print(
        ('Could only collect {}/{} antennae, '
          '{} does not exist in channel {}').format(
          len(antennae_names), antennae_count, 'ANTNMS%02d'%key_enum, redis_chan
        )
      )
      break
    antennae_names += ant_names.split(',')
  return antennae_names

def get_stream_hostnames_of_redis_chan(redis_obj, redis_chan):
  antennae = get_antennae_of_redis_chan(redis_obj, redis_chan)
  return get_stream_hostname_per_antenna_names(antennae)

def redis_hashpipe_channels_from_dict(
  hashpipe_targets,
  set_channels=True,
  postproc=False
):
  '''
  Parameters
  ----------
  hashpipe_targets: dict
    expected to be of form {hostname: [instance_num]}
  set_channels: bool
    switch to template set channels or get channels
  postproc: bool
    switch to template channels for hashpipe or postproc
  
  Returns
  -------
  list: hashpipe set redis-channels (from `hpguppi_defaults.REDISSETGW` 
    template, or `hpguppi_defaults.REDISPOSTPROCHASH`)
  '''
  redis_channel_list = []
  template = hpguppi_defaults.REDISSETGW if set_channels else hpguppi_defaults.REDISGETGW
  if postproc:
    template = hpguppi_defaults.REDISPOSTPROCHASH
  for (hostname, instance_num_list) in hashpipe_targets.items():
        for instance_num in instance_num_list:
            redis_channel_list.append(
              template.substitute(
                host=hostname, 
                inst=instance_num
              )
            )
  return redis_channel_list

def redis_publish_command_from_dict(key_val_dict):
  return "\n".join(['%s=%s' %(key,val)
            for key,val in key_val_dict.items()])

def publish_keyval_dict_to_redis(
  keyval_dict,
  targets,
  postproc=False,
  dry_run=False
):
  '''
  Will determine if the targets are channels or hashes, and populate
  with the keyval_dict's items.

  Parameters
  ----------
  keyval_dict: dict
    key-str(value) pairs to populate to targets
  targets: list,dict
    If a list, then expected to be a list of redis channels or hashes to 
    populate with the keyvals.
    If a dict, then expected to be of form {hostname: [instance_num]} to 
    populate with the keyvals.
  postproc: bool
    Passed through to redis_hashpipe_channels_from_dict if targets is dict 
  dry_run: bool
    Whether or not to publish the keys, or just print
  '''

  print(keyval_dict)
  redis_publish_command = redis_publish_command_from_dict(keyval_dict)
  redis_pubsub_channels = [
    chan.decode()
      for chan in hpguppi_defaults.redis_obj.pubsub_channels()
  ]
  
  if isinstance(targets, dict):
    targets = redis_hashpipe_channels_from_dict(targets, postproc=postproc)
  
  print('Publishing to:')
  for target in targets:
    if target in redis_pubsub_channels:
      print('\t@', target)
      if dry_run:
        print('*** Dry Run ***')
      else:
        hpguppi_defaults.redis_obj.publish(
          target,
          redis_publish_command
        )
    else:
      print('\t# ', target)
      if dry_run:
        print('*** Dry Run ***')
      else:
        hpguppi_defaults.redis_obj.hset(target, mapping=keyval_dict)


def _block_until_key_has_value(targets, key, value, verbose=True):
    '''
    Loop (block) until the key in all the targets match the value given.

    Parameters
    ----------
    targets: list,dict
      Specifies the redis hashes to consult the key in.
      Expected to be a list of redis channels or hashes to populate with the
      keyvals.
    key: str
        The key, the value of which is to be consulted
    value: str,regex
        The value to be matched (uses `re.fullmatch`)
    verbose: bool
        Whether or not to print the values while blocking
    '''
    len_per_value = 80//len(targets)
    value_slice = slice(-len_per_value, None)

    while True:
      rr = [hpguppi_defaults.redis_obj.hget(hsh, key) for hsh in targets]
      rets = [r.decode() if(r) else 'NONE' for r in rr]
      if verbose:
        print_strings = [
          ('{: ^%d}'%len_per_value).format(ret[value_slice]) for ret in rets
        ]
        print('[{: ^80}]'.format(', '.join(print_strings)), end='\r')
      if all([re.fullmatch(value, ret) for ret in rets]):
        if verbose:
          print()
        break
      time.sleep(1)

def filter_unique_fengines(feng_objs):
    host_unique_fengs = {}
    for feng in feng_objs:
      host_name = feng.host
      if host_name.startswith('rfsoc'):
        rfsoc_match = re.match(r'(rfsoc\d+.*)-(\d+)$', host_name)
        if int(rfsoc_match.group(2)) < 5:
          host_name = rfsoc_match.group(1) + '-1'
        else:
          host_name = rfsoc_match.group(1) + '-4'
      if host_name not in host_unique_fengs:
        host_unique_fengs[host_name] = feng
    return list(host_unique_fengs.values())

def filter_unique_hostnames(host_names):
    unique_host_names = {}
    for full_host_name in host_names:
      host_name = full_host_name
      if host_name.startswith('rfsoc'):
        rfsoc_match = re.match(r'(rfsoc\d+.*)-(\d+)$', host_name)
        if int(rfsoc_match.group(2)) < 5:
          host_name = rfsoc_match.group(1) + '-1'
        else:
          host_name = rfsoc_match.group(1) + '-4'
      if host_name not in unique_host_names:
        unique_host_names[host_name] = full_host_name
    return list(unique_host_names.values())