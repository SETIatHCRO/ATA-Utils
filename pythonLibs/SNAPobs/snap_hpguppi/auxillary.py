from SNAPobs import snap_config, snap_dada
from . import snap_hpguppi_defaults as hpguppi_defaults
from . import record_in as hpguppi_record_in
import re

# Gather antenna-configuration for the listed snaps
def get_antenna_name_dict_for_stream_hostnames(stream_hostnames):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(snap in list(ATA_SNAP_TAB.snap_hostname) for snap in stream_hostnames):
      raise RuntimeError("Not all snaps (%s) are provided in the config table (%s)",
              stream_hostnames, ATA_SNAP_TAB.snap_hostname)
  stream_hostnames_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname.isin(stream_hostnames)]
  return {i.snap_hostname:i.antlo for i in stream_hostnames_ant_tab.itertuples()}

# Gather antenna-configuration for the listed snaps
def get_stream_hostname_dict_for_antenna_names(antenna_names):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(ant in list(ATA_SNAP_TAB.antlo) for ant in antenna_names):
      raise RuntimeError("Not all antennae (%s) are provided in the config table (%s)",
              antenna_names, ATA_SNAP_TAB.antlo)
  antenna_names_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.antlo.isin(antenna_names)]
  return {i.antlo:i.snap_hostname for i in antenna_names_ant_tab.itertuples()}

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
    snaps = hpguppi_record_in._get_snaps_of_redis_chan(redis_obj, channel)
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
  return redis_hget_retry(redis_obj, redis_chan, 'ANTNAMES').split(',')

def get_snaps_of_redis_chan(redis_obj, redis_chan):
  antennae = get_antennae_of_redis_chan(redis_obj, redis_chan)
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  return [i.snap_hostname for i in ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(antennae)].itertuples()]

def redis_publish_command_from_dict(key_val_dict):
  return "\n".join(['%s=%s' %(key,val)
            for key,val in key_val_dict.items()])