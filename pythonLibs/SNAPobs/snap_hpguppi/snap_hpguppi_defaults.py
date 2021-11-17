import redis
from string import Template
from SNAPobs import snap_defaults

NBITS              = 4
REDISHOST          = 'redishost'
MAX_CHANS_PER_PKT  = 128

def fengine_meta_key_values(n_bits=8):
	FEnChan = 4096 if n_bits == 4 else 2048 if n_bits == 8 else 0
	BW			= snap_defaults.bw * 1e6 # in Hz
	return {
		'NBITS'	   : n_bits,
		'FENCHAN'  : FEnChan,
		'NPOL'     : 2,
		'TBIN'     : 1/(BW/FEnChan),
		'N_TIMES_PER_PKT' : 16,
		'FOFF'		 : BW / (FEnChan * 1e6) # in Mhz
	}


# BINDHOST           = 'ens6d1'# static once the instance starts
# DATADIR            = '/mnt/buf0' # best left to the configuration (numactl grouping of NVMe mounts)
PROJID             = 'dmpauto'
BACKEND            = 'GUPPI'
BANK               = '.'
PKTFMT             = 'ATASNAPV'
OBSSTART           = 0
OBSSTOP            = 0

REDISGETGW = Template('hashpipe://${host}/${inst}/status')
REDISGETGW_re = r'hashpipe://(?P<host>[^/]+)/(?P<inst>[^/]+)/status'
REDISSETGW = Template('hashpipe://${host}/${inst}/set')
REDISSETGW_re = r'hashpipe://(?P<host>[^/]+)/(?P<inst>[^/]+)/set'
REDISSET = 'hashpipe:///set'

redis_obj = redis.Redis(host=REDISHOST)