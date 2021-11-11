from SNAPobs import snap_config, snap_dada
from . import snap_hpguppi_defaults as hpguppi_defaults
from . import record_in as hpguppi_record_in
import re

# Gather antenna-names for the listed stream hostnames
def get_antenna_name_dict_for_stream_hostnames(stream_hostnames):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(snap in list(ATA_SNAP_TAB.snap_hostname) for snap in stream_hostnames):
      raise RuntimeError("Not all stream hostnames (%s) are provided in the config table (%s)",
              stream_hostnames, ATA_SNAP_TAB.snap_hostname)
  stream_hostnames_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname.isin(stream_hostnames)]
  return {i.snap_hostname:i.antlo for i in stream_hostnames_ant_tab.itertuples()}

# List antenna-names instead of the given stream names
def get_antenna_name_per_stream_hostnames(stream_hostnames):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(snap in list(ATA_SNAP_TAB.snap_hostname) for snap in stream_hostnames):
      raise RuntimeError("Not all snaps (%s) are provided in the config table (%s)",
              stream_hostnames, ATA_SNAP_TAB.snap_hostname)
  stream_hostnames_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname.isin(stream_hostnames)]
  return [i.antlo for i in stream_hostnames_ant_tab.itertuples()]

# Gather stream hostnames for the listed antenna names
def get_stream_hostname_dict_for_antenna_names(antenna_names):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(ant in list(ATA_SNAP_TAB.antlo) for ant in antenna_names):
      raise RuntimeError("Not all antennae (%s) are provided in the config table (%s)",
              antenna_names, ATA_SNAP_TAB.antlo)
  antenna_names_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.antlo.isin(antenna_names)]
  return {i.antlo:i.snap_hostname for i in antenna_names_ant_tab.itertuples()}

# List stream hostnames instead of the listed antenna names
def get_stream_hostname_per_antenna_names(antenna_names):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(ant in list(ATA_SNAP_TAB.antlo) for ant in antenna_names):
      raise RuntimeError("Not all antennae (%s) are provided in the config table (%s)",
              antenna_names, ATA_SNAP_TAB.antlo)
  antenna_names_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.antlo.isin(antenna_names)]
  return [i.snap_hostname for i in antenna_names_ant_tab.itertuples()]

def redis_get_channel_from_set_channel(set_channel):
  match = re.match(hpguppi_defaults.REDISSETGW_re, set_channel)
  return hpguppi_defaults.REDISGETGW.substitute(host=match.group('host'), inst=match.group('inst'))

def redis_set_channel_from_get_channel(get_channel):
  match = re.match(hpguppi_defaults.REDISGETGW_re, get_channel)
  return hpguppi_defaults.REDISSETGW.substitute(host=match.group('host'), inst=match.group('inst'))

def _generate_hpguppi_redis_channels(hpguppi_hostnames, hpguppi_instance_ids, redisgw_template):
  return [redisgw_template.substitute(host=hostname, inst=instid) 
          for hostname in hpguppi_hostnames for instid in hpguppi_instance_ids]

def generate_hpguppi_redis_set_channels(hpguppi_hostnames, hpguppi_instance_ids):
  return _generate_hpguppi_redis_channels(hpguppi_hostnames, hpguppi_instance_ids, hpguppi_defaults.REDISSETGW)

def generate_hpguppi_redis_get_channels(hpguppi_hostnames, hpguppi_instance_ids):
  return _generate_hpguppi_redis_channels(hpguppi_hostnames, hpguppi_instance_ids, hpguppi_defaults.REDISGETGW)

def generate_freq_auto_string_per_channel(redis_obj, hpguppi_redis_get_channels):
  log_string_per_channel = []
  for channel in hpguppi_redis_get_channels:
    snaps = get_stream_hostnames_of_redis_chan(redis_obj, channel)
    antdict = get_antenna_name_dict_for_stream_hostnames(snaps)
    log_string_per_channel.append(str(snap_dada.get_freq_auto([antdict[snap] for snap in snaps])))
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
      print('Could only collect {}/{} antennae, {} does not exist in channel {}'.format(
        len(antennae_names), antennae_count, 'ANTNMS%02d'%key_enum, redis_chan
      ))
      break
    antennae_names += ant_names.split(',')
  return antennae_names

def get_stream_hostnames_of_redis_chan(redis_obj, redis_chan):
  antennae = get_antennae_of_redis_chan(redis_obj, redis_chan)
  return get_stream_hostname_per_antenna_names(antennae)

def redis_publish_command_from_dict(key_val_dict):
  return "\n".join(['%s=%s' %(key,val)
            for key,val in key_val_dict.items()])

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