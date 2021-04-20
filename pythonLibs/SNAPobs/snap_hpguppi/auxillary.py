from SNAPobs import snap_config
from . import snap_hpguppi_defaults as hpguppi_defaults
import re

# Gather antenna-configuration for the listed snaps
def get_antenna_name_dict_for_snap_hostnames(snap_hostnames):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(snap in list(ATA_SNAP_TAB.snap_hostname) for snap in snap_hostnames):
      raise RuntimeError("Not all snaps (%s) are provided in the config table (%s)",
              snap_hostnames, ATA_SNAP_TAB.snap_hostname)
  snap_hostnames_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname.isin(snap_hostnames)]
  return {i.snap_hostname:i.ANT_name for i in snap_hostnames_ant_tab.itertuples()}

# Gather antenna-configuration for the listed snaps
def get_snap_hostname_dict_for_antenna_names(antenna_names):
  ATA_SNAP_TAB = snap_config.get_ata_snap_tab()
  if not all(ant in list(ATA_SNAP_TAB.ANT_name) for ant in antenna_names):
      raise RuntimeError("Not all antennae (%s) are provided in the config table (%s)",
              antenna_names, ATA_SNAP_TAB.ANT_name)
  antenna_names_ant_tab = ATA_SNAP_TAB[ATA_SNAP_TAB.ANT_name.isin(antenna_names)]
  return {i.ANT_name:i.snap_hostname for i in antenna_names_ant_tab.itertuples()}

def redis_get_channel_from_set_channel(set_channel):
  match = re.match(hpguppi_defaults.REDISSETGW_re, set_channel)
  return hpguppi_defaults.REDISGETGW.substitute(host=match.group('host'), inst=match.group('inst'))