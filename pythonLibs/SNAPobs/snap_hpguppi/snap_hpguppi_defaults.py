import redis
from string import Template
from SNAPobs import snap_defaults

NBITS              = 4
NPOL               = 2
REDISHOST          = 'redishost'
N_TIMES_PER_PKT    = 16
MAX_CHANS_PER_PKT  = 8*8192 // (2*NBITS) // N_TIMES_PER_PKT // 2
FENCHAN            = snap_defaults.nchan
BW                 = snap_defaults.bw * 1e6 # in Hz
FOFF               = snap_defaults.bw / snap_defaults.nchan # in Mhz
TBIN               = 1/(BW/FENCHAN) # in seconds

# BINDHOST           = 'ens6d1'# static once the instance starts
# DATADIR            = '/mnt/buf0' # best left to the configuration (numactl grouping of NVMe mounts)
PROJID             = 'dmpauto'
BACKEND            = 'GUPPI'
BANK               = '.'
PKTFMT             = 'ATASNAPV'
SNAPPAT            = 'frb-snap,-pi'
OBSSTART           = 0
OBSSTOP            = 0

REDISGETGW = Template('hashpipe://${host}/${inst}/status')
REDISGETGW_re = r'hashpipe://(?P<host>[^/]+)/(?P<inst>[^/]+)/status'
REDISSETGW = Template('hashpipe://${host}/${inst}/set')
REDISSETGW_re = r'hashpipe://(?P<host>[^/]+)/(?P<inst>[^/]+)/set'
REDISSET = 'hashpipe:///set'

redis_obj = redis.Redis(host=REDISHOST)